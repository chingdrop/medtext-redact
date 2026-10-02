# 0001. Rule-based detection, not NER

Status: Superseded by [0007](0007-presidio-detection-with-ported-rules.md) (2026-10-01). Originally accepted; predates recorded reasoning in this repository's history; earliest evidence 2025-06-04.

## Context

Medtext-Redact needs to detect and mask HIPAA Safe Harbor identifier categories (names, dates, ages, phone numbers, addresses, MRNs, gender terms) in unstructured clinical text.

## Decision

`PhiSanitizer` (`src/medtext_redact/core/text_tools.py`) detects every category with regular expressions and a loaded surname gazetteer (`NameMasker`, Aho-Corasick). There is no named-entity-recognition model, no machine-learning component, and no training or labeled corpus anywhere in this repository — confirmed by inspection of every `sanitize_*` method.

## Alternatives considered

Not recorded: no commit message, code comment, or doc discusses why NER wasn't used. The open question is tracked in [`TODO.md`](../../TODO.md).

## Consequences

- Every match is explainable and directly testable: `tests/e2e/test_recall_precision.py` measures exact recall/precision per category against a synthetic ground-truth manifest.
- Detection is strictly bounded by what's pattern-matched or gazetteer-listed. It will miss identifiers a human reader would catch instantly if they don't match a known pattern or name list — documented plainly in `docs/provenance-and-data-boundary.md`, not glossed over.
- No model weights, no GPU, no inference dependency — the entire detection surface is auditable regex and a flat name list.

## Evidence

- `src/medtext_redact/core/text_tools.py` (`PhiSanitizer`, all `sanitize_*` methods)
- `src/medtext_redact/core/utils/regex_utils.py` (`NameMasker`, `compile_keywords_pattern`)
- README.md, "Process" section ("Rule-based pattern matching... not named-entity recognition")
- `docs/provenance-and-data-boundary.md`, "Scope disclaimer"
