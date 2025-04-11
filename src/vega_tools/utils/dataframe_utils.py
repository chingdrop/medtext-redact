import re
import pandas as pd
from pathlib import Path


def search_keywords(value, keywords):
    if isinstance(keywords, str):
        keywords = [keywords]
    pattern = r'\b(?:' + '|'.join(map(re.escape, keywords)) + r')\b'
    found_keywords = re.findall(pattern, value, flags=re.IGNORECASE)
    return set(found_keywords)


def search_single_word(text, keywords):
    res = search_keywords(text, keywords)
    if res:
        res = str(res).title()
    return res

if __name__ == '__main__':
    data_path = Path.cwd() / 'data'
    df = pd.read_excel(data_path / "PRJ116405_ClientFacing_Reference_SpreadsheetvB.xlsx")
    df['BiopsySide'] = df['ReportText'].apply(lambda x: search_single_word(x, 'left'))
    df['BiopsySide'] = df['ReportText'].apply(lambda x: search_single_word(x, 'right'))
    df['BiopsyResult'] = df['ReportText'].apply(lambda x: search_single_word(x, 'benign'))
    df['BiopsyResult'] = df['ReportText'].apply(lambda x: search_single_word(x, 'malignant'))
