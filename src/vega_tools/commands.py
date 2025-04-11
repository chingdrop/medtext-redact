import re
import click
from rich.console import Console
from rich.text import Text
from pathlib import Path


def print_line_with_keywords(text, keywords):
    console = Console()
    split_text = re.split(r'(?<=\.)\s*', text)
    pattern = r'(?i)^.*\b(?:' + '|'.join(map(re.escape, keywords)) + r')'
    for line in split_text:
        if re.match(pattern, line, flags=re.IGNORECASE):
            text_obj = Text(line.title())
            text_obj.highlight_words(keywords, style="bold yellow", case_sensitive=False)
            console.print(f"[bold green]{', '.join(set(keywords))}[/bold green] -", text_obj)


@click.command()
def main():
    data_dir = Path.cwd() / 'data'
    with open(data_dir / 'report_text.txt', 'r') as f:
        report_text = f.read()

    report_text = re.sub(r'\s+', ' ', report_text).strip()
    report_text = re.sub(r'(?<=\.)\s*', '\n', report_text).title()
    with open(data_dir / 'new_report_text.txt', 'w') as f:
        f.write(report_text)

    print(('-' * 79), '\n')
    print_line_with_keywords(report_text, ['left'])
    print_line_with_keywords(report_text, ['right'])
    print_line_with_keywords(report_text, ['wire', 'localization'])
    print_line_with_keywords(report_text, ['benign'])
    print_line_with_keywords(report_text, ['malignant'])
    print_line_with_keywords(report_text, ['results'])
    print_line_with_keywords(report_text, ['impression'])
    print_line_with_keywords(report_text, ['pathology'])
