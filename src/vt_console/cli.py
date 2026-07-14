from vt_console.commands import cli
from vt_console.config.settings import DATA_DIRECTORY
from vt_console.common.utils.files_and_storage import create_directory


def main():
    create_directory(DATA_DIRECTORY)
    cli()


if __name__ == '__main__':
    main()
