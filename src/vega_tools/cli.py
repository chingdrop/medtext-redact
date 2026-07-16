import click
import pandas as pd

from vega_tools.commands.philter import philter
from vega_tools.commands.reports import parse_report
from vega_tools.commands.spark_nlp import spark_nlp
from vega_tools.commands.studies import audit_series_by_study, compare_projects, validate_studies
from vega_tools.core.utils.files_and_storage import create_directory
from vega_tools.paths import DATA_DIRECTORY


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
    create_directory(DATA_DIRECTORY)
    cli()


if __name__ == "__main__":
    main()
