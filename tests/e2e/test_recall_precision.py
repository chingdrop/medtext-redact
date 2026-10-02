"""
End-to-end recall/precision test: generates synthetic notes via
tools/gen_fixtures.py, runs the existing `parse-report single` CLI command
(the actual redact + highlight code path), and compares the result against
the generator's independent ground-truth manifest.

Recall is the metric that matters most for a redaction tool -- a missed
identifier is the dangerous failure mode -- so this file never tunes
thresholds or trims hard cases to make a number look better.
"""

import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path

import pytest
from click.testing import CliRunner

from medtext_redact.commands.reports import parse_report
from medtext_redact.core import text_tools

TOOLS_DIR = Path(__file__).resolve().parents[2] / "tools"
_spec = importlib.util.spec_from_file_location("gen_fixtures", TOOLS_DIR / "gen_fixtures.py")
gen_fixtures = importlib.util.module_from_spec(_spec)
sys.modules["gen_fixtures"] = gen_fixtures
_spec.loader.exec_module(gen_fixtures)

SEED = 20260925
# A multiple of the template count, so every template appears equally often.
NOTE_COUNT = 48

HIGHLIGHT_PREFIX = "highlight_"
HIGHLIGHT_START = "\x1b[1;33m"
HIGHLIGHT_END = "\x1b[0m"


def extract_highlights(raw: str) -> tuple[str, list[tuple[int, int]]]:
    """Strip Rich's SGR codes, returning the plain text and each highlighted run's span.

    `Console(force_terminal=True)` word-wraps its output at its rendered
    width, breaking the line at whatever space it wraps on. It isn't
    consistent about whether it *keeps* that space and adds a `\\n` next to
    it, or *consumes* the space and leaves only the `\\n` -- so a wrapped
    "a b" can come back as either "a \\nb" or "a\\nb". Since these single-line
    generated notes never contain a real newline, every `\\n` found here is a
    wrap artifact standing in for exactly one space: emit a space for it
    only if one isn't already there, so the reconstructed text stays
    character-for-character aligned with the manifest's offsets either way.
    """
    plain: list[str] = []
    ranges: list[tuple[int, int]] = []
    i = 0
    n = len(raw)
    start = None
    while i < n:
        if raw.startswith(HIGHLIGHT_START, i):
            start = len(plain)
            i += len(HIGHLIGHT_START)
            continue
        if raw.startswith(HIGHLIGHT_END, i):
            if start is not None:
                ranges.append((start, len(plain)))
                start = None
            i += len(HIGHLIGHT_END)
            continue
        if raw[i] == "\n":
            if not plain or plain[-1] != " ":
                plain.append(" ")
            i += 1
            continue
        plain.append(raw[i])
        i += 1

    plain_text = "".join(plain)
    # A highlighted match that straddles a wrap point comes back as two
    # adjacent styled runs (e.g. "low-grade " + "fever"); merge runs
    # separated only by whitespace back into one contiguous range.
    ranges.sort()
    merged: list[list[int]] = []
    for r in ranges:
        if merged and plain_text[merged[-1][1] : r[0]].strip() == "":
            merged[-1][1] = r[1]
        else:
            merged.append(list(r))
    return plain_text, [(s, e) for s, e in merged]


def run_single(runner: CliRunner, config_path: str, text: str, keywords: list[str]) -> str:
    args = ["--config", config_path, "single", "--text", text, "--verbose"]
    for kw in keywords:
        args += ["--keywords", kw]
    outcome = runner.invoke(parse_report, args)
    assert outcome.exit_code == 0, outcome.output
    return outcome.output


def is_fully_masked(rendered: str, span_text: str, start: int, end: int) -> bool:
    """True only if every alnum character in the span became '*' -- a partial
    leak still counts as a miss, matching the recall-first standard."""
    window = rendered[start:end]
    if len(window) != len(span_text):
        return False
    return all((c == "*") for orig, c in zip(span_text, window, strict=True) if orig.isalnum())


def is_fully_highlighted(ranges: list[tuple[int, int]], start: int, end: int) -> bool:
    return any(rs <= start and re_ >= end for rs, re_ in ranges)


@pytest.fixture()
def config_path(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"Masking": {"Manufacturers": [], "Locations": []}}), encoding="utf-8")
    return str(path)


@pytest.fixture(autouse=True)
def stubbed_gazetteer(monkeypatch):
    """Stub the census surname gazetteer to exactly what the generator injects.

    This isolates the masking *mechanism's* correctness from the census
    data's real-world coverage (a separate, external data-quality question)
    -- the same pattern the unit tests already use via `fake_census_names`.
    """
    monkeypatch.setattr(text_tools, "load_census_names", lambda: gen_fixtures.GAZETTEER_SURNAMES)


def all_vocab_keywords() -> list[str]:
    vocab = gen_fixtures.CLINICAL_VOCAB
    return [*vocab["symptom"], *vocab["diagnosis"], *vocab["medication"]]


def test_recall_and_precision_by_category(config_path, capsys):
    runner = CliRunner()
    notes = gen_fixtures.generate_notes(seed=SEED, count=NOTE_COUNT)
    keywords = all_vocab_keywords()

    # category -> counts
    tp = defaultdict(int)
    fn = defaultdict(int)
    fp = defaultdict(int)
    tn = defaultdict(int)
    misses: list[str] = []
    false_positives: list[str] = []

    for note in notes:
        output = run_single(runner, config_path, note["text"], keywords)
        # Strip the fixed CLI preamble and the single trailing newline
        # console.print adds, isolating exactly the rendered note content.
        preamble = ("-" * 104) + "\n\n" + "Verbose mode is on.\n"
        assert output.startswith(preamble), output
        body = output[len(preamble) :]
        assert body.endswith("\n"), repr(body)
        body = body[:-1]

        rendered, highlight_ranges = extract_highlights(body)

        for span in note["spans"]:
            category = span["category"]
            start, end, text = span["start"], span["end"], span["text"]

            if category.startswith(HIGHLIGHT_PREFIX):
                hit = is_fully_highlighted(highlight_ranges, start, end)
            else:
                hit = is_fully_masked(rendered, text, start, end)

            if span["expected_redacted"]:
                if hit:
                    tp[category] += 1
                else:
                    fn[category] += 1
                    misses.append(f"note {note['note_id']} [{category}] missed: {text!r} ({span['note']})")
            else:
                if hit:
                    fp[category] += 1
                    false_positives.append(
                        f"note {note['note_id']} [{category}] false positive: {text!r} ({span['note']})"
                    )
                else:
                    tn[category] += 1

    categories = sorted(set(tp) | set(fn) | set(fp) | set(tn))
    report_lines = [f"{'category':22s} {'recall':>8s} {'precision':>10s} {'TP':>4s} {'FN':>4s} {'FP':>4s} {'TN':>4s}"]
    results = {}
    for cat in categories:
        n_tp, n_fn, n_fp, n_tn = tp[cat], fn[cat], fp[cat], tn[cat]
        recall = n_tp / (n_tp + n_fn) if (n_tp + n_fn) else None
        precision = n_tp / (n_tp + n_fp) if (n_tp + n_fp) else None
        results[cat] = {"recall": recall, "precision": precision, "tp": n_tp, "fn": n_fn, "fp": n_fp, "tn": n_tn}
        recall_s = f"{recall:.0%}" if recall is not None else "n/a"
        precision_s = f"{precision:.0%}" if precision is not None else "n/a"
        report_lines.append(f"{cat:22s} {recall_s:>8s} {precision_s:>10s} {n_tp:>4d} {n_fn:>4d} {n_fp:>4d} {n_tn:>4d}")

    if misses:
        report_lines.append("\nMisses:")
        report_lines.extend(f"  {m}" for m in misses)
    if false_positives:
        report_lines.append("\nFalse positives:")
        report_lines.extend(f"  {m}" for m in false_positives)

    report = "\n".join(report_lines)
    with capsys.disabled():
        print("\n" + report)

    # Presidio's NER plus the ported rule recognizers: perfect recall and
    # precision on every category with a detector, including what NER adds
    # over the old rules -- names regardless of gazetteer coverage and dates
    # in any format.
    for cat in [
        "name",
        "name_ungazetteered",
        "date",
        "date_mismatched_sep",
        "date_out_of_range",
        "age",
        "gender",
        "phone",
        "address",
        "mrn",
        "email",
        "ssn",
        "url",
        "ip_address",
        "credit_card",
        "bank_account",
        "driver_license",
        "passport",
        "itin",
        "medical_license",
        "iban",
        "crypto_wallet",
        "mac_address",
        "nhs_number",
        "highlight_symptom",
        "highlight_medication",
        "highlight_diagnosis",
    ]:
        assert results[cat]["recall"] == 1.0, f"{cat}: {results}"
        assert results[cat]["precision"] == 1.0, f"{cat}: {results}"
    assert results["age_out_of_range"]["fp"] == 0, f"unexpected false positive for age_out_of_range: {results}"

    # Reported, not gated:
    # - "name_firstname_only": caught by NER alone (the gazetteer is
    #   surnames only), so it varies with which names the generator draws.
    # - "name_common_word": the surname gazetteer masks "Grace period", as
    #   the old rules-only engine did. spaCy's parse could filter it ("Grace" modifies a
    #   noun there), but the same filter would drop real names in phrases
    #   like "the Okafor family", and recall comes first.
    # - "date_space_sep": the bare-number age pattern masks the small
    #   numbers and spaCy's date entity takes the year, so the union covers
    #   the whole triplet. The old rules-only engine left the year visible.
    # - "age_bare_number": masked by the age pattern's documented design (a
    #   bare in-range number is treated as a possible age), not a bug.
    for cat in ["name_firstname_only", "name_common_word", "date_space_sep", "age_bare_number"]:
        assert cat in results
