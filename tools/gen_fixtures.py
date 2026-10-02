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
import hashlib
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


_BASE58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def _bitcoin_address(rng: random.Random) -> str:
    """A legacy (P2PKH) Bitcoin address with a valid Base58Check checksum,
    as Presidio's crypto recognizer validates, over a random payload."""
    payload = bytes([0]) + bytes(rng.getrandbits(8) for _ in range(20))
    data = payload + hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    n = int.from_bytes(data, "big")
    encoded = ""
    while n:
        n, r = divmod(n, 58)
        encoded = _BASE58[r] + encoded
    return "1" * (len(data) - len(data.lstrip(b"\0"))) + encoded


def _dea_number(rng: random.Random) -> str:
    """A DEA registration number (Presidio's MEDICAL_LICENSE) with a valid check digit."""
    d = [rng.randint(0, 9) for _ in range(6)]
    check = (d[0] + d[2] + d[4] + 2 * (d[1] + d[3] + d[5])) % 10
    return rng.choice("ABFGM") + rng.choice("ABCDEFGHJKLMNPRSTW") + "".join(map(str, d)) + str(check)


def _nhs_number(rng: random.Random) -> str:
    """A UK NHS number with a valid mod-11 check digit, in its usual 3-3-4 grouping."""
    while True:
        d = [rng.randint(0, 9) for _ in range(9)]
        check = 11 - sum(x * w for x, w in zip(d, range(10, 1, -1), strict=True)) % 11
        check = 0 if check == 11 else check
        if check != 10:  # 10 is never issued
            digits = "".join(map(str, d)) + str(check)
            return f"{digits[:3]} {digits[3:6]} {digits[6:]}"


def _itin(rng: random.Random) -> str:
    """An ITIN: 9XX-XX-XXXX with the middle group in an IRS-issued range."""
    middle = rng.choice([*range(50, 66), *range(70, 89), *range(90, 93), *range(94, 100)])
    return f"9{rng.randint(0, 99):02d}-{middle}-{rng.randint(0, 9999):04d}"


def _driver_license(rng: random.Random) -> str:
    """A US driver's license number in one of three common state formats."""
    letter = rng.choice("ABCDEFGHJKLMNPRSTWY")
    return rng.choice(
        [
            f"{letter}{rng.randint(0, 9_999_999):07d}",  # one letter + 7 digits (e.g. CA)
            f"{rng.randint(100_000_000, 999_999_999)}",  # 9 digits (e.g. NY)
            f"{letter}{rng.randint(0, 10**12 - 1):012d}",  # one letter + 12 digits (e.g. FL)
        ]
    )


def _mrn(rng: random.Random) -> str:
    return "MRN-" + "".join(rng.choice("0123456789") for _ in range(7))


def make_generators(fake: Faker, rng: random.Random) -> dict:
    """Each generator returns (text, category, expected_redacted, note)."""
    # IBANs come from the UK locale; seed it from rng so output stays deterministic.
    fake_gb = Faker("en_GB")
    fake_gb.seed_instance(rng.randint(0, 2**32 - 1))

    def name_gazetteered(_):
        surname = rng.choice(GAZETTEER_SURNAMES)
        return surname, "name", True, "surname present in the stubbed gazetteer"

    def name_ungazetteered(_):
        # Faker's full last-name pool is effectively disjoint from our small
        # fixed gazetteer. Still a real name, so still PHI: a gazetteer-only
        # detector missing it is a recall gap, counted as one.
        surname = fake.last_name()
        return surname, "name_ungazetteered", True, "surname NOT in the loaded gazetteer -- still PHI"

    def name_firstname_only(_):
        first = fake.first_name()
        return first, "name_firstname_only", True, "bare first name -- still PHI, though the gazetteer is surnames only"

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
            True,
            "mismatched separators -- still a date, so still PHI",
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
        return "5/6/1850", "date_out_of_range", True, "year outside the 1900-2099 window -- still a date, so still PHI"

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

    def email_valid(_):
        return fake.email(), "email", True, ""

    def ssn_valid(_):
        # Faker only generates SSNs in ranges the SSA actually issues (no
        # 000/666/9xx area numbers), matching what Presidio's SSN recognizer
        # accepts as plausible.
        return fake.ssn(), "ssn", True, ""

    def url_valid(_):
        return fake.url(), "url", True, ""

    def ip_valid(_):
        address = fake.ipv4_public() if rng.random() < 0.5 else fake.ipv6()
        return address, "ip_address", True, "IPv4 or IPv6"

    def credit_card_valid(_):
        # visa19 included deliberately: Presidio's own recognizer stops at 16
        # digits, so 19-digit Visa numbers exercise the Luhn backstop.
        card_type = rng.choice(["visa16", "visa19", "mastercard", "amex", "discover"])
        return fake.credit_card_number(card_type=card_type), "credit_card", True, card_type

    def bank_account_valid(_):
        digits = "".join(rng.choice("0123456789") for _ in range(rng.randint(8, 17)))
        return digits, "bank_account", True, ""

    def driver_license_valid(_):
        return _driver_license(rng), "driver_license", True, ""

    def passport_valid(_):
        passport = rng.choice([f"{rng.randint(100_000_000, 999_999_999)}", f"A{rng.randint(0, 99_999_999):08d}"])
        return passport, "passport", True, "9 digits, or the newer letter + 8 digits"

    def itin_valid(_):
        return _itin(rng), "itin", True, ""

    def dea_valid(_):
        return _dea_number(rng), "medical_license", True, "DEA registration number"

    def iban_valid(_):
        return fake_gb.iban(), "iban", True, ""

    def crypto_valid(_):
        return _bitcoin_address(rng), "crypto_wallet", True, "Bitcoin address"

    def mac_valid(_):
        return fake.mac_address(), "mac_address", True, "device identifier"

    def nhs_valid(_):
        return _nhs_number(rng), "nhs_number", True, ""

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
        "email": email_valid,
        "ssn": ssn_valid,
        "url": url_valid,
        "ip": ip_valid,
        "credit_card": credit_card_valid,
        "bank_account": bank_account_valid,
        "driver_license": driver_license_valid,
        "passport": passport_valid,
        "itin": itin_valid,
        "dea": dea_valid,
        "iban": iban_valid,
        "crypto": crypto_valid,
        "mac": mac_valid,
        "nhs": nhs_valid,
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
    # Date edge cases: a mismatched separator and an out-of-range year are
    # still dates (PHI); the space-separated triplet is a count, not a date.
    "Prior note dated <<date_bad_sep>> was amended; rechecked <<date_space>> times, old record <<date_oor>>.",
    # Age boundary: a plausible in-range bare number (masked by design) next
    # to a clearly out-of-range one (should not be masked).
    "Lab value of <<age_bare>> was recorded; unrelated tracking id <<age_oor>> was not a patient age.",
    # Electronic and government identifiers, as they'd appear in a portal or
    # intake note.
    "Patient portal account <<email>> (SSN <<ssn>>) last signed in from <<ip>>; "
    "records shared via <<url>> for <<diagnosis>>.",
    # Billing and prescribing identifiers.
    "Billing on file: card <<credit_card>>, bank account <<bank_account>>, ITIN <<itin>>; "
    "<<medication>> prescribed under DEA <<dea>>; refund to IBAN <<iban>>.",
    # Identity documents, a device identifier, and a non-US health number.
    "Identity verified with driver's license <<driver_license>> and passport <<passport>>; "
    "home monitor MAC <<mac>> paired; NHS number <<nhs>>; donation from wallet <<crypto>>.",
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
