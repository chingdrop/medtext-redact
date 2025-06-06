import sys
from pathlib import Path

import click
import numpy as np
import pandas as pd
from click import Context

from vt_console.common.pandas_tools import read_structured_file, write_structured_file, audit_images, \
    search_report_text, find_column_for_value, merge_on_matched_column
from vt_console.common.text_tools import print_lines_with_keywords, print_text_with_keywords, white_rabbit_parse_report, \
    PhiSanitizer
from vt_console.common.utils.config_loader import ConfigLoader
from vt_console.common.utils.enums import DICOM_2D_SERIES_DESCRIPTIONS, DICOM_3D_SERIES_DESCRIPTIONS
from vt_console.common.utils.files_and_storage import read_text_from_file
from vt_console.common.utils.regex_utils import parse_project_name


@click.group()
def cli():
    """Command Line Interface for custom use cases in data analysis."""
    pd.set_option('future.no_silent_downcasting', True)


@cli.command()
@click.option('--project', '-p', help='Project tag to filter from the reference spreadsheet.')
@click.option('--sample', '-s', type=click.Path(exists=True), help='File path to Sample Spreadsheet')
@click.option('--result', '-r', type=click.Path(), help='File path to Result Spreadsheet')
@click.option(
    '--order',
    '-o',
    type=click.Choice(['first', 'second'], case_sensitive=False),
    help='Choose which project order to use'
)
def validate_studies(project, sample, result, order):
    data_path = Path(__file__).resolve().parent.parent.parent / 'data'
    if order == 'first':
        proj_col = 'project_1'
        access_col = 'accession_1'
    else:
        proj_col = 'project_2'
        access_col = 'accession_2'

    ref_df = read_structured_file(data_path / 'dupe_audit.xlsx')
    ref_df = ref_df[ref_df[proj_col] == project]

    data_df = read_structured_file(sample)
    matched_col = ref_df[access_col].apply(lambda x: find_column_for_value(data_df, x))
    result_df = pd.DataFrame({
        'study_instance_uid': ref_df['study_instance_uid'],
        'accession': ref_df[access_col],
        'matched_col': matched_col
    })
    result_df['failure'] = result_df['matched_col'] == 'Failure Not Found'
    result_df['type'] = np.where(
        result_df['matched_col'].str.contains('prior', case=False, na=False),
        'Prior',
        'Index'
    )
    result_df = merge_on_matched_column(result_df, data_df, key_col="accession", matched_col_col="matched_col")

    keep_columns = ['study_instance_uid', 'accession', 'matched_col', 'failure', 'type']
    group_columns = [col for col in result_df.columns if 'group' in str(col).lower()]
    final_columns = keep_columns + group_columns
    result_df = result_df[final_columns]
    write_structured_file(result_df, result, index=False)


@cli.command()
@click.option('--sample', '-s', type=click.Path(exists=True), help='File path to Sample Spreadsheet')
@click.option('--result', '-r', type=click.Path(), help='File path to Result Spreadsheet')
def compare_projects(sample, result):
    def find_project_order(row):
        p1 = row['file_1']
        p2 = row['file_2']

        t1 = parse_project_name(p1)
        t2 = parse_project_name(p2)
        if t1 < t2:
            return p1, p2
        else:
            return p2, p1

    def find_accession_order(row):
        t1 = parse_project_name(row['file_1'])
        t2 = parse_project_name(row['file_2'])
        if t1 < t2:
            return row['file_1_accession'], row['file_2_accession']
        else:
            return row['file_2_accession'], row['file_1_accession']

    data_df = read_structured_file(sample)
    result_df = data_df[['study_instance_uid']].copy()
    result_df[['project_1', 'project_2']] = data_df.apply(find_project_order, axis=1, result_type="expand")
    result_df[['accession_1', 'accession_2']] = data_df.apply(find_accession_order, axis=1, result_type="expand")
    write_structured_file(result_df, result, index=False)


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
