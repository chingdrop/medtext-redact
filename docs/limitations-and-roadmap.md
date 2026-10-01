# Limitations and roadmap

## Known limitations

This is a reference implementation of redaction aligned to HIPAA Safe Harbor's identifier categories, built on Microsoft Presidio — not a validated or certified de-identification tool. See [`docs/threat-model.md`](threat-model.md) for the full picture; this section states the specifics plainly.

**Recall/precision, from a fresh run of `tests/e2e/test_recall_precision.py`** (full table in [`docs/threat-model.md`](threat-model.md)): 100% recall and precision on every category with a detector — names inside and outside the surname gazetteer, dates in any of the tested formats, ages, gender terms, phone numbers, street addresses, MRNs, email addresses, US SSNs, URLs, IP addresses — except:

- **Bare first names.** Caught only by spaCy's NER (the gazetteer holds surnames only), so recall depends on the names drawn: 4 of 4 in the current fixture set, 3 of 4 in the previous one. Not gated.
- **"Grace period": 4 of 4 false positives.** The surname gazetteer masks any listed surname, including when it's used as an ordinary word. spaCy's parse could tell the two apart here ("Grace" modifies a noun), but the same filter would drop real names in phrases like "the Okafor family", so recall wins.
- **Space-separated number triplets: 4 of 4 false positives.** The age recognizer treats any bare number from 0 to 150 as a possible age (a deliberate recall-over-precision choice), and spaCy tags the year as a date, so a count like "rechecked 9 28 1952 times" is fully masked.

**Not measured or not detected**: email addresses, US SSNs, URLs, and IP addresses are measured at 100%. Presidio also has built-in recognizers for US bank account, driver's license, passport, ITIN, and medical license numbers, and credit card numbers, but no fixture exercises them yet. Nothing detects health plan beneficiary numbers, vehicle or device identifiers, biometric identifiers, or full-face photographs (this tool processes text only).

## Possible next steps

The first item is a planned next step. The rest are pulled from existing `TODO`/`FIXME` comments in code and `TODO(craig)` markers already left in `docs/decisions/`, `docs/provenance-and-data-boundary.md`, and `docs/threat-model.md` — directions someone left a note about, not commitments.

- **Measure the rest of Presidio's built-in recognizers**: add fixtures for bank account, driver's license, passport, ITIN, medical license, and credit card numbers.
- **Performance**: `src/medtext_redact/commands/reports.py:31` — `parse-report`'s commands are noted as too slow and a candidate for optimization.
- **Document why the gazetteer approach was chosen for names**, with no alternative currently recorded — [`docs/decisions/0002-gazetteer-based-name-detection.md`](decisions/0002-gazetteer-based-name-detection.md).
- **Confirm the repository-rename record is complete** — [`docs/decisions/0006-repository-rename-before-public-release.md`](decisions/0006-repository-rename-before-public-release.md) flags that its generic framing needs a maintainer's confirmation.
