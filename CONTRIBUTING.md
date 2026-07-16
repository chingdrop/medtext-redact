# Contributing

## Setup

```bash
git clone git@github.com:chingdrop/vega-tools.git
cd vega-tools
git submodule update --init  # needed for the philter command
uv sync
```

This installs `vega-tools` in editable mode along with its dev dependencies (`pytest`, `ruff`, `mypy`, `pre-commit`, plus type stubs for `pandas`/`PyYAML`).

Then install the git hook so linting/formatting/type-checking run automatically on each commit:

```bash
uv run pre-commit install
```

## Project layout

```
src/vega_tools/
    cli.py            # entry point; registers every command onto the top-level group
    commands/          # one module per command domain (studies, reports, philter, spark_nlp)
    core/               # shared library code the commands are built on
    paths.py             # PROJECT_DIRECTORY / DATA_DIRECTORY constants
integrations/
    spark-nlp/         # Docker/GPU Spark NLP + OCR environment, wrapped by `vega-tools spark-nlp`
    philter/            # Philter-UCSF, vendored as a git submodule, wrapped by `vega-tools philter`
tests/
    core/               # unit tests for core/
    commands/            # integration tests for commands/, driven through Click's CliRunner
```

## Running tests

```bash
uv run pytest
```

Tests are organized to mirror `src/vega_tools/`. `tests/core/` covers the library layer directly; `tests/commands/` and `tests/test_cli.py` drive the actual CLI commands end-to-end through `click.testing.CliRunner`, mocking only genuine external boundaries (Docker, the separate `philter-ucsf` interpreter, the census name API) rather than internal collaborators.

If you add a new function or command, add tests alongside it in the mirrored location.

## Code quality

```bash
uv run ruff check --fix src/ tests/   # lint
uv run ruff format src/ tests/        # format
uv run mypy src/vega_tools            # type-check
```

`pre-commit` (installed via `uv run pre-commit install`, see Setup) runs all three automatically on `git commit`, scoped to `src/` and `tests/` — `integrations/` is intentionally excluded, since it holds vendored/third-party code (a git submodule, a notebook written in John Snow Labs' own idioms) that isn't ours to lint.

## Commit style

Prefer small, focused commits over one large one — a structural change, a bug fix, and its test are each usually worth their own commit, even when they land in the same session. Commit messages should explain *why*, not just *what*; the diff already shows what changed.

## Two things to know about `philter` and `spark-nlp`

- `philter-ucsf` pins `pandas`/`numpy` versions that conflict with this project's own, and imports the long-removed `distutils` module, so it can never run in the same Python environment as `vega-tools` itself. It always runs as a subprocess in a separate interpreter (`--python` / `PHILTER_PYTHON`).
- `spark-nlp` requires Docker and, for the licensed John Snow Labs models, a `.env` file with license keys — neither is available in this dev setup by default.

Tests for both fake the external boundary (a stub script standing in for `philter-ucsf/main.py`'s CLI contract; a mocked `subprocess.run` for Docker) rather than requiring either to actually be installed.
