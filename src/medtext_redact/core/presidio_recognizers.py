"""
Presidio recognizers ported from the rule-based engine.

Presidio's built-in recognizers have no gender detector and weak coverage of
ages, MRNs, street addresses, and phone numbers it can't validate -- exactly
the categories the regex rules were written for. These recognizers bring the
rules' patterns and surname gazetteer into Presidio so one engine covers
both NER and the rules.
"""

import re
from re import Pattern as RePattern

from presidio_analyzer import EntityRecognizer, Pattern, PatternRecognizer, RecognizerResult
from presidio_analyzer.nlp_engine import NlpArtifacts

from medtext_redact.core.phi_patterns import (
    ADDRESS_PATTERN,
    AGE_PATTERN,
    CARD_PATTERN,
    DATE_PATTERN,
    MRN_PATTERN,
    PHONE_PATTERN,
    URL_PATTERN,
)
from medtext_redact.core.utils.regex_utils import NameMasker

#   Every match is masked regardless of score (no threshold is applied), so
#   scores only matter when Presidio resolves overlapping results of
#   different entity types -- which doesn't change what gets masked.
RULE_SCORE = 0.85

GENDER_TERMS = ["male", "female", "males", "females"]


def _from_rule(entity: str, name: str, pattern: RePattern[str]) -> PatternRecognizer:
    # Presidio compiles with the third-party `regex` module, whose flag
    # values match the stdlib `re` flags these patterns were written with.
    return PatternRecognizer(
        supported_entity=entity,
        name=name,
        patterns=[Pattern(name=name, regex=pattern.pattern, score=RULE_SCORE)],
        global_regex_flags=pattern.flags,
    )


def rule_recognizers() -> list[EntityRecognizer]:
    """The rules' regex detectors, as Presidio recognizers."""
    return [
        _from_rule("DATE_TIME", "RuleDateRecognizer", DATE_PATTERN),
        # Unlike Presidio's own phone recognizer, this one doesn't validate
        # the number -- matching the rules, which mask any phone-shaped digits.
        _from_rule("PHONE_NUMBER", "RulePhoneRecognizer", PHONE_PATTERN),
        _from_rule("MEDICAL_RECORD_NUMBER", "RuleMrnRecognizer", MRN_PATTERN),
        _from_rule("STREET_ADDRESS", "RuleAddressRecognizer", ADDRESS_PATTERN),
        _from_rule("AGE", "RuleAgeRecognizer", AGE_PATTERN),
        _from_rule("URL", "RuleUrlRecognizer", URL_PATTERN),
        LuhnCardRecognizer(),
        PatternRecognizer(
            supported_entity="GENDER", name="RuleGenderRecognizer", deny_list=GENDER_TERMS, deny_list_score=RULE_SCORE
        ),
    ]


def luhn_valid(digits: str) -> bool:
    """True if `digits` passes the Luhn checksum every payment card number carries."""
    total = 0
    for i, d in enumerate(int(c) for c in reversed(digits)):
        if i % 2:
            d = d * 2 - 9 if d > 4 else d * 2
        total += d
    return total % 10 == 0


class LuhnCardRecognizer(PatternRecognizer):
    """Card numbers of 12-19 digits that pass the Luhn check.

    Presidio's own credit card recognizer stops at 16 digits, so a 19-digit
    Visa number passes through it -- and every other recognizer -- unmasked.
    """

    def __init__(self) -> None:
        super().__init__(
            supported_entity="CREDIT_CARD",
            name="RuleCardRecognizer",
            patterns=[Pattern(name="RuleCardRecognizer", regex=CARD_PATTERN.pattern, score=RULE_SCORE)],
            global_regex_flags=CARD_PATTERN.flags,
        )

    def validate_result(self, pattern_text: str) -> bool:
        return luhn_valid(re.sub(r"\D", "", pattern_text))


class SurnameGazetteerRecognizer(EntityRecognizer):
    """Detects PERSON entities by exact, whole-word match against a surname list."""

    def __init__(self, surnames: list[str]) -> None:
        self._masker = NameMasker(surnames)
        super().__init__(supported_entities=["PERSON"], name="SurnameGazetteerRecognizer", supported_language="en")

    def load(self) -> None:
        """Nothing to load: the automaton is built from the surname list in __init__."""

    def analyze(
        self, text: str, entities: list[str], nlp_artifacts: NlpArtifacts | None = None
    ) -> list[RecognizerResult]:
        return [RecognizerResult("PERSON", start, end, RULE_SCORE) for start, end in self._masker.spans(text)]
