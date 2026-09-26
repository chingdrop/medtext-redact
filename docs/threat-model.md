# Threat model

## What this tool processes

Medtext-Redact processes arbitrary text supplied by the user — directly via `--text`, piped via stdin, or read from a file the user points it at (`--sample`/`--result` spreadsheets, `--keywords-file`).

Confirmed by reading the code, not assumed:

- `parse-report single` and `parse-report spreadsheet` — the redaction/highlighting commands — write **nothing to disk** beyond the explicit output the user requested: `single` writes only to stdout; `spreadsheet` writes only to the `--result` file. Neither logs report content; the only logging in this path (`core/utils/files_and_storage.py`) logs file paths and byte/character counts, never content.
- The separate `philter` command (a Philter-UCSF wrapper, a different code path entirely) is **not** the same: `split_csv_to_txt` writes the user's raw, pre-redaction report text to per-accession `.txt` files in a system temp directory (`tempfile.mkdtemp(prefix="medtext_redact_philter_")`) so it can hand them to a separate subprocess. On success this directory is removed (`shutil.rmtree`). **On failure, it is left on disk** — the subprocess-failure path prints its location to stderr; the "interpreter not found" failure path does not mention it at all, though the directory (containing unredacted text) still exists on disk in both cases.
- The only network call anywhere in `src/medtext_redact` is a one-time, one-directional download of a public US Census surname list (`core/api_tools.py`). No user-provided text is ever transmitted over a network by this tool.

## The detection boundary, with real numbers

Detection is rule-based (regex and a loaded surname gazetteer), not NER, not machine learning — see [`docs/decisions/0001-rule-based-detection-not-ner.md`](decisions/0001-rule-based-detection-not-ner.md). Current measured recall/precision, from `tests/e2e/test_recall_precision.py`, run fresh for this document:

| Category | Recall | Precision |
|---|---|---|
| Names (surname in gazetteer) | 100% | 100% |
| Dates | 100% | 100% |
| Ages | 100% | 100% |
| Gender terms | 100% | 100% |
| Phone numbers | 100% | 100% |
| Street addresses | 100% | 100% |
| Medical record numbers | 100% | 100% |

**Identifier categories with no detector at all**: fax numbers, email addresses, Social Security numbers, health plan beneficiary numbers, account numbers, certificate/license numbers, vehicle identifiers (including license plates), device identifiers, web URLs, IP addresses, biometric identifiers, and full-face photographs (this tool processes text only). Anything in this list, present in real text, passes through unredacted. Anything requiring NER — an identifier this tool's patterns or gazetteer don't happen to match — is missed regardless of how obvious it would be to a human reader.

## The single most important sentence in this document

**This tool's recall is not 100% on real clinical text, stated plainly and not softened by the clean table above: that table measures 100% recall only for the categories and identifiers this tool actually attempts, and whole real-world categories — a real name outside its loaded surname gazetteer, any bare first name, and every "not covered at all" category listed above — are structural misses this measurement never counts as failures because they're out of scope by design, not because they're rare.** The one number in the whole suite that is measured below 100% is a precision failure, not a recall one — **0% precision on a gazetteer surname used as an ordinary English word** (4 of 4 occurrences in the fixture set were false positives) — but a real miss on real text means PHI remains in the "redacted" output regardless of which metric moves. Anyone using this tool against real patient data must treat its output as **assistive, not authoritative**, and follow it with manual or clinically-validated review before relying on it for any compliance purpose.

## Residual risk: this repository's own history

This repository's git history predates its current synthetic-only data policy (see [`docs/provenance-and-data-boundary.md`](provenance-and-data-boundary.md)) and was manually audited and cleaned before public release. That audit is a **point-in-time human review, not an automated guarantee**. This repository's CI now runs `gitleaks` against full history (`fetch-depth: 0`) on every push, PR, and weekly, as a standing, automated supplement to that manual review — not a replacement for it. **Result of that scan as run for this document: 390 commits scanned, no leaks found.** If a future automated or manual review finds something this one didn't, that finding takes precedence over this statement.

## Scope

This is a reference implementation demonstrating a rule-based approach to HIPAA Safe Harbor's identifier categories — not a certified or clinically validated de-identification product. See [`docs/provenance-and-data-boundary.md`](provenance-and-data-boundary.md) for the full scope disclaimer.
