import re


# def extract_keywords(text, keywords):
#     pattern = r'\b(?:' + '|'.join(map(re.escape, keywords)) + r')'
#     found_keywords = re.findall(pattern, text, flags=re.IGNORECASE)
#     if found_keywords:
#         print(f"Found the following keywords: {', '.join(set(found_keywords))}")


def print_line_with_keywords(text, keywords):
    split_text = re.split(r'(?<=\.)\s*', text)
    pattern = r'(?i)^.*\b(?:' + '|'.join(map(re.escape, keywords)) + r')'
    for line in split_text:
        if re.match(pattern, line, flags=re.IGNORECASE):
            print(f"{', '.join(set(keywords))} - {line.title()}")


if __name__ == '__main__':
    while True:
        print(('-' * 79), '\n')
        report_text = input("Please enter the report text: ")
        if report_text == 'quit':
            break

        print('\n')
        report_text = re.sub(r'(?<=\.)\s*', '\n', report_text).title()
        print(report_text)
        print('\n')

        print_line_with_keywords(report_text, ['left'])
        print_line_with_keywords(report_text, ['right'])
        print_line_with_keywords(report_text, ['wire', 'localization'])
        print_line_with_keywords(report_text, ['benign'])
        print_line_with_keywords(report_text, ['malignant'])
        print_line_with_keywords(report_text, ['Results:'])
        print_line_with_keywords(report_text, ['Impression:'])
        print_line_with_keywords(report_text, ['Pathology'])
