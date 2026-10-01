# Contributing

## Setup

```bash
git clone git@github.com:chingdrop/medtext-redact.git
cd medtext-redact
uv sync
```

This installs `medtext-redact` in editable mode along with its dev dependencies (`pytest`, `ruff`, `mypy`, `pre-commit`, plus type stubs for `pandas`/`PyYAML`). It also downloads spaCy's `en_core_web_lg` model (about 400 MB), which Presidio uses for named-entity recognition.

Then install the git hook so linting/formatting/type-checking run automatically on each commit:

```bash
uv run pre-commit install
```

## Project layout

```
src/medtext_redact/
    cli.py             # entry point; registers every command onto the top-level group
    commands/          # one module per command domain (studies, reports)
    core/              # domain logic: PHI patterns, Presidio recognizers and engine, DICOM audits, census API
    vendor/            # generic infrastructure inlined from a shared library (HTTP, config, file I/O)
    paths.py           # PROJECT_DIRECTORY / DATA_DIRECTORY constants
tests/
    core/              # unit tests for core/
    commands/          # integration tests for commands/, driven through Click's CliRunner
    e2e/               # recall/precision suite against synthetic notes
    vendor/            # unit tests for vendor/
tools/
    gen_fixtures.py    # synthetic clinical-note generator with a ground-truth manifest
docs/                  # threat model, limitations, provenance, and design decisions (ADRs)
```

## Running tests

```bash
uv run pytest
```

Tests are organized to mirror `src/medtext_redact/`. `tests/core/` covers the library layer directly; `tests/commands/` and `tests/test_cli.py` drive the actual CLI commands end-to-end through `click.testing.CliRunner`, mocking only genuine external boundaries (the census name API) rather than internal collaborators.

If you add a new function or command, add tests alongside it in the mirrored location.

`tests/e2e/test_recall_precision.py` prints a per-category recall/precision table. If you add or change a detector, add a matching generator and template to `tools/gen_fixtures.py`, gate the new category in the e2e suite, and update the numbers in the README, `docs/threat-model.md`, `docs/provenance-and-data-boundary.md`, and `docs/limitations-and-roadmap.md` from a fresh run. New test data must be synthetic; see [`docs/provenance-and-data-boundary.md`](docs/provenance-and-data-boundary.md).

## Code quality

```bash
uv run ruff check --fix src/ tests/ tools/   # lint
uv run ruff format src/ tests/ tools/        # format
uv run mypy src/medtext_redact tools/gen_fixtures.py  # type-check
```

`pre-commit` (installed via `uv run pre-commit install`, see Setup) runs ruff on `src/` and `tests/` and mypy on `src/` automatically on `git commit`. It doesn't cover `tools/`, so run the commands above before committing changes there; CI checks all three directories.

## Commit style

Prefer small, focused commits over one large one — a structural change, a bug fix, and its test are each usually worth their own commit, even when they land in the same session. Commit messages should explain *why*, not just *what*; the diff already shows what changed.
