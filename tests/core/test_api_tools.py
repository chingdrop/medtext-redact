import io
import zipfile

import pandas as pd
import pytest

from vega_tools.core.api_tools import CensusNamesApi


class FakeRestAdapter:
    def __init__(self, response):
        self.response = response
        self.requested_endpoint = None

    def get(self, endpoint):
        self.requested_endpoint = endpoint
        return self.response


def make_zip_with_csv(rows):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        csv_content = "name\n" + "\n".join(rows)
        zf.writestr("names.csv", csv_content)
    return buf.getvalue()


class TestInit:
    def test_rejects_invalid_year(self):
        with pytest.raises(ValueError):
            CensusNamesApi(year="1999")

    def test_accepts_valid_years(self):
        CensusNamesApi(year="2000", rest_adapter=FakeRestAdapter(b""))
        CensusNamesApi(year="2010", rest_adapter=FakeRestAdapter(b""))

    def test_default_save_file_under_data_directory(self):
        from vega_tools.paths import DATA_DIRECTORY

        api = CensusNamesApi(year="2010", rest_adapter=FakeRestAdapter(b""))
        assert api.save_file == DATA_DIRECTORY / "census_2010_names.txt"

    def test_custom_save_file_respected(self, tmp_path):
        target = tmp_path / "custom.txt"
        api = CensusNamesApi(year="2010", save_file=target, rest_adapter=FakeRestAdapter(b""))
        assert api.save_file == target


class TestDownloadNames:
    def test_extracts_csv_from_zip(self):
        zip_bytes = make_zip_with_csv(["Smith", "Jones"])
        api = CensusNamesApi(year="2010", rest_adapter=FakeRestAdapter(zip_bytes))
        df = api.download_names()
        assert list(df["name"]) == ["Smith", "Jones"]

    def test_requests_the_zip_endpoint(self):
        zip_bytes = make_zip_with_csv(["Smith"])
        fake_adapter = FakeRestAdapter(zip_bytes)
        api = CensusNamesApi(year="2010", rest_adapter=fake_adapter)
        api.download_names()
        assert fake_adapter.requested_endpoint == CensusNamesApi.ZIP_ENDPOINT

    def test_raises_runtime_error_when_zip_has_no_csv(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("readme.txt", "not a csv")
        api = CensusNamesApi(year="2010", rest_adapter=FakeRestAdapter(buf.getvalue()))
        with pytest.raises(RuntimeError):
            api.download_names()

    def test_raises_runtime_error_when_download_fails(self):
        class FailingAdapter:
            def get(self, endpoint):
                raise ConnectionError("network down")

        api = CensusNamesApi(year="2010", rest_adapter=FailingAdapter())
        with pytest.raises(RuntimeError):
            api.download_names()


class TestSaveToFile:
    def test_writes_first_column_one_per_line(self, tmp_path):
        target = tmp_path / "out.txt"
        api = CensusNamesApi(year="2010", save_file=target, rest_adapter=FakeRestAdapter(b""))
        df = pd.DataFrame({"name": ["Smith", "Jones"], "other": [1, 2]})

        result_path = api.save_to_file(df)

        assert result_path == target
        assert target.read_text().splitlines() == ["Smith", "Jones"]

    def test_creates_parent_directories(self, tmp_path):
        target = tmp_path / "nested" / "out.txt"
        api = CensusNamesApi(year="2010", save_file=target, rest_adapter=FakeRestAdapter(b""))
        api.save_to_file(pd.DataFrame({"name": ["Smith"]}))
        assert target.exists()


class TestDownloadAndSave:
    def test_downloads_then_saves(self, tmp_path):
        target = tmp_path / "out.txt"
        zip_bytes = make_zip_with_csv(["Smith", "Jones"])
        api = CensusNamesApi(year="2010", save_file=target, rest_adapter=FakeRestAdapter(zip_bytes))

        result_path = api.download_and_save()

        assert result_path == target
        assert target.read_text().splitlines() == ["Smith", "Jones"]
