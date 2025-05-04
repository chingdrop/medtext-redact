import re
from typing import List

import pandas as pd
from pandas import Series
from pathlib import Path

from vega_tools.text_tools import ReportWriter
from vega_tools.utils.regex_patterns import create_keywords_pattern


def read_excel_file(file_path: str | Path, sheet_name: str | int = 0):
    """
    Reads an Excel file into a pandas DataFrame.

    Args:
        file_path (str | Path): Path to the Excel file.
        sheet_name (str | int, default = 0): Name or index of the sheet to read.

    Returns:
        pd.DataFrame: The data from the Excel sheet as a DataFrame.
    """
    try:
        return pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')
    except Exception as e:
        print(f'Error reading Excel file: {e}')
        return None


# ToDo - Add docstring for function.
def search_column_for_keywords(series: Series, keywords: List[str]) -> Series:
    pattern = create_keywords_pattern(keywords)
    return series.str.extract(pattern)
