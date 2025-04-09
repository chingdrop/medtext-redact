import re


def search_keywords(text, keywords):
    pattern = r'\b(?:' + '|'.join(map(re.escape, keywords)) + r')\b'
    found_keywords = re.findall(pattern, text, flags=re.IGNORECASE)
    if found_keywords:
        print(f"Found the following keywords: {', '.join(set(found_keywords))}")
    else:
        print("No keywords found.")


if __name__ == '__main__':
    report_text = input("Please enter the report text: ")
    search_keywords(report_text, ['left'])
    search_keywords(report_text, ['right'])
    search_keywords(report_text, ['benign'])
    search_keywords(report_text, ['malignant'])