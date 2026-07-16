import pandas as pd
from click.testing import CliRunner

from vega_tools.commands import studies
from vega_tools.commands.studies import audit_series_by_study, compare_projects, validate_studies


class TestValidateStudies:
    def test_writes_matched_and_grouped_results(self, tmp_path, monkeypatch):
        monkeypatch.setattr(studies, "DATA_DIRECTORY", tmp_path)

        pd.DataFrame({
            "project_1": ["vega-100"],
            "project_2": ["vega-200"],
            "accession_1": ["ACC1"],
            "accession_2": ["ACC2"],
            "study_instance_uid": ["UID1"],
        }).to_excel(tmp_path / "dupe_audit.xlsx", index=False, engine="openpyxl")

        sample_path = tmp_path / "sample.csv"
        pd.DataFrame({
            "PriorStudyAccession": ["ACC1"],
            "GroupName": ["TestGroup"],
        }).to_csv(sample_path, index=False)

        result_path = tmp_path / "result.csv"
        runner = CliRunner()
        outcome = runner.invoke(validate_studies, [
            "--project", "vega-100",
            "--sample", str(sample_path),
            "--result", str(result_path),
            "--order", "first",
        ])

        assert outcome.exit_code == 0, outcome.output
        result_df = pd.read_csv(result_path)
        row = result_df.iloc[0]
        assert row["study_instance_uid"] == "UID1"
        assert row["accession"] == "ACC1"
        assert row["matched_col"] == "PriorStudyAccession"
        assert row["failure"] == False  # noqa: E712
        assert row["type"] == "Prior"
        assert row["GroupName"] == "TestGroup"

    def test_failure_when_accession_not_found_anywhere(self, tmp_path, monkeypatch):
        monkeypatch.setattr(studies, "DATA_DIRECTORY", tmp_path)

        pd.DataFrame({
            "project_1": ["vega-100"],
            "project_2": ["vega-200"],
            "accession_1": ["ACC1"],
            "accession_2": ["ACC2"],
            "study_instance_uid": ["UID1"],
        }).to_excel(tmp_path / "dupe_audit.xlsx", index=False, engine="openpyxl")

        sample_path = tmp_path / "sample.csv"
        pd.DataFrame({"SomeColumn": ["nothing-relevant"]}).to_csv(sample_path, index=False)

        result_path = tmp_path / "result.csv"
        runner = CliRunner()
        outcome = runner.invoke(validate_studies, [
            "--project", "vega-100",
            "--sample", str(sample_path),
            "--result", str(result_path),
            "--order", "first",
        ])

        assert outcome.exit_code == 0, outcome.output
        result_df = pd.read_csv(result_path)
        assert pd.isna(result_df.iloc[0]["matched_col"])


class TestCompareProjects:
    def test_orders_projects_and_writes_result(self, tmp_path):
        sample_path = tmp_path / "sample.csv"
        pd.DataFrame({
            "file_1": ["vega-200"],
            "file_2": ["vega-100"],
            "file_1_accession": ["ACC2"],
            "file_2_accession": ["ACC1"],
            "study_instance_uid": ["UID1"],
        }).to_csv(sample_path, index=False)
        result_path = tmp_path / "result.csv"

        runner = CliRunner()
        outcome = runner.invoke(compare_projects, [
            "--sample", str(sample_path),
            "--result", str(result_path),
        ])

        assert outcome.exit_code == 0, outcome.output
        result_df = pd.read_csv(result_path)
        assert result_df.iloc[0]["project_1"] == "vega-100"
        assert result_df.iloc[0]["project_2"] == "vega-200"


class TestAuditSeriesByStudy:
    def test_writes_2d_and_3d_audit_rows(self, tmp_path):
        sample_path = tmp_path / "sample.csv"
        pd.DataFrame({
            "File": ["f1", "f2"],
            "0008:0050": ["ACC1", "ACC1"],
            "0010:0020": ["PID1", "PID1"],
            "0008:0018": ["SOP1", "SOP2"],
            "0008:0008": ["", ""],
            "0028:0008": [1, 3],
            "0020:0062": ["", ""],
            "5200:9229.#0.0020:9071.#0.0020:9072": ["", ""],
            "5200:9229.#0.0028:9110.#0.0018:0050": [0, 1],
            "0054:0220.#0.0008:0100": ["", ""],
            "0054:0220.#0.0054:0222.#0.0008:0100": ["", ""],
            "0008:0070": ["", ""],
            "0008:1090": ["", ""],
            "0008:103E": ["V-Preview RCC", "ROUTINE3D_VOL_RCC"],
            "0008:1030": ["", ""],
            "0002:0010": ["", ""],
        }).to_csv(sample_path, index=False)
        result_path = tmp_path / "result.csv"

        runner = CliRunner()
        outcome = runner.invoke(audit_series_by_study, [
            "--sample", str(sample_path),
            "--result", str(result_path),
        ])

        assert outcome.exit_code == 0, outcome.output
        result_df = pd.read_csv(result_path)
        assert set(result_df["Image Type"]) == {"2D", "3D"}
        assert (result_df["Accession"] == "ACC1").all()
