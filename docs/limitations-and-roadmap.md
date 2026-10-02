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

## Possible next steps

Planned features, known bugs, and open questions are tracked in [`TODO.md`](../TODO.md).
