from pathlib import Path

from vega_tools.commands import cli
from vega_tools.utils.files_and_storage import create_directory


PROJECT_DIRECTORY = Path.cwd().parent
DATA_DIRECTORY = PROJECT_DIRECTORY / 'data'


def main():
    create_directory(DATA_DIRECTORY)
    cli()


if __name__ == '__main__':
    main()
