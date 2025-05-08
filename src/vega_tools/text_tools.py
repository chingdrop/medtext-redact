import re
from typing import List, Dict, Any

import numpy as np
from rich.console import Console
from rich.text import Text

from vega_tools.utils.regex_utils import create_keywords_pattern, mask_regex_pattern, mask_keywords


# ToDo - Add docstrings for class.
class ReportWriter:

    def __init__(self, text: str) -> None:
        self.text = None
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
        from vega_tools.utils.enums import generate_common_names

        names = generate_common_names()
        for name in list(names):
            name_pattern = fr"\b({re.escape(name)})"
            self.text = mask_regex_pattern(name_pattern, self.text)


# ToDo - Add docstring for function.
def sanitize_report_text(text: str, config: Dict[str, Any], full: bool = False) -> str:
    rw = ReportWriter(text)
    rw.sanitize_names()
    rw.sanitize_dates()
    if full:
        rw.sanitize_gender()
        rw.sanitize_age()

    masking = config['Masking']
    rw.sanitize_keywords(masking['Manufacturers'])
    rw.sanitize_keywords(masking['Locations'])
    return rw.get_text()


# ToDo - Add docstring for function.
def print_line_with_keywords(keywords: List[str], text: str) -> None:
    console = Console()
    pattern = create_keywords_pattern(keywords)
    split_text = re.split(r'(?<=[.!])\s+(?=\D)', text)
    for line in split_text:
        if re.match(pattern, line):
            text_obj = Text(line.title())
            text_obj.highlight_words(keywords, style="bold yellow", case_sensitive=False)
            console.print(f"[bold green]{', '.join(set(keywords))}[/bold green] -", text_obj)


# ToDo - Add docstring for function.
def print_text_with_keywords(keywords: List[str], text: str) -> None:
    import pydoc
    from io import StringIO

    buffer = StringIO()
    console = Console(file=buffer, force_terminal=True)
    text_obj = Text(text.title())
    text_obj.highlight_words(keywords, style="bold yellow", case_sensitive=False)
    console.print(text_obj)
    pydoc.pager(buffer.getvalue())


# ---- Client Specific Functions ---- #
# ToDo - Add docstring for function.
def white_rabbit_parse_report(text: str) -> str:
    penrad_pattern = r'[a-zA-Z]{2,3}/Penrad'
    return mask_regex_pattern(penrad_pattern, text)
