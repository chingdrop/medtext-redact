# Contributing

## Prerequisites

- Python 3.12, pinned in [`.python-version`](.python-version). `uv` reads that file and installs the interpreter if it's missing.
- [uv](https://docs.astral.sh/uv/) for dependency management.

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
    core/              # domain logic: PHI patterns, Presidio recognizers and engine, DICOM audits
    data/              # bundled public reference data (the 2010 Census surname list)
    vendor/            # generic infrastructure inlined from py-shared-tools (config, file I/O, logging)
    paths.py           # PROJECT_DIRECTORY / DATA_DIRECTORY constants
tests/
    core/              # unit tests for core/
    commands/          # integration tests for commands/, driven through Click's CliRunner
    e2e/               # recall/precision suite against synthetic notes
    tools/             # tests for the scripts in tools/
    vendor/            # unit tests for vendor/
tools/
    gen_fixtures.py    # synthetic clinical-note generator with a ground-truth manifest
    build_surname_list.py  # rebuilds the bundled Census surname list
    results_sheet.py   # renders docs/results-sheet.png from a run of the recall/precision suite
docs/                  # threat model, limitations, provenance, ADRs, and the README's demo.gif (demo.tape) and results-sheet.png
```

## Running tests

```bash
uv run pytest
```

Tests mirror `src/medtext_redact/`: once a repository has more than 10 test modules, each `tests/` subdirectory matches the source package it tests, and this one already does. `tests/core/` covers the library layer directly; `tests/commands/` and `tests/test_cli.py` drive the actual CLI commands end-to-end through `click.testing.CliRunner`, faking only genuine external boundaries rather than internal collaborators.

If you add a new function or command, add tests alongside it in the mirrored location.

`tests/e2e/test_recall_precision.py` prints a per-category recall/precision table. If you add or change a detector, add a matching generator and template to `tools/gen_fixtures.py`, gate the new category in the e2e suite, and update the numbers in the README, `docs/threat-model.md`, `docs/provenance-and-data-boundary.md`, and `docs/limitations-and-roadmap.md` from a fresh run. Then regenerate the README's results image with `uv run python tools/results_sheet.py --png docs/results-sheet.png` (it reruns the suite; a new category also needs a label in its `GROUPS`). New test data must be synthetic; see [`docs/provenance-and-data-boundary.md`](docs/provenance-and-data-boundary.md).

## Code quality

```bash
uv run ruff check --fix src/ tests/ tools/   # lint
uv run ruff format src/ tests/ tools/        # format
uv run mypy src/medtext_redact tools/  # type-check
```

`pre-commit` (installed via `uv run pre-commit install`, see Setup) runs automatically on `git commit`: ruff check and format on `src/`, `tests/`, and `tools/`; mypy on `src/` only; plus gitleaks, a private-key check, and a 500 KB limit on newly added files. CI runs mypy on both `src/medtext_redact` and `tools/`, so run the type-check command above before committing changes to `tools/`.

## Before opening a PR

Run the same checks CI does:

```bash
uv run ruff check src/ tests/ tools/
uv run ruff format --check src/ tests/ tools/
uv run mypy src/medtext_redact tools/
uv run pytest --cov
```

## Coverage

`uv run pytest --cov` measures branch coverage and fails below `fail_under` in `pyproject.toml`'s `[tool.coverage.report]`. The floor is the measured baseline minus 2, rounded down. When the measured baseline climbs more than 4 points above the floor, raise the floor in the same PR.

## Design decisions (ADRs)

Significant, load-bearing decisions are recorded in [`docs/decisions/`](docs/decisions/README.md). To add one, take the next number, follow the existing records' sections (Status, Context, Decision, Alternatives considered, Consequences, Evidence), and add a row to the index table in `docs/decisions/README.md` with its Status, as the other rows do. Write only what the repository actually records; where it doesn't say why, say so rather than guessing. When a decision changes, update the old record's Status (e.g. "Superseded by 0007") rather than rewriting it.

## Changelog

Record user-visible changes in [`CHANGELOG.md`](CHANGELOG.md), under `[Unreleased]`, in the matching `Added`/`Changed`/`Removed`/`Fixed`/`Security` subsection. Don't edit entries for past releases.

## Vendored code

`src/medtext_redact/vendor/` holds copies of modules from [py-shared-tools](https://github.com/chingdrop/py-shared-tools); see [ADR 0005](docs/decisions/0005-vendor-inlined-shared-infrastructure.md). Each module's docstring records which upstream version it matches.

## Open work

Planned features, known bugs, and open questions are tracked in [`TODO.md`](TODO.md). Add new items there rather than as `TODO` comments in code or docs, and remove an item in the same change that resolves it.

## Commit style

Prefer small, focused commits over one large one — a structural change, a bug fix, and its test are each usually worth their own commit, even when they land in the same session. Commit messages should explain *why*, not just *what*; the diff already shows what changed.
