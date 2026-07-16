from pathlib import Path

from vega_tools.paths import DATA_DIRECTORY, PROJECT_DIRECTORY


def test_project_directory_is_repo_root():
    assert (PROJECT_DIRECTORY / "pyproject.toml").is_file()
    assert (PROJECT_DIRECTORY / "src" / "vega_tools").is_dir()


def test_data_directory_is_under_project_directory():
    assert DATA_DIRECTORY == PROJECT_DIRECTORY / "data"


def test_both_are_absolute_paths():
    assert Path(PROJECT_DIRECTORY).is_absolute()
    assert Path(DATA_DIRECTORY).is_absolute()
