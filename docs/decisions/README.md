# Architecture decision records

Lightweight [MADR](https://adr.github.io/madr/)-style records of the significant, load-bearing decisions behind this repository's current design. Each one is drafted only from what this repository actually records — the code, tests, README.md, `docs/provenance-and-data-boundary.md`, `CLAUDE.md`, and `git log` commit bodies — not from memory or invented rationale. Where the repository doesn't record *why* a choice was made, the record says so with a `TODO(craig)` marker rather than guessing.

| # | Title | Status |
|---|---|---|
| [0001](0001-rule-based-detection-not-ner.md) | Rule-based detection, not NER | Superseded by 0007 |
| [0002](0002-gazetteer-based-name-detection.md) | Gazetteer-based name detection, and its documented limits | Accepted, amended by 0007 |
| [0003](0003-synthetic-data-only-testing.md) | Synthetic-data-only testing, with a construction-time manifest as ground truth | Accepted |
| [0004](0004-packaging-consolidation-to-pyproject-toml.md) | Packaging consolidated to pyproject.toml only | Accepted |
| [0005](0005-vendor-inlined-shared-infrastructure.md) | Vendor-inlined shared infrastructure instead of a second-repo dependency | Accepted |
| [0006](0006-repository-rename-before-public-release.md) | Repository renamed before public release | Accepted |
| [0007](0007-presidio-detection-with-ported-rules.md) | Presidio detection, with the regex rules ported in as recognizers | Accepted |

Two candidate decisions were considered for this index and **not** written up, because the actual code contradicts their premise:

- **Separate `redact` and `highlight` commands** — the CLI has no such commands. Redaction and highlighting are both delivered through `parse-report single`/`parse-report spreadsheet`; redaction always runs, and `--keywords` additionally highlights matches rather than masking them. See README.md, "Process".
- **Span-based detection** (`(start, end, category)` tuples) — at the time, detectors didn't work this way: each `sanitize_*` method on `PhiSanitizer` transformed and returned text directly. Presidio detection ([0007](0007-presidio-detection-with-ported-rules.md)) is span-based (`RecognizerResult`), so this is now part of 0007 rather than a separate decision.
