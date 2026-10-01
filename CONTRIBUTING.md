# Contributing

## Setup

```bash
git clone git@github.com:chingdrop/medtext-redact.git
cd medtext-redact
uv sync
```

This installs `medtext-redact` in editable mode along with its dev dependencies (`pytest`, `ruff`, `mypy`, `pre-commit`, plus type stubs for `pandas`/`PyYAML`).

Then install the git hook so linting/formatting/type-checking run automatically on each commit:

```bash
uv run pre-commit install
```

## Project layout

```
src/medtext_redact/
    cli.py            # entry point; registers every command onto the top-level group
    commands/          # one module per command domain (studies, reports)
    core/               # shared library code the commands are built on
    paths.py             # PROJECT_DIRECTORY / DATA_DIRECTORY constants
tests/
    core/               # unit tests for core/
    commands/            # integration tests for commands/, driven through Click's CliRunner
```

## Running tests

```bash
uv run pytest
```

Tests are organized to mirror `src/medtext_redact/`. `tests/core/` covers the library layer directly; `tests/commands/` and `tests/test_cli.py` drive the actual CLI commands end-to-end through `click.testing.CliRunner`, mocking only genuine external boundaries (the census name API) rather than internal collaborators.

If you add a new function or command, add tests alongside it in the mirrored location.

## Code quality

```bash
uv run ruff check --fix src/ tests/ tools/   # lint
uv run ruff format src/ tests/ tools/        # format
uv run mypy src/medtext_redact tools/gen_fixtures.py  # type-check
```

`pre-commit` (installed via `uv run pre-commit install`, see Setup) runs all three automatically on `git commit`, scoped to `src/` and `tests/`.

## Commit style

Prefer small, focused commits over one large one — a structural change, a bug fix, and its test are each usually worth their own commit, even when they land in the same session. Commit messages should explain *why*, not just *what*; the diff already shows what changed.
