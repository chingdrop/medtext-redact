# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Vega-Tools is a Click-based CLI for HIPAA PHI redaction and related medical-imaging data workflows (health data engineers, clinical researchers, compliance teams). It was consolidated from four originally-separate repos (`vt-console`, `vega-spark-nlp`, `vega-philter`, plus the original `vega-tools`), each merged in with full git history preserved — that history explains why `integrations/` exists as a separate top-level area from `src/`.

## Commands

Setup (uses [uv](https://docs.astral.sh/uv/)):

```bash
git submodule update --init  # needed for the philter command
uv sync
uv run pre-commit install    # lint/format/type-check hooks on every commit
```

Run the CLI:

```bash
uv run vega-tools --help
```

Tests:

```bash
uv run pytest                                  # full suite
uv run pytest tests/core/test_pandas_tools.py  # one file
uv run pytest tests/core/test_pandas_tools.py::TestAuditImages::test_2d_filters_single_frame_series  # one test
```

Lint / format / type-check (all scoped to `src/` and `tests/` — `integrations/` is vendored/third-party code and is excluded):

```bash
uv run ruff check --fix src/ tests/
uv run ruff format src/ tests/
uv run mypy src/vega_tools
```

## Architecture

**Command registration is explicit, not decorator-magic.** Each file under `src/vega_tools/commands/` (`studies.py`, `reports.py`, `philter.py`, `spark_nlp.py`) defines its commands with plain `@click.command()`/`@click.group()` — not `@cli.command()`. `cli.py` imports each command function and wires it on with `cli.add_command(...)`. This avoids the common Click pattern of importing submodules purely for their registration side effects. When adding a new command, define it standalone in its own `commands/` module and add one `cli.add_command(...)` line in `cli.py`.

**`core/` vs. `py-shared-tools`: generic infra lives upstream, domain logic stays local.** `py-shared-tools` (a separate repo, pulled in as a pinned git dependency via `[tool.uv.sources]`) owns generic, reusable infrastructure: `RestAdapter` (HTTP client), `ConfigLoader` (JSON/YAML config with dot-notation lookup), `tabular_io` (structured file read/write), `atomic_io.ensure_dir` (crash-safe directory creation), `logging_setup.setup_logging` (idempotent logging config). `vega_tools/core/` owns everything domain-specific to this project: `text_tools.PhiSanitizer` (the actual PHI redaction rules), `pandas_tools.py` (DICOM series auditing, project-accession reconciliation, the philter CSV split/repackage helpers), `api_tools.CensusNamesApi` (business wrapper around the Census API, built on `shared_tools.rest_adapter`). When adding new functionality, ask which side it belongs on: reusable-across-any-project infra goes upstream to `py-shared-tools`; anything tied to PHI rules, DICOM fields, or this project's specific workflows stays in `core/`.

**Two commands (`philter`, `spark-nlp`) wrap external systems that can never run in-process**, for different reasons:
- `philter` shells out to Philter-UCSF (`integrations/philter/philter-ucsf`, a git submodule) as a subprocess in a *separate* Python interpreter. `philter-ucsf` pins `pandas`/`numpy` versions that conflict with this project's own, and imports the long-removed `distutils` module — it cannot be imported directly, ever. The interpreter is explicit (`--python` / `PHILTER_PYTHON` env var), not an implicit `PATH` lookup, since this is the primary production de-identification path.
- `spark-nlp` is a thin `docker compose` passthrough wrapper around `integrations/spark-nlp/`, a GPU-based Jupyter/Spark NLP+OCR environment. Requires Docker and (for the licensed John Snow Labs models) a `.env` with license keys.

Both `integrations/` subsystems are intentionally excluded from this project's own lint/type-check/test scope — they're vendored or infrastructure-only, not Python source this project maintains in the usual sense.

**`paths.py`'s `PROJECT_DIRECTORY` must be computed as `Path(__file__).resolve().parent...`, never `Path.cwd()`-relative.** A prior bug had it cwd-relative, which silently broke `DATA_DIRECTORY` resolution depending on where the CLI was invoked from. Every other path constant in the codebase (`SPARK_NLP_DIR`, `PHILTER_UCSF_DIR`) follows the `__file__`-relative pattern; keep new ones consistent with that.

**Test philosophy: mock only real external boundaries.** `tests/core/` unit-tests the library layer directly, mocking things like the census name HTTP API. `tests/commands/` and `tests/test_cli.py` are integration tests that drive the actual CLI commands end-to-end through `click.testing.CliRunner` with real files — the only things faked are genuine external systems: Docker (`subprocess.run` mocked in `test_spark_nlp.py`), the separate `philter-ucsf` interpreter (a fixture stub script in `tests/fixtures/` standing in for its CLI contract), and the census API. Internal collaborators (other `vega_tools` functions) are exercised for real, not mocked. Several real bugs (a silent PHI-leak in `parse-report spreadsheet`, a couple of crash-on-first-use bugs) were only caught by this integration-level testing, not the unit tests — new commands should get both kinds of coverage, not just unit tests of their helper functions.
