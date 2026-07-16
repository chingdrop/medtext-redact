import io
import logging
import zipfile
from pathlib import Path
from typing import Any

import pandas as pd

from vega_tools.core.utils.rest_utils import RestAdapter, RestAdapterConfig
from vega_tools.paths import DATA_DIRECTORY


class CensusNamesApi:
    """
    API client for downloading and saving US Census surnames.

    Usage:
        api = CensusNamesApi(year="2010")
        df = api.download_names()
        path = api.save_to_file(df)
        # or
        path = api.download_and_save()

    Args:
        year: Must be '2000' or '2010'.
        save_file: Path where the names list will be written (defaults to DATA_DIRECTORY / 'census_{year}_names.txt').
        rest_adapter: Optional RestAdapter instance; if None one will be created.
    """

    VALID_YEARS = {"2000", "2010"}
    ZIP_ENDPOINT = "/names.zip"

    def __init__(
        self,
        year: str,
        save_file: Path | str | None = None,
        rest_adapter: RestAdapter | None = None,
        adapter_config: dict[str, Any] | None = None,
    ):
        if year not in self.VALID_YEARS:
            raise ValueError(f"Year must be one of {sorted(self.VALID_YEARS)}, got '{year}'")
        self.year = year

        # Determine where to save the output
        default_name = f"census_{year}_names.txt"
        if save_file is None:
            self.save_file = DATA_DIRECTORY / default_name
        else:
            self.save_file = Path(save_file)

        # Prepare RestAdapter
        if rest_adapter is not None:
            self._rest = rest_adapter
        else:
            base_url = (
                "https://www2.census.gov/topics/genealogy/2000surnames"
                if year == "2000"
                else "https://www2.census.gov/topics/genealogy/2010surnames"
            )
            config = adapter_config or {}
            rest_config = RestAdapterConfig(base_url=base_url, **config)
            self._rest = RestAdapter(rest_config)

        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def download_names(self) -> pd.DataFrame:
        """
        Fetches the census name ZIP, extracts the first CSV found, and returns a DataFrame.

        Returns:
            pd.DataFrame: DataFrame of the census names data.

        Raises:
            RuntimeError: If download or extraction fails.
        """
        try:
            self.logger.info(f"Downloading census names ZIP for year {self.year}")
            raw = self._rest.get(self.ZIP_ENDPOINT)
            zip_buf = io.BytesIO(raw if isinstance(raw, (bytes, bytearray)) else raw.encode())
        except Exception as e:
            self.logger.error("Failed to download ZIP", exc_info=e)
            raise RuntimeError("Could not retrieve census names archive") from e

        try:
            with zipfile.ZipFile(zip_buf) as z:
                # pick the first CSV file in the archive
                csv_files = [f for f in z.namelist() if f.lower().endswith(".csv")]
                if not csv_files:
                    raise KeyError("No CSV file found in the ZIP archive")
                filename = csv_files[0]
                self.logger.debug(f"Extracting '{filename}' from ZIP")
                with z.open(filename) as csvfile:
                    df = pd.read_csv(csvfile)
        except Exception as e:
            self.logger.error("Failed to extract or parse CSV", exc_info=e)
            raise RuntimeError("Could not extract census names CSV") from e

        return df

    def save_to_file(self, df: pd.DataFrame) -> Path:
        """
        Saves the first-column values from df to self.save_file, one name per line.

        Returns:
            Path: Path to the written file.
        """
        names = df.iloc[:, 0].astype(str)
        # Ensure parent directory exists
        self.save_file.parent.mkdir(parents=True, exist_ok=True)
        names.to_csv(self.save_file, index=False, header=False)
        self.logger.info(f"Wrote {len(names)} names to {self.save_file}")
        return self.save_file

    def download_and_save(self) -> Path:
        """
        Convenience method: download the names DataFrame and save it.

        Returns:
            Path: Path to the written file.
        """
        df = self.download_names()
        return self.save_to_file(df)
