import re
from rich.console import Console
from rich.text import Text


class ReportWriter:
    def __init__(self, text):
        self.console = Console()
        self.text = text
        self.__format_text()
        self.__sanitize_dates()

    def __format_text(self):
        self.text = self.text.replace('M.D.', 'MD')
        self.text = re.sub(r'\s+', ' ', self.text).strip()
        end_of_sentence = r'(?<=\.)\s+(?=\D)'
        self.text = re.sub(end_of_sentence, '\n', self.text).title()
        self.split_text = re.split(end_of_sentence, self.text)

    def __sanitize_dates(self):
        pattern = r'(?:0[1-9]|1[0-2]|[1-9])\/(?:0[1-9]|[12][0-9]|3[01]|[1-9])\/\d{4}'
        self.text = re.sub(pattern, '**/**/****', self.text)

    def print_line_with_keywords(self, keywords):
        pattern = r'(?i)^.*\b(?:' + '|'.join(map(re.escape, keywords)) + r')'
        for line in self.split_text:
            if re.match(pattern, line, flags=re.IGNORECASE):
                text_obj = Text(line.title())
                text_obj.highlight_words(keywords, style="bold yellow", case_sensitive=False)
                self.console.print(f"[bold green]{', '.join(set(keywords))}[/bold green] -", text_obj)
