import pandas as pd
import pytest

from medtext_redact.core import text_tools
from medtext_redact.core.text_tools import PhiSanitizer, white_rabbit_parse_report


@pytest.fixture(autouse=True)
def fake_census_names(monkeypatch):
    """sanitize_names() calls load_census_names(), which would otherwise hit the network."""
    monkeypatch.setattr(text_tools, "load_census_names", lambda: ["Smith", "Jones"])


class FakeConfig:
    def __init__(self, data):
        self._data = data

    def get(self, key, default=None):
        parts = key.split(".")
        current = self._data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        return current


class TestInitAndFormatting:
    def test_strips_and_collapses_whitespace(self):
        sanitizer = PhiSanitizer("  hello   world  ")
        assert sanitizer.text == "hello world"

    def test_normalizes_comma_spacing(self):
        sanitizer = PhiSanitizer("a ,b  ,  c")
        assert sanitizer.text == "a, b, c"

    def test_none_input_becomes_empty_string(self):
        assert PhiSanitizer(None).text == ""

    def test_nan_input_becomes_empty_string(self):
        assert PhiSanitizer(pd.NA).text == ""

    def test_title_case_capitalizes_sentences(self):
        sanitizer = PhiSanitizer("hello world. another sentence.", title_case=True)
        assert sanitizer.text == "Hello world. Another sentence."


class TestSanitizeKeywords:
    def test_masks_provided_keywords(self):
        result = PhiSanitizer("the patient has cancer").sanitize_keywords(["cancer"]).text
        assert result == "the patient has ******"


class TestSanitizeNames:
    def test_masks_known_census_names(self, fake_census_names):
        result = PhiSanitizer("Smith went home").sanitize_names().text
        assert result == "***** went home"

    def test_does_not_mask_name_as_substring_of_other_word(self, monkeypatch):
        monkeypatch.setattr(text_tools, "load_census_names", lambda: ["Ann"])
        result = PhiSanitizer("Announced the biopsy results to the family").sanitize_names().text
        assert result == "Announced the biopsy results to the family"

    def test_leaves_unlisted_surname_untouched(self, fake_census_names):
        # Documents a real scope limit, not a bug: only surnames present in
        # the loaded gazetteer are ever masked.
        result = PhiSanitizer("Patel went home").sanitize_names().text
        assert result == "Patel went home"

    def test_leaves_bare_first_name_untouched(self, fake_census_names):
        # sanitize_names() only ever loads census *surnames* -- a bare first
        # name with no accompanying surname is never caught.
        result = PhiSanitizer("Adam went home").sanitize_names().text
        assert result == "Adam went home"


class TestSanitizeDates:
    def test_masks_slash_separated_date(self):
        result = PhiSanitizer("seen on 01/02/2020 today").sanitize_dates().text
        assert result == "seen on **/**/**** today"

    def test_masks_dash_separated_date(self):
        result = PhiSanitizer("seen on 01-02-2020 today").sanitize_dates().text
        assert result == "seen on **-**-**** today"

    def test_does_not_mask_mismatched_separators(self):
        result = PhiSanitizer("01/02-2020").sanitize_dates().text
        assert result == "01/02-2020"

    def test_does_not_mask_non_date_numbers(self):
        result = PhiSanitizer("value is 99/99/9999").sanitize_dates().text
        assert result == "value is 99/99/9999"

    def test_masks_dot_separated_date(self):
        result = PhiSanitizer("seen on 01.02.2020 today").sanitize_dates().text
        assert result == "seen on **.**.**** today"

    def test_does_not_mask_space_separated_triplet(self):
        # Regression: the separator class used to include `\s`, contradicting
        # the code's own comment ("Allow `/`, `-` or `.` as separators").
        result = PhiSanitizer("counted 2 3 2024 times").sanitize_dates().text
        assert result == "counted 2 3 2024 times"

    def test_does_not_mask_year_outside_1900_2099(self):
        result = PhiSanitizer("record dated 5/6/1850 was archived").sanitize_dates().text
        assert result == "record dated 5/6/1850 was archived"

    def test_masks_multiple_dates_in_one_note(self):
        result = PhiSanitizer("admitted 1/2/2020 and discharged 3/4/2020").sanitize_dates().text
        assert result == "admitted */*/**** and discharged */*/****"


class TestSanitizeAge:
    def test_masks_years_old_phrase(self):
        result = PhiSanitizer("patient is 34 years old").sanitize_age().text
        assert "34" not in result
        assert "*" in result

    def test_masks_hyphenated_yrs_old(self):
        result = PhiSanitizer("100-yrs-old male").sanitize_age().text
        assert "100" not in result

    def test_masks_bare_in_range_number_by_design(self):
        # Not a bug: the code's own comment explicitly lists a bare "34" as
        # an intended match, favoring recall over precision for ages.
        result = PhiSanitizer("prescribed 50 mg twice daily").sanitize_age().text
        assert "50" not in result

    def test_does_not_mask_number_above_150(self):
        result = PhiSanitizer("weight 151 lbs").sanitize_age().text
        assert result == "weight 151 lbs"

    def test_masks_boundary_value_150(self):
        result = PhiSanitizer("reading of 150 units").sanitize_age().text
        assert "150" not in result


class TestSanitizeGender:
    def test_masks_male_and_female(self):
        result = PhiSanitizer("the male and female patients").sanitize_gender().text
        assert result == "the **** and ****** patients"

    def test_masks_plural_forms(self):
        result = PhiSanitizer("the females and males in the study").sanitize_gender().text
        assert result == "the ******* and ***** in the study"


class TestSanitizeAll:
    def test_full_masks_names_dates_gender_age(self, fake_census_names):
        config = FakeConfig({"Masking": {}})
        text = "Smith is a 34 year old male, seen 01/02/2020"
        result = PhiSanitizer(text).sanitize_all(config, full=True).text
        assert "Smith" not in result
        assert "01/02/2020" not in result
        assert "male" not in result
        assert "34" not in result

    def test_not_full_skips_gender_and_age(self, fake_census_names):
        config = FakeConfig({"Masking": {}})
        text = "34 year old male"
        result = PhiSanitizer(text).sanitize_all(config, full=False).text
        assert result == text

    def test_masks_configured_manufacturers_and_locations(self, fake_census_names):
        config = FakeConfig({"Masking": {"Manufacturers": ["GE"], "Locations": ["Boston"]}})
        result = PhiSanitizer("scanned on GE in Boston").sanitize_all(config).text
        assert "GE" not in result
        assert "Boston" not in result

    def test_no_manufacturers_or_locations_configured(self, fake_census_names):
        config = FakeConfig({"Masking": {}})
        result = PhiSanitizer("scanned on GE in Boston").sanitize_all(config).text
        assert result == "scanned on GE in Boston"


class TestWhiteRabbitParseReport:
    def test_masks_penrad_signature(self):
        result = white_rabbit_parse_report("Signed, XY/Penrad")
        assert "Penrad" not in result

    def test_leaves_unrelated_text_untouched(self):
        result = white_rabbit_parse_report("no signature here")
        assert result == "no signature here"


class TestHighlightText:
    def test_stylizes_every_match(self):
        text = "the patient has cancer"
        pattern = text_tools.compile_keywords_pattern(["cancer"])
        styled = text_tools._highlight_text(text, pattern)
        assert styled.plain == text
        start = text.index("cancer")
        end = start + len("cancer")
        spans = [(s.start, s.end, s.style) for s in styled.spans]
        assert (start, end, "bold yellow") in spans

    def test_no_match_produces_no_spans(self):
        pattern = text_tools.compile_keywords_pattern(["cancer"])
        styled = text_tools._highlight_text("nothing relevant here", pattern)
        assert styled.spans == []

    def test_matches_multiple_keywords(self):
        pattern = text_tools.compile_keywords_pattern(["fever", "cough"])
        styled = text_tools._highlight_text("fever and a persistent cough", pattern)
        assert len(styled.spans) == 2


class TestPrintLinesWithKeywords:
    def test_prints_only_sentences_containing_a_match(self, capsys):
        text = "Patient reports no distress. Patient has a persistent cough. Follow up in two weeks."
        text_tools.print_lines_with_keywords(["cough"], text)
        out = capsys.readouterr().out
        assert "persistent cough" in out
        assert "no distress" not in out
        assert "Follow up" not in out

    def test_no_match_prints_nothing(self, capsys):
        text_tools.print_lines_with_keywords(["cough"], "nothing relevant here.")
        assert capsys.readouterr().out == ""

    def test_matches_are_case_insensitive(self, capsys):
        text_tools.print_lines_with_keywords(["fever"], "Patient has a FEVER today.")
        assert "FEVER" in capsys.readouterr().out
