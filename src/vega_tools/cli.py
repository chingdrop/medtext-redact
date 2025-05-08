from vega_tools.commands import cli
from vega_tools.settings import DATA_DIRECTORY
from vega_tools.utils.files_and_storage import create_directory


def main():
    create_directory(DATA_DIRECTORY)
    cli()


if __name__ == '__main__':
    main()
