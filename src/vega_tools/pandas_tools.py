from pathlib import Path
from typing import Set, List, Any, Union, Optional, Callable, Dict

import pandas as pd
from pandas import Series, DataFrame

from vega_tools.utils.regex_utils import compile_keywords_pattern


Reader = Callable[..., pd.DataFrame]
READERS: Dict[str, Reader] = {
    "csv": pd.read_csv,
    "txt": pd.read_csv,
    "xls": pd.read_excel,
    "xlsx": pd.read_excel,
    "json": pd.read_json,
    "html": lambda path, **kw: pd.read_html(path, **kw)[0],
    "htm": lambda path, **kw: pd.read_html(path, **kw)[0],
}

def read_structured_file(
        file_path: Union[str, Path],
        file_type: Optional[str] = None,
        **kwargs
) -> Optional[pd.DataFrame]:
    """
    Reads a structured data file (CSV, Excel, JSON, Parquet, etc.) into a DataFrame.

    Args:
        file_path (Union[str, Path]): Structured data file to read.
        file_type (Optional[str]): Override the extension detection; e.g. "csv", "json".
        **kwargs: Passed verbatim to the underlying pandas' reader.

    Returns:
        A DataFrame, or None if the file type is unsupported or an error occurs.
    """
    path = Path(file_path)
    ext = (file_type or path.suffix.lstrip(".")).lower()

    reader = READERS.get(ext)
    if reader is None:
        print(f"Unsupported file type: .{ext}")
        return None

    try:
        if ext in ("xls", "xlsx") and "engine" not in kwargs:
            kwargs.setdefault("engine", "openpyxl")
        return reader(path, **kwargs)
    except Exception as e:
        print(f"Error reading .{ext} file at {path!r}: {e}")
        return None


Writer = Callable[..., None]
WRITERS: Dict[str, Writer] = {
    "csv": lambda df, path, **kw: df.to_csv(path, **kw),
    "txt": lambda df, path, **kw: df.to_csv(path, **kw),
    "xls": lambda df, path, **kw: df.to_excel(path, **kw),
    "xlsx": lambda df, path, **kw: df.to_excel(path, **kw),
    "json": lambda df, path, **kw: df.to_json(path, **kw),
    "html": lambda df, path, **kw: df.to_html(path, **kw),
    "htm": lambda df, path, **kw: df.to_html(path, **kw),
}

def write_structured_file(
        df: pd.DataFrame,
        file_path: Union[str, Path],
        file_type: Optional[str] = None,
        **kwargs
) -> bool:
    """
    Writes a DataFrame to a structured-data file (CSV, Excel, JSON, Parquet, etc.).

    Args:
        df (DataFrame): The DataFrame you want to write.
        file_path (Union[str, Path]): Output file path.
        file_type (Optional[str]): Override the extension detection; e.g. "csv", "json".
        **kwargs: Passed along to the underlying pandas writer
            (e.g. index=False, sheet_name="Data", orient="records").

    Returns:
        True if write succeeds; False on unsupported type or error.
    """
    path = Path(file_path)
    ext = (file_type or path.suffix.lstrip(".")).lower()

    writer = WRITERS.get(ext)
    if writer is None:
        print(f"Unsupported file type for writing: .{ext}")
        return False

    try:
        if ext in ("xls", "xlsx") and "engine" not in kwargs:
            kwargs.setdefault("engine", "openpyxl")

        writer(df, path, **kwargs)
        return True
    except Exception as e:
        print(f"Error writing .{ext} file to {path!r}: {e}")
        return False


def search_column_for_keywords(series: Series, keywords: List[str]) -> Series:
    """
    Search a Pandas Series for keywords and extracts the keywords from the value.

    Args:
        series (Series): The series to search for keywords.
        keywords (List[str]): The keywords to search for.

    Returns:
        Series: The series containing the keywords.
    """
    pattern = compile_keywords_pattern(keywords)
    return series.str.extract(pattern)


def search_report_text(df: DataFrame, config: Dict[str, Any]) -> DataFrame:
    """
    Use client configuration file to search report text and create subsequent columns.

    Args:
        df (DataFrame): The DataFrame to analyze.
        config (Dict[str, Any]): The configuration to use.

    Returns:
        DataFrame: The Final DataFrame with new columns.
    """
    searching = config['Searching']
    df['FoundBiopsySide'] = search_column_for_keywords(df['ReportText'], searching['AnatomicalTags'])
    df['FoundBiopsyResult'] = search_column_for_keywords(df['ReportText'], ['benign', 'malignant'])
    df['FoundPathologyType'] = search_column_for_keywords(df['ReportText'], searching['PathologyKeywords'])
    return df


def check_series_by_study(df: DataFrame, accession_col: str, series_col: str, descriptions: Set[str]) -> DataFrame:
    """
    Groups series descriptions by accession number.
    Uses a sample Set of strings to compare the constituency of Series Description.

    Args:
        df (DataFrame): The DataFrame to analyze.
        accession_col (str): The column name of the accession ID.
        series_col (str): The column name of the series description.
        descriptions (Set[str]): The set of descriptions of series of images.

    Returns:
        DataFrame: The resulting DataFrame containing the found and missing series.
    """
    study = df.groupby(accession_col)[series_col].apply(set)

    found = study[study == descriptions]
    found_df = found.reset_index()
    found_df.columns = [accession_col, 'Found Set']
    found_df.insert(1, 'Status', 'Found')

    missing = study[study != descriptions]
    missing_df = missing.reset_index()
    missing_df.columns = [accession_col, 'Found Set']
    missing_df.insert(1, 'Status', 'Missing')
    missing_df['Missing Set'] = missing_df['Found Set'].apply(lambda x: descriptions - x)

    return pd.concat([found_df, missing_df], ignore_index=True)


def audit_images(df: DataFrame, img_type: str, descriptions: Set[str], slice_thickness: int = 1) -> DataFrame:
    """
    Audit Series by Study using Exodus Indexer text export.
    Specify image type to handle both 2D and 3D images. Filter export to only the specified series descriptions.

    Args:
        df (DataFrame): The DataFrame to analyze.
        img_type (str): The type of image to analyze.
        descriptions: Set of series descriptions to audit.
        slice_thickness (int): The number of frames to filter from the DataFrame.

    Returns:
        DataFrame: The resulting DataFrame containing the audit sets.
    """
    if img_type == '2D':
        img_df = df[df['Number of Frames'] == 1]
    elif img_type == '3D':
        img_df = df[df['Number of Frames'] > 1]
        img_df = img_df[img_df['Slice Thickness'] == slice_thickness]
    else:
        raise ValueError(f"Invalid img_type, must be '2D' or '3D': {img_type}")

    img_df = img_df[img_df['Series Description'].isin(descriptions)]
    audit_df = check_series_by_study(
        img_df, 'Accession', 'Series Description', descriptions
    )
    audit_df.insert(2, 'Image Type', img_type)
    return audit_df
