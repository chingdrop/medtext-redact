# 0003. Synthetic-data-only testing, with a construction-time manifest as ground truth

Status: Accepted (2026-09-25)

## Context

Testing recall/precision needs real-looking clinical text with known identifier locations. Using real (even anonymized or previously redacted) clinical text for this repository's test suite would reintroduce exactly the risk the provenance audit exists to eliminate — see `docs/provenance-and-data-boundary.md`: redacted real text is still real text.

## Decision

`tools/gen_fixtures.py` generates synthetic clinical notes from hand-written sentence templates, filled with Faker-generated fake demographics (names, dates, addresses, phone numbers, MRN-shaped IDs) and generic clinical vocabulary. As each note is assembled, the generator records a manifest of exactly which synthetic identifier was injected and at what character span — the ground truth `tests/e2e/test_recall_precision.py` scores against. The manifest is never reconstructed by re-running the redactor on its own output.

## Alternatives considered

Real (even de-identified) clinical text was not an option under this repository's data boundary. No other synthetic-data approach (e.g. a third-party synthetic-clinical-text corpus) is discussed anywhere in this repository's history.

## Consequences

- Recall/precision numbers are real and independently verifiable, but only against this generator's specific templates and vocabulary — they are not a claim about performance on arbitrary real clinical prose.
- Hard cases (near-misses, common-word/name collisions, out-of-range values) must be deliberately authored into the generator to be tested at all; the suite cannot discover a real-world failure mode the generator doesn't anticipate.
- New detector categories require corresponding generator support before they can be measured this way.

## Evidence

- `tools/gen_fixtures.py`
- `tests/e2e/test_recall_precision.py`
- `docs/provenance-and-data-boundary.md`, "Data boundary going forward"
- Commit `86aadb9` ("Add synthetic clinical-note test coverage for redact/highlight, fix bugs it surfaced")
