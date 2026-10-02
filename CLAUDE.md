# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Medtext-Redact is a Click-based CLI for HIPAA PHI redaction and related medical-imaging data workflows (health data engineers, clinical researchers, compliance teams). It was consolidated from four originally-separate repos (`vt-console`, `vega-spark-nlp`, `vega-philter`, plus the original `vega-tools`), each merged in with full git history preserved. The Spark NLP and Philter-UCSF integrations have since been removed to focus the project on a single de-identification engine, Microsoft Presidio.

## Commands

Setup (uses [uv](https://docs.astral.sh/uv/)):

```bash
uv sync
uv run pre-commit install    # lint/format/type-check hooks on every commit
```

Run the CLI:

```bash
uv run medtext-redact --help
```

Tests:

```bash
uv run pytest                                  # full suite
uv run pytest tests/core/test_pandas_tools.py  # one file
uv run pytest tests/core/test_pandas_tools.py::TestAuditImages::test_2d_filters_single_frame_series  # one test
```

Lint / format / type-check (scoped to `src/`, `tests/`, and `tools/`):

```bash
uv run ruff check --fix src/ tests/ tools/
uv run ruff format src/ tests/ tools/
uv run mypy src/medtext_redact tools/gen_fixtures.py
```

Open work — planned features, known bugs, and unanswered questions — is tracked in `TODO.md`. Add new items there rather than as `TODO` comments or doc markers, and remove them when they land.

## Architecture

**Command registration is explicit, not decorator-magic.** Each file under `src/medtext_redact/commands/` (`studies.py`, `reports.py`) defines its commands with plain `@click.command()`/`@click.group()` — not `@cli.command()`. `cli.py` imports each command function and wires it on with `cli.add_command(...)`. This avoids the common Click pattern of importing submodules purely for their registration side effects. When adding a new command, define it standalone in its own `commands/` module and add one `cli.add_command(...)` line in `cli.py`.

**`core/` vs. `vendor/`: domain logic stays local, generic infra is inlined, not fetched.** `medtext_redact/vendor/` holds `RestAdapter` (HTTP client), `ConfigLoader` (JSON/YAML config with dot-notation lookup), `tabular_io` (structured file read/write), `atomic_io.ensure_dir` (crash-safe directory creation), and `logging_setup.setup_logging` (idempotent logging config) — generic infrastructure factored out of a separate shared library (`py-shared-tools`) and inlined directly into this repo (only the modules this project actually uses; keeping their original module and symbol names), so a fresh clone has no dependency on that second, private repo and no submodule step for it. `medtext_redact/core/` owns everything domain-specific to this project: `text_tools.PhiSanitizer` (report normalization and the redaction entry point), `pandas_tools.py` (DICOM series auditing, project-accession reconciliation, report keyword search), `api_tools.CensusNamesApi` (business wrapper around the Census API, built on `vendor.rest_adapter`), `phi_patterns`/`presidio_recognizers`/`presidio_tools` (the PHI detection patterns, their Presidio recognizers, and the Presidio engine). When adding new functionality, ask which side it belongs on: anything generic enough to be reusable across unrelated projects goes in `vendor/`; anything tied to PHI rules, DICOM fields, or this project's specific workflows stays in `core/`.

**Detection is Presidio; masking is length-preserving.** `parse-report` redacts with `PhiSanitizer.sanitize_presidio()` → `core/presidio_tools.presidio_redact`: spaCy's `en_core_web_lg` (a URL-pinned wheel in `[tool.uv.sources]`, since spaCy models aren't on PyPI), Presidio's built-in recognizers, and the custom recognizers in `core/presidio_recognizers.py` built from the regexes in `core/phi_patterns.py` plus a census-surname gazetteer. Every entity is masked by replacing each word character with `*`, preserving length: keyword highlighting and the recall/precision suite's span offsets depend on that, so don't switch to a replace/redact operator that changes length. The analyzer is built once per process (loading spaCy takes seconds); the gazetteer is passed to `analyze()` per call as an ad-hoc recognizer so tests can substitute a surname list without reloading spaCy. `presidio_tools` pins `tldextract` to its bundled suffix list so Presidio never makes a network call — the census surname download is the tool's only one.

**A failed surname download stops redaction; it never degrades it.** census.gov sometimes answers with a 200 OK "Request Rejected" HTML page. `CensusNamesApi` checks for the zip signature and raises `CensusDownloadError` (a `RuntimeError` subclass) explaining the manual workaround, and `parse-report` turns that into a one-line `click.ClickException`. Don't add a fallback that redacts without the gazetteer — it would lower recall silently.

**`paths.py`'s `PROJECT_DIRECTORY` must be computed as `Path(__file__).resolve().parent...`, never `Path.cwd()`-relative.** A prior bug had it cwd-relative, which silently broke `DATA_DIRECTORY` resolution depending on where the CLI was invoked from. Any new path constant must follow the same `__file__`-relative pattern.

**Test philosophy: mock only real external boundaries.** `tests/core/` unit-tests the library layer directly, mocking things like the census name HTTP API. `tests/commands/` and `tests/test_cli.py` are integration tests that drive the actual CLI commands end-to-end through `click.testing.CliRunner` with real files — the only thing faked is a genuine external system, the census API. Internal collaborators (other `medtext_redact` functions) are exercised for real, not mocked. `tests/e2e/test_recall_precision.py` scores redaction against the ground-truth manifest `tools/gen_fixtures.py` builds while generating synthetic notes; that manifest labels what *is* PHI, not what the detectors are designed to catch. A new detector category needs a generator and template in `gen_fixtures.py` and a gate in the e2e suite (adding a template shifts every category's counts, so update the docs' numbers from a fresh run, and keep the suite's `NOTE_COUNT` a multiple of the template count so every template appears equally often). Checksum-validating recognizers (credit card, DEA, NHS, IBAN, crypto) need generators that produce valid values, or the fixture tests the generator rather than the detector. Several real bugs (a silent PHI-leak in `parse-report spreadsheet`, a couple of crash-on-first-use bugs) were only caught by this integration-level testing, not the unit tests — new commands should get both kinds of coverage, not just unit tests of their helper functions.
