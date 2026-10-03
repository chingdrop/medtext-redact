import pytest
import tldextract.tldextract

from medtext_redact.core.presidio_tools import presidio_redact
from medtext_redact.core.utils.enums import load_census_names


class TestPresidioRedact:
    def test_masks_names_outside_any_gazetteer(self):
        result = presidio_redact("Dr. Novak examined Elena this morning.")
        assert "Novak" not in result
        assert "Elena" not in result

    def test_masks_email_address(self):
        result = presidio_redact("Contact elena.novak@example.com for records.")
        assert "elena.novak@example.com" not in result

    def test_masks_word_characters_only_preserving_length(self):
        text = "Patient Elena Novak, DOB 5/6/1950, reports chest pain."
        result = presidio_redact(text)
        assert len(result) == len(text)
        assert "DOB */*/****," in result

    def test_leaves_clinical_terms_intact(self):
        text = "Elena Novak was started on metformin for type 2 diabetes mellitus."
        result = presidio_redact(text)
        assert "metformin" in result
        assert "type 2 diabetes mellitus" in result

    def test_text_without_phi_is_unchanged(self):
        text = "Routine follow-up visit. Continue management for hypertension."
        assert presidio_redact(text) == text

    def test_domain_lookups_never_fetch_the_public_suffix_list(self, monkeypatch):
        def no_network(*args, **kwargs):
            raise AssertionError("tldextract tried to fetch the Public Suffix List")

        monkeypatch.setattr(tldextract.suffix_list, "find_first_response", no_network)
        result = presidio_redact("Contact elena.novak@example.com for records.")
        assert "elena.novak@example.com" not in result
        assert tldextract.tldextract.TLD_EXTRACTOR.suffix_list_urls == ()

    def test_rule_recognizers_cover_what_built_ins_miss(self):
        text = "Patient is a 52 yo female, MRN-5427721, at 765 Castro Skyway, phone (369) 033-2171."
        result = presidio_redact(text)
        for phi in ["52 yo", "female", "MRN-5427721", "765 Castro Skyway", "(369) 033-2171"]:
            assert phi not in result

    def test_masks_surnames_from_the_given_gazetteer(self):
        text = "The chart for Hope was updated."
        assert "Hope" in presidio_redact(text)
        assert "Hope" not in presidio_redact(text, surnames=["Hope"])


class TestWithTheRealSurnameList:
    """The full bundled census list, not a stand-in: 107 of spaCy's English stop words and many clinical
    words are real census surnames, and a plain gazetteer match masked them at every sentence start."""

    @pytest.mark.parametrize(
        "text",
        [
            "The chart was reviewed.",
            "In clinic, She reported fatigue.",
            "No acute distress noted.",
            "Patient reports chest pain.",
            "Chief complaint: fever.",
            "Plan: continue current care.",
            "Seen by the team in clinic.",
            "Called back regarding labs.",
            "Long term care plan.",
        ],
    )
    def test_common_and_clinical_words_survive(self, text):
        assert presidio_redact(text, load_census_names()) == text

    @pytest.mark.parametrize(
        ("text", "surname"),
        [
            ("Okafor called back.", "Okafor"),
            ("The chart for Hope was updated.", "Hope"),
            ("Contacted White at home.", "White"),
            ("Seen by Dr. Hand in clinic.", "Hand"),
            ("Nurse Back documented vitals.", "Back"),
            ("Called Mrs. Doctor regarding labs.", "Doctor"),
        ],
    )
    def test_real_surnames_are_still_masked(self, text, surname):
        assert surname not in presidio_redact(text, load_census_names())
