import re
from rich.console import Console
from rich.text import Text


def extract_keywords(text, keywords):
    pattern = r'\b(?:' + '|'.join(map(re.escape, keywords)) + r')'
    found_keywords = re.findall(pattern, text, flags=re.IGNORECASE)
    if found_keywords:
        print(f"Found the following keywords: {', '.join(set(found_keywords))}")


def print_line_with_keywords(text, keywords):
    split_text = re.split(r'(?<=\.)\s+', text)
    pattern = r'(?i)^.*\b(?:' + '|'.join(map(re.escape, keywords)) + r')\b'
    for line in split_text:
        if re.match(pattern, line, flags=re.IGNORECASE):
            print(line.title())


if __name__ == '__main__':
    console = Console()
    while True:
        print(('-' * 79), '\n')
        report_text = input("Please enter the report text: ")
        if report_text == 'quit':
            break

        print('\n')
        report_text = re.sub(r'(?<=\.)\s+', '\n', report_text).title()
        print(report_text)
        print('\n')

        print_line_with_keywords(report_text, ['Impression:', 'Pathology'])
        print('\n')

        extract_keywords(report_text, ['left'])
        extract_keywords(report_text, ['right'])
        extract_keywords(report_text, ['benign'])
        extract_keywords(report_text, ['malignant'])
        extract_keywords(report_text, ['wire', 'localization'])