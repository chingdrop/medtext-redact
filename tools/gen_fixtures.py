#!/usr/bin/env python3
"""
Generate synthetic clinical notes plus a ground-truth manifest of exactly
which synthetic identifiers were injected and where (category + span).

All demographics are Faker-generated fakes; all clinical vocabulary below is
generic medical terminology, not copied from any real patient record. The
manifest is built while the note is assembled -- never by re-running the
redactor on its own output -- so it's an independent ground truth for
recall/precision testing.

Usage:
    uv run python tools/gen_fixtures.py --seed 42 --count 20 --out-dir tools/fixtures_out
"""

from __future__ import annotations

import argparse
import json
import random
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from faker import Faker

# ---------------------------------------------------------------------------
# Ground-truth gazetteer: the exact surname list the redactor's NameMasker is
# stubbed to load during recall/precision testing. This mirrors how the real
# tool depends on an external, exact-match census surname list (see
# `fake_census_names` in tests/core/test_text_tools.py) -- it isolates the
# masking *mechanism's* correctness from the census data's real-world
# coverage, which is a separate, external data-quality question.
#
# "Grace" and "Hope" are included deliberately: both are real US surnames
# *and* ordinary English words, used below to generate a documented
# precision hit (a name-shaped word used in a non-PHI sense still gets
# masked, since the tool has no way to tell PHI usage from common-word usage
# without a surrounding-context model).
GAZETTEER_SURNAMES = [
    "Whitfield",
    "Delacroix",
    "Nakamura",
    "Okafor",
    "Abernathy",
    "Castellano",
    "Grace",
    "Hope",
]

CLINICAL_VOCAB = {
    "symptom": [
        "shortness of breath",
        "chest pain",
        "persistent cough",
        "abdominal pain",
        "fatigue",
        "dizziness",
        "nausea",
        "low-grade fever",
    ],
    "diagnosis": [
        "hypertension",
        "type 2 diabetes mellitus",
        "community-acquired pneumonia",
        "atrial fibrillation",
        "chronic kidney disease",
        "osteoarthritis",
        "hypothyroidism",
    ],
    "medication": [
        "lisinopril",
        "metformin",
        "atorvastatin",
        "levothyroxine",
        "amoxicillin",
        "albuterol",
    ],
}


@dataclass
class Span:
    category: str
    text: str
    start: int
    end: int
    expected_redacted: bool
    note: str = ""


TOKEN_RE = re.compile(r"<<(\w+)>>")


def _fmt_date(d, sep: str) -> str:
    return f"{d.month}{sep}{d.day}{sep}{d.year}"


def _mrn(rng: random.Random) -> str:
    return "MRN-" + "".join(rng.choice("0123456789") for _ in range(7))


def make_generators(fake: Faker, rng: random.Random) -> dict:
    """Each generator returns (text, category, expected_redacted, note)."""

    def name_gazetteered(_):
        surname = rng.choice(GAZETTEER_SURNAMES)
        return surname, "name", True, "surname present in the stubbed gazetteer"

    def name_ungazetteered(_):
        # Faker's full last-name pool is effectively disjoint from our small
        # fixed gazetteer; a real miss here documents a *data coverage* gap
        # (the tool only masks surnames it's been given), not a mechanism bug.
        surname = fake.last_name()
        return surname, "name_ungazetteered", False, "surname NOT in the loaded gazetteer (coverage gap, not a bug)"

    def name_firstname_only(_):
        first = fake.first_name()
        return first, "name_firstname_only", False, "bare first name -- sanitize_names() only ever loads surnames"

    def name_common_word(_):
        # Used in a template where it reads as an ordinary word, not a name.
        word = rng.choice(["Grace", "Hope"])
        return word, "name_common_word", False, "gazetteer surname used as an ordinary word, not as PHI"

    def date_valid(_):
        d = fake.date_of_birth(minimum_age=1, maximum_age=95)
        sep = rng.choice(["/", "-", "."])
        return _fmt_date(d, sep), "date", True, ""

    def date_mismatched_sep(_):
        d = fake.date_of_birth(minimum_age=1, maximum_age=95)
        return (
            f"{d.month}/{d.day}-{d.year}",
            "date_mismatched_sep",
            False,
            "mismatched separators, per the code's own doc comment",
        )

    def date_space_sep(_):
        d = fake.date_of_birth(minimum_age=1, maximum_age=95)
        return (
            f"{d.month} {d.day} {d.year}",
            "date_space_sep",
            False,
            "space-separated triplet -- not a documented date separator",
        )

    def date_out_of_range_year(_):
        return "5/6/1850", "date_out_of_range", False, "year outside the 1900-2099 window the pattern allows"

    def age_valid(_):
        n = rng.randint(1, 99)
        phrasing = rng.choice([f"{n} years old", f"{n}-yrs-old", f"{n} yo"])
        return phrasing, "age", True, ""

    def age_bare_number(_):
        # Masked by design per the code's own comment ("Allow '34'..."); not
        # a bug, but a real precision cost worth reporting honestly.
        n = rng.randint(1, 149)
        return str(n), "age_bare_number", True, "bare in-range number -- masked by documented design, not a bug"

    def age_out_of_range(_):
        return str(rng.randint(151, 999)), "age_out_of_range", False, "outside the documented 0-150 age range"

    def gender_valid(_):
        term = rng.choice(["male", "female", "males", "females"])
        return term, "gender", True, ""

    def phone_valid(_):
        return fake.numerify("(###) ###-####"), "phone", True, ""

    def address_valid(_):
        return fake.street_address(), "address", True, ""

    def mrn_valid(rng_):
        return _mrn(rng_), "mrn", True, ""

    def symptom(_):
        return rng.choice(CLINICAL_VOCAB["symptom"]), "highlight_symptom", True, ""

    def diagnosis(_):
        return rng.choice(CLINICAL_VOCAB["diagnosis"]), "highlight_diagnosis", True, ""

    def medication(_):
        return rng.choice(CLINICAL_VOCAB["medication"]), "highlight_medication", True, ""

    return {
        "name": name_gazetteered,
        "name_other": name_ungazetteered,
        "firstname": name_firstname_only,
        "common_word_name": name_common_word,
        "date": date_valid,
        "date2": date_valid,
        "date_bad_sep": date_mismatched_sep,
        "date_space": date_space_sep,
        "date_oor": date_out_of_range_year,
        "age": age_valid,
        "age_bare": age_bare_number,
        "age_oor": age_out_of_range,
        "gender": gender_valid,
        "phone": phone_valid,
        "address": address_valid,
        "mrn": mrn_valid,
        "symptom": symptom,
        "symptom2": symptom,
        "diagnosis": diagnosis,
        "medication": medication,
    }


# Hand-written sentence templates. Placeholders are filled left-to-right by
# `make_generators()`; every template's rendered text must stay single-spaced
# with no leading/trailing whitespace, since PhiSanitizer._format_text()
# collapses whitespace and would otherwise shift span offsets out from under
# the manifest.
TEMPLATES = [
    # Straightforward positive case across every "real" category at once.
    "Patient <<name>>, DOB <<date>>, is a <<age>> <<gender>> presenting with <<symptom>>.",
    # Identifiers embedded mid-sentence rather than at clause boundaries.
    "Contacted <<name>> at <<phone>> regarding the <<diagnosis>> diagnosis noted on <<date>>.",
    # Multiple dates in one note.
    "Admitted on <<date>> and discharged on <<date2>>, patient <<name>> was started on <<medication>>.",
    # MRN and address embedded, plus a decoy dosage number.
    "Chart <<mrn>> for <<name>> at <<address>> notes <<medication>> 50 mg twice daily for <<diagnosis>>.",
    # Surname not in the loaded gazetteer -- a first-name-only mention too.
    "Dr. <<name_other>> examined <<firstname>>, who reported <<symptom>> and <<symptom2>>.",
    # The gazetteer surname used as an ordinary word, not as a patient name.
    "The <<common_word_name>> period for this <<diagnosis>> follow-up ends in two weeks.",
    # Edge cases the code's own comments flag: mismatched separator, a
    # space-separated non-date triplet, and an out-of-range year -- none of
    # these should be masked.
    "Prior note dated <<date_bad_sep>> was amended; rechecked <<date_space>> times, old record <<date_oor>>.",
    # Age boundary: a plausible in-range bare number (masked by design) next
    # to a clearly out-of-range one (should not be masked).
    "Lab value of <<age_bare>> was recorded; unrelated tracking id <<age_oor>> was not a patient age.",
    # A note with no identifiers at all.
    "Routine follow-up visit. Patient reports improvement in <<symptom>>. Continue management for <<diagnosis>>.",
]


def render(template: str, generators: dict, rng: random.Random) -> tuple[str, list[Span]]:
    out: list[str] = []
    spans: list[Span] = []
    pos = 0
    offset = 0
    for m in TOKEN_RE.finditer(template):
        literal = template[pos : m.start()]
        out.append(literal)
        offset += len(literal)

        token = m.group(1)
        text, category, expected, note = generators[token](rng)
        start = offset
        out.append(text)
        offset += len(text)
        end = offset
        spans.append(Span(category=category, text=text, start=start, end=end, expected_redacted=expected, note=note))
        pos = m.end()

    out.append(template[pos:])
    full_text = "".join(out)
    return full_text, spans


def generate_notes(seed: int, count: int) -> list[dict]:
    fake = Faker()
    fake.seed_instance(seed)
    rng = random.Random(seed)
    generators = make_generators(fake, rng)

    notes = []
    for i in range(count):
        template = TEMPLATES[i % len(TEMPLATES)]
        text, spans = render(template, generators, rng)
        # Guard the offset invariant the whole manifest depends on: the
        # generated text must already be in the normalized form
        # PhiSanitizer._format_text() would produce, or span offsets recorded
        # here would silently drift from the sanitizer's output.
        normalized = re.sub(r"\s+", " ", text).strip()
        assert normalized == text, f"template produced non-normalized text: {text!r}"
        notes.append(
            {
                "note_id": i,
                "template_index": i % len(TEMPLATES),
                "text": text,
                "spans": [asdict(s) for s in spans],
            }
        )
    return notes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--count", "-n", type=int, default=20)
    parser.add_argument("--out-dir", type=Path, default=Path("tools/fixtures_out"))
    args = parser.parse_args()

    notes = generate_notes(args.seed, args.count)

    notes_dir = args.out_dir / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    for note in notes:
        (notes_dir / f"note_{note['note_id']:04d}.txt").write_text(note["text"], encoding="utf-8")

    manifest = {
        "seed": args.seed,
        "count": args.count,
        "gazetteer_surnames": GAZETTEER_SURNAMES,
        "clinical_vocab": CLINICAL_VOCAB,
        "notes": notes,
    }
    (args.out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {len(notes)} notes and manifest.json to {args.out_dir}")


if __name__ == "__main__":
    main()
