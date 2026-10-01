# 0007. Presidio detection, with the regex rules ported in as recognizers

Status: Accepted (2026-10-01). Supersedes [0001](0001-rule-based-detection-not-ner.md); amends [0002](0002-gazetteer-based-name-detection.md).

## Context

[0001](0001-rule-based-detection-not-ner.md) recorded detection as regex plus a surname gazetteer, with no NER. Its measured 100% recall only covered what the rules attempted: the recall/precision fixtures labeled surnames outside the gazetteer, bare first names, and dates with mismatched separators or pre-1900 years as non-PHI, because the rules were never designed to catch them. Once those were relabeled as the PHI they are, the rules measured **0% recall** on all four.

The repository also wrapped two other de-identification systems — Philter-UCSF (a submodule run in a separate interpreter) and a Spark NLP Docker environment — neither of which could run in-process. They were removed to focus the project on one engine.

## Decision

Detect PHI with [Microsoft Presidio](https://microsoft.github.io/presidio/) (`presidio-analyzer`/`presidio-anonymizer`), using spaCy's `en_core_web_lg` NER model, Presidio's built-in recognizers, and the old regex rules ported in as custom recognizers (`src/medtext_redact/core/presidio_recognizers.py`):

- Each regex in `src/medtext_redact/core/phi_patterns.py` (dates, unvalidated US phone numbers, labeled MRNs, street addresses, ages) becomes a `PatternRecognizer`; gender terms become a deny list.
- The census surname gazetteer becomes `SurnameGazetteerRecognizer`, reusing `NameMasker`'s Aho-Corasick matching.
- Masking keeps the old format — every word character replaced with `*`, length preserved — so keyword highlighting and the test suite's span offsets are unaffected.

## Alternatives considered

- **Presidio's built-in recognizers alone.** Measured with the corrected ground truth: no gender detector (0% recall), and 40% / 20% / 20% recall on ages, MRNs, and street addresses. Its phone recognizer validates numbers and rejected 2 of 5 synthetic ones.
- **Keep both engines behind a `--engine` flag.** Built and measured as an intermediate step. The two failed in opposite places, and Presidio with the ported rules matched or beat the rules alone on recall in every category, so a second engine would only have been maintenance cost.
- **Filter gazetteer hits with spaCy's dependency parse** to stop masking surnames used as ordinary words ("Grace period", where "Grace" modifies a noun). Rejected: the same filter drops real names in phrases like "the Okafor family", and recall comes first.

## Consequences

- Recall: 100% on every measured category except bare first names (75%, NER only). See `docs/threat-model.md` for the table.
- Precision: the gazetteer still masks "Grace period" (4 of 4), as the rules always did. New: a space-separated number triplet that reads as a count is fully masked (4 of 4), because the age recognizer masks the small numbers and spaCy tags the year as a date.
- Presidio's built-in recognizers add detectors for email addresses, URLs, IP addresses, SSNs, and other categories the rules never covered — but none is measured by the test suite yet.
- The install grows by about 400 MB (the spaCy model, pinned to its official release wheel since spaCy models aren't on PyPI), and the analyzer takes several seconds to load once per process.
- The census surname download remains the tool's only network call: Presidio's email recognizer is pinned to `tldextract`'s bundled Public Suffix List rather than fetching it.

## Evidence

- `src/medtext_redact/core/presidio_tools.py`, `presidio_recognizers.py`, `phi_patterns.py`
- `tests/e2e/test_recall_precision.py` and its gated expectations
- The commit history of this change: relabeling the ground truth, adding Presidio as a second engine, porting the rules, then retiring the rules engine
