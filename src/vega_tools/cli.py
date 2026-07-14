from vega_tools.commands import cli
from vega_tools.config.settings import DATA_DIRECTORY
from vega_tools.common.utils.files_and_storage import create_directory


def main():
    create_directory(DATA_DIRECTORY)
    cli()


if __name__ == '__main__':
    main()
