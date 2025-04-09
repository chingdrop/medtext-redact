import re


def search_report_text(text, keywords):
    pattern = r'\b(?:' + '|'.join(map(re.escape, keywords)) + r')'
    found_keywords = re.findall(pattern, text, flags=re.IGNORECASE)
    if found_keywords:
        print(f"Found the following keywords: {', '.join(set(found_keywords))}")
    else:
        print("No keywords found")


if __name__ == '__main__':
    while True:
        print(('-' * 79), '\n')
        report_text = input("Please enter the report text: ")
        if report_text == 'quit':
            break

        print('\n')
        print(re.sub(r'(?<=\.)\s+', '\n', report_text))
        print('\n')

        search_report_text(report_text, ['left'])
        search_report_text(report_text, ['right'])
        search_report_text(report_text, ['benign'])
        search_report_text(report_text, ['malignant'])