import re
from re import Pattern

import pandas as pd
from rich.console import Console
from rich.text import Text

from medtext_redact.core.phi_patterns import ADDRESS_PATTERN, AGE_PATTERN, DATE_PATTERN, MRN_PATTERN, PHONE_PATTERN
from medtext_redact.core.utils.enums import load_census_names
from medtext_redact.core.utils.regex_utils import (
    NameMasker,
    compile_keywords_pattern,
    mask_keywords,
    mask_regex_pattern,
)
from medtext_redact.vendor.config_loader import ConfigLoader


class PhiSanitizer:
    """
    Phi Sanitizer de-identifies sensitive information using regex patterns and a custom regex replacer.

    Args:
        text (str): The report text.
    """

    def __init__(self, text: str | None, title_case: bool = False) -> None:
        self.title_case = title_case
        self._text = "" if pd.isna(text) else text.strip()
        self._format_text()

    def _format_text(self) -> None:
        text = re.sub(r"\s+", " ", self._text)
        text = re.sub(r"\s*,\s*", ", ", text)
        if self.title_case:
            # Only uppercase first letter of sentence, if needed, rather than each word
            text = ". ".join(s.capitalize() for s in text.split(". "))
        self._text = text.strip()

    @property
    def text(self) -> str:
        return self._text

    def sanitize_keywords(self, keywords: list[str]) -> "PhiSanitizer":
        """Mask out any occurrences of the provided keywords."""
        self._text = mask_keywords(self._text, keywords)
        return self

    def sanitize_names(self) -> "PhiSanitizer":
        """Load census names and mask any occurrences."""
        names = load_census_names()
        nm = NameMasker(names)
        self._text = nm.mask(self._text)
        return self

    def sanitize_dates(self) -> "PhiSanitizer":
        """Mask all dates matching MM/DD/YYYY or M/D/YYYY."""
        self._text = mask_regex_pattern(DATE_PATTERN, self._text)
        return self

    def sanitize_mrn(self) -> "PhiSanitizer":
        """Mask medical record numbers labeled with 'MRN' (e.g. 'MRN-1234567')."""
        self._text = mask_regex_pattern(MRN_PATTERN, self._text)
        return self

    def sanitize_phone(self) -> "PhiSanitizer":
        """Mask US phone numbers in common formats."""
        self._text = mask_regex_pattern(PHONE_PATTERN, self._text)
        return self

    def sanitize_address(self) -> "PhiSanitizer":
        """Mask street addresses (house number + street name + USPS suffix)."""
        self._text = mask_regex_pattern(ADDRESS_PATTERN, self._text)
        return self

    def sanitize_age(self) -> "PhiSanitizer":
        """Mask age expressions like '34 years old' or '100-yrs-old'."""
        self._text = mask_regex_pattern(AGE_PATTERN, self._text)
        return self

    def sanitize_gender(self) -> "PhiSanitizer":
        """Mask simple gender terms."""
        return self.sanitize_keywords(["male", "female", "males", "females"])

    def sanitize_all(self, config: ConfigLoader, full: bool = False) -> "PhiSanitizer":
        """
        De‐identify PHI using the provided ConfigLoader.

        Args:
            config: a ConfigLoader instance whose config contains
                    a 'Masking' section with 'Manufacturers' and 'Locations'.
            full: if True, also mask gender + age
        """
        # MRN before phone: a labeled MRN ("MRN 1234567890") is otherwise
        # digit-shaped enough to also match the phone pattern -- masking it
        # first removes the ambiguity rather than relying on match order
        # inside a single pass.
        self.sanitize_names().sanitize_mrn().sanitize_phone().sanitize_address().sanitize_dates()
        if full:
            self.sanitize_gender().sanitize_age()
        return self.sanitize_configured_keywords(config)

    def sanitize_configured_keywords(self, config: ConfigLoader) -> "PhiSanitizer":
        """Mask the config's 'Masking.Manufacturers' and 'Masking.Locations' keyword lists."""
        manufacturers = config.get("Masking.Manufacturers")
        locations = config.get("Masking.Locations")

        if manufacturers:
            self.sanitize_keywords(manufacturers)
        if locations:
            self.sanitize_keywords(locations)

        return self

    def sanitize_presidio(self) -> "PhiSanitizer":
        """Mask every entity Microsoft Presidio detects, instead of the regex/gazetteer rules."""
        # Imported here so the rules engine doesn't pay for loading spaCy.
        from medtext_redact.core.presidio_tools import presidio_redact

        self._text = presidio_redact(self._text)
        return self


def _highlight_text(text: str, pattern: Pattern[str], style: str = "bold yellow") -> Text:
    """
    Return a Rich Text object with every regex match styled.
    """
    t = Text(text)
    for m in pattern.finditer(text):
        t.stylize(style, m.start(), m.end())
    return t


def print_lines_with_keywords(
    keywords: list[str],
    text: str,
    *,
    boundary: bool = True,
    style: str = "bold yellow",
    console: Console | None = None,
) -> None:
    """
    Split `text` into sentences (on .?!), find lines containing any keyword,
    and print each line with the keywords highlighted.
    """
    console = console or Console()
    pattern = compile_keywords_pattern(keywords, boundary=boundary)

    sentences = re.split(r"(?<=[.?!])\s+", text)
    for sentence in sentences:
        if pattern.search(sentence):
            highlighted = _highlight_text(sentence.strip(), pattern, style)
            console.print(highlighted)


def print_text_with_keywords(
    keywords: list[str], text: str, *, boundary: bool = True, style: str = "bold yellow"
) -> None:
    """Highlight all occurrences of `keywords` in the full `text` and page it via the system pager (using PyDoc)."""
    import pydoc
    from io import StringIO

    pattern = compile_keywords_pattern(keywords, boundary=boundary)
    highlighted = _highlight_text(text, pattern, style)

    buffer = StringIO()
    console = Console(file=buffer, force_terminal=True)
    console.print(highlighted)
    pydoc.pager(buffer.getvalue())


# ---- Client Specific Functions ---- #
def white_rabbit_parse_report(text: str) -> str:
    """
    Sanitize Penrad Doctor signature with custom masking.

    Args:
        text (str): The report text.

    Returns:
        str: The report text with Penrad masked.
    """
    penrad_pattern = r"[a-zA-Z]{2,3}/Penrad"
    return mask_regex_pattern(penrad_pattern, text)
