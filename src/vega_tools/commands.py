import click
from pathlib import Path

from vega_tools.text_tools import print_line_with_keywords
from vega_tools.pandas_tools import read_excel_file, search_column_for_keywords, white_rabbit_parse_report
from vega_tools.utils.files_and_storage import read_text_from_file, write_text_to_file


@click.group()
def cli():
    pass


@cli.group()
def parse_report():
    """Parse medical reports."""
    pass


@parse_report.command()
def single():
    data_dir = Path.cwd().parent / 'data'
    text = read_text_from_file(data_dir / 'text.txt')

    result_text = white_rabbit_parse_report(text)
    write_text_to_file(result_text, data_dir / 'new_report_text.txt')

    print(('-' * 104), '\n')
    # Keywords were found from initially skimming the report
    print_line_with_keywords(['left'], result_text)
    print_line_with_keywords(['right'], result_text)
    print_line_with_keywords(['wire', 'localization'], result_text)
    print_line_with_keywords(['benign'], result_text)
    print_line_with_keywords(['malignant'], result_text)
    print_line_with_keywords(['results'], result_text)
    print_line_with_keywords(['impression'], result_text)
    print_line_with_keywords(['pathology'], result_text)


@parse_report.command()
def spreadsheet():
    data_dir = Path.cwd().parent / 'data'
    df = read_excel_file(data_dir / "PRJ116405_ClientFacing_Reference_SpreadsheetvB.xlsx")
    result_df = df[(df['StudyDescription'] == 'BIOPSY') & (df['ExamCategory'] == 'Biopsy')]
    result_df = result_df[[
        'Accession',
        # 'Original PID',
        # 'Orig BX Date',
        'ReportText',
        # 'BiopsyDate',
        # 'BiopsySide',
        # 'BiopsyResult',
        # 'PathologyType'
    ]]
    result_df['ReportText'] = result_df['ReportText'].apply(white_rabbit_parse_report)
    result_df['FoundBiopsySide'] = search_column_for_keywords(
        result_df['ReportText'], ['left breast', 'right breast']
    )
    result_df['FoundBiopsyResult'] = search_column_for_keywords(
        result_df['ReportText'], ['benign', 'malignant']
    )
    result_df['FoundPathologyType'] = search_column_for_keywords(
        result_df['ReportText'],
        [
            'Carcinoma',
            'Fibroadenoma',
            'Hyperplasia',
            'Lymphoma',
            'Benign Cyst',
            'Fibrocystic Changes',
            'Papilloma',
            'Stromal Fibrosis',
            'Spindle Cell',
            'Metastatic',
            'Radial Scar'
        ]
    )
    result_df.to_excel(data_dir / 'result_reports.xlsx', index=False)
