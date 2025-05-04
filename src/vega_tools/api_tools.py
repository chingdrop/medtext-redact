import io
import zipfile
import pandas as pd

from vega_tools.utils.rest import RestAdapter
from vega_tools.cli import DATA_DIRECTORY


# ToDo - Add docstrings for class.
class CensusApi:
    def __init__(self):
        self.rest = RestAdapter(base_url='https://www2.census.gov/topics/genealogy/2010surnames')

    def download_name_list(self):
        data = self.rest.get('/names.zip')
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            with z.open('Names_2010Census.csv') as csvfile:
                df = pd.read_csv(csvfile)
                names = df['name']
                names.to_csv(DATA_DIRECTORY / 'census_names.txt', index=False, header=False)