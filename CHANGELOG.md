# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project intends to follow [Semantic Versioning](https://semver.org/) once it's tagged.

**This changelog begins retroactively.** The tool was originally developed independently for real professional use prior to this documented history — see [`docs/provenance-and-data-boundary.md`](docs/provenance-and-data-boundary.md). The entries below cover that original development plus its later preparation for public release; nothing here should be read as a from-scratch project starting now.

## [Unreleased]

### Added

- Consolidated `vt-console`, `vega-spark-nlp`, and `vega-philter` into this repo, preserving each repo's full commit history.
- `spark-nlp` command: a thin `docker compose` wrapper for the Spark NLP / Spark OCR de-identification environment (`integrations/spark-nlp/`).
- `philter` command: runs the Philter-UCSF de-identification pipeline (`integrations/philter/philter-ucsf`, vendored as a git submodule) as a subprocess in a separate interpreter, since its pinned dependencies conflict with this project's own.
- `compare-projects` and `validate-studies` commands (from the `vt-console` merge).
- A unit and integration test suite (209 tests) covering the `core/` library layer and every CLI command, using `pytest` and Click's `CliRunner`.
- This changelog, plus `LICENSE` (MIT) and `CONTRIBUTING.md`.
- Phone number, street address, and medical-record-number redaction (`sanitize_phone`, `sanitize_address`, `sanitize_mrn` on `PhiSanitizer`) — categories the tool previously had no detector for at all.
- `tools/gen_fixtures.py`, a deterministic, Faker-based synthetic clinical-note generator with a construction-time ground-truth manifest, and `tests/e2e/test_recall_precision.py`, an end-to-end recall/precision test suite that runs the actual CLI against it. Current measured numbers: names, dates, ages, gender terms, phone numbers, addresses, and MRNs are each at 100% recall / 100% precision; the one measured shortfall in the whole suite is a false-positive case — 0% precision when a gazetteer surname is used as an ordinary English word. See [`docs/threat-model.md`](docs/threat-model.md) for the full picture, including identifier categories with no detector at all.
- `src/medtext_redact/vendor/`, inlining the five shared-infrastructure modules this project actually imports (`RestAdapter`, `ConfigLoader`, `tabular_io`, `atomic_io`, `logging_setup`) — see [`docs/decisions/0005-vendor-inlined-shared-infrastructure.md`](docs/decisions/0005-vendor-inlined-shared-infrastructure.md).
- `docs/provenance-and-data-boundary.md` and an "About this project" section in README.md, documenting this repository's pre-release history audit, its synthetic-data-only policy going forward, and its scope as a reference implementation.
- `docs/decisions/`: six lightweight ADRs recording the load-bearing design decisions behind this repository's current form (rule-based detection, gazetteer name limits, synthetic-only testing, packaging, vendored infrastructure, and the pre-release rename).
- CI (`.github/workflows/ci.yml`): lint (ruff check/format), type-check (mypy), and test (pytest across Python 3.12–3.14) jobs, plus a `security` job (`pip-audit` against locked dependencies, full-history `gitleaks`) running on push, PRs, and weekly.
- `.github/dependabot.yml` (uv and github-actions ecosystems, weekly, grouped minor/patch updates), `.github/workflows/codeql.yml` (Python analysis), `SECURITY.md`, and `docs/threat-model.md`.
- `docs/limitations-and-roadmap.md`, separating known limitations (with real numbers) from possible next steps sourced only from existing TODO markers in the repo.

### Changed

- Switched dependency management and packaging from `setuptools`/`pip` to `uv`, with `hatchling` as the build backend.
- Restructured the package for clarity: `commands.py` (one 258-line file) split into `commands/` (one module per command domain); `common/` renamed to `core/`; `config/settings.py` flattened to a top-level `paths.py` module.
- Grouped `spark-nlp/` and `philter/` under `integrations/`, separating the installable package from the adjacent infrastructure it wraps.
- Renamed the project, prior to public release, from its original name to `medtext-redact` (package, CLI entry point, and every path/import/doc reference) — see [`docs/decisions/0006-repository-rename-before-public-release.md`](docs/decisions/0006-repository-rename-before-public-release.md).
- `sanitize_gender()` now also matches plural forms ("males"/"females"); `_AGE_PATTERN` now recognizes the "34yo" shorthand common in real clinical notes and no longer treats a clinical staging/grading number ("type 2 diabetes") as an age.

### Removed

- The `spark-nlp` and `philter` commands, along with `integrations/` (the Spark NLP Docker environment and the Philter-UCSF submodule) and the `nltk` dependency only `philter` used, to focus the project on a single de-identification engine. Microsoft Presidio is planned to take that role.
- The `py-shared-tools` git dependency (a separate, private repository) — replaced by the vendored copy under `src/medtext_redact/vendor/` (see Added, above), so a fresh clone no longer needs access to it.

### Fixed

- `PROJECT_DIRECTORY` was computed from the current working directory at runtime instead of the install location, so running the CLI from anywhere but one specific directory silently pointed `DATA_DIRECTORY` at the wrong place.
- `ConfigLoader` had no `.copy()` method, so `parse-report single` and `parse-report spreadsheet` crashed with `AttributeError` on every invocation.
- `search_column_for_keywords` raised `ValueError: pattern contains no capture groups` on every call, which also broke `search_report_text` and therefore `parse-report spreadsheet`.
- `parse-report spreadsheet` discarded all PHI sanitization (names, dates, gender, age, manufacturers, locations) before writing its output, silently writing un-redacted PHI to the result file.
- `parse-report single`'s `--text` flag was unreachable outside a literal interactive terminal session, because the stdin check ran before the `--text` check.
- `NameMasker` had no word-boundary check, so a short gazetteer surname could match as a substring inside an unrelated longer word.
- The date pattern's separator class allowed a plain space, contradicting its own documented intent, so a space-separated number triplet could be masked as a date.
- The census-surname download used a malformed URL join that always failed, and a genuinely blank row in the real Census data crashed name loading — together these broke `parse-report single`/`spreadsheet` outright for anyone without an already-cached name list.

### Security

- This repository's own git history was audited for PHI, credentials, and client-identifying material (manual review plus `gitleaks` and TruffleHog scans, completed 2026-09-29), and rewritten to remove what that audit found — see [`docs/provenance-and-data-boundary.md`](docs/provenance-and-data-boundary.md) for what that covers and its limits.
- Added automated, standing supplements to that manual audit: `gitleaks` over full git history in CI (weekly and on every push/PR), `pip-audit` against locked dependencies, CodeQL analysis, and Dependabot version updates.

[Unreleased]: https://github.com/chingdrop/medtext-redact/commits/main
