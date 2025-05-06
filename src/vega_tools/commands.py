import sys
import click
import pandas as pd
import numpy as np
from click import Context

from vega_tools.text_tools import print_line_with_keywords, print_text_with_keywords, white_rabbit_parse_report
from vega_tools.pandas_tools import read_excel_file, write_excel_file, search_column_for_keywords, audit_images
from vega_tools.utils.config_loader import ConfigLoader
from vega_tools.utils.enums import DICOM_2D_SERIES_DESCRIPTIONS, DICOM_3D_SERIES_DESCRIPTIONS
from vega_tools.utils.file_utils import read_text_from_file


@click.group()
def cli():
    """Command Line Interface for custom use cases in data analysis."""
    pd.set_option('future.no_silent_downcasting', True)

@cli.command()
@click.option('--sample', '-s', type=click.Path(exists=True), help='File path to Sample Spreadsheet')
@click.option('--result', '-r', type=click.Path(), help='File path to Result Spreadsheet')
def audit_series_by_study(sample, result):
    data_df = read_excel_file(sample)
    data_df.replace('<NONE>', np.nan, inplace=True)
    missing_2d_df = audit_images(data_df, '2D', DICOM_2D_SERIES_DESCRIPTIONS)
    missing_3d_df = audit_images(data_df, '3D', DICOM_3D_SERIES_DESCRIPTIONS, 1)
    missing_df = pd.concat([missing_2d_df, missing_3d_df])
    missing_df.sort_values(['Accession'], inplace=True)
    with open(result, 'w', newline='') as csvfile:
        csvfile.write("Series Audit for 2D and 3D 1mm images by Study\n")
        missing_df.to_csv(csvfile, index=False)


@cli.group()
@click.option(
    '--config', '-c', type=click.Path(exists=True), required=True,
    help='Path to JSON config file.'
)
@click.pass_context
def parse_report(ctx, config):
    """Parse medical reports."""
    loader = ConfigLoader(config)
    ctx.obj = loader.as_kwargs()


# ToDo - Refactor click command to use proper file filepath options for parameters.
@parse_report.command()
@click.option('--text', '-t', help='Input text directly (use instead of stdin).')
@click.option('--keywords', '-k', multiple=True, help='List of keywords provided.')
@click.option(
    '--keywords-file', '-f', type=click.Path(exists=True),
    help='Path to a file containing keywords (one per line)'
)
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output.')
@click.pass_context
def single(ctx: Context, text, keywords, keywords_file, verbose):
    config = ctx.obj.copy()
    if not sys.stdin.isatty():
        input_text = sys.stdin.read()
    elif text:
        input_text = text
    else:
        click.echo("No input provided. Use --text or pipe data via stdin.")
        sys.exit(1)

    if keywords_file and not keywords:
        keywords = read_text_from_file(keywords_file)
        keywords = keywords.splitlines()

    result_text = white_rabbit_parse_report(input_text)
    click.echo(('-' * 104) + '\n')
    if verbose:
        click.echo("Verbose mode is on.")
        print_text_with_keywords(keywords, result_text)
    else:
        # Keywords were found from initially skimming the report
        for keyword in keywords:
            print_line_with_keywords([keyword], result_text)


# ToDo - Refactor click command to use proper filepath options for parameters.
@parse_report.command()
@click.argument('sample')
@click.argument('result')
@click.pass_context
def spreadsheet(ctx: Context, sample, result):
    config = ctx.obj.copy()
    df = read_excel_file(sample)
    result_df = df[(df['StudyDescription'] == 'BIOPSY') & (df['ExamCategory'] == 'Biopsy')]
    result_df = result_df[['Accession', 'ReportText']]
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
