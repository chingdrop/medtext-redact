# 0006. Repository renamed before public release

Status: Accepted (2026-09-25)

## Context

Prior to public release, this repository's name and installable package name referenced its original context.

## Decision

The repository name was changed prior to public release to remove the original client company's name. The installable package was renamed `src/vega_tools` → `src/medtext_redact`, along with the `pyproject.toml` package/CLI name and every import, path, and user-facing string that referenced the old name (README, CONTRIBUTING.md, CLAUDE.md, `--help` text, docstrings).

## Alternatives considered

None: keeping any reference to the client's name in a public repository wasn't an option, given this project's confidentiality constraints — see [`docs/provenance-and-data-boundary.md`](../provenance-and-data-boundary.md).

## Consequences

- Functional behavior (redact/highlight logic) was explicitly unchanged by this rename — confirmed by the full test suite passing before and after.
- Deliberately left unrenamed: `CHANGELOG.md`'s historical entries and a `CLAUDE.md` note describing the repository's original four-way consolidation, both of which describe what was true at the time under the old name, and test fixtures using a domain-specific project-code naming convention (`parse_project_name`, whose regex is generic and not hardcoded to any specific prefix) unrelated to the software's own identity.
- git history itself was separately audited and rewritten (see `docs/provenance-and-data-boundary.md`) — this ADR concerns only the naming decision, not that rewrite.

## Evidence

- `pyproject.toml` (`name = "medtext-redact"`)
- `src/medtext_redact/` (package path)
- Commit `9e5a052` ("Rename project identity from vega-tools to medtext-redact")
- `docs/provenance-and-data-boundary.md`, "Provenance"
