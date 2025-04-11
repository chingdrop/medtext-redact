import re
from rich.console import Console
from rich.text import Text


class ReportWriter:
    def __init__(self, text):
        self.console = Console()
        self.text = text
        self.__format_text()
        self.__split_text()

    def __format_text(self):
        self.text = re.sub(r'\s+', ' ', self.text).strip()
        self.text = re.sub(r'(?<=\.)\s*', '\n', self.text).title()

    def __split_text(self):
        self.split_text = re.split(r'(?<=\.)\s*', self.text)

    def sanitize_dates(self):
        pattern = r'\b(?:0[1-9]|1[0-2])\/(?:0[1-9]|[12][0-9]|3[01])\/\d{4}'
        self.text = re.sub(pattern, '**/**/****', self.text)

    def print_line_with_keywords(self, keywords):
        pattern = r'(?i)^.*\b(?:' + '|'.join(map(re.escape, keywords)) + r')'
        for line in self.split_text:
            if re.match(pattern, line, flags=re.IGNORECASE):
                text_obj = Text(line.title())
                text_obj.highlight_words(keywords, style="bold yellow", case_sensitive=False)
                self.console.print(f"[bold green]{', '.join(set(keywords))}[/bold green] -", text_obj)
