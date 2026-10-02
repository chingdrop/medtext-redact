# Security policy

## Supported versions

This is a single-maintainer reference implementation, not a versioned product with a support matrix. Only the latest commit on `main` is supported; there is no backport or LTS policy.

## Reporting a vulnerability

Please report security issues privately via GitHub's [private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing/privately-reporting-a-security-vulnerability) (Security tab → Advisories → "Report a vulnerability") rather than opening a public issue.

This is a solo-maintained portfolio project: reports are handled best-effort, with no guaranteed response-time SLA.

## Scope

This tool processes text the user provides on the command line or in a file they point it at. Specifically, confirmed by reading the code, not assumed:

- **Network activity**: none. The tool makes no outbound network calls: the US Census surname list is bundled with the package, spaCy's NER model is an installed package, and Presidio's email recognizer is pinned to `tldextract`'s bundled Public Suffix List rather than fetching it. No user-provided text, file content, or other input is ever transmitted anywhere over a network by this tool. (Only `tools/build_surname_list.py`, a maintainer script that rebuilds the bundled list, contacts the Census Bureau.)
- **Credentials**: this tool holds no credentials or secrets of its own. The vendored `ConfigLoader` (`src/medtext_redact/vendor/config_loader.py`) supports an optional `${VAR}` environment-variable expansion feature (`env_expand`), inherited from vendored shared infrastructure — it is `False` by default and never enabled by any command in this project.
- **Disk writes**: `parse-report single`/`parse-report spreadsheet` — the redact/highlight commands — write no report content to disk beyond the explicit output the user requested (stdout, or the `--result` file). See `docs/threat-model.md` for the full picture.

## This repository's own history

This repository's git history predates its current synthetic-only data policy and was manually audited and cleaned prior to public release — see [`docs/provenance-and-data-boundary.md`](docs/provenance-and-data-boundary.md) for what that means concretely and its limits. That audit's findings are supplemented, not replaced, by this repository's own automated `gitleaks` scans in CI (new commits on every push and PR, full history weekly) — see [`docs/threat-model.md`](docs/threat-model.md) for the most recent full-history result.
