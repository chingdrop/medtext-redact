from vega_tools.utils.files_and_storage import read_text_from_file
from vega_tools.cli import DATA_DIRECTORY


def generate_common_names():
    names = read_text_from_file(DATA_DIRECTORY + 'census_names.txt')
    for name in names:
        yield name.title()
