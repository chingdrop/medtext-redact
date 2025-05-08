import re
from typing import List, Dict, Any

import numpy as np
from rich.console import Console
from rich.text import Text

from vega_tools.utils.regex_utils import create_keywords_pattern, mask_regex_pattern, mask_keywords


class PhiSanitizer:
    """
    Phi Sanitizer de-identifies sensitive information using regex patterns and a custom regex replacer.

    Args:
        text (str): The report text.
    """

    def __init__(self, text: str) -> None:
        self.text = ''
        if text is np.nan:
            text = ''
        self.__format_text(text)

    def __format_text(self, text: str) -> None:
        text = text.strip().title()
        text = text.replace(',', ', ')
        self.text = re.sub(r'\s+', ' ', text)

    def get_text(self):
        return self.text

    def sanitize_keywords(self, keywords: List[str]) -> None:
        """
        Sanitizes keywords from the report text.

        Args:
            keywords (List[str]): The keywords to sanitize.
        """
        self.text = mask_keywords(self.text, keywords)

    def sanitize_gender(self):
        self.sanitize_keywords(['male', 'female'])

    def sanitize_dates(self) -> None:
        date_pattern = r'(?:0[1-9]|1[0-2]|[1-9])\/(?:0[1-9]|[12][0-9]|3[01]|[1-9])\/\d{4}'
        self.text = mask_regex_pattern(date_pattern, self.text)

    def sanitize_age(self) -> None:
        age_pattern = r'\d{1,3}[-\s]?(?:years|yrs)?[-\s]?old'
        self.text = mask_regex_pattern(age_pattern, self.text)

    def sanitize_names(self) -> None:
        """Use custom name generator to iterate through the names and mask the report text."""
        from vega_tools.utils.enums import generate_common_names

        names = generate_common_names()
        for name in list(names):
            name_pattern = fr"\b({re.escape(name)})"
            self.text = mask_regex_pattern(name_pattern, self.text)


def sanitize_report_text(text: str, config: Dict[str, Any], full: bool = False) -> str:
    """
    Remove Personalized Health Information from the report text.
    Name and Dates are by default but full will mask gender and age as well.

    Args:
        text: Report text to sanitize.
        config: Client configuration dictionary.
        full (bool): Sanitization level to be used.

    Returns:
        str: The sanitized report text.
    """
    ps = PhiSanitizer(text)
    ps.sanitize_names()
    ps.sanitize_dates()
    if full:
        ps.sanitize_gender()
        ps.sanitize_age()

    masking = config['Masking']
    ps.sanitize_keywords(masking['Manufacturers'])
    ps.sanitize_keywords(masking['Locations'])
    return ps.get_text()


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
