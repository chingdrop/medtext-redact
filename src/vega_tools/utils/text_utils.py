import re
from rich.console import Console
from rich.text import Text
from pathlib import Path
from typing import List


class ReportWriter:
    # ToDo: Split the methods in this class to either handle censoring or highlighting text.

    def __init__(self, text: str) -> None:
        self.split_text = None
        self.console = Console()
        self._format_text(text)
        self._sanitize_dates()
        self._sanitize_age()

    def _sub_split_text(self, pattern: str, replace: str) -> List[str]:
        return [re.sub(pattern, replace, text) for text in self.split_text]

    def _format_text(self, text: str) -> None:
        text = text.strip().title()
        text = text.replace(',', ', ')
        text = re.sub(r'\s+', ' ', text)
        # ToDo - Find a way to reliably standardize middle names and name pre-fixes/suffixes with periods,
        #  ex: Dr. John R. Smith Jr.
        text = text.replace('M.D.', 'MD')
        self.split_text = re.split(r'(?<=[.!])\s+(?=\D)', text)

    def _sanitize_dates(self) -> None:
        pattern = r'(?:0[1-9]|1[0-2]|[1-9])\/(?:0[1-9]|[12][0-9]|3[01]|[1-9])\/\d{4}'
        self.split_text = self._sub_split_text(pattern, '**/**/****')

    def _sanitize_age(self):
        pattern = re.compile(
            r'\b\d{1,3}'  # Match 1 to 3 digits (e.g. 8, 45, 103)
            r'[\s\-]?'  # Optional space or dash
            r'years[\s\-]?old\b',  # Match "years-old", "years old", etc.
            flags=re.IGNORECASE
        )
        self.split_text = self._sub_split_text(pattern, '** *****-***')

    def get_report_text(self) -> str:
        return '\n'.join(self.split_text)

    def write_report_to_file(self, filename: Path | str) -> None:
        with open(filename, 'w') as f:
            f.write(self.get_report_text())
 
    def sanitize_keywords(self, keywords: List[str], replace: str) -> None:
        pattern = r'(?i)\b(?:' + '|'.join(map(re.escape, keywords)) + r')'
        self.split_text = self._sub_split_text(pattern, replace)

    def print_line_with_keywords(self, keywords: List[str]) -> None:
        pattern = r'(?i)^.*\b(?:' + '|'.join(map(re.escape, keywords)) + r')'
        for line in self.split_text:
            if re.match(pattern, line, flags=re.IGNORECASE):
                text_obj = Text(line.title())
                text_obj.highlight_words(keywords, style="bold yellow", case_sensitive=False)
                self.console.print(f"[bold green]{', '.join(set(keywords))}[/bold green] -", text_obj)
