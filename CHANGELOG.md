# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project intends to follow [Semantic Versioning](https://semver.org/) once it's tagged.

**This changelog begins retroactively.** The tool was originally developed independently for real professional use prior to this documented history — see [`docs/provenance-and-data-boundary.md`](docs/provenance-and-data-boundary.md). The entries below cover that original development plus its later preparation for public release; nothing here should be read as a from-scratch project starting now.

## [Unreleased]

### Added

- `TODO.md`, tracking planned features, known bugs, and open questions in one place. The `TODO(craig)` markers from ADRs 0001 and 0002, the `parse-report` performance `ToDo` comment, and the roadmap list in `docs/limitations-and-roadmap.md` moved into it.
- Recall/precision fixtures for every remaining built-in Presidio recognizer active in this tool: credit card, US bank account, driver's license, passport, ITIN, DEA, IBAN, crypto wallet, MAC address, and UK NHS numbers, all measured at 100%. A `LuhnCardRecognizer` backstops Presidio's credit card recognizer, which stops at 16 digits and left 19-digit Visa numbers completely unmasked. The suite now generates 48 notes, 4 from each of 12 templates.
- Recall/precision fixtures for email addresses, US SSNs, URLs, and IP addresses (IPv4 and IPv6), all measured at 100%. A `URL_PATTERN` recognizer backstops Presidio's URL recognizer, which matches `.biz` as `.bi` and leaves the final letter unmasked.
- PHI detection with Microsoft Presidio and spaCy's `en_core_web_lg` NER model (`core/presidio_tools.py`), with the previous regex rules and surname gazetteer ported in as custom Presidio recognizers (`core/presidio_recognizers.py`). Catches names outside the gazetteer, bare first names (NER only), and dates in formats the rules missed, and adds Presidio's built-in recognizers for email addresses, URLs, IP addresses, SSNs and more. See [`docs/decisions/0007-presidio-detection-with-ported-rules.md`](docs/decisions/0007-presidio-detection-with-ported-rules.md).
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
- CI (`.github/workflows/ci.yml`): lint (ruff check/format), type-check (mypy), and test (pytest across Python 3.12–3.14) jobs, plus separate `pip-audit` (against locked dependencies) and `gitleaks` (over new commits on push and PRs, and over full history weekly) jobs.
- `.github/dependabot.yml` (uv and github-actions ecosystems, weekly, grouped minor/patch updates), `.github/workflows/codeql.yml` (Python analysis), `SECURITY.md`, and `docs/threat-model.md`.
- `docs/limitations-and-roadmap.md`, separating known limitations (with real numbers) from possible next steps sourced only from existing TODO markers in the repo.

### Changed

- The 2010 US Census surname list is bundled with the package (`src/medtext_redact/data/census_2010_surnames.txt`) instead of downloaded on first use, so the tool makes no network calls at all. It's read once per process instead of once per report. `tools/build_surname_list.py` rebuilds it from the Census Bureau's `names.zip` or the Census Data API.
- Requires pandas 3 (`pandas>=3.0.0`). pandas 3 makes no-silent-downcasting the default, so the deprecated `future.no_silent_downcasting` opt-in, which warned on every CLI run, was removed.
- CI's `security` job is split into separate `pip-audit` and `gitleaks` jobs, so a dependency advisory can no longer skip the secrets scan, as it did on the 2026-09-28 scheduled run. The `pip-audit` job no longer installs the project (`uv export` reads `uv.lock` directly), which skips the spaCy model download.
- Documentation of CI's `gitleaks` scan corrected: on pushes and pull requests it scans only the new commits, not full history; the weekly scheduled run scans full history.
- The recall/precision ground truth now labels surnames outside the gazetteer, bare first names, and dates with mismatched separators or pre-1900 years as PHI. They were previously labeled non-PHI because the rule-based engine was never designed to catch them, which hid those misses from its recall numbers.
- Switched dependency management and packaging from `setuptools`/`pip` to `uv`, with `hatchling` as the build backend.
- Restructured the package for clarity: `commands.py` (one 258-line file) split into `commands/` (one module per command domain); `common/` renamed to `core/`; `config/settings.py` flattened to a top-level `paths.py` module.
- Grouped `spark-nlp/` and `philter/` under `integrations/`, separating the installable package from the adjacent infrastructure it wraps.
- Renamed the project, prior to public release, from its original name to `medtext-redact` (package, CLI entry point, and every path/import/doc reference) — see [`docs/decisions/0006-repository-rename-before-public-release.md`](docs/decisions/0006-repository-rename-before-public-release.md).
- `sanitize_gender()` now also matches plural forms ("males"/"females"); `_AGE_PATTERN` now recognizes the "34yo" shorthand common in real clinical notes and no longer treats a clinical staging/grading number ("type 2 diabetes") as an age.

### Removed

- `CensusNamesApi` and the vendored `RestAdapter` HTTP client, along with the `requests`, `certifi`, `urllib3`, and `charset-normalizer` dependencies, all of which existed only to download the census surname list.
- The rule-based detection methods on `PhiSanitizer` (`sanitize_names`, `sanitize_dates`, `sanitize_all`, etc.), now superseded by the Presidio recognizers built from the same patterns. Their regex tests live on in `tests/core/test_phi_patterns.py`.
- The `spark-nlp` and `philter` commands, along with `integrations/` (the Spark NLP Docker environment and the Philter-UCSF submodule) and the `nltk` dependency only `philter` used, to focus the project on a single de-identification engine, Microsoft Presidio.
- The `py-shared-tools` git dependency (a separate, private repository) — replaced by the vendored copy under `src/medtext_redact/vendor/` (see Added, above), so a fresh clone no longer needs access to it.

### Fixed

- The surname gazetteer masked capitalized common words, typically at the start of every sentence: 107 of spaCy's 326 English stop words are real 2010 Census surnames ("The", "And", "In", "May", ...), as are many clinical words ("Patient", "Plan", "Chief"). Common and clinical words now match only directly after a title ("Dr. Hand", "Nurse Back"), and other matches are skipped when spaCy tags them as a verb, adjective, or other non-name word class ("Seen by...", "Long term..."). Surname recall in the suite stays at 100%. New tests run against the real bundled list, which the recall/precision suite's 8-name stand-in hid this from.
- Redaction failed with a misleading "Could not extract census names CSV" traceback whenever census.gov rejected the surname-list download, which its firewall does for automated requests from some networks. The list is now bundled with the package (see Changed), so redaction no longer downloads anything.
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
- Added automated, standing supplements to that manual audit: `gitleaks` in CI (new commits on every push and PR, full git history weekly), `pip-audit` against locked dependencies, CodeQL analysis, and Dependabot version updates.

[Unreleased]: https://github.com/chingdrop/medtext-redact/commits/main
