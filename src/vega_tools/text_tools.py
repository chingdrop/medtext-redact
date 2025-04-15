import re
from rich.console import Console
from rich.text import Text
from typing import List

from vega_tools.utils.regex_patterns import create_keywords_pattern


class ReportWriter:

    def __init__(self, text: str) -> None:
        self.text = None
        self.console = Console()
        self.__format_text(text)

    def __format_text(self, text: str) -> None:
        text = text.strip().title()
        text = text.replace(',', ', ')
        self.text = re.sub(r'\s+', ' ', text)
        # ToDo - Find a way to reliably standardize middle names and name pre-fixes/suffixes with periods,
        #  ex: Dr. John R. Smith Jr.
        # text = text.replace('M.D.', 'MD')

    def sanitize_keywords(self, keywords: List[str], replace: str) -> None:
        pattern = create_keywords_pattern(keywords)
        self.text = pattern.sub(replace, self.text)

    def sanitize_dates(self) -> None:
        date_pattern = r'(?:0[1-9]|1[0-2]|[1-9])\/(?:0[1-9]|[12][0-9]|3[01]|[1-9])\/\d{4}'
        self.text = re.sub(date_pattern, '**/**/****', self.text)

    def sanitize_age(self) -> None:
        age_pattern = re.compile(r'\d{1,3}[-\s]?(?:years|yrs)?[-\s]?old', flags=re.IGNORECASE)
        self.text = age_pattern.sub('** *****-***', self.text)

    def print_line_with_keywords(self, keywords: List[str]) -> None:
        pattern = create_keywords_pattern(keywords)
        split_text = re.split(r'(?<=[.!])\s+(?=\D)', self.text)
        for line in split_text:
            if re.match(pattern, line):
                text_obj = Text(line.title())
                text_obj.highlight_words(keywords, style="bold yellow", case_sensitive=False)
                self.console.print(f"[bold green]{', '.join(set(keywords))}[/bold green] -", text_obj)
