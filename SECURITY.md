# Security policy

## Supported versions

This is a single-maintainer reference implementation, not a versioned product with a support matrix. Only the latest commit on `main` is supported; there is no backport or LTS policy.

## Reporting a vulnerability

Please report security issues privately via GitHub's [private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing/privately-reporting-a-security-vulnerability) (Security tab → Advisories → "Report a vulnerability") rather than opening a public issue.

This is a solo-maintained portfolio project: reports are handled best-effort, with no guaranteed response-time SLA.

## Scope

This tool processes text the user provides on the command line or in a file they point it at. Specifically, confirmed by reading the code, not assumed:

- **Network activity**: the tool makes exactly one kind of outbound network call — `CensusNamesApi` (`src/medtext_redact/core/api_tools.py`) downloads a public US Census surname list from `census.gov` the first time name detection runs, caching it locally afterward. This is a one-directional download of public reference data. No user-provided text, file content, or other input is ever transmitted anywhere over a network by this tool. There is no other `requests`/HTTP usage in `src/medtext_redact` outside this one path.
- **Credentials**: this tool holds no credentials or secrets of its own. The vendored `ConfigLoader` (`src/medtext_redact/vendor/config_loader.py`) supports an optional `${VAR}` environment-variable expansion feature (`env_expand`), inherited from vendored shared infrastructure — it is `False` by default and never enabled by any command in this project.
- **Disk writes**: `parse-report single`/`parse-report spreadsheet` — the redact/highlight commands — write nothing to disk beyond the explicit output the user requested (stdout, or the `--result` file). See `docs/threat-model.md` for the full picture.

## This repository's own history

This repository's git history predates its current synthetic-only data policy and was manually audited and cleaned prior to public release — see [`docs/provenance-and-data-boundary.md`](docs/provenance-and-data-boundary.md) for what that means concretely and its limits. That audit's findings are supplemented, not replaced, by this repository's own automated `gitleaks` scan over full history in CI — see [`docs/threat-model.md`](docs/threat-model.md) for that scan's actual result.
