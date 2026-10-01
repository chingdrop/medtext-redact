# Threat model

## What this tool processes

Medtext-Redact processes arbitrary text supplied by the user — directly via `--text`, piped via stdin, or read from a file the user points it at (`--sample`/`--result` spreadsheets, `--keywords-file`).

Confirmed by reading the code, not assumed:

- `parse-report single` and `parse-report spreadsheet` — the redaction/highlighting commands — write **no report content to disk** beyond the explicit output the user requested: `single` writes only to stdout; `spreadsheet` writes only to the `--result` file. Neither logs report content; the only logging in this path (`core/utils/files_and_storage.py`) logs file paths and byte/character counts, never content. The one other file written is the cached public Census surname list (`data/census_2010_names.txt`), on first use.
- The only network call anywhere in `src/medtext_redact` is a one-time, one-directional download of a public US Census surname list (`core/api_tools.py`). No user-provided text is ever transmitted over a network by this tool. Presidio and spaCy run locally and make no network calls: the model is an installed package, and Presidio's email recognizer is pinned to `tldextract`'s bundled Public Suffix List rather than fetching it.
- If the surname download fails — census.gov sometimes rejects automated requests with an HTML page — `parse-report` stops with an error (`CensusDownloadError`) explaining how to save the list manually. It never falls back to redacting without the surname gazetteer, which would silently lower recall.

## The detection boundary, with real numbers

Detection uses Microsoft Presidio: spaCy's `en_core_web_lg` NER model, Presidio's built-in recognizers, and custom recognizers ported from this project's earlier regex rules (ages, gender terms, labeled MRNs, street addresses, unvalidated US phone numbers, MM/DD/YYYY-family dates, and a US Census surname gazetteer) — see `src/medtext_redact/core/presidio_recognizers.py`. It runs entirely locally: the model ships as an installed package, and the domain lookups in Presidio's email recognizer are pinned to `tldextract`'s bundled Public Suffix List snapshot so they never fetch it over the network. Current measured recall/precision, from `tests/e2e/test_recall_precision.py`, run fresh for this document:

| Category | Recall | Precision |
|---|---|---|
| Names (surname in the loaded gazetteer) | 100% | 100% |
| Names (surname *not* in the gazetteer) | 100% | 100% |
| Bare first names | 100%* | 100% |
| Dates (MM/DD/YYYY family) | 100% | 100% |
| Dates (mismatched separators, pre-1900 years) | 100% | 100% |
| Ages | 100% | 100% |
| Gender terms | 100% | 100% |
| Phone numbers | 100% | 100% |
| Street addresses | 100% | 100% |
| Medical record numbers | 100% | 100% |
| Email addresses | 100% | 100% |
| US Social Security numbers | 100% | 100% |
| URLs | 100% | 100% |
| IP addresses (IPv4 and IPv6) | 100% | 100% |
| Highlighted keywords (symptoms, diagnoses, medications) | 100% | 100% |

\* Bare first names are caught by NER alone (the surname gazetteer has no first names), so this varies with the names the generator draws: 4 of 4 in the current fixture set, 3 of 4 in the previous one. Reported, not gated.

Two measured false positives, stated plainly: a gazetteer surname used as an ordinary word ("Grace period") is masked in 4 of 4 cases, and a space-separated number triplet that reads as a count ("rechecked 9 28 1952 times") is masked in 4 of 4 cases.

URLs are covered by both Presidio's recognizer and a pattern of this project's own (`URL_PATTERN`): Presidio's alone matches `miller.biz` as `miller.bi` and leaves the final letter visible. **Built-in Presidio categories not yet measured**: US bank account, driver's license, passport, ITIN, and medical license numbers, and credit card numbers all have recognizers, but **no fixture in this repository's test suite exercises them** — treat them as unverified. **No detector at all**: fax numbers (unless phone-shaped), health plan beneficiary numbers, vehicle identifiers (including license plates), device identifiers, biometric identifiers, and full-face photographs (this tool processes text only).

## The single most important sentence in this document

**This tool's recall is not 100% on real clinical text.** The table above is measured on synthetic notes built from a handful of templates, against a small stubbed surname gazetteer; real clinical text is far more varied, and spaCy's NER model was trained on general English, not clinical notes. It missed 1 of 4 bare first names on a previous fixture set. And the table only measures the categories this repository's fixtures contain — identifiers no fixture exercises are unmeasured, not safe. A real miss on real text means PHI remains in the "redacted" output. Anyone using this tool against real patient data must treat its output as **assistive, not authoritative**, and follow it with manual or clinically-validated review before relying on it for any compliance purpose.

## Residual risk: this repository's own history

This repository's git history predates its current synthetic-only data policy (see [`docs/provenance-and-data-boundary.md`](provenance-and-data-boundary.md)) and was manually audited and cleaned before public release, combined with `gitleaks` and TruffleHog scans over full history (completed 2026-09-29). That audit is a **point-in-time human review, not an automated guarantee**. This repository's CI runs `gitleaks` as a standing, automated supplement to that manual review — not a replacement for it. On pushes and pull requests, the `gitleaks-action` scans only the new commits; the weekly scheduled run scans full history (`fetch-depth: 0`). Because `gitleaks` runs after `pip-audit` in the same CI job, a `pip-audit` failure skips it for that run — the scheduled run on 2026-09-28 never reached it. **Result of a full-history scan run locally for this document (gitleaks 8.30.1, 2026-10-01): 403 commits scanned, no leaks found.** If a future automated or manual review finds something this one didn't, that finding takes precedence over this statement.

## Scope

This is a reference implementation of redaction aligned to HIPAA Safe Harbor's identifier categories — not a certified or clinically validated de-identification product. See [`docs/provenance-and-data-boundary.md`](provenance-and-data-boundary.md) for the full scope disclaimer.
