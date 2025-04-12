import click
from pathlib import Path

from vega_tools.utils.text_utils import CustomWriter


@click.command()
def main():
    data_dir = Path.cwd() / 'data'
    with open(data_dir / 'report_text.txt', 'r') as f:
        text = f.read()

    rw = CustomWriter(text)
    rw.write_report_to_file(data_dir / 'new_report_text.txt')

    print(('-' * 79), '\n')
    rw.print_line_with_keywords(['left'])
    rw.print_line_with_keywords(['right'])
    rw.print_line_with_keywords(['wire', 'localization'])
    rw.print_line_with_keywords(['benign'])
    rw.print_line_with_keywords(['malignant'])
    rw.print_line_with_keywords(['results'])
    rw.print_line_with_keywords(['impression'])
    rw.print_line_with_keywords(['pathology'])
