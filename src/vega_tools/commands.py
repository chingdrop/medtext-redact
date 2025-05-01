import click
import pandas as pd
from pathlib import Path

from vega_tools.text_tools import print_line_with_keywords
from vega_tools.pandas_tools import read_excel_file, write_excel_file, search_column_for_keywords, \
    white_rabbit_parse_report
from vega_tools.utils.files_and_storage import read_text_from_file, write_text_to_file


@click.group()
def cli():
    """Command Line Interface for custom use cases in data analysis."""
    pass


@cli.group()
def parse_report():
    """Parse medical reports."""
    # ToDo - Develop a mechanism for storing a Client's custom parsing needs in a config file, i.e., JSON.
    pass


# ToDo - Update the DICOM tag parser to version 2
#  1. Remove the use of the key DataFrame
#  2. Confirm there are LCC, RCC, RMLO, LMLO views and both 2D and 3D images for each accession.
@cli.command()
def confirm_dicom_tags():
    data_path = Path.cwd().parent / 'data'
    key_df = pd.read_csv(data_path / 'missing_accession_numbers.csv')
    key_df['Missing Views'] = key_df['Missing Views'].str.split(',')
    key_df = key_df.explode('Missing Views').reset_index(drop=True)
    key_df.rename(columns={'Missing Views': 'Missing View'}, inplace=True)
    data_df = read_excel_file(data_path / 'Batch_Spreadsheet.xlsx')
    data_df = data_df[~data_df['Image Type'].str.contains('2D', na=False)]
    merge_df = pd.merge(key_df, data_df, how='inner', on='Accession')
    merge_df = merge_df[merge_df.apply(lambda x: x['Missing View'] in x['Series Description'], axis=1)]
    merge_df = merge_df[merge_df['View Code'] == 1]
    write_excel_file(merge_df, data_path / 'Merge_Spreadsheet.xlsx')


@parse_report.command()
@click.argument('text')
def single(text):
    result_text = white_rabbit_parse_report(text)
    # ToDo - Find a way to best display the entire report instead of saving the result to a file.
    write_text_to_file(result_text, Path.cwd().parent / 'data' / 'new_report_text.txt')

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
@click.argument('path')
def spreadsheet(path):
    df = read_excel_file(path)
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
    result_df.to_excel(Path.cwd().parent / 'data' / 'result_reports.xlsx', index=False)
