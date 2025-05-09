import re
from typing import List, Dict, Any
from typing import Optional

import pandas as pd
from rich.console import Console
from rich.text import Text

from vega_tools.utils.enums import load_census_names
from vega_tools.utils.regex_utils import create_keywords_pattern, mask_regex_pattern, mask_keywords, NameMasker


class PhiSanitizer:
    """
    Phi Sanitizer de-identifies sensitive information using regex patterns and a custom regex replacer.

    Args:
        text (str): The report text.
    """

    # ‣ Allow `/`, `-` or `.` as separators (and require you use the same one each time)
    # ‣ Constrain years to 1900–2099
    # ‣ Word‐boundaries so you don’t accidentally pick up “20212” or “13/40/1990”
    _DATE_PATTERN = re.compile(
        r"""\b
            (?:0?[1-9]|1[0-2])           # month 1–9 or 01–09 or 10–12
            (?P<sep>[\/\-\.\s])          # separator: slash, dash, dot or space
            (?:0?[1-9]|[12][0-9]|3[01])  # day 1–9, 01–09, 10–29, 30, 31
            (?P=sep)                     # same sep as before
            (?:19|20)\d{2}               # year 1900–2099
            \b
            """,
        re.VERBOSE
    )

    # ‣ Restrict age to 0–150
    # ‣ Allow “34”, “34 yrs”, “34-yrs-old”, “34 years old”, case‐insensitive
    _AGE_PATTERN = re.compile(
        r"""\b
            (?:                           # whole age number
               0|[1-9][0-9]?|1[0-4][0-9]|150
            )
            (?:                           # optional unit + “old”
              [\s\-]*                     # space or hyphen
              (?:years?|yrs?|y|yr)        # year(s) variants
            )?
            (?:[\s\-]*old)?               # optional “old”
            \b
            """,
        re.IGNORECASE | re.VERBOSE
    )

    def __init__(self, text: Optional[str], title_case: bool = False) -> None:
        self.title_case = title_case
        self._text = '' if pd.isna(text) else text.strip()
        self._format_text()

    def _format_text(self) -> None:
        # Normalize whitespace and spacing around commas
        text = re.sub(r'\s+', ' ', self._text)
        text = re.sub(r'\s*,\s*', ', ', text)
        if self.title_case:
            # Only uppercase first letter of sentence, if needed, rather than each word
            text = '. '.join(s.capitalize() for s in text.split('. '))
        self._text = text.strip()

    @property
    def text(self) -> str:
        return self._text

    def sanitize_keywords(self, keywords: List[str]) -> "PhiSanitizer":
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
        self._text = mask_regex_pattern(self._DATE_PATTERN, self._text)
        return self

    def sanitize_age(self) -> "PhiSanitizer":
        """Mask age expressions like '34 years old' or '100-yrs-old'."""
        self._text = mask_regex_pattern(self._AGE_PATTERN, self._text)
        return self

    def sanitize_gender(self) -> "PhiSanitizer":
        """Mask simple gender terms."""
        return self.sanitize_keywords(['male', 'female'])

    def sanitize_all(self, config: Dict[str, Any], full: bool = False) -> "PhiSanitizer":
        """
        Apply all sanitization steps based on client config.
        Names and dates always; gender and age if full=True.
        Also masks additional keywords from config['Masking'].

        Args:
            config: Client configuration dict with a 'Masking' key.
            full: If True, also mask gender and age.

        Returns:
            self (with _text updated)
        """
        self.sanitize_names().sanitize_dates()
        if full:
            self.sanitize_gender().sanitize_age()

        masking = config.get('Masking', {})
        for key in masking.keys():
            kws = masking.get(key) or []
            if kws:
                self.sanitize_keywords(kws)

        return self


def print_line_with_keywords(keywords: List[str], text: str) -> None:
    """
    Split the report text into lines with by periods.
    Iterate through the lines of the report text and highlight the keywords in each line.

    Args:
        keywords (List[str]): The keywords to sanitize.
        text (str): The report text.
    """
    console = Console()
    pattern = create_keywords_pattern(keywords)
    split_text = re.split(r'(?<=[.!])\s+(?=\D)', text)
    for line in split_text:
        if re.match(pattern, line):
            text_obj = Text(line.title())
            text_obj.highlight_words(keywords, style="bold yellow", case_sensitive=False)
            console.print(f"[bold green]{', '.join(set(keywords))}[/bold green] -", text_obj)


def print_text_with_keywords(keywords: List[str], text: str) -> None:
    """
    Highlight the keywords in the report text. Send highlighted text to PyDoc pager view.

    Args:
        keywords (List[str]): The keywords to sanitize.
        text (str): The report text.
    """
    import pydoc
    from io import StringIO

    buffer = StringIO()
    console = Console(file=buffer, force_terminal=True)
    text_obj = Text(text.title())
    text_obj.highlight_words(keywords, style="bold yellow", case_sensitive=False)
    console.print(text_obj)
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
    penrad_pattern = r'[a-zA-Z]{2,3}/Penrad'
    return mask_regex_pattern(penrad_pattern, text)
