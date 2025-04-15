import re
import pandas as pd
from pathlib import Path


def read_excel_file(file_path: str | Path, sheet_name: str | int=0):
    """
    Reads an Excel file into a pandas DataFrame.

    Parameters:
    - file_path (str or Path): Path to the Excel file.
    - sheet_name (str or int, default=0): Name or index of the sheet to read.

    Returns:
    - pd.DataFrame: The data from the Excel sheet as a DataFrame.
    """
    try:
        return pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')
    except Exception as e:
        print(f'Error reading Excel file: {e}')
        return None

if __name__ == '__main__':
    data_path = Path.cwd() / 'data'
    df = pd.read_excel(data_path / "PRJ116405_ClientFacing_Reference_SpreadsheetvB.xlsx")
    df['BiopsySide'] = df['ReportText'].apply(lambda x: search_single_word(x, 'left'))
    df['BiopsySide'] = df['ReportText'].apply(lambda x: search_single_word(x, 'right'))
    df['BiopsyResult'] = df['ReportText'].apply(lambda x: search_single_word(x, 'benign'))
    df['BiopsyResult'] = df['ReportText'].apply(lambda x: search_single_word(x, 'malignant'))
