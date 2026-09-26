import pandas as pd

from medtext_redact.core.api_tools import CensusNamesApi


def load_census_names(year: str = "2010") -> list[str]:
    api = CensusNamesApi(year=year)
    file_path = api.save_file
    if not file_path.exists():
        api.download_and_save()

    df = pd.read_csv(file_path, header=None, names=["name"])
    # The real Census surnames file has at least one genuinely blank row,
    # which pandas parses as NaN (a float) rather than an empty string --
    # .title() on that crashes, so drop non-string rows before masking.
    return [n.title() for n in df["name"] if isinstance(n, str)]


DICOM_2D_SERIES_DESCRIPTIONS = {"V-Preview RCC", "V-Preview LCC", "V-Preview LMLO", "V-Preview RMLO"}
DICOM_3D_SERIES_DESCRIPTIONS = {"ROUTINE3D_VOL_RCC", "ROUTINE3D_VOL_LCC", "ROUTINE3D_VOL_LMLO", "ROUTINE3D_VOL_RMLO"}
