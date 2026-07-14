import sys

import click
import numpy as np
import pandas as pd
from click import Context

from vega_tools.common.pandas_tools import read_structured_file, write_structured_file, audit_images, search_report_text
from vega_tools.common.text_tools import print_lines_with_keywords, print_text_with_keywords, white_rabbit_parse_report, \
    PhiSanitizer
from vega_tools.common.utils.config_loader import ConfigLoader
from vega_tools.common.utils.enums import DICOM_2D_SERIES_DESCRIPTIONS, DICOM_3D_SERIES_DESCRIPTIONS
from vega_tools.common.utils.files_and_storage import read_text_from_file


@click.group()
def cli():
    """Command Line Interface for custom use cases in data analysis."""
    pd.set_option('future.no_silent_downcasting', True)


@cli.command()
@click.option('--sample', '-s', type=click.Path(exists=True), help='File path to Sample Spreadsheet')
@click.option('--result', '-r', type=click.Path(), help='File path to Result Spreadsheet')
def audit_series_by_study(sample, result):
    data_df = read_structured_file(sample)
    data_df.replace('<NONE>', np.nan, inplace=True)
    data_df.drop('File', axis=1, inplace=True)
    data_df.rename(
        columns={
            '0008:0050': 'Accession',
            '0010:0020': 'PID',
            '0008:0018': 'SOP Instance UID',
            '0008:0008': 'Image Type',
            '0028:0008': 'Number of Frames',
            '0020:0062': 'Image Laterality (2D Only)',
            '5200:9229.#0.0020:9071.#0.0020:9072': 'Frame Laterality (3D Only)',
            '5200:9229.#0.0028:9110.#0.0018:0050': 'Slice Thickness',
            '0054:0220.#0.0008:0100': 'View Code',
            '0054:0220.#0.0054:0222.#0.0008:0100': 'View Modifier Code',
            '0008:0070': 'Manufacturer',
            '0008:1090': 'Model',
            '0008:103E': 'Series Description',
            '0008:1030': 'Study Description',
            '0002:0010': 'Transfer Syntax'
        }, inplace=True
    )
    audit_2d_df = audit_images(data_df, '2D', DICOM_2D_SERIES_DESCRIPTIONS)
    audit_3d_df = audit_images(data_df, '3D', DICOM_3D_SERIES_DESCRIPTIONS, 1)
    audit_df = pd.concat([audit_2d_df, audit_3d_df])
    audit_df.sort_values(['Accession'], inplace=True)
    write_structured_file(audit_df, result, index=False)


# ToDo - Optimize the commands in parse_report, they are too slow.
@cli.group()
@click.option(
    '--config', '-c', type=click.Path(exists=True), required=True,
    help='Path to JSON config file.'
)
@click.pass_context
def parse_report(ctx: Context, config):
    """Parse medical reports."""
    ctx.obj = ConfigLoader(config)


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

    result_text = PhiSanitizer(input_text).sanitize_all(config, full=True).text
    result_text = white_rabbit_parse_report(result_text)
    click.echo(('-' * 104) + '\n')
    if verbose:
        click.echo("Verbose mode is on.")
        print_text_with_keywords(keywords, result_text)
    else:
        # Keywords were found from initially skimming the report
        for keyword in keywords:
            print_lines_with_keywords([keyword], result_text)


@parse_report.command()
@click.option('--sample', '-s', type=click.Path(exists=True), help='File path to Sample Spreadsheet')
@click.option('--result', '-r', type=click.Path(), help='File path to Result Spreadsheet')
@click.pass_context
def spreadsheet(ctx: Context, sample, result):
    config = ctx.obj.copy()
    df = read_structured_file(sample)
    result_df = df[['Accession', 'ReportText']]
    result_df.replace('<NONE>', np.nan, inplace=True)
    result_df['ReportText'] = result_df['ReportText'].apply(
        lambda x: PhiSanitizer(x).sanitize_all(config, full=True).text
    )
    result_df['ReportText'] = result_df['ReportText'].apply(white_rabbit_parse_report)
    result_df = search_report_text(df, config=config)
    write_structured_file(result_df, result, index=False)
