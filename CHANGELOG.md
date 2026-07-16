# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- Consolidated `vt-console`, `vega-spark-nlp`, and `vega-philter` into this repo, preserving each repo's full commit history.
- `spark-nlp` command: a thin `docker compose` wrapper for the Spark NLP / Spark OCR de-identification environment (`integrations/spark-nlp/`).
- `philter` command: runs the Philter-UCSF de-identification pipeline (`integrations/philter/philter-ucsf`, vendored as a git submodule) as a subprocess in a separate interpreter, since its pinned dependencies conflict with this project's own.
- `compare-projects` and `validate-studies` commands (from the `vt-console` merge).
- A unit and integration test suite (154 tests) covering the `core/` library layer and every CLI command, using `pytest` and Click's `CliRunner`.
- This changelog, plus `LICENSE` (GPL-3.0) and `CONTRIBUTING.md`.

### Changed

- Switched dependency management and packaging from `setuptools`/`pip` to `uv`, with `hatchling` as the build backend.
- Restructured the package for clarity: `commands.py` (one 258-line file) split into `commands/` (one module per command domain); `common/` renamed to `core/`; `config/settings.py` flattened to a top-level `paths.py` module.
- Grouped `spark-nlp/` and `philter/` under `integrations/`, separating the installable `vega_tools` package from the adjacent infrastructure it wraps.

### Fixed

- `PROJECT_DIRECTORY` was computed from the current working directory at runtime instead of the install location, so running `vega-tools` from anywhere but one specific directory silently pointed `DATA_DIRECTORY` at the wrong place.
- `ConfigLoader` had no `.copy()` method, so `parse-report single` and `parse-report spreadsheet` crashed with `AttributeError` on every invocation.
- `search_column_for_keywords` raised `ValueError: pattern contains no capture groups` on every call, which also broke `search_report_text` and therefore `parse-report spreadsheet`.
- `parse-report spreadsheet` discarded all PHI sanitization (names, dates, gender, age, manufacturers, locations) before writing its output, silently writing un-redacted PHI to the result file.
- `parse-report single`'s `--text` flag was unreachable outside a literal interactive terminal session, because the stdin check ran before the `--text` check.

[Unreleased]: https://github.com/chingdrop/vega-tools/commits/main
