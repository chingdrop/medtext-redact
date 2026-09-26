# 0004. Packaging consolidated to pyproject.toml only

Status: Accepted (2026-07-16)

## Context

The project previously carried a hand-maintained `requirements.txt` (a `pip freeze` snapshot) alongside `setup.py` and `pyproject.toml`, with dependency and build metadata split across files that could drift out of sync with each other.

## Decision

Switched to `uv` for dependency management and packaging: `pyproject.toml` is the sole source of dependency and build metadata, with `hatchling` as the build backend and a committed `uv.lock`. `setup.py` and `requirements.txt` were removed.

## Alternatives considered

None documented beyond matching the convention already used in this author's other portfolio projects (referred to in the commit message as "agent-parity" and "py-shared-tools").

## Consequences

- One file to update when a dependency changes; no risk of `requirements.txt` silently drifting from what the code actually imports. The commit that made this change explicitly notes `requirements.txt` was "already stale — missing nltk" at the time.
- `uv sync` / `uv run` become the documented setup and run path (README, CONTRIBUTING.md, CLAUDE.md, CI).
- Scoped to the root package only: `integrations/spark-nlp/` and `integrations/philter/` keep their own separate `requirements.txt` files, since those describe different, intentionally isolated execution environments (a Docker image, and `philter-ucsf`'s own incompatible dependency pins) that don't belong in this project's own dependency graph.

## Evidence

- `pyproject.toml` (sole packaging file — confirmed via `git ls-files`)
- Commit `6c4038f` ("Switch to uv for dependency management and packaging")
- CLAUDE.md, "Commands" section (documented `uv sync` setup)
