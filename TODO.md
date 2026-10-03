# TODO

Open bugs, planned features, and unanswered questions. Add new items here; remove them when they land, and record the change in [`CHANGELOG.md`](CHANGELOG.md).

## Bugs

- [ ] **Common English words are masked as surnames.** 107 of spaCy's 326 English stop words are real 2010 Census surnames ("The", "And", "In", "On", "For", "He", "She", "We", "No", "May", "Will", …), as are "Patient" and "Doctor". The gazetteer is case-sensitive, so it masks them whenever they're capitalized — typically at the start of a sentence ("The chart for…" → "*** chart for…"). The recall/precision suite can't see this because it substitutes an 8-name list for the real one. Fix: drop gazetteer entries that are common words (spaCy's `STOP_WORDS` is available offline), or mask them only when NER also tags a PERSON; measure with an e2e test that uses the real bundled list. Recall cost: real surnames like May (rank 304) or Will (rank 2,869) would then depend on NER.
- [ ] **Surnames with apostrophes, hyphens, or spaces aren't in the gazetteer.** The Census list strips punctuation ("O'Brien" is listed as "Obrien"), so the gazetteer never matches the usual spelling and those names depend on NER alone. Add punctuated variants, or normalize text the same way before matching.
- [ ] **Every standalone number of 6–17 digits is masked.** Presidio's bank account, driver's license, and passport recognizers match bare digit runs, and no score threshold is applied, so lab values and accession numbers are masked. See the score-threshold decision under Features.
- [ ] **Surnames used as ordinary words are masked** ("Grace period", 4 of 4 in the suite). The gazetteer can't tell a surname from the same word used ordinarily. A spaCy dependency-parse filter fixes this case but drops real names in phrases like "the Okafor family" (see ADR 0007).
- [ ] **Space-separated counts are masked** ("rechecked 9 28 1952 times", 4 of 4). The bare-number age pattern masks the small numbers and spaCy tags the year as a date.
- [ ] **Capitalized clinical words can be masked by NER.** Seen while probing card numbers: in "Accession 4555106199010102807 filed.", spaCy's NER masked the word "Accession". Not measured by the suite; needs fixtures with capitalized clinical terms to size it.
- [ ] **Bare first names depend on NER alone.** 4 of 4 in the current fixtures, 3 of 4 in the previous set. Not gated.

## Features

- [ ] **Release v3.0.0.** The `philter` and `spark-nlp` commands were removed and detection replaced since `v2.1.0`. Bump `version` in `pyproject.toml`, turn the changelog's Unreleased section into a release entry, and tag.
- [ ] **Enable Presidio's Medicare Beneficiary Identifier recognizer** (`UsMbiRecognizer`) with a fixture to measure it — the only available detector for the health plan beneficiary number Safe Harbor category. NPI and ABA routing number recognizers are candidates too. None is enabled by default.
- [ ] **Decide on a score threshold or context requirements** for Presidio's weak, bare-digit recognizers. That would fix the 6–17 digit over-masking above, at the cost of missing identifiers written without a label. Recall currently comes first.
- [ ] **More varied fixture templates.** The suite's notes come from 12 hand-written templates, 4 notes each; more phrasings would make the numbers mean more. Real clinical text, even de-identified, is ruled out by `docs/provenance-and-data-boundary.md`.
- [ ] **Performance.** `parse-report`'s commands are too slow (moved from a `ToDo` comment in `src/medtext_redact/commands/reports.py`). The surname list is now read once per process rather than once per report; profile what's left (spaCy's model load is several seconds per run).

## CI

- [ ] **Type-check all of `tools/` in CI.** `.github/workflows/ci.yml` runs `mypy src/medtext_redact tools/gen_fixtures.py`; change it to `tools/` so `tools/build_surname_list.py` is checked too.
- [ ] **Add the missing final newline** to `.github/workflows/ci.yml`.
- [ ] **Confirm the first full-history gitleaks run** in the new standalone `gitleaks` job: the weekly scheduled run on Monday 2026-10-05 at 06:00 UTC.

## Open questions

Moved from `TODO(craig)` markers in the ADRs. These need the maintainer's own knowledge; the repository doesn't record the answers.

- [ ] **Why wasn't NER used originally?** (from [ADR 0001](docs/decisions/0001-rule-based-detection-not-ner.md)) No commit message, code comment, or doc discusses the tradeoff. If there was a real reason (testability against synthetic ground truth without a trained model, no labeled corpus available, simplicity, etc.), state it in ADR 0001's "Alternatives considered"; otherwise say no alternative was documented. Mostly historical now that [ADR 0007](docs/decisions/0007-presidio-detection-with-ported-rules.md) supersedes 0001.
- [ ] **Were alternatives to the gazetteer considered for names?** (from [ADR 0002](docs/decisions/0002-gazetteer-based-name-detection.md)) No alternative (a first-name list, NER, or a hybrid) is documented anywhere in the repo's history for this choice. Record it in ADR 0002 if there was one.
- [ ] **Is the repository-rename record complete?** [ADR 0006](docs/decisions/0006-repository-rename-before-public-release.md) was flagged as needing a maintainer's confirmation of its generic framing. Its marker has since been removed, so this may already be done; confirm and close.
