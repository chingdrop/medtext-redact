import pandas as pd
from pandas import Series, DataFrame
from pathlib import Path
from typing import Set, List

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


# ToDo - Add docstring for function.
def audit_images(df: DataFrame, img_type: str, descriptions: Set[str], slice_thickness: int = 1) -> DataFrame:
    if img_type == '2D':
        img_df = df[df['Number of Frames'] == 1]
    elif img_type == '3D':
        img_df = df[df['Number of Frames'] > 1]
        img_df = img_df[img_df['Slice Thickness'] == slice_thickness]
    else:
        raise ValueError(f"Invalid img_type, must be '2D' or '3D': {img_type}")

    img_df = img_df[img_df['Series Description'].isin(descriptions)]
    missing_df = check_series_by_study(
        img_df, 'Accession', 'Series Description', descriptions
    )
    missing_df.insert(1, 'Image Type', img_type)
    return missing_df
