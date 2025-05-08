import io
import zipfile
from pathlib import Path

import pandas as pd

from vega_tools.settings import DATA_DIRECTORY
from vega_tools.utils.rest_utils import RestAdapter


# ToDo - Add docstrings for class.
class CensusNamesApi:
    def __init__(
            self,
            year: str,
            save_file: Path | str = None
    ):
        if year == '2010':
            base_url = 'https://www2.census.gov/topics/genealogy/2010surnames'
        elif year == '2000':
            base_url = 'https://www2.census.gov/topics/genealogy/2000surnames/'
        else:
            raise ValueError("Year must be '2010' or '2000'")

        if save_file is None:
            save_file = DATA_DIRECTORY / 'census_names.txt'
        self.save_file = save_file
        self._rest = RestAdapter(base_url=base_url)

    def get_save_file(self) -> Path:
        return self.save_file

    def download_name_list(self):
        data = self._rest.get('/names.zip')
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            with z.open('Names_2010Census.csv') as csvfile:
                df = pd.read_csv(csvfile)
                names = df['name']
                names.to_csv(self.save_file, index=False, header=False)
