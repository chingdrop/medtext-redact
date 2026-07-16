import re

import pytest

from vega_tools.core.utils.regex_utils import (
    NameMasker,
    compile_keywords_pattern,
    mask_keywords,
    mask_regex_pattern,
    parse_project_name,
    to_snake_case,
)


class TestCompileKeywordsPattern:
    def test_matches_any_keyword_case_insensitively(self):
        pattern = compile_keywords_pattern(["foo", "bar"])
        assert pattern.search("a FOO b")
        assert pattern.search("a bar b")
        assert not pattern.search("a baz b")

    def test_whole_word_boundary_by_default(self):
        pattern = compile_keywords_pattern(["cat"])
        assert pattern.search("a cat sat")
        assert not pattern.search("concatenate")

    def test_boundary_false_matches_substrings(self):
        pattern = compile_keywords_pattern(["cat"], boundary=False)
        assert pattern.search("concatenate")

    def test_longer_keywords_matched_before_shorter_prefixes(self):
        pattern = compile_keywords_pattern(["Wash", "Washington"], boundary=False)
        m = pattern.search("Washington")
        assert m.group(0) == "Washington"

    def test_empty_keywords_raises_value_error(self):
        with pytest.raises(ValueError):
            compile_keywords_pattern([])

    def test_non_string_keyword_raises_type_error(self):
        with pytest.raises(TypeError):
            compile_keywords_pattern(["ok", 123])

    def test_special_regex_characters_are_escaped(self):
        pattern = compile_keywords_pattern(["a.b"], boundary=False)
        assert pattern.search("a.b")
        assert not pattern.search("aXb")


class TestMaskRegexPattern:
    def test_masks_alphanumeric_characters_only(self):
        result = mask_regex_pattern(r"\d{3}-\d{2}", "call 123-45 now")
        assert result == "call ***-** now"

    def test_accepts_string_pattern(self):
        result = mask_regex_pattern(r"foo", "foobar")
        assert result == "***bar"

    def test_accepts_compiled_pattern(self):
        compiled = re.compile(r"foo")
        result = mask_regex_pattern(compiled, "foobar")
        assert result == "***bar"

    def test_leaves_punctuation_unmasked_within_match(self):
        result = mask_regex_pattern(r"a-b", "a-b done")
        assert result == "*-* done"


class TestMaskKeywords:
    def test_masks_whole_word_keywords(self):
        result = mask_keywords("the cat sat", ["cat"])
        assert result == "the *** sat"

    def test_does_not_mask_partial_words_by_default(self):
        result = mask_keywords("concatenate", ["cat"])
        assert result == "concatenate"


class TestNameMasker:
    def test_masks_known_names(self):
        masker = NameMasker(["John", "Smith"])
        assert masker.mask("John Smith went home") == "**** ***** went home"

    def test_leaves_unknown_words_untouched(self):
        masker = NameMasker(["John"])
        assert masker.mask("Jane went home") == "Jane went home"

    def test_no_overlap_double_masking(self):
        masker = NameMasker(["Ann"])
        assert masker.mask("Ann") == "***"


class TestParseProjectName:
    def test_parses_base_number_with_no_revision(self):
        assert parse_project_name("vega-116214") == (116214, 0)

    def test_parses_revision_letter_a(self):
        assert parse_project_name("vega-116214a") == (116214, 1)

    def test_parses_revision_letter_b(self):
        assert parse_project_name("vega-116214b") == (116214, 2)

    def test_ignores_trailing_suffix(self):
        assert parse_project_name("vega-116471-Fuji") == (116471, 0)

    def test_revision_letter_with_suffix(self):
        assert parse_project_name("vega-116471b-GE") == (116471, 2)

    def test_unparseable_string_raises_value_error(self):
        with pytest.raises(ValueError):
            parse_project_name("not-a-project-name-at-all")


class TestToSnakeCase:
    def test_replaces_non_alphanumeric_with_underscore(self):
        assert to_snake_case("Hello World-Test") == "hello_world_test"

    def test_inserts_underscore_between_lower_and_upper(self):
        assert to_snake_case("camelCaseWords") == "camel_case_words"

    def test_collapses_multiple_underscores(self):
        assert to_snake_case("a___b") == "a_b"

    def test_strips_leading_and_trailing_underscores(self):
        assert to_snake_case("-leading and trailing-") == "leading_and_trailing"
