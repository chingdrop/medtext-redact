# Limitations and roadmap

## Known limitations

This is a reference implementation of redaction aligned to HIPAA Safe Harbor's identifier categories, built on Microsoft Presidio — not a validated or certified de-identification tool. See [`docs/threat-model.md`](threat-model.md) for the full picture; this section states the specifics plainly.

**Recall/precision, from a fresh run of `tests/e2e/test_recall_precision.py`** (full table in [`docs/threat-model.md`](threat-model.md)): 100% recall and precision on every category with a detector — names inside and outside the surname gazetteer, dates in any of the tested formats, ages, gender terms, phone numbers, street addresses, MRNs, email addresses, US SSNs, URLs, IP addresses, credit card, bank account, driver's license, passport, ITIN, DEA, IBAN, crypto wallet, MAC address, and UK NHS numbers — except:

- **Bare first names.** Caught only by spaCy's NER (the gazetteer holds surnames only), so recall depends on the names drawn: 4 of 4 in the current fixture set, 3 of 4 in the previous one. Not gated.
- **Clinical text in general.** spaCy's `en_core_web_lg` was trained on general English, not clinical notes, and the suite's notes come from ten hand-written templates. The numbers above say how the detectors behave on those templates, not on real clinical prose.
- **"Grace period": 4 of 4 false positives.** The surname gazetteer masks any listed surname, including when it's used as an ordinary word. spaCy's parse could tell the two apart here ("Grace" modifies a noun), but the same filter would drop real names in phrases like "the Okafor family", so recall wins.
- **Space-separated number triplets: 4 of 4 false positives.** The age recognizer treats any bare number from 0 to 150 as a possible age (a deliberate recall-over-precision choice), and spaCy tags the year as a date, so a count like "rechecked 9 28 1952 times" is fully masked.
- **Long numbers: masked regardless of meaning.** Presidio's bank account, driver's license, and passport recognizers match bare digit runs, and this tool applies no score threshold, so any standalone number of 6 to 17 digits — a lab value, an accession number — is masked. A threshold or context requirement would restore those, at the cost of missing identifiers written without a label.

**Not detected**: Presidio ships recognizers for Medicare Beneficiary Identifiers (a health plan beneficiary number), NPIs, and ABA routing numbers, but they aren't enabled. Nothing detects health plan beneficiary numbers, vehicle or device identifiers, biometric identifiers, or full-face photographs (this tool processes text only).

**The census surname download can be rejected.** census.gov sometimes answers automated requests with a "Request Rejected" HTML page instead of the archive. `parse-report` then stops with an error explaining how to download the list in a browser and save it to `data/census_2010_names.txt`; it never redacts without the gazetteer.

## Possible next steps

The first item is a planned next step. The rest are pulled from existing `TODO`/`FIXME` comments in code and `TODO(craig)` markers already left in `docs/decisions/`, `docs/provenance-and-data-boundary.md`, and `docs/threat-model.md` — directions someone left a note about, not commitments.

- **Enable Presidio's Medicare Beneficiary Identifier recognizer** (`UsMbiRecognizer`), the closest thing available to a health plan beneficiary number detector, with a fixture to measure it. NPIs and ABA routing numbers are candidates too.
- **Performance**: `src/medtext_redact/commands/reports.py:25` — `parse-report`'s commands are noted as too slow and a candidate for optimization. One concrete cost: `PhiSanitizer.sanitize_presidio()` calls `load_census_names()` for every report, re-reading the surname file each time, so `parse-report spreadsheet` pays that once per row.
- **Document why the gazetteer approach was chosen for names**, with no alternative currently recorded — [`docs/decisions/0002-gazetteer-based-name-detection.md`](decisions/0002-gazetteer-based-name-detection.md).
- **Confirm the repository-rename record is complete** — [`docs/decisions/0006-repository-rename-before-public-release.md`](decisions/0006-repository-rename-before-public-release.md) flags that its generic framing needs a maintainer's confirmation.
