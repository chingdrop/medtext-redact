# Architecture decision records

Lightweight [MADR](https://adr.github.io/madr/)-style records of the significant, load-bearing decisions behind this repository's current design. Each one is drafted only from what this repository actually records — the code, tests, README.md, `docs/provenance-and-data-boundary.md`, `CLAUDE.md`, and `git log` commit bodies — not from memory or invented rationale. Where the repository doesn't record *why* a choice was made, the record says so with a `TODO(craig)` marker rather than guessing.

| # | Title | Status |
|---|---|---|
| [0001](0001-rule-based-detection-not-ner.md) | Rule-based detection, not NER | Accepted |
| [0002](0002-gazetteer-based-name-detection.md) | Gazetteer-based name detection, and its documented limits | Accepted |
| [0003](0003-synthetic-data-only-testing.md) | Synthetic-data-only testing, with a construction-time manifest as ground truth | Accepted |
| [0004](0004-packaging-consolidation-to-pyproject-toml.md) | Packaging consolidated to pyproject.toml only | Accepted |
| [0005](0005-vendor-inlined-shared-infrastructure.md) | Vendor-inlined shared infrastructure instead of a second-repo dependency | Accepted |
| [0006](0006-repository-rename-before-public-release.md) | Repository renamed before public release | Accepted |

Two candidate decisions were considered for this index and **not** written up, because the actual code contradicts their premise:

- **Separate `redact` and `highlight` commands** — the CLI has no such commands. Redaction and highlighting are both delivered through `parse-report single`/`parse-report spreadsheet`; redaction always runs, and `--keywords` additionally highlights matches rather than masking them. See README.md, "Process".
- **Span-based detection** (`(start, end, category)` tuples) — detectors don't work this way. Each `sanitize_*` method on `PhiSanitizer` (`src/medtext_redact/core/text_tools.py`) transforms and returns text directly, chained via method calls that progressively mutate the sanitizer's own text buffer.
