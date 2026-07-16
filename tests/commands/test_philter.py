import shutil
import sys
from pathlib import Path

import pandas as pd
from click.testing import CliRunner

from vega_tools.commands import philter as philter_module
from vega_tools.commands.philter import philter

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def make_fake_philter_ucsf_dir(tmp_path, stub_name="fake_philter_main.py"):
    ucsf_dir = tmp_path / "philter-ucsf"
    (ucsf_dir / "configs").mkdir(parents=True)
    (ucsf_dir / "configs" / "philter_delta.json").write_text("{}", encoding="utf-8")
    shutil.copy(FIXTURES_DIR / stub_name, ucsf_dir / "main.py")
    return ucsf_dir


class TestPhilterCommand:
    def test_full_pipeline_with_stub_philter(self, tmp_path, monkeypatch):
        monkeypatch.setattr(philter_module, "PHILTER_UCSF_DIR", make_fake_philter_ucsf_dir(tmp_path))

        sample_path = tmp_path / "sample.csv"
        pd.DataFrame({
            "Accession": ["ACC001", "ACC002"],
            "Reports": ["First report text", "Second report text"],
        }).to_csv(sample_path, index=False)
        result_path = tmp_path / "result.csv"

        runner = CliRunner()
        outcome = runner.invoke(philter, [
            "--sample", str(sample_path),
            "--result", str(result_path),
            "--python", sys.executable,
        ])

        assert outcome.exit_code == 0, outcome.output
        result_df = pd.read_csv(result_path).sort_values("Filename").reset_index(drop=True)
        assert list(result_df["Filename"]) == ["ACC001", "ACC002"]
        assert list(result_df["Contents"]) == ["First report text", "Second report text"]

    def test_python_interpreter_not_found(self, tmp_path, monkeypatch):
        monkeypatch.setattr(philter_module, "PHILTER_UCSF_DIR", make_fake_philter_ucsf_dir(tmp_path))

        sample_path = tmp_path / "sample.csv"
        pd.DataFrame({"Accession": ["A1"], "Reports": ["text"]}).to_csv(sample_path, index=False)
        result_path = tmp_path / "result.csv"

        runner = CliRunner()
        outcome = runner.invoke(philter, [
            "--sample", str(sample_path),
            "--result", str(result_path),
            "--python", "/nonexistent/python-does-not-exist",
        ])

        assert outcome.exit_code == 1
        assert "is not installed or not on PATH" in outcome.output
        assert not result_path.exists()

    def test_subprocess_failure_preserves_intermediate_files(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            philter_module, "PHILTER_UCSF_DIR",
            make_fake_philter_ucsf_dir(tmp_path, stub_name="fake_philter_main_failing.py"),
        )

        sample_path = tmp_path / "sample.csv"
        pd.DataFrame({"Accession": ["A1"], "Reports": ["text"]}).to_csv(sample_path, index=False)
        result_path = tmp_path / "result.csv"

        runner = CliRunner()
        outcome = runner.invoke(philter, [
            "--sample", str(sample_path),
            "--result", str(result_path),
            "--python", sys.executable,
        ])

        assert outcome.exit_code != 0
        assert "intermediate files left at" in outcome.output
        assert not result_path.exists()

        # Extract the preserved tmp dir path from the log line and confirm
        # it (and the split input file) really was left in place, then
        # clean it up since the command intentionally didn't.
        marker = "intermediate files left at "
        line = next(line for line in outcome.output.splitlines() if marker in line)
        tmp_dir = Path(line.split(marker, 1)[1].strip())
        assert tmp_dir.exists()
        assert (tmp_dir / "input" / "A1.txt").exists()
        shutil.rmtree(tmp_dir, ignore_errors=True)
