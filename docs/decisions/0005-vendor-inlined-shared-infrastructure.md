# 0005. Vendor-inlined shared infrastructure instead of a second-repo dependency

Status: Accepted (2026-09-25)

## Context

`medtext_redact` depended on `py-shared-tools`, a separate, private repository pulled in as a pinned git dependency, for five modules: `RestAdapter`, `ConfigLoader`, `tabular_io`, `atomic_io.ensure_dir`, `logging_setup.setup_logging`. A public, portfolio-facing clone of this repository would either fail to resolve that dependency or require access to a second private repo.

## Decision

Copied only the five modules actually imported (confirmed by grepping real imports, not declared dependencies) into `src/medtext_redact/vendor/`, keeping original module/symbol names so call sites needed only an import-path change. Everything else `py-shared-tools` offers (`remote_exec`, `script_export`, `sentinelone`, `storage`, generic retry-with-backoff) was never imported here and was not copied. Removed the `py-shared-tools` dependency entry and its `[tool.uv.sources]` git pin from `pyproject.toml`.

## Alternatives considered

None documented other than keeping the git dependency as-is, which was rejected because it blocks a fresh, public clone from building without access to a second private repository.

## Consequences

- A fresh clone has zero dependency on `py-shared-tools` and needs no submodule step for it — verified by resolving `pyproject.toml` and running the full test suite from a clean clone with no access to that repo.
- `py-shared-tools` is the author's own original, sole-authored work, so inlining and relicensing these five modules under this repository's license (MIT) raised no licensing concern.
- This repository's copy of these five modules will not receive future fixes made upstream in `py-shared-tools`; it now owns them independently.
- Update: `RestAdapter` was later removed, along with its `requests`/`certifi`/`urllib3`/`charset-normalizer` dependencies, once the census surname list was bundled with the package instead of downloaded through it. Four vendored modules remain.

## Evidence

- `src/medtext_redact/vendor/` (`atomic_io.py`, `config_loader.py`, `logging_setup.py`, `rest_adapter.py`, `tabular_io.py`)
- `tests/vendor/` (moved test coverage for the same five modules)
- `pyproject.toml` (no `py-shared-tools` entry)
- Commit `066bc00` ("Inline py-shared-tools, drop the dependency on that second repo")
