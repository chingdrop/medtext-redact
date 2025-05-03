import csv
import re

import click
import pandas as pd
from pathlib import Path

from vega_tools.text_tools import print_line_with_keywords
from vega_tools.pandas_tools import read_excel_file, search_column_for_keywords, white_rabbit_parse_report, \
    check_series_by_study, audit_images
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


@cli.command()
@click.argument('sample')
@click.argument('result')
def audit_series_by_study(sample, result):
    data_df = read_excel_file(sample)
    descriptions_2d = {'V-Preview RCC', 'V-Preview LCC', 'V-Preview LMLO', 'V-Preview RMLO'}
    missing_2d_df = audit_images(data_df, '2D', descriptions_2d)
    descriptions_3d = {'ROUTINE3D_VOL_RCC', 'ROUTINE3D_VOL_LCC', 'ROUTINE3D_VOL_LMLO', 'ROUTINE3D_VOL_RMLO'}
    missing_3d_df = audit_images(data_df, '3D', descriptions_3d, 1)
    missing_df = pd.concat([missing_2d_df, missing_3d_df])
    missing_df.sort_values(['Accession'], inplace=True)
    with open(result, 'w', newline='') as csvfile:
        csvfile.write("Series Audit for 2D and 3D 1mm images by Study\n")
        missing_df.to_csv(csvfile, index=False)


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
