import re
from typing import List

import pandas as pd
from pandas import Series, DataFrame
from pathlib import Path
from typing import Set

from vega_tools.text_tools import ReportWriter
from vega_tools.utils.regex_patterns import create_keywords_pattern


def read_excel_file(file_path: str | Path) -> DataFrame | None:
    """
    Reads an Excel file into a pandas DataFrame.

    Args:
        file_path (str | Path): Path to the Excel file.

    Returns:
        DataFrame | None: The data from the Excel sheet as a DataFrame.
    """
    try:
        return pd.read_excel(file_path, engine='openpyxl')
    except Exception as e:
        print(f'Error reading Excel file: {e}')
        return None


def write_excel_file(df: DataFrame, file_path: str | Path):
    """
    Writes a Pandas DataFrame to an Excel file.

    Args:
        df (DataFrame): The DataFrame to write.
        file_path (str | Path): Path to the Excel file.
    """
    try:
        df.to_excel(file_path, index=False, engine='openpyxl')
    except Exception as e:
        print(f'Error writing Excel file: {e}')


# ToDo - Add docstring for function.
def search_column_for_keywords(series: Series, keywords: List[str]) -> Series:
    """
    Search a Pandas Series for keywords and extracts the keywords from the value.

    Args:
        series (Series): The series to search for keywords.
        keywords (List[str]): The keywords to search for.

    Returns:
        Series: The series containing the keywords.
    """
    pattern = create_keywords_pattern(keywords)
    return series.str.extract(pattern)


# ToDo - Add docstring for function.
def check_series_by_study(df: DataFrame, accession_col: str, series_col: str, descriptions: Set[str]) -> DataFrame:
    """
    Groups series descriptions by accession number.
    Uses a sample Set of strings to compare the constituency of Series Description.

    Args:
        df (DataFrame): The DataFrame to write.
        accession_col (str): The column name of the accession ID.
        series_col (str): The column name of the series description.
        descriptions (Set[str]): The set of descriptions of series of images.

    Returns:
        DataFrame: The resulting DataFrame containing the found and missing series.
    """
    study = df.groupby(accession_col)[series_col].apply(set)
    missing = study[study.apply(lambda x: x != descriptions)]
    missing_df = missing.reset_index()
    missing_df.columns = [accession_col, 'Found Set']
    missing_df['Missing Set'] = missing_df['Found Set'].apply(lambda x: descriptions.difference(x))
    return missing_df


# ---- Client Specific Functions ---- #
def white_rabbit_parse_report(text: str) -> str:
    rw = ReportWriter(text)
    rw.sanitize_dates()
    rw.sanitize_age()
    rw.sanitize_keywords(['female', 'male'], '******')

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
