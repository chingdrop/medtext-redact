import importlib.util
import io
import json
import sys
import zipfile
from pathlib import Path

import pytest

TOOLS_DIR = Path(__file__).resolve().parents[2] / "tools"
_spec = importlib.util.spec_from_file_location("build_surname_list", TOOLS_DIR / "build_surname_list.py")
build = importlib.util.module_from_spec(_spec)
sys.modules["build_surname_list"] = build
_spec.loader.exec_module(build)

# The census CSV's real header, with made-up rows.
CENSUS_HEADER = "name,rank,count,prop100k,cum_prop100k,pctwhite,pctblack,pctapi,pctaian,pct2prace,pcthispanic"


def make_names_zip(path: Path, names: list[str]) -> Path:
    rows = [f"{name},{rank},100,0.1,0.1,(S),(S),(S),(S),(S),(S)" for rank, name in enumerate(names, start=1)]
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("Names_2010Census.csv", "\n".join([CENSUS_HEADER, *rows]) + "\n")
    return path


class TestSurnamesFromZip:
    def test_reads_name_column_in_rank_order(self, tmp_path):
        archive = make_names_zip(tmp_path / "names.zip", ["SMITH", "JOHNSON", "ALL OTHER NAMES"])
        assert build.surnames_from_zip(archive) == ["SMITH", "JOHNSON", "ALL OTHER NAMES"]


def fake_urlopen(body: bytes):
    """Stands in for urllib.request.urlopen, the API's only network boundary."""
    return lambda url, timeout: io.BytesIO(body)


class TestSurnamesFromApi:
    def test_sorts_by_rank_and_returns_names(self, monkeypatch):
        payload = [["NAME", "RANK"], ["JOHNSON", "2"], ["SMITH", "1"]]
        monkeypatch.setattr(build.urllib.request, "urlopen", fake_urlopen(json.dumps(payload).encode()))
        assert build.surnames_from_api("key") == ["SMITH", "JOHNSON"]

    def test_non_json_response_says_check_the_key(self, monkeypatch):
        monkeypatch.setattr(build.urllib.request, "urlopen", fake_urlopen(b"<html>Invalid Key</html>"))
        with pytest.raises(SystemExit, match="is the key valid"):
            build.surnames_from_api("bad")


class TestNormalize:
    def test_title_cases_and_drops_aggregate_blank_and_repeats(self):
        raw = ["SMITH", " JOHNSON ", "", "ALL OTHER NAMES", "smith", "O'BRIEN"]
        assert build.normalize(raw) == ["Smith", "Johnson", "O'Brien"]


class TestMain:
    def test_writes_one_surname_per_line(self, tmp_path, monkeypatch):
        names = [f"NAME{i}" for i in range(build._MIN_EXPECTED)]
        archive = make_names_zip(tmp_path / "names.zip", names)
        out = tmp_path / "out.txt"
        monkeypatch.setattr(sys, "argv", ["build", "--zip", str(archive), "--out", str(out)])

        build.main()

        lines = out.read_text(encoding="utf-8").splitlines()
        assert len(lines) == build._MIN_EXPECTED
        assert lines[:2] == ["Name0", "Name1"]

    def test_refuses_to_write_a_truncated_list(self, tmp_path, monkeypatch):
        archive = make_names_zip(tmp_path / "names.zip", ["SMITH", "JOHNSON"])
        out = tmp_path / "out.txt"
        monkeypatch.setattr(sys, "argv", ["build", "--zip", str(archive), "--out", str(out)])

        with pytest.raises(SystemExit, match="Only 2 surnames"):
            build.main()
        assert not out.exists()
