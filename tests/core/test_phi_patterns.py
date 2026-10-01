"""
Behavior of the PHI regex patterns, which the Presidio rule recognizers
are built on. Each test masks with mask_regex_pattern(), the same
word-character masking presidio_redact() applies to every detected entity.
"""

from medtext_redact.core.phi_patterns import (
    ADDRESS_PATTERN,
    AGE_PATTERN,
    DATE_PATTERN,
    MRN_PATTERN,
    PHONE_PATTERN,
    URL_PATTERN,
)
from medtext_redact.core.utils.regex_utils import mask_regex_pattern


class TestDatePattern:
    def test_masks_slash_separated_date(self):
        result = mask_regex_pattern(DATE_PATTERN, "seen on 01/02/2020 today")
        assert result == "seen on **/**/**** today"

    def test_masks_dash_separated_date(self):
        result = mask_regex_pattern(DATE_PATTERN, "seen on 01-02-2020 today")
        assert result == "seen on **-**-**** today"

    def test_does_not_mask_mismatched_separators(self):
        result = mask_regex_pattern(DATE_PATTERN, "01/02-2020")
        assert result == "01/02-2020"

    def test_does_not_mask_non_date_numbers(self):
        result = mask_regex_pattern(DATE_PATTERN, "value is 99/99/9999")
        assert result == "value is 99/99/9999"

    def test_masks_dot_separated_date(self):
        result = mask_regex_pattern(DATE_PATTERN, "seen on 01.02.2020 today")
        assert result == "seen on **.**.**** today"

    def test_does_not_mask_space_separated_triplet(self):
        # Regression: the separator class used to include `\s`, contradicting
        # the code's own comment ("Allow `/`, `-` or `.` as separators").
        result = mask_regex_pattern(DATE_PATTERN, "counted 2 3 2024 times")
        assert result == "counted 2 3 2024 times"

    def test_does_not_mask_year_outside_1900_2099(self):
        result = mask_regex_pattern(DATE_PATTERN, "record dated 5/6/1850 was archived")
        assert result == "record dated 5/6/1850 was archived"

    def test_masks_multiple_dates_in_one_note(self):
        result = mask_regex_pattern(DATE_PATTERN, "admitted 1/2/2020 and discharged 3/4/2020")
        assert result == "admitted */*/**** and discharged */*/****"


class TestAgePattern:
    def test_masks_years_old_phrase(self):
        result = mask_regex_pattern(AGE_PATTERN, "patient is 34 years old")
        assert "34" not in result
        assert "*" in result

    def test_masks_hyphenated_yrs_old(self):
        result = mask_regex_pattern(AGE_PATTERN, "100-yrs-old male")
        assert "100" not in result

    def test_masks_bare_in_range_number_by_design(self):
        # Not a bug: the code's own comment explicitly lists a bare "34" as
        # an intended match, favoring recall over precision for ages.
        result = mask_regex_pattern(AGE_PATTERN, "prescribed 50 mg twice daily")
        assert "50" not in result

    def test_does_not_mask_number_above_150(self):
        result = mask_regex_pattern(AGE_PATTERN, "weight 151 lbs")
        assert result == "weight 151 lbs"

    def test_masks_boundary_value_150(self):
        result = mask_regex_pattern(AGE_PATTERN, "reading of 150 units")
        assert "150" not in result

    def test_does_not_mask_staging_or_grading_numbers(self):
        # Regression: the bare-number match used to also catch clinical
        # staging/grading numbers, silently corrupting the diagnosis term
        # itself ("type 2 diabetes mellitus" -> "type * diabetes mellitus"),
        # which in turn broke --keywords highlighting for that term.
        for text in ["type 2 diabetes mellitus", "stage 3 cancer", "grade 2 lesion", "class 4 recall"]:
            assert mask_regex_pattern(AGE_PATTERN, text) == text

    def test_masks_shorthand_yo(self):
        result = mask_regex_pattern(AGE_PATTERN, "34yo female presents")
        assert "34" not in result


class TestMrnPattern:
    def test_masks_hyphenated_mrn(self):
        result = mask_regex_pattern(MRN_PATTERN, "Chart MRN-6001338 for review")
        assert "6001338" not in result

    def test_masks_labeled_mrn_with_colon(self):
        result = mask_regex_pattern(MRN_PATTERN, "MRN: 6001338")
        assert "6001338" not in result

    def test_masks_mrn_with_no_separator(self):
        result = mask_regex_pattern(MRN_PATTERN, "chart MRN123456 today")
        assert "123456" not in result

    def test_does_not_mask_unlabeled_number(self):
        result = mask_regex_pattern(MRN_PATTERN, "accession number 1234567")
        assert result == "accession number 1234567"

    def test_does_not_mask_bare_word_mrn(self):
        result = mask_regex_pattern(MRN_PATTERN, "the acronym MRN stands for medical record number")
        assert result == "the acronym MRN stands for medical record number"


class TestPhonePattern:
    def test_masks_parenthesized_phone(self):
        result = mask_regex_pattern(PHONE_PATTERN, "call (281) 699-3976 now")
        assert "699" not in result and "3976" not in result

    def test_masks_dash_separated_phone(self):
        result = mask_regex_pattern(PHONE_PATTERN, "call 281-699-3976 now")
        assert "281-699-3976" not in result

    def test_masks_phone_with_country_code(self):
        result = mask_regex_pattern(PHONE_PATTERN, "reach us at +1 281-699-3976")
        assert "699" not in result

    def test_does_not_mask_short_numbers(self):
        result = mask_regex_pattern(PHONE_PATTERN, "room 281, bed 6")
        assert result == "room 281, bed 6"

    def test_does_not_mask_mrn_shaped_number(self):
        # A bare 7-digit MRN body has too few digits to look like a phone
        # number, which needs 10.
        result = mask_regex_pattern(PHONE_PATTERN, "6001338")
        assert result == "6001338"


class TestAddressPattern:
    def test_masks_simple_street_address(self):
        result = mask_regex_pattern(ADDRESS_PATTERN, "lives at 386 Shane Harbors")
        assert "Shane" not in result

    def test_masks_address_with_unit(self):
        result = mask_regex_pattern(ADDRESS_PATTERN, "53993 Aguilar Avenue Apt. 384")
        assert "Aguilar" not in result

    def test_masks_address_with_full_word_suffix(self):
        result = mask_regex_pattern(ADDRESS_PATTERN, "facility located at 4821 Meadowbrook Boulevard")
        assert "Meadowbrook" not in result

    def test_does_not_mask_plain_number_and_word(self):
        result = mask_regex_pattern(ADDRESS_PATTERN, "patient reports 3 years of symptoms")
        assert result == "patient reports 3 years of symptoms"

    def test_does_not_mask_dosage_or_lab_value(self):
        result = mask_regex_pattern(ADDRESS_PATTERN, "prescribed 10 mg twice daily")
        assert result == "prescribed 10 mg twice daily"

    def test_does_not_mask_the_word_via(self):
        # "Via" is a real USPS street suffix but also an ordinary English
        # preposition common in clinical text -- deliberately excluded to
        # avoid mangling sentences like this one.
        result = mask_regex_pattern(ADDRESS_PATTERN, "123 patients were treated via telehealth")
        assert "telehealth" in result
        assert "treated" in result


class TestUrlPattern:
    def test_masks_whole_url_including_tld(self):
        # Regression: Presidio's own URL recognizer matches "miller.biz" as
        # "miller.bi" and leaves the "z" visible.
        assert (
            mask_regex_pattern(URL_PATTERN, "shared via http://miller.biz/ today")
            == "shared via ****://******.***/ today"
        )

    def test_masks_www_url_without_scheme(self):
        assert mask_regex_pattern(URL_PATTERN, "see www.example.org/a?b=1 now") == "see ***.*******.***/*?*=* now"

    def test_leaves_trailing_sentence_punctuation(self):
        assert mask_regex_pattern(URL_PATTERN, "Visit https://gray.biz.") == "Visit *****://****.***."

    def test_does_not_mask_bare_domain_words(self):
        assert mask_regex_pattern(URL_PATTERN, "the example.com domain") == "the example.com domain"
