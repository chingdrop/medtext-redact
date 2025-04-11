import re

from rich import Console
from rich.text import Text


def format_text(text):
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'(?<=\.)\s*', '\n', text).title()
    return text


def sanitize_dates(text):
    pattern = r'\b(?:0[1-9]|1[0-2])/(?:0[1-9]|[12][0-9]|3[01])/\d{4}\b'
    text = re.sub(pattern, '**/**/****', text)


def print_line_with_keywords(text, keywords):
    console = Console()
    split_text = re.split(r'(?<=\.)\s*', text)
    pattern = r'(?i)^.*\b(?:' + '|'.join(map(re.escape, keywords)) + r')'
    for line in split_text:
        if re.match(pattern, line, flags=re.IGNORECASE):
            text_obj = Text(line.title())
            text_obj.highlight_words(keywords, style="bold yellow", case_sensitive=False)
            console.print(f"[bold green]{', '.join(set(keywords))}[/bold green] -", text_obj)
