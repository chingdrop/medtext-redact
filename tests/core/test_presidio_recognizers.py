import pytest

from medtext_redact.core.presidio_recognizers import SurnameGazetteerRecognizer, rule_recognizers


def detect(text: str, entity: str) -> list[str]:
    """Run the rule recognizer for `entity` on `text` and return the matched substrings."""
    (recognizer,) = [r for r in rule_recognizers() if entity in r.supported_entities]
    return [text[r.start : r.end] for r in recognizer.analyze(text, [entity])]


class TestRuleRecognizers:
    @pytest.mark.parametrize("term", ["male", "Female", "males", "FEMALES"])
    def test_gender_terms_any_case(self, term):
        assert detect(f"a 34 year old {term} patient", "GENDER") == [term]

    def test_gender_skips_words_containing_the_term(self):
        assert detect("maleficent and femaleness", "GENDER") == []

    @pytest.mark.parametrize("age", ["34 years old", "34-yrs-old", "34 yo", "34yo"])
    def test_age_phrasings(self, age):
        assert age in detect(f"Patient is {age} today", "AGE")

    def test_age_skips_clinical_staging_numbers(self):
        assert detect("type 2 diabetes, stage 3 cancer", "AGE") == []

    def test_mrn_requires_label(self):
        assert detect("Chart MRN-1234567 reviewed; ref 1234567", "MEDICAL_RECORD_NUMBER") == ["MRN-1234567"]

    def test_phone_without_validation(self):
        # 033 isn't a valid US exchange, so Presidio's own validating phone
        # recognizer rejects it; the ported rule masks any phone-shaped digits.
        assert detect("call (369) 033-2171 today", "PHONE_NUMBER") == ["(369) 033-2171"]

    def test_street_address_with_unit(self):
        assert detect("lives at 5427 White Court Suite 619 now", "STREET_ADDRESS") == ["5427 White Court Suite 619"]

    def test_date_requires_matching_separators(self):
        assert detect("seen 12/27/1949 and 12/27-1949", "DATE_TIME") == ["12/27/1949"]


class TestSurnameGazetteerRecognizer:
    def test_detects_listed_surnames_as_person(self):
        results = SurnameGazetteerRecognizer(["Okafor"]).analyze("Contacted Okafor today", ["PERSON"])
        assert [(r.entity_type, r.start, r.end) for r in results] == [("PERSON", 10, 16)]

    def test_is_case_sensitive_like_the_rules(self):
        assert SurnameGazetteerRecognizer(["Hope"]).analyze("there is hope", ["PERSON"]) == []
