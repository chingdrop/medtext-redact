#!/usr/bin/env python3
"""
One-page results sheet for the README: what the redactor does to synthetic
clinical notes, and its recall/precision per identifier category.

Every number and example comes from one run of the recall/precision suite
(tests/e2e/test_recall_precision.py), which writes its results as JSON when
MEDTEXT_RESULTS_JSON is set -- nothing on the sheet is typed in by hand.

    uv run python tools/results_sheet.py                            # HTML only
    uv run python tools/results_sheet.py --png docs/results-sheet.png

It runs the suite itself unless given `--results` (a JSON file from an
earlier run). `--png` finds Chrome, Chromium, Edge, or Brave on its own --
including the Chromium vhs downloads for docs/demo.tape -- or takes
`--chrome <path>`, and also needs ffmpeg. Synthetic data only.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
WIDTH = 1400  # CSS px; the sheet's body width
SCALE = 2  # device pixel ratio of the PNG

HIGHLIGHT_PREFIX = "highlight_"

# Groups and labels for the per-category table, in display order. A category
# missing here still appears, under "Other", so a new detector can't vanish.
GROUPS: list[tuple[str, list[tuple[str, str]]]] = [
    (
        "Names",
        [
            ("name", "Surname in the gazetteer"),
            ("name_ungazetteered", "Surname not in the gazetteer"),
            ("name_firstname_only", "Bare first name"),
        ],
    ),
    (
        "Dates and ages",
        [
            ("date", "Date (MM/DD/YYYY family)"),
            ("date_mismatched_sep", "Date, mismatched separators"),
            ("date_out_of_range", "Date before 1900"),
            ("age", "Age"),
            ("age_bare_number", "Age as a bare number"),
            ("gender", "Gender term"),
        ],
    ),
    (
        "Contact and location",
        [
            ("phone", "Phone number"),
            ("address", "Street address"),
            ("email", "Email address"),
            ("url", "URL"),
            ("ip_address", "IP address"),
        ],
    ),
    (
        "Record and government IDs",
        [
            ("mrn", "Medical record number"),
            ("ssn", "US Social Security number"),
            ("itin", "US ITIN"),
            ("driver_license", "Driver's license"),
            ("passport", "Passport"),
            ("medical_license", "DEA registration"),
            ("nhs_number", "UK NHS number"),
            ("mac_address", "MAC address (device)"),
        ],
    ),
    (
        "Financial",
        [
            ("credit_card", "Credit card"),
            ("bank_account", "Bank account"),
            ("iban", "IBAN"),
            ("crypto_wallet", "Crypto wallet"),
        ],
    ),
]
HIGHLIGHT_LABELS = {
    "highlight_symptom": "Symptoms",
    "highlight_diagnosis": "Diagnoses",
    "highlight_medication": "Medications",
}
# Look-alikes that aren't PHI: the suite counts any masking as a false positive.
DECOY_LABELS = {
    "name_common_word": 'Surname used as a word ("Grace period")',
    "date_space_sep": 'A count, not a date ("rechecked 9 28 1952 times")',
    "age_out_of_range": "A tracking number above 150, not an age",
}
# Notes shown before and after, by template: demographics, billing, identity.
EXAMPLE_TEMPLATES = [0, 10, 11]


def _pct(x: float | None) -> str:
    return "n/a" if x is None else f"{100 * x:.0f}%"


def _between(text: str, original: str | None) -> str:
    """Text outside any scored span. In the redacted line, mark runs that were
    masked although the original there wasn't a labeled identifier."""
    if original is None:
        return html.escape(text)
    out, run = [], []
    for got, was in zip(text, original, strict=True):
        if got == "*" and was != "*":
            run.append(got)
            continue
        if run:
            out.append(f"<span class='over'>{''.join(run)}</span>")
            run = []
        out.append(html.escape(got))
    if run:
        out.append(f"<span class='over'>{''.join(run)}</span>")
    return "".join(out)


def _marked(text: str, spans: list[dict[str, Any]], *, original: str | None = None) -> str:
    """`text` as HTML, with each scored span wrapped by its kind and outcome.
    Pass the note's `original` text when `text` is its redacted rendering."""
    rendered = original is not None
    out, pos = [], 0
    for span in sorted(spans, key=lambda s: s["start"]):
        out.append(_between(text[pos : span["start"]], original[pos : span["start"]] if original else None))
        piece = html.escape(text[span["start"] : span["end"]])
        if span["category"].startswith(HIGHLIGHT_PREFIX):
            kind = "term"
        elif span["expected_redacted"]:
            kind = "phi" if span["hit"] else "phi miss"
        else:
            kind = "decoy fp" if span["hit"] else "decoy"
        out.append(f"<span class='{kind}{' out' if rendered else ''}'>{piece}</span>")
        pos = span["end"]
    out.append(_between(text[pos:], original[pos:] if original else None))
    return "".join(out)


def _row(label: str, r: dict[str, Any]) -> str:
    recall = r["recall"]
    width = 0 if recall is None else 100 * recall
    ok = recall == 1.0 and r["precision"] in (1.0, None)
    return f"""
      <div class="cat">
        <div class="cat-name">{html.escape(label)}</div>
        <div class="bar"><div class="fill{"" if ok else " short"}" style="width:{width:.1f}%"></div></div>
        <div class="n">{_pct(recall)}</div>
        <div class="n muted">{_pct(r["precision"])}</div>
        <div class="counts">{r["tp"]} of {r["tp"] + r["fn"]}</div>
      </div>"""


def build(data: dict[str, Any]) -> str:
    results: dict[str, dict[str, Any]] = data["results"]
    phi = {c: r for c, r in results.items() if not c.startswith(HIGHLIGHT_PREFIX) and r["tp"] + r["fn"] > 0}
    terms = {c: r for c, r in results.items() if c.startswith(HIGHLIGHT_PREFIX)}

    found = sum(r["tp"] for r in phi.values())
    total = sum(r["tp"] + r["fn"] for r in phi.values())
    perfect = sum(r["recall"] == 1.0 for r in phi.values())
    terms_kept = sum(r["tp"] for r in terms.values())
    terms_total = sum(r["tp"] + r["fn"] for r in terms.values())
    decoys = {c: results[c] for c in DECOY_LABELS if c in results}
    decoy_fp = sum(r["fp"] for r in decoys.values())
    decoy_total = sum(r["fp"] + r["tn"] for r in decoys.values())

    # -- per-category table ------------------------------------------------------
    grouped: set[str] = set()
    groups_html = []
    for title, cats in GROUPS:
        rows = [_row(label, phi[c]) for c, label in cats if c in phi]
        grouped.update(c for c, _ in cats)
        if rows:
            groups_html.append(f"<div class='group'><h3>{html.escape(title)}</h3>{''.join(rows)}</div>")
    other = [_row(c, r) for c, r in sorted(phi.items()) if c not in grouped]
    if other:
        groups_html.append(f"<div class='group'><h3>Other</h3>{''.join(other)}</div>")
    half = (len(groups_html) + 1) // 2
    columns = "".join(f"<div>{CAT_HEAD}{''.join(col)}</div>" for col in (groups_html[:half], groups_html[half:]))
    term_rows = "".join(_row(HIGHLIGHT_LABELS.get(c, c), r) for c, r in sorted(terms.items()))

    decoy_rows = "".join(
        f"""
      <div class="decoy-row">
        <div>{html.escape(DECOY_LABELS[c])}</div>
        <div class="n{" bad" if r["fp"] else ""}">{r["fp"]} of {r["fp"] + r["tn"]} masked</div>
      </div>"""
        for c, r in decoys.items()
    )

    # -- before and after --------------------------------------------------------
    by_template = {n["template_index"]: n for n in data["notes"]}
    examples = []
    for t in EXAMPLE_TEMPLATES:
        note = by_template.get(t)
        if note is None:
            continue
        examples.append(
            f"""
      <div class="example">
        <div class="lbl">Synthetic note</div>
        <div class="text">{_marked(note["text"], note["spans"])}</div>
        <div class="lbl">Redacted</div>
        <div class="text mono">{_marked(note["rendered"], note["spans"], original=note["text"])}</div>
      </div>"""
        )

    return TEMPLATE.format(
        seed=data["seed"],
        note_count=data["note_count"],
        template_count=data["template_count"],
        found=found,
        total=total,
        perfect=perfect,
        categories=len(phi),
        terms_kept=terms_kept,
        terms_total=terms_total,
        decoy_fp=decoy_fp,
        decoy_total=decoy_total,
        examples="".join(examples),
        groups=columns,
        terms=term_rows,
        decoys=decoy_rows,
    )


CAT_HEAD = (
    "<div class='cat-head'><div></div><div></div><div class='n'>recall</div>"
    "<div class='n'>precision</div><div class='counts'>masked</div></div>"
)

TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Redaction results</title>
<style>
  :root {{
    --surface: #fcfcfb; --card: #ffffff; --line: #e6e4df;
    --ink: #0b0b0b; --ink-2: #52514e; --ink-3: #8a8984;
    --phi: #2a78d6; --phi-bg: #e3eefb; --term: #f5c518; --term-bg: #fdf3c4;
    --good: #0ca30c; --good-ink: #006300; --bad: #d03b3b; --bad-bg: #fbe3e3;
    --over: #a9a8a3; --over-bg: #eeede9;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--surface); color: var(--ink); width: 1400px; min-height: 100vh;
         font: 15px/1.45 -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", sans-serif;
         padding: 44px 48px 36px; }}
  .muted {{ color: var(--ink-3); }}
  header {{ display: flex; justify-content: space-between; align-items: flex-end;
           border-bottom: 1px solid var(--line); padding-bottom: 20px; }}
  .eyebrow {{ font-size: 12px; letter-spacing: .08em; text-transform: uppercase;
             color: var(--ink-2); font-weight: 600; }}
  h1 {{ font-size: 30px; font-weight: 700; letter-spacing: -.01em; margin-top: 4px; }}
  .meta {{ text-align: right; color: var(--ink-2); font-size: 13px; line-height: 1.6; }}
  .meta b {{ color: var(--ink); font-weight: 600; }}
  .badge {{ display: inline-block; background: #f0efec; color: var(--ink-2);
           border-radius: 4px; padding: 1px 7px; font-size: 12px; font-weight: 600; }}

  .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 24px 0; }}
  .stat {{ background: var(--card); border: 1px solid var(--line); border-radius: 10px;
          padding: 16px 18px; }}
  .stat .v {{ font-size: 30px; font-weight: 700; letter-spacing: -.01em;
             font-variant-numeric: tabular-nums; }}
  .stat .v small {{ font-size: 16px; color: var(--ink-2); font-weight: 600; }}
  .stat .l {{ color: var(--ink-2); font-size: 13px; margin-top: 2px; }}

  h2 {{ font-size: 13px; letter-spacing: .08em; text-transform: uppercase;
       color: var(--ink-2); font-weight: 700; margin-bottom: 12px; }}
  section {{ background: var(--card); border: 1px solid var(--line); border-radius: 10px;
            padding: 20px 22px; margin-bottom: 16px; }}
  .legend {{ display: flex; gap: 18px; font-size: 12.5px; color: var(--ink-2); margin: -4px 0 12px; }}
  .legend i {{ display: inline-block; width: 10px; height: 10px; border-radius: 2px;
              margin-right: 6px; vertical-align: -1px; }}

  .example {{ display: grid; grid-template-columns: 120px 1fr; gap: 4px 14px; padding: 12px 0;
             border-bottom: 1px solid #f0efec; }}
  .example:last-child {{ border-bottom: 0; }}
  .lbl {{ font-size: 12px; color: var(--ink-3); padding-top: 2px; }}
  .text {{ font-size: 14.5px; }}
  .mono {{ font-family: ui-monospace, Menlo, monospace; font-size: 13.5px; }}
  .phi {{ background: var(--phi-bg); border-bottom: 2px solid var(--phi); border-radius: 2px; }}
  .phi.out {{ background: var(--phi); color: #fff; }}
  .phi.miss {{ background: var(--bad-bg); border-bottom-color: var(--bad); }}
  .term {{ background: var(--term-bg); border-bottom: 2px solid var(--term); border-radius: 2px; }}
  .decoy {{ border-bottom: 2px dotted var(--ink-3); }}
  .over {{ background: var(--over-bg); border-bottom: 2px solid var(--over); border-radius: 2px; }}
  .decoy.fp {{ background: var(--bad-bg); border-bottom: 2px solid var(--bad); }}

  .two {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
  .two section {{ margin-bottom: 0; }}
  .groups {{ display: grid; grid-template-columns: 1fr 1fr; gap: 40px; }}
  .group {{ margin-bottom: 14px; }}
  h3 {{ font-size: 13px; font-weight: 700; margin-bottom: 4px; }}
  .cat-head, .cat {{ display: grid; grid-template-columns: 180px 1fr 44px 44px 58px; gap: 10px;
                    align-items: center; font-size: 13px; }}
  .cat-head {{ font-size: 11.5px; color: var(--ink-3); border-bottom: 1px solid var(--line);
              padding-bottom: 4px; margin-bottom: 8px; }}
  .cat {{ padding: 3px 0; }}
  .bar {{ height: 9px; background: #f0efec; border-radius: 3px; overflow: hidden; }}
  .fill {{ height: 100%; background: var(--good); }}
  .fill.short {{ background: var(--bad); }}
  .n {{ text-align: right; font-variant-numeric: tabular-nums; font-weight: 600; }}
  .counts {{ text-align: right; color: var(--ink-3); font-size: 12px;
            font-variant-numeric: tabular-nums; }}
  .decoy-row {{ display: grid; grid-template-columns: 1fr auto; gap: 12px; font-size: 13px;
               padding: 6px 0; border-bottom: 1px solid #f0efec; }}
  .decoy-row:last-child {{ border-bottom: 0; }}
  .decoy-row .n.bad {{ color: var(--bad); }}
  .note {{ font-size: 12px; color: var(--ink-3); margin-top: 10px; }}

  footer {{ display: flex; justify-content: space-between; color: var(--ink-3);
           font-size: 12px; margin-top: 18px; }}
</style></head>
<body>
  <header>
    <div>
      <div class="eyebrow">Clinical text de-identification &middot; Microsoft Presidio</div>
      <h1>Redaction results on synthetic clinical notes</h1>
    </div>
    <div class="meta">
      <span class="badge">Synthetic data only</span> &nbsp;seed <b>{seed}</b><br>
      <b>{note_count}</b> notes from <b>{template_count}</b> templates
    </div>
  </header>

  <div class="stats">
    <div class="stat"><div class="v">{found}<small> / {total}</small></div>
      <div class="l">identifiers masked</div></div>
    <div class="stat"><div class="v">{perfect}<small> / {categories}</small></div>
      <div class="l">identifier categories at 100% recall</div></div>
    <div class="stat"><div class="v">{terms_kept}<small> / {terms_total}</small></div>
      <div class="l">clinical terms kept readable and highlighted</div></div>
    <div class="stat"><div class="v">{decoy_fp}<small> / {decoy_total}</small></div>
      <div class="l">look-alike decoys masked (false positives)</div></div>
  </div>

  <section>
    <h2>Before and after</h2>
    <div class="legend">
      <span><i style="background:var(--phi)"></i>identifier, masked</span>
      <span><i style="background:var(--term)"></i>clinical term, highlighted with --keywords</span>
      <span><i style="background:var(--bad)"></i>missed identifier or masked decoy</span>
      <span><i style="background:var(--over)"></i>masked, though not a labeled identifier</span>
    </div>
    {examples}
  </section>

  <section>
    <h2>Recall by identifier category</h2>
    <div class="groups">{groups}</div>
  </section>

  <div class="two">
      <section>
        <h2>Clinical terms</h2>
        <div class="cat-head"><div></div><div></div><div class="n">recall</div>
          <div class="n">precision</div><div class="counts">kept</div></div>
        {terms}
        <div class="note">Masking must leave these readable so --keywords can highlight them.</div>
      </section>
      <section>
        <h2>Known false positives</h2>
        {decoys}
        <div class="note">Look-alikes that aren't PHI. Recall comes first, so these are reported,
          not tuned away; see docs/limitations-and-roadmap.md.</div>
      </section>
  </div>

  <footer>
    <span>Built by tools/results_sheet.py from one run of tests/e2e/test_recall_precision.py.</span>
    <span>Synthetic templates only: recall on real clinical text is lower; see docs/threat-model.md.</span>
  </footer>
</body></html>
"""


def run_suite(results_json: Path) -> None:
    """Run the recall/precision suite, which writes its results to `results_json`."""
    env = {**os.environ, "MEDTEXT_RESULTS_JSON": str(results_json)}
    subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests/e2e/test_recall_precision.py"],
        cwd=REPO,
        env=env,
        check=True,
    )


# Browser lookup and the screenshot crop are adapted from medicare-rebuild's
# tools/audit_sheet.py.
BROWSERS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
]


def find_browser() -> str | None:
    """A Chromium-based browser that can screenshot headlessly: a known install, one
    on PATH, or the Chromium vhs (via go-rod) downloads for recording demo.tape."""
    for candidate in BROWSERS:
        found = shutil.which(candidate) or (candidate if Path(candidate).is_file() else None)
        if found:
            return found
    for root in sorted(Path.home().glob(".cache/rod/browser/chromium-*"), reverse=True):
        for exe in (root / "Chromium.app/Contents/MacOS/Chromium", root / "chrome"):
            if exe.is_file():
                return str(exe)
    return None


def render_png(page: Path, png: Path, chrome: str, margin: int = 32) -> None:
    """Screenshot `page` in a deliberately tall headless window, crop to the last row
    that differs from the background plus `margin` CSS px, and reduce the result to a
    256-color palette: the sheet is flat colors and text, and this keeps it small."""
    with tempfile.TemporaryDirectory() as tmp:
        shot = Path(tmp) / "tall.png"
        subprocess.run(
            [
                chrome,
                "--headless=new",
                "--hide-scrollbars",
                f"--force-device-scale-factor={SCALE}",
                f"--window-size={WIDTH},2400",
                f"--screenshot={shot}",
                page.resolve().as_uri(),
            ],
            check=True,
            capture_output=True,
        )
        gray = subprocess.run(
            ["ffmpeg", "-loglevel", "error", "-i", str(shot), "-f", "rawvideo", "-pix_fmt", "gray", "-"],
            check=True,
            capture_output=True,
        ).stdout
        w = WIDTH * SCALE
        background = gray[0]
        last = max(
            y for y in range(len(gray) // w) if any(abs(b - background) > 6 for b in gray[y * w : (y + 1) * w : 2])
        )
        crop = f"crop=iw:{last + 1 + margin * SCALE}:0:0"
        subprocess.run(
            ["ffmpeg", "-loglevel", "error", "-y", "-i", str(shot), "-vf",
             f"{crop},split[a][b];[a]palettegen=max_colors=256[p];[b][p]paletteuse=dither=none", str(png)],
            check=True,
        )  # fmt: skip


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results", type=Path, help="Results JSON from an earlier suite run (default: run it now)")
    ap.add_argument("--out", type=Path, default=Path("results-sheet.html"), help="HTML output path")
    ap.add_argument("--png", type=Path, help="Also render a PNG here")
    ap.add_argument("--chrome", help="Chrome/Chromium binary (default: look for one)")
    a = ap.parse_args()

    if a.results:
        data = json.loads(a.results.read_text(encoding="utf-8"))
    else:
        with tempfile.TemporaryDirectory() as tmp:
            results_json = Path(tmp) / "results.json"
            run_suite(results_json)
            data = json.loads(results_json.read_text(encoding="utf-8"))

    a.out.write_text(build(data), encoding="utf-8")
    print(f"Wrote {a.out}")
    if a.png:
        chrome = a.chrome or find_browser()
        if not chrome or not (shutil.which(chrome) or Path(chrome).is_file()):
            raise SystemExit(
                f"no browser found{f' at {chrome}' if chrome else ''}: install Chrome "
                "or Chromium, or pass --chrome <path> to one"
            )
        render_png(a.out, a.png, chrome)
        print(f"Wrote {a.png} (rendered with {chrome})")


if __name__ == "__main__":
    main()
