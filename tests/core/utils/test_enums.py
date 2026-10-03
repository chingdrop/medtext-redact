import pytest

from medtext_redact.core.utils import enums
from medtext_redact.core.utils.enums import (
    DICOM_2D_SERIES_DESCRIPTIONS,
    DICOM_3D_SERIES_DESCRIPTIONS,
    load_census_names,
)


class TestDicomSeriesDescriptions:
    def test_2d_descriptions_non_empty(self):
        assert DICOM_2D_SERIES_DESCRIPTIONS

    def test_3d_descriptions_non_empty(self):
        assert DICOM_3D_SERIES_DESCRIPTIONS

    def test_2d_and_3d_are_disjoint(self):
        assert DICOM_2D_SERIES_DESCRIPTIONS.isdisjoint(DICOM_3D_SERIES_DESCRIPTIONS)


class TestLoadCensusNames:
    @pytest.fixture()
    def surnames_file(self, tmp_path, monkeypatch):
        """Point the loader at a temporary list, clearing its per-process cache around the test."""
        path = tmp_path / "surnames.txt"
        monkeypatch.setattr(enums, "SURNAMES_RESOURCE", path)
        load_census_names.cache_clear()
        yield path
        load_census_names.cache_clear()

    def test_reads_one_surname_per_line(self, surnames_file):
        surnames_file.write_text("Smith\nJohnson\n", encoding="utf-8")
        assert load_census_names() == ("Smith", "Johnson")

    def test_skips_blank_lines(self, surnames_file):
        surnames_file.write_text("Smith\n\nJohnson\n\n", encoding="utf-8")
        assert load_census_names() == ("Smith", "Johnson")

    def test_reads_the_file_once_per_process(self, surnames_file):
        surnames_file.write_text("Smith\n", encoding="utf-8")
        first = load_census_names()
        surnames_file.write_text("Changed\n", encoding="utf-8")
        assert load_census_names() is first

    def test_missing_file_explains_how_to_rebuild(self, surnames_file):
        with pytest.raises(FileNotFoundError, match="tools/build_surname_list.py"):
            load_census_names()


class TestBundledSurnameList:
    """The real list must ship with the package: a .gitignore rule once hid it from git and the wheel."""

    def test_is_present_complete_and_in_rank_order(self):
        load_census_names.cache_clear()
        try:
            names = load_census_names()
        finally:
            load_census_names.cache_clear()
        assert len(names) == 162_253
        assert names[:3] == ("Smith", "Johnson", "Williams")
        assert len(set(names)) == len(names)
