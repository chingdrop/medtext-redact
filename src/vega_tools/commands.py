import sys
import click
from pathlib import Path

from vega_tools.text_tools import print_line_with_keywords, print_text_with_keywords, white_rabbit_parse_report
from vega_tools.pandas_tools import read_excel_file, search_column_for_keywords
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
