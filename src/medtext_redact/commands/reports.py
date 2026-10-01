import sys

import click
import numpy as np
from click import Context

from medtext_redact.core.pandas_tools import search_report_text
from medtext_redact.core.text_tools import (
    PhiSanitizer,
    print_lines_with_keywords,
    print_text_with_keywords,
    white_rabbit_parse_report,
)
from medtext_redact.core.utils.files_and_storage import read_text_from_file
from medtext_redact.vendor.config_loader import ConfigLoader
from medtext_redact.vendor.tabular_io import TabularIOError, read_structured_file, write_structured_file

ENGINE_KEY = "medtext_redact.engine"


def redact(text: str | None, config: ConfigLoader, engine: str) -> str:
    """Redact PHI from one report with the chosen engine, then apply the config's keyword masks."""
    sanitizer = PhiSanitizer(text)
    if engine == "presidio":
        sanitizer.sanitize_presidio().sanitize_configured_keywords(config)
    else:
        sanitizer.sanitize_all(config, full=True)
    return sanitizer.text


# ToDo - Optimize the commands in parse_report, they are too slow.
@click.group()
@click.option("--config", "-c", type=click.Path(exists=True), required=True, help="Path to JSON config file.")
@click.option(
    "--engine",
    "-e",
    type=click.Choice(["rules", "presidio"], case_sensitive=False),
    default="rules",
    show_default=True,
    help="PHI detection engine: regex/gazetteer rules, or Microsoft Presidio (NER + pattern recognizers).",
)
@click.pass_context
def parse_report(ctx: Context, config, engine):
    """Parse medical reports."""
    ctx.obj = ConfigLoader(config)
    ctx.meta[ENGINE_KEY] = engine.lower()


@parse_report.command()
@click.option("--text", "-t", help="Input text directly (use instead of stdin).")
@click.option("--keywords", "-k", multiple=True, help="List of keywords provided.")
@click.option(
    "--keywords-file", "-f", type=click.Path(exists=True), help="Path to a file containing keywords (one per line)"
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output.")
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

    result_text = redact(input_text, config, ctx.meta[ENGINE_KEY])
    result_text = white_rabbit_parse_report(result_text)
    click.echo(("-" * 104) + "\n")
    if verbose:
        click.echo("Verbose mode is on.")
        print_text_with_keywords(keywords, result_text)
    else:
        # Keywords were found from initially skimming the report
        for keyword in keywords:
            print_lines_with_keywords([keyword], result_text)


@parse_report.command()
@click.option("--sample", "-s", type=click.Path(exists=True), help="File path to Sample Spreadsheet")
@click.option("--result", "-r", type=click.Path(), help="File path to Result Spreadsheet")
@click.pass_context
def spreadsheet(ctx: Context, sample, result):
    config = ctx.obj.copy()
    try:
        df = read_structured_file(sample)
    except TabularIOError as exc:
        click.echo(f"Could not read sample spreadsheet: {sample} ({exc})", err=True)
        sys.exit(1)
    result_df = df[["Accession", "ReportText"]]
    result_df.replace("<NONE>", np.nan, inplace=True)
    engine = ctx.meta[ENGINE_KEY]
    result_df["ReportText"] = result_df["ReportText"].apply(lambda x: redact(x, config, engine))
    result_df["ReportText"] = result_df["ReportText"].apply(white_rabbit_parse_report)
    result_df = search_report_text(result_df, config=config)
    write_structured_file(result_df, result, index=False)
