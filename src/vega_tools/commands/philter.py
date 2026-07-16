import logging
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import click
import nltk

from vega_tools.core.pandas_tools import repackage_txts_to_csv, split_csv_to_txt

PHILTER_UCSF_DIR = Path(__file__).resolve().parent.parent.parent.parent / "integrations" / "philter" / "philter-ucsf"


@click.command()
@click.option(
    "--sample",
    "-s",
    type=click.Path(exists=True),
    required=True,
    help="File path to a reports CSV with 'Accession' and 'Reports' columns.",
)
@click.option("--result", "-r", type=click.Path(), required=True, help="File path to write the de-identified CSV.")
@click.option(
    "--python",
    "python_executable",
    envvar="PHILTER_PYTHON",
    default="python",
    show_default=True,
    help="Python interpreter with philter-ucsf's own dependencies installed. "
    "philter-ucsf pins pandas/numpy versions that conflict with vega-tools' own, "
    "so it must run in a separate environment from this CLI. Can also be set via "
    "the PHILTER_PYTHON environment variable.",
)
def philter(sample, result, python_executable):
    """De-identify a reports spreadsheet using Philter-UCSF."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")

    nltk.download("averaged_perceptron_tagger", quiet=True)
    nltk.download("averaged_perceptron_tagger_eng", quiet=True)

    tmp_dir = Path(tempfile.mkdtemp(prefix="vega_tools_philter_"))
    input_path = tmp_dir / "input"
    output_path = tmp_dir / "output"
    input_path.mkdir()
    output_path.mkdir()
    philter_delta_path = PHILTER_UCSF_DIR / "configs" / "philter_delta.json"

    try:
        logging.info(f"Splitting {sample} into per-accession text files at {input_path}")
        split_csv_to_txt(sample, input_path)

        cmd = [
            python_executable,
            str(PHILTER_UCSF_DIR / "main.py"),
            "-i",
            str(input_path),
            "-o",
            str(output_path),
            "-f",
            str(philter_delta_path),
            "--prod",
            "True",
            "--outputformat",
            "asterisk",
        ]
        logging.info(f"Running PHILTER: {' '.join(cmd)}")
        subprocess.run(cmd, cwd=str(PHILTER_UCSF_DIR), check=True)

        logging.info(f"Repackaging de-identified text files into {result}")
        repackage_txts_to_csv(output_path, result)
    except FileNotFoundError:
        click.echo(
            f"'{python_executable}' is not installed or not on PATH. "
            f"Pass --python or set PHILTER_PYTHON to point at an interpreter with "
            f"philter-ucsf's dependencies installed (see philter/philter-ucsf/requirements.txt).",
            err=True,
        )
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        click.echo(f"PHILTER failed (exit {e.returncode}); intermediate files left at {tmp_dir}", err=True)
        sys.exit(e.returncode)
    else:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        logging.info("All done!")
