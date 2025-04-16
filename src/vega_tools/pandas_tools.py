import re
from typing import List

import pandas as pd
from pandas import Series
from pathlib import Path

from vega_tools.text_tools import ReportWriter
from vega_tools.utils.regex_patterns import create_keywords_pattern


def read_excel_file(file_path: str | Path, sheet_name: str | int=0):
    """
    Reads an Excel file into a pandas DataFrame.

    Parameters:
      file_path (str or Path): Path to the Excel file.
      sheet_name (str or int, default=0): Name or index of the sheet to read.

    Returns:
      pd.DataFrame: The data from the Excel sheet as a DataFrame.
    """
    try:
        return pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')
    except Exception as e:
        print(f'Error reading Excel file: {e}')
        return None


def search_column_for_keywords(series: Series, keywords: List[str]) -> Series:
    pattern = create_keywords_pattern(keywords)
    return series.str.extract(pattern)

# ---- Client Specific Functions ---- #
def white_rabbit_parse_report(text: str) -> str:
    rw = ReportWriter(text)
    rw.sanitize_dates()
    rw.sanitize_age()
    rw.sanitize_keywords(['female', 'male'], '******')

    # ToDo - Develop a mechanism for dynamically running the report-specific sanitization functions;
    #  given a JSON configuration file.
    # Medical supplies names
    rw.sanitize_keywords(['hydromark', 'marquee', 'suros celeros', 'suros eviva'], '********')
    penrad_pattern = re.compile(r'[a-zA-Z]{2,3}/Penrad', flags=re.IGNORECASE)
    rw.text = penrad_pattern.sub('***/******', rw.text)

    # Medical location names
    rw.sanitize_keywords(
        ['Laboratory For Pathological Analysis'], '*********** For ************ *********'
    )
    rw.sanitize_keywords(
        [
            'Southside Imaging Center - Radiology Associates',
            'Portland Imaging Center - Radiology Associates',
            'Six Points Office - Radiology Associates'
        ],
        '********* ******* ****** - ********* *********'
    )

    # ToDo - Find a way to reference a database of common names, instead of manually filling what you find.
    rw.sanitize_keywords(
        [
            'Michael',
            'Wayne',
            'Michell',
            'Mailan',
            'Melissa',
            'Cao',
            'Kenneth',
            'Cook',
            'Turner',
            'Jennifer',
            'Christopher',
            'Thomas',
            'Bruce'
        ], '********'
    )
    return rw.text
