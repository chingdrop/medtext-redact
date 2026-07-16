from vega_tools.core.utils import enums
from vega_tools.core.utils.enums import DICOM_2D_SERIES_DESCRIPTIONS, DICOM_3D_SERIES_DESCRIPTIONS, load_census_names


class TestDicomSeriesDescriptions:
    def test_2d_descriptions_non_empty(self):
        assert DICOM_2D_SERIES_DESCRIPTIONS

    def test_3d_descriptions_non_empty(self):
        assert DICOM_3D_SERIES_DESCRIPTIONS

    def test_2d_and_3d_are_disjoint(self):
        assert DICOM_2D_SERIES_DESCRIPTIONS.isdisjoint(DICOM_3D_SERIES_DESCRIPTIONS)


class FakeCensusNamesApi:
    """Stands in for CensusNamesApi(year=...), matching its real call signature."""

    def __init__(self, save_file, seed_content=None):
        self.save_file = save_file
        self.downloaded = False
        if seed_content is not None:
            self.save_file.parent.mkdir(parents=True, exist_ok=True)
            self.save_file.write_text(seed_content, encoding="utf-8")

    def download_and_save(self):
        self.downloaded = True
        self.save_file.parent.mkdir(parents=True, exist_ok=True)
        self.save_file.write_text("Smith\nJones\n", encoding="utf-8")


class TestLoadCensusNames:
    def test_downloads_when_file_missing(self, tmp_path, monkeypatch):
        target = tmp_path / "census.txt"
        api_instance = FakeCensusNamesApi(target)
        monkeypatch.setattr(enums, "CensusNamesApi", lambda year: api_instance)

        names = load_census_names(year="2010")

        assert names == ["Smith", "Jones"]
        assert api_instance.downloaded is True

    def test_skips_download_when_file_already_exists(self, tmp_path, monkeypatch):
        target = tmp_path / "census.txt"
        api_instance = FakeCensusNamesApi(target, seed_content="Existing\n")
        monkeypatch.setattr(enums, "CensusNamesApi", lambda year: api_instance)

        names = load_census_names(year="2010")

        assert names == ["Existing"]
        assert api_instance.downloaded is False

    def test_titlecases_names(self, tmp_path, monkeypatch):
        target = tmp_path / "census.txt"
        api_instance = FakeCensusNamesApi(target, seed_content="SMITH\njones\n")
        monkeypatch.setattr(enums, "CensusNamesApi", lambda year: api_instance)

        names = load_census_names(year="2010")

        assert names == ["Smith", "Jones"]
