import pandas as pd
import pytest

from medtext_redact.core import text_tools
from medtext_redact.core.text_tools import PhiSanitizer, white_rabbit_parse_report


@pytest.fixture(autouse=True)
def fake_census_names(monkeypatch):
    """A two-name gazetteer keeps these tests independent of the bundled census list."""
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


class TestSanitizePresidio:
    def test_masks_names_dates_gender_age(self, fake_census_names):
        text = "Smith is a 34 year old male, seen 01/02/2020"
        result = PhiSanitizer(text).sanitize_presidio().text
        assert "Smith" not in result
        assert "01/02/2020" not in result
        assert "male" not in result
        assert "34" not in result

    def test_masks_names_without_the_gazetteer(self):
        result = PhiSanitizer("Dr. Novak examined Elena").sanitize_presidio().text
        assert "Novak" not in result
        assert "Elena" not in result

    def test_masks_surnames_from_the_census_gazetteer(self, monkeypatch):
        monkeypatch.setattr(text_tools, "load_census_names", lambda: ["Hope"])
        result = PhiSanitizer("The chart for Hope was updated.").sanitize_presidio().text
        assert "Hope" not in result


class TestSanitizeConfiguredKeywords:
    def test_masks_configured_manufacturers_and_locations(self):
        config = FakeConfig({"Masking": {"Manufacturers": ["GE"], "Locations": ["Boston"]}})
        result = PhiSanitizer("scanned on GE in Boston").sanitize_configured_keywords(config).text
        assert "GE" not in result
        assert "Boston" not in result

    def test_no_manufacturers_or_locations_configured(self):
        config = FakeConfig({"Masking": {}})
        result = PhiSanitizer("scanned on GE in Boston").sanitize_configured_keywords(config).text
        assert result == "scanned on GE in Boston"

    def test_applies_after_presidio(self):
        config = FakeConfig({"Masking": {"Manufacturers": ["GE"], "Locations": []}})
        result = PhiSanitizer("scanned on GE").sanitize_presidio().sanitize_configured_keywords(config).text
        assert "GE" not in result


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
