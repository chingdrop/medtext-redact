# 0008. Adopt the shared Python tooling standard

Status: Accepted (2026-10-03)

## Context

The maintainer applies one Python project standard across four repositories, this one included. Most of it already held here: hatchling, a `src/` layout, `requires-python >=3.12`, ruff at line length 120 with `E,F,I,UP,B,SIM`, tests mirroring `src/`, Dependabot, and separate `pip-audit` and `gitleaks` CI jobs. This record covers what changed to close the remaining gaps.

## Decision

- **Packaging metadata.** `license = "MIT"` (SPDX) with `license-files = ["LICENSE"]` replaces the deprecated `license = { file = ... }` table; the wheel carries `License-Expression: MIT`. A `.python-version` file pins the development interpreter to 3.12.
- **ruff `S` (flake8-bandit).** Added to `select`. It found nothing in `src/`. Outside it: `S101` in `tests/**` and `S311` in `tools/gen_fixtures.py` (a seeded `random.Random` for reproducible fixtures) are per-file ignores; `S310` on the single `urlopen` in `tools/build_surname_list.py` (a constant `https://api.census.gov` endpoint) is an inline `noqa`. One finding was fixed instead of ignored: an `assert` in `tools/gen_fixtures.py` guarding the manifest's span offsets, which `python -O` would strip, became an explicit `raise`.
- **mypy.** `strict_equality` and `check_untyped_defs` added, alongside the existing flags. Both produced zero errors across `src/medtext_redact` and `tools/`; no flag was left out.
- **Coverage gate.** `pytest-cov` in the dev group; branch coverage over `medtext_redact`. The measured baseline was 98.21% (e2e suite included), so `fail_under = 96`: the baseline minus 2, rounded down.
- **Pre-commit.** The ruff hooks extend to `tools/`; the mypy hook stays on `src/`. Added gitleaks (v8.30.1), `detect-private-key`, and `check-added-large-files` (500 KB). The tracked 1.26 MB surname list isn't flagged, since that hook only checks files being added.
- **CI hardening.** Every action in `ci.yml` and `codeql.yml` is pinned to a full commit SHA, each checked against its upstream tag; `astral-sh/setup-uv` moves from `@v7` to v10.2.0. Every checkout sets `persist-credentials: false` (the gitleaks job keeps `fetch-depth: 0`). `codeql.yml` gets the same concurrency group as `ci.yml`.
- **Test matrix.** One Python 3.12 job replaces the 3.12–3.14 matrix, matching `requires-python` and `.python-version`. It runs `pytest --cov`; the floor lives in `pyproject.toml`.
- **pip-audit.** Audits an exported, fully pinned requirements file with `--no-deps --disable-pip`, pinned to pip-audit 2.10.1. The standard form worked as-is: pip-audit skips the spaCy model wheel (a URL requirement) rather than rejecting it, so no `--no-emit-package` was needed.
- **mypy in CI.** CI now runs `mypy src/medtext_redact tools/`, matching `CLAUDE.md` and `CONTRIBUTING.md`; it was clean.
- **Vendored provenance.** Each `vendor/` module's docstring names the py-shared-tools version it matches: v1.3.1, commit `d54dcd6`. Compared against a fresh clone, `atomic_io`, `logging_setup`, and `tabular_io` are identical in code; `config_loader` differs only by defining `ConfigError` inline.

## Alternatives considered

None documented.

## Consequences

- Python 3.13 and 3.14 are no longer tested in CI, though `requires-python` still allows them.
- A coverage drop of more than about 2 points below today's baseline fails CI. `CONTRIBUTING.md` says to raise the floor in the same PR once the baseline exceeds it by more than 4.
- Moving to a new action release means updating a SHA rather than a tag, and checking that SHA against the upstream tag first.
- setup-uv v9 stopped pruning the uv cache by default, so CI caches will grow.
- Secrets and private keys are now caught at commit time, not only in CI after a push.

## Evidence

- `pyproject.toml` (`license`, `license-files`, `[tool.ruff.lint]`, `[tool.ruff.lint.per-file-ignores]`, `[tool.mypy]`, `[tool.coverage.*]`), `.python-version`
- `.pre-commit-config.yaml`
- `.github/workflows/ci.yml`, `.github/workflows/codeql.yml`
- `src/medtext_redact/vendor/*.py` module docstrings
- The commits on the `chore/python-standard` branch
