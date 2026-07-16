import subprocess
import sys
from pathlib import Path

import click

SPARK_NLP_DIR = Path(__file__).resolve().parent.parent.parent.parent / 'integrations' / 'spark-nlp'


@click.command(context_settings={'ignore_unknown_options': True})
@click.argument('compose_args', nargs=-1, type=click.UNPROCESSED)
def spark_nlp(compose_args):
    """
    Launch the Spark NLP / OCR Jupyter environment via Docker Compose.

    Passes any arguments straight through to `docker compose` (run from the
    spark-nlp/ directory), e.g. `vega-tools spark-nlp down` or
    `vega-tools spark-nlp logs -f`. Defaults to `up --build`.
    """
    args = list(compose_args) or ['up', '--build']
    try:
        subprocess.run(['docker', 'compose', *args], cwd=SPARK_NLP_DIR, check=True)
    except FileNotFoundError:
        click.echo("docker is not installed or not on PATH.", err=True)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)
