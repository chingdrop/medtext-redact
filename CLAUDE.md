# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Medtext-Redact is a Click-based CLI for HIPAA PHI redaction and related medical-imaging data workflows (health data engineers, clinical researchers, compliance teams). It was consolidated from four originally-separate repos (`vt-console`, `vega-spark-nlp`, `vega-philter`, plus the original `vega-tools`), each merged in with full git history preserved. The Spark NLP and Philter-UCSF integrations have since been removed to focus the project on a single de-identification engine; Microsoft Presidio is planned as that engine (see `docs/limitations-and-roadmap.md`).

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

## Architecture

**Command registration is explicit, not decorator-magic.** Each file under `src/medtext_redact/commands/` (`studies.py`, `reports.py`) defines its commands with plain `@click.command()`/`@click.group()` — not `@cli.command()`. `cli.py` imports each command function and wires it on with `cli.add_command(...)`. This avoids the common Click pattern of importing submodules purely for their registration side effects. When adding a new command, define it standalone in its own `commands/` module and add one `cli.add_command(...)` line in `cli.py`.

**`core/` vs. `vendor/`: domain logic stays local, generic infra is inlined, not fetched.** `medtext_redact/vendor/` holds `RestAdapter` (HTTP client), `ConfigLoader` (JSON/YAML config with dot-notation lookup), `tabular_io` (structured file read/write), `atomic_io.ensure_dir` (crash-safe directory creation), and `logging_setup.setup_logging` (idempotent logging config) — generic infrastructure factored out of a separate shared library (`py-shared-tools`) and inlined directly into this repo (only the modules this project actually uses; keeping their original module and symbol names), so a fresh clone has no dependency on that second, private repo and no submodule step for it. `medtext_redact/core/` owns everything domain-specific to this project: `text_tools.PhiSanitizer` (the actual PHI redaction rules), `pandas_tools.py` (DICOM series auditing, project-accession reconciliation, report keyword search), `api_tools.CensusNamesApi` (business wrapper around the Census API, built on `vendor.rest_adapter`), `presidio_tools.presidio_redact` (the Presidio engine behind `parse-report --engine presidio`). When adding new functionality, ask which side it belongs on: anything generic enough to be reusable across unrelated projects goes in `vendor/`; anything tied to PHI rules, DICOM fields, or this project's specific workflows stays in `core/`.

**Two detection engines, one masking format.** `parse-report --engine rules` (default) runs `PhiSanitizer`'s regex/gazetteer rules; `--engine presidio` runs Microsoft Presidio with spaCy's `en_core_web_lg` (a URL-pinned wheel in `[tool.uv.sources]`, since spaCy models aren't on PyPI). Both mask by replacing each word character with `*`, preserving length: keyword highlighting and the recall/precision suite's span offsets depend on that, so don't switch Presidio to a replace/redact operator that changes length. `presidio_tools` is imported lazily (inside `PhiSanitizer.sanitize_presidio`) so the rules path doesn't pay spaCy's load time, and it pins `tldextract` to its bundled suffix list so Presidio never makes a network call. The plan is to port the rules into Presidio custom recognizers and retire `PhiSanitizer`'s own detection (see `docs/limitations-and-roadmap.md`).

**`paths.py`'s `PROJECT_DIRECTORY` must be computed as `Path(__file__).resolve().parent...`, never `Path.cwd()`-relative.** A prior bug had it cwd-relative, which silently broke `DATA_DIRECTORY` resolution depending on where the CLI was invoked from. Any new path constant must follow the same `__file__`-relative pattern.

**Test philosophy: mock only real external boundaries.** `tests/core/` unit-tests the library layer directly, mocking things like the census name HTTP API. `tests/commands/` and `tests/test_cli.py` are integration tests that drive the actual CLI commands end-to-end through `click.testing.CliRunner` with real files — the only thing faked is a genuine external system, the census API. Internal collaborators (other `medtext_redact` functions) are exercised for real, not mocked. Several real bugs (a silent PHI-leak in `parse-report spreadsheet`, a couple of crash-on-first-use bugs) were only caught by this integration-level testing, not the unit tests — new commands should get both kinds of coverage, not just unit tests of their helper functions.
