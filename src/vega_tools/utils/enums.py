from vega_tools.utils.files_and_storage import read_text_from_file
from vega_tools.api_tools import CensusApi
from vega_tools.cli import DATA_DIRECTORY


def generate_common_names():
    census_api = CensusApi()
    census_api.download_name_list()

    names = read_text_from_file(DATA_DIRECTORY + 'census_names.txt')
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