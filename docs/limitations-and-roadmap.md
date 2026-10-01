# Limitations and roadmap

## Known limitations

This is a reference implementation demonstrating a rule-based approach to HIPAA Safe Harbor's identifier categories — not a validated or certified de-identification tool. See [`docs/threat-model.md`](threat-model.md) for the full picture; this section states the specifics plainly.

**Recall/precision, from a fresh run of `tests/e2e/test_recall_precision.py`:** every category with a real detector — names (surname in the loaded gazetteer), dates, ages, gender terms, phone numbers, street addresses, medical record numbers — currently measures **100% recall and 100% precision**. No category currently measures below 100% recall in this suite. The one number in the whole suite measured below 100% is a **precision** failure, not recall: **0% precision** when a gazetteer surname is used as an ordinary English word (e.g. "Grace period") — 4 of 4 such cases in the fixture set were false positives. In practice: this tool will over-redact a small, predictable class of common-word/name collisions rather than under-redact within its covered categories. See `src/medtext_redact/core/utils/regex_utils.py:NameMasker` and the `name_common_word` case in `tests/e2e/test_recall_precision.py`.

That clean 100%-recall table only covers what the tool *attempts*. Structural gaps that the test suite doesn't count as recall failures, because they're out of scope by design:

- **Bare first names**: `sanitize_names()` only ever loads Census *surnames* — a first name with no accompanying surname is never caught. See `src/medtext_redact/core/text_tools.py:sanitize_names`, and the `name_firstname_only` case in the test suite.
- **Surnames outside the loaded gazetteer**: detection is only as complete as the gazetteer's real-world coverage. See the `name_ungazetteered` case.

**Identifier categories with no detector at all**: fax numbers, email addresses, Social Security numbers, health plan beneficiary numbers, account numbers, certificate/license numbers, vehicle identifiers (including license plates), device identifiers, web URLs, IP addresses, biometric identifiers, and full-face photographs (this tool processes text only). Anything requiring named-entity recognition — an identifier that doesn't happen to match this tool's regex patterns or gazetteer — is missed regardless of how obvious it would be to a human reader; see [`docs/decisions/0001-rule-based-detection-not-ner.md`](decisions/0001-rule-based-detection-not-ner.md).

## Possible next steps

Pulled only from existing `TODO`/`FIXME` comments in code and `TODO(craig)` markers already left in `docs/decisions/`, `docs/provenance-and-data-boundary.md`, and `docs/threat-model.md`. These are directions someone left a note about, not commitments, and not this document's own ideas.

- **Performance**: `src/medtext_redact/commands/reports.py:19` — `parse-report`'s commands are noted as too slow and a candidate for optimization.
- **Document why rule-based detection was chosen over NER** — [`docs/decisions/0001-rule-based-detection-not-ner.md`](decisions/0001-rule-based-detection-not-ner.md) notes the repository doesn't currently record this reasoning anywhere.
- **Document why the gazetteer approach was chosen for names**, with no alternative currently recorded — [`docs/decisions/0002-gazetteer-based-name-detection.md`](decisions/0002-gazetteer-based-name-detection.md).
- **Confirm the repository-rename record is complete** — [`docs/decisions/0006-repository-rename-before-public-release.md`](decisions/0006-repository-rename-before-public-release.md) flags that its generic framing needs a maintainer's confirmation.
