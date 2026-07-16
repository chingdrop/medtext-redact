import pandas as pd
import pytest

from vega_tools.core import text_tools
from vega_tools.core.text_tools import PhiSanitizer, white_rabbit_parse_report


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


class TestSanitizeAge:
    def test_masks_years_old_phrase(self):
        result = PhiSanitizer("patient is 34 years old").sanitize_age().text
        assert "34" not in result
        assert "*" in result

    def test_masks_hyphenated_yrs_old(self):
        result = PhiSanitizer("100-yrs-old male").sanitize_age().text
        assert "100" not in result


class TestSanitizeGender:
    def test_masks_male_and_female(self):
        result = PhiSanitizer("the male and female patients").sanitize_gender().text
        assert result == "the **** and ****** patients"


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
