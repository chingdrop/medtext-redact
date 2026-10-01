# 0002. Gazetteer-based name detection, and its documented limits

Status: Accepted, amended by [0007](0007-presidio-detection-with-ported-rules.md) (predates recorded reasoning in this repository's history; limits measured and documented 2026-09-25). Since 0007, the gazetteer runs as a Presidio recognizer alongside spaCy NER, which catches names outside the list; the method names below describe the original implementation.

## Context

Names are one of the hardest Safe Harbor categories to detect without NER: no fixed pattern distinguishes a name from any other capitalized word.

## Decision

`sanitize_names()` loads a flat list of US Census **surnames** (`load_census_names()`, via `CensusNamesApi`) and masks exact, word-boundary matches with `NameMasker` (Aho-Corasick). It does not load first names, and it matches nothing outside that loaded list.

## Alternatives considered

<!-- TODO(craig): no alternative to the gazetteer approach (e.g. a first-name list, NER, or a hybrid) is documented anywhere in the repo's history for this specific choice. -->

## Consequences

From `tests/e2e/test_recall_precision.py`, run against the current codebase:

- **`name`** (surname present in the loaded gazetteer): **100% recall, 100% precision**.
- **`name_firstname_only`**: a bare first name with no accompanying surname is **never caught** — `sanitize_names()` has no first-name data at all. Structural, not a bug.
- **`name_ungazetteered`**: a real surname absent from the loaded list is **never caught**. Detection is only as complete as the gazetteer's real-world coverage.
- **`name_common_word`**: a gazetteer surname used as an ordinary English word (e.g. "Grace period") is still masked — **0% precision** on this case (4 of 4 occurrences in the fixture set were false positives). No surrounding-context model exists to disambiguate PHI usage from common-word usage.

Weakest category by design — stated plainly here with real numbers, not a vague caveat.

## Evidence

- `src/medtext_redact/core/text_tools.py:sanitize_names`
- `src/medtext_redact/core/utils/regex_utils.py:NameMasker`
- `src/medtext_redact/core/utils/enums.py:load_census_names`
- `tests/e2e/test_recall_precision.py` (categories `name`, `name_firstname_only`, `name_ungazetteered`, `name_common_word`)
- Commit `86aadb9` ("Add synthetic clinical-note test coverage...")
