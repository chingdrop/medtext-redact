# Threat model

## What this tool processes

Medtext-Redact processes arbitrary text supplied by the user — directly via `--text`, piped via stdin, or read from a file the user points it at (`--sample`/`--result` spreadsheets, `--keywords-file`).

Confirmed by reading the code, not assumed:

- `parse-report single` and `parse-report spreadsheet` — the redaction/highlighting commands — write **nothing to disk** beyond the explicit output the user requested: `single` writes only to stdout; `spreadsheet` writes only to the `--result` file. Neither logs report content; the only logging in this path (`core/utils/files_and_storage.py`) logs file paths and byte/character counts, never content.
- The only network call anywhere in `src/medtext_redact` is a one-time, one-directional download of a public US Census surname list (`core/api_tools.py`). No user-provided text is ever transmitted over a network by this tool.

## The detection boundary, with real numbers

`parse-report` has two detection engines. `--engine rules` (the default) is regex and a loaded surname gazetteer, with no NER — see [`docs/decisions/0001-rule-based-detection-not-ner.md`](decisions/0001-rule-based-detection-not-ner.md). `--engine presidio` uses Microsoft Presidio's built-in recognizers with spaCy's `en_core_web_lg` NER model, running entirely locally: the model ships as an installed package, and the domain lookups in Presidio's email recognizer are pinned to `tldextract`'s bundled Public Suffix List snapshot so they never fetch it over the network. Current measured recall/precision, from `tests/e2e/test_recall_precision.py`, run fresh for this document:

| Category | `rules` recall | `rules` precision | `presidio` recall | `presidio` precision |
|---|---|---|---|---|
| Names (surname in the loaded gazetteer) | 100% | 100% | 85% | 100% |
| Names (surname *not* in the gazetteer) | **0%** | n/a | 100% | 100% |
| Bare first names | **0%** | n/a | 75% | 100% |
| Dates (MM/DD/YYYY family, 1900–2099) | 100% | 100% | 95% | 100% |
| Dates (mismatched separators, pre-1900) | **0%** | n/a | 100% | 100% |
| Ages | 100% | 100% | **40%** | 100% |
| Gender terms | 100% | 100% | **0%** | n/a |
| Phone numbers | 100% | 100% | 60% | 100% |
| Street addresses | 100% | 100% | **20%** | 100% |
| Medical record numbers | 100% | 100% | **20%** | 100% |
| Highlighted keywords (symptoms, diagnoses, medications) | 100% | 100% | 100% | 100% |

False positives on non-PHI decoys: a gazetteer surname used as an ordinary word ("Grace period") is masked by `rules` in 4 of 4 cases and by `presidio` in 0 of 4; a space-separated number triplet that reads as a count is masked by `presidio` in 1 of 4 cases and by `rules` in none.

**Identifier categories with no detector in `rules`**: fax numbers, email addresses, Social Security numbers, health plan beneficiary numbers, account numbers, certificate/license numbers, vehicle identifiers (including license plates), device identifiers, web URLs, IP addresses, biometric identifiers, and full-face photographs (this tool processes text only). `presidio` has built-in recognizers for several of these (email addresses, URLs, IP addresses, US SSNs, US bank account numbers, US driver's license and passport numbers, medical license numbers), but **none of them is measured by this repository's test suite yet** — treat them as unverified. Neither engine detects biometric identifiers, device identifiers, vehicle identifiers, or health plan beneficiary numbers.

## The single most important sentence in this document

**This tool's recall is not 100% on real clinical text, under either engine.** The table above shows each engine missing whole categories the other catches: `rules` misses every name outside its surname gazetteer, every bare first name, and every date outside its pattern; `presidio` misses every gender term and most ages, MRNs, and street addresses. And the table only measures the categories this repository's synthetic fixtures contain — identifiers no fixture exercises are unmeasured, not safe. A real miss on real text means PHI remains in the "redacted" output. Anyone using this tool against real patient data must treat its output as **assistive, not authoritative**, and follow it with manual or clinically-validated review before relying on it for any compliance purpose.

## Residual risk: this repository's own history

This repository's git history predates its current synthetic-only data policy (see [`docs/provenance-and-data-boundary.md`](provenance-and-data-boundary.md)) and was manually audited and cleaned before public release, combined with `gitleaks` and TruffleHog scans over full history (completed 2026-09-29). That audit is a **point-in-time human review, not an automated guarantee**. This repository's CI now runs `gitleaks` against full history (`fetch-depth: 0`) on every push, PR, and weekly, as a standing, automated supplement to that manual review — not a replacement for it. **Result of that scan as run for this document: 408 commits scanned, no leaks found.** If a future automated or manual review finds something this one didn't, that finding takes precedence over this statement.

## Scope

This is a reference implementation demonstrating a rule-based approach to HIPAA Safe Harbor's identifier categories — not a certified or clinically validated de-identification product. See [`docs/provenance-and-data-boundary.md`](provenance-and-data-boundary.md) for the full scope disclaimer.
