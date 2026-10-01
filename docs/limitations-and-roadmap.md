# Limitations and roadmap

## Known limitations

This is a reference implementation demonstrating a rule-based approach to HIPAA Safe Harbor's identifier categories — not a validated or certified de-identification tool. See [`docs/threat-model.md`](threat-model.md) for the full picture; this section states the specifics plainly.

**Recall/precision, from a fresh run of `tests/e2e/test_recall_precision.py`:** `parse-report` has two engines, and they fail in opposite places. The full per-category table is in [`docs/threat-model.md`](threat-model.md); in short:

- **`--engine rules` (default)** measures 100% recall and precision on every category it has a pattern or gazetteer entry for — gazetteer surnames, MM/DD/YYYY-family dates, ages, gender terms, phone numbers, street addresses, MRNs. It measures **0% recall** on real PHI outside those patterns: surnames missing from the gazetteer, bare first names (it only ever loads Census *surnames*; see `src/medtext_redact/core/text_tools.py:sanitize_names`), and dates with mismatched separators or pre-1900 years. It also masks a gazetteer surname used as an ordinary word ("Grace period") in 4 of 4 cases.
- **`--engine presidio`** catches all of those (100% on unlisted surnames and unusual dates, 75% on bare first names, 0 of 4 false positives on "Grace period"), but its built-in recognizers have **no gender detector** (0% recall) and weak coverage of ages (40%), MRNs (20%), and street addresses (20%). Its phone recognizer validates numbers and so rejects ones with invalid area codes (60% here, on Faker-generated numbers).

**Identifier categories with no detector at all in `rules`**: fax numbers, email addresses, Social Security numbers, health plan beneficiary numbers, account numbers, certificate/license numbers, vehicle identifiers (including license plates), device identifiers, web URLs, IP addresses, biometric identifiers, and full-face photographs (this tool processes text only). `presidio` has built-in recognizers for email addresses, URLs, IP addresses, US SSNs, bank account, driver's license and passport numbers, and medical license numbers — none yet measured by this repository's test suite.

## Possible next steps

The first item is the planned next step for the Presidio engine. The rest are pulled from existing `TODO`/`FIXME` comments in code and `TODO(craig)` markers already left in `docs/decisions/`, `docs/provenance-and-data-boundary.md`, and `docs/threat-model.md` — directions someone left a note about, not commitments.

- **Port the `rules` patterns into Presidio** as custom recognizers (gender terms, ages, MRNs, street addresses, unvalidated phone numbers, and the surname gazetteer), so a single Presidio-based engine combines both columns of the table above, then retire `PhiSanitizer`'s own detection. Add fixtures for the Presidio categories the suite doesn't measure yet (email, SSN, URLs, IP addresses).
- **Performance**: `src/medtext_redact/commands/reports.py:31` — `parse-report`'s commands are noted as too slow and a candidate for optimization.
- **Document why rule-based detection was chosen over NER** — [`docs/decisions/0001-rule-based-detection-not-ner.md`](decisions/0001-rule-based-detection-not-ner.md) notes the repository doesn't currently record this reasoning anywhere.
- **Document why the gazetteer approach was chosen for names**, with no alternative currently recorded — [`docs/decisions/0002-gazetteer-based-name-detection.md`](decisions/0002-gazetteer-based-name-detection.md).
- **Confirm the repository-rename record is complete** — [`docs/decisions/0006-repository-rename-before-public-release.md`](decisions/0006-repository-rename-before-public-release.md) flags that its generic framing needs a maintainer's confirmation.
