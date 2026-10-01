import io
import logging
import zipfile
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import pandas as pd

from medtext_redact.paths import DATA_DIRECTORY
from medtext_redact.vendor.rest_adapter import RestAdapter, RestAdapterConfig


class CensusDownloadError(RuntimeError):
    """The census surname list couldn't be downloaded or read."""


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
    # No leading slash: RestAdapter.request() joins this against base_url with
    # urljoin(), and a leading "/" makes urljoin treat it as domain-absolute,
    # discarding base_url's own path (https://www2.census.gov/names.zip --
    # always 404s -- instead of .../2010surnames/names.zip).
    ZIP_ENDPOINT = "names.zip"
    # Every zip archive starts with this local-file-header signature.
    _ZIP_MAGIC = b"PK\x03\x04"

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
            # Trailing slash required: RestAdapter.request() joins ZIP_ENDPOINT
            # against this with urljoin(), which treats a base URL with no
            # trailing slash as ending in a "file" to be replaced rather than
            # a directory to append to.
            base_url = (
                "https://www2.census.gov/topics/genealogy/2000surnames/"
                if year == "2000"
                else "https://www2.census.gov/topics/genealogy/2010surnames/"
            )
            config = adapter_config or {}
            rest_config = RestAdapterConfig(base_url=base_url, **config)
            self._rest = RestAdapter(rest_config)

        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @property
    def zip_url(self) -> str:
        """The full URL of the names archive, for error messages."""
        config = getattr(self._rest, "config", None)
        return urljoin(config.base_url, self.ZIP_ENDPOINT) if config else self.ZIP_ENDPOINT

    def _manual_install_hint(self) -> str:
        return (
            f"To work around it, download {self.zip_url} in a web browser, open the CSV inside, "
            f"and save the surnames from its first column (without the header row), one per line, "
            f"to {self.save_file}. Redaction will use that file instead of downloading."
        )

    def download_names(self) -> pd.DataFrame:
        """
        Fetches the census name ZIP, extracts the first CSV found, and returns a DataFrame.

        Returns:
            pd.DataFrame: DataFrame of the census names data.

        Raises:
            CensusDownloadError: If the download fails, isn't a zip archive, or has no readable CSV.
        """
        try:
            self.logger.info(f"Downloading census names ZIP for year {self.year}")
            raw = self._rest.get(self.ZIP_ENDPOINT)
            if isinstance(raw, dict):
                raise RuntimeError(f"Expected a binary ZIP response, got a JSON object: {raw!r}")
            payload = raw if isinstance(raw, (bytes, bytearray)) else raw.encode()
        except Exception as e:
            self.logger.error("Failed to download ZIP", exc_info=e)
            raise CensusDownloadError(
                f"Could not retrieve the census names archive from {self.zip_url} ({e}). {self._manual_install_hint()}"
            ) from e

        # census.gov's firewall sometimes answers automated requests with a
        # 200 OK "Request Rejected" HTML page instead of the archive. Say so,
        # rather than failing later with a confusing "not a zip file".
        if not payload.startswith(self._ZIP_MAGIC):
            excerpt = payload[:200].decode("utf-8", errors="replace")
            raise CensusDownloadError(
                f"The census names download from {self.zip_url} did not return a zip archive; "
                f"the server may have rejected the automated request. Response began: {excerpt!r}\n"
                f"{self._manual_install_hint()}"
            )
        zip_buf = io.BytesIO(payload)

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
            raise CensusDownloadError(
                f"Could not extract the census names CSV from {self.zip_url} ({e}). {self._manual_install_hint()}"
            ) from e

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
