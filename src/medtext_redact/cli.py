import click
import pandas as pd
from shared_tools.atomic_io import ensure_dir

from medtext_redact.commands.philter import philter
from medtext_redact.commands.reports import parse_report
from medtext_redact.commands.spark_nlp import spark_nlp
from medtext_redact.commands.studies import audit_series_by_study, compare_projects, validate_studies
from medtext_redact.paths import DATA_DIRECTORY


@click.group()
def cli():
    """Command Line Interface for custom use cases in data analysis."""
    pd.set_option("future.no_silent_downcasting", True)


cli.add_command(audit_series_by_study)
cli.add_command(compare_projects)
cli.add_command(parse_report)
cli.add_command(philter)
cli.add_command(spark_nlp)
cli.add_command(validate_studies)


def main():
    ensure_dir(DATA_DIRECTORY)
    cli()


if __name__ == "__main__":
    main()
