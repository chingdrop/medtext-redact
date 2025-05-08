from typing import Iterator

from vega_tools.api_tools import CensusNamesApi
from vega_tools.settings import DATA_DIRECTORY
from vega_tools.utils.files_and_storage import read_text_from_file


def generate_common_names() -> Iterator[str]:
    """
    Generator of common names using word list from the 2010 census.

    Returns:
        Iterator[str]: The generator of common names.
    """
    census_api = CensusNamesApi()
    save_file = census_api.get_save_file()
    if not save_file.exists():
        census_api.download_name_list()

    names = read_text_from_file(DATA_DIRECTORY / 'census_names.txt')
    for name in names:
        yield name.title()


DICOM_2D_SERIES_DESCRIPTIONS = {
    'V-Preview RCC',
    'V-Preview LCC',
    'V-Preview LMLO',
    'V-Preview RMLO'
}
DICOM_3D_SERIES_DESCRIPTIONS = {
    'ROUTINE3D_VOL_RCC',
    'ROUTINE3D_VOL_LCC',
    'ROUTINE3D_VOL_LMLO',
    'ROUTINE3D_VOL_RMLO'
}
