from typing import List

import pandas as pd

from vega_tools.api_tools import CensusNamesApi


def load_census_names(year: str = "2010") -> List[str]:
    api = CensusNamesApi(year=year)
    path = api.get_save_file()
    if not path.exists():
        api.download_name_list()

    df = pd.read_csv(path, header=None, names=["name"])
    return [n.title() for n in df["name"]]


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
