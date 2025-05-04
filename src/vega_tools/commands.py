import sys
import click
import pandas as pd

from vega_tools.text_tools import print_line_with_keywords, print_text_with_keywords, white_rabbit_parse_report
from vega_tools.pandas_tools import read_excel_file, write_excel_file, search_column_for_keywords, audit_images
from vega_tools.utils.enums import DICOM_2D_SERIES_DESCRIPTIONS, DICOM_3D_SERIES_DESCRIPTIONS


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
    missing_2d_df = audit_images(data_df, '2D', DICOM_2D_SERIES_DESCRIPTIONS)
    missing_3d_df = audit_images(data_df, '3D', DICOM_3D_SERIES_DESCRIPTIONS, 1)
    missing_df = pd.concat([missing_2d_df, missing_3d_df])
    missing_df.sort_values(['Accession'], inplace=True)
    with open(result, 'w', newline='') as csvfile:
        csvfile.write("Series Audit for 2D and 3D 1mm images by Study\n")
        missing_df.to_csv(csvfile, index=False)


@parse_report.command()
@click.option('--text', '-t', help='Input text directly (use instead of stdin).')
@click.option('--verbose', is_flag=True, help='Enable verbose output.')
def single(text, verbose):
    if not sys.stdin.isatty():
        input_text = sys.stdin.read()
    elif text:
        input_text = text
    else:
        click.echo("No input provided. Use --text or pipe data via stdin.")
        sys.exit(1)

    result_text = white_rabbit_parse_report(input_text)
    click.echo(('-' * 104) + '\n')
    if verbose:
        click.echo("Verbose mode is on.")
        print_text_with_keywords(result_text)
    else:
        # Keywords were found from initially skimming the report
        print_line_with_keywords(['left'], result_text)
        print_line_with_keywords(['right'], result_text)
        print_line_with_keywords(['wire', 'localization'], result_text)
        print_line_with_keywords(['benign'], result_text)
        print_line_with_keywords(['malignant'], result_text)
        print_line_with_keywords(['results'], result_text)
        print_line_with_keywords(['impression'], result_text)
        print_line_with_keywords(['pathology'], result_text)


# ToDo - Refactor click command to use proper file path options for parameters.
@parse_report.command()
@click.argument('sample')
@click.argument('result')
def spreadsheet(sample, result):
    df = read_excel_file(sample)
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
    write_excel_file(result_df, result)
