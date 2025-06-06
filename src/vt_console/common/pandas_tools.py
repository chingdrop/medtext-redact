from pathlib import Path
from typing import Set, List, Any, Union, Optional, Callable, Dict, Hashable

import pandas as pd
from pandas import Series, DataFrame

from vt_console.common.utils.regex_utils import compile_keywords_pattern

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


def check_series_by_study(
        df: pd.DataFrame,
        accession_col: str,
        series_col: str,
        descriptions: Set[str]
) -> pd.DataFrame:
    """
    Summarize which required series are present or missing per study.

    Args:
        df: DataFrame containing image series rows.
        accession_col: Column name identifying each study (accession).
        series_col: Column name for series descriptions.
        descriptions: Set of expected series descriptions.

    Returns:
        DataFrame with one row per accession and columns:
          - Found Set: actual set of descriptions found
          - Missing Set: descriptions not found (empty if all present)
          - Status: 'Found' if no missing, else 'Missing'
    """
    grouped = df.groupby(accession_col)[series_col].agg(lambda vals: set(vals.dropna()))

    records = []
    for accession, found in grouped.items():
        missing = descriptions - found
        status = 'Found' if not missing else 'Missing'
        records.append({
            accession_col: accession,
            'Found Set': found if found else pd.NA,
            'Missing Set': missing if missing else pd.NA,
            'Status': status
        })

    summary = pd.DataFrame.from_records(records)
    # Ensure consistent column order
    cols = [accession_col, 'Status', 'Found Set', 'Missing Set']
    return summary.loc[:, cols]


def audit_images(
        df: pd.DataFrame,
        img_type: str,
        descriptions: Set[str],
        slice_thickness: int = 1,
        accession_col: str = 'Accession',
        series_col: str = 'Series Description',
        frames_col: str = 'Number of Frames',
        thickness_col: str = 'Slice Thickness'
) -> pd.DataFrame:
    """
    Audit image series by study, filtering on 2D vs 3D and summarizing completeness.

    Args:
        df: Input DataFrame of image instances.
        img_type: '2D' or '3D'.
        descriptions: Set of expected series descriptions.
        slice_thickness: Required slice thickness for 3D images.
        accession_col: Column name for study accession.
        series_col: Column name for series description.
        frames_col: Column name for number of frames.
        thickness_col: Column name for slice thickness.

    Returns:
        DataFrame with one row per study, plus 'Image Type' column.
    """
    audit_df = df.copy()

    audit_df[frames_col] = pd.to_numeric(audit_df[frames_col], errors='coerce').fillna(0).astype(int)
    if img_type.upper() == '3D':
        audit_df[thickness_col] = pd.to_numeric(audit_df[thickness_col], errors='coerce').fillna(-1).astype(int)

    if img_type.upper() == '2D':
        mask = audit_df[frames_col] == 1
    elif img_type.upper() == '3D':
        mask = (audit_df[frames_col] > 1) & (audit_df[thickness_col] == slice_thickness)
    else:
        raise ValueError("img_type must be '2D' or '3D'")

    filtered_df = audit_df.loc[mask & audit_df[series_col].isin(descriptions)]

    final_df = check_series_by_study(filtered_df, accession_col, series_col, descriptions)
    final_df.insert(2, 'Image Type', img_type.upper())

    return final_df


def find_column_for_value(df: pd.DataFrame, value) -> str | None:
    """
    Scan each column of df. If `value` appears anywhere in column `col`,
    return the column name. If not found in any column, return None.
    """
    for col in df.columns:
        # You can use .values or faster checks like .eq(..).any()
        if value in df[col].values:
            return col
    return 'Failure Not Found'
