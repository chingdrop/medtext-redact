from typing import List

import pandas as pd

from vt_console.api_tools import CensusNamesApi


def load_census_names(year: str = "2010") -> List[str]:
    api = CensusNamesApi(year=year)
    file_path = api.save_file
    if not file_path.exists():
        api.download_and_save()

    df = pd.read_csv(file_path, header=None, names=["name"])
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
