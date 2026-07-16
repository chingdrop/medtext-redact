import sys

import click
import numpy as np
from click import Context

from vega_tools.core.pandas_tools import read_structured_file, write_structured_file, search_report_text
from vega_tools.core.text_tools import print_lines_with_keywords, print_text_with_keywords, \
    white_rabbit_parse_report, PhiSanitizer
from vega_tools.core.utils.config_loader import ConfigLoader
from vega_tools.core.utils.files_and_storage import read_text_from_file


# ToDo - Optimize the commands in parse_report, they are too slow.
@click.group()
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
    if text:
        input_text = text
    elif not sys.stdin.isatty():
        input_text = sys.stdin.read()
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
    result_df = search_report_text(result_df, config=config)
    write_structured_file(result_df, result, index=False)
