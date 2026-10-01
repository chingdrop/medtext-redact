import click

from medtext_redact.commands.reports import parse_report
from medtext_redact.commands.studies import audit_series_by_study, compare_projects, validate_studies
from medtext_redact.paths import DATA_DIRECTORY
from medtext_redact.vendor.atomic_io import ensure_dir


@click.group()
def cli():
    """A Command-Line Interface for HIPAA Redaction and Semantic Highlighting in Medical Text."""


cli.add_command(audit_series_by_study)
cli.add_command(compare_projects)
cli.add_command(parse_report)
cli.add_command(validate_studies)


def main():
    ensure_dir(DATA_DIRECTORY)
    cli()


if __name__ == "__main__":
    main()
