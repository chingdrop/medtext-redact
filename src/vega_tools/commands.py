import click
from pathlib import Path

from vega_tools.utils.text_utils import format_text, print_line_with_keywords


@click.command()
def main():
    data_dir = Path.cwd() / 'data'
    with open(data_dir / 'report_text.txt', 'r') as f:
        report_text = f.read()

    report_text = format_text(report_text)
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
