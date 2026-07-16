import json

import pandas as pd
import pytest
from click.testing import CliRunner

from vega_tools.commands.reports import parse_report
from vega_tools.core import text_tools


@pytest.fixture(autouse=True)
def fake_census_names(monkeypatch):
    """sanitize_names() would otherwise hit the real census network API."""
    monkeypatch.setattr(text_tools, "load_census_names", lambda: ["Smith"])


@pytest.fixture()
def config_path(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps(
            {
                "Masking": {"Manufacturers": [], "Locations": []},
                "Searching": {"AnatomicalTags": ["left", "right"], "PathologyKeywords": ["carcinoma"]},
            }
        ),
        encoding="utf-8",
    )
    return path


class TestSingle:
    def test_masks_name_and_prints_matching_line(self, config_path):
        runner = CliRunner()
        outcome = runner.invoke(
            parse_report,
            ["--config", str(config_path), "single", "--keywords", "carcinoma"],
            input="Smith has left breast carcinoma",
        )
        assert outcome.exit_code == 0, outcome.output
        assert "Smith" not in outcome.output
        assert "carcinoma" in outcome.output

    def test_keywords_file_used_when_no_direct_keywords(self, tmp_path, config_path):
        keywords_file = tmp_path / "keywords.txt"
        keywords_file.write_text("carcinoma\n", encoding="utf-8")

        runner = CliRunner()
        outcome = runner.invoke(
            parse_report,
            ["--config", str(config_path), "single", "--keywords-file", str(keywords_file)],
            input="Smith has left breast carcinoma",
        )
        assert outcome.exit_code == 0, outcome.output
        assert "carcinoma" in outcome.output

    def test_explicit_text_flag_takes_priority_over_stdin(self, config_path):
        runner = CliRunner()
        outcome = runner.invoke(
            parse_report,
            ["--config", str(config_path), "single", "--text", "Smith has carcinoma", "--keywords", "carcinoma"],
        )
        assert outcome.exit_code == 0, outcome.output
        assert "Smith" not in outcome.output
        assert "carcinoma" in outcome.output


class TestSpreadsheet:
    def test_output_keeps_sanitized_text_and_search_columns(self, tmp_path, config_path):
        sample_path = tmp_path / "sample.csv"
        pd.DataFrame(
            {
                "Accession": ["A1"],
                "ReportText": ["Smith has left breast carcinoma, benign result"],
            }
        ).to_csv(sample_path, index=False)
        result_path = tmp_path / "result.csv"

        runner = CliRunner()
        outcome = runner.invoke(
            parse_report,
            [
                "--config",
                str(config_path),
                "spreadsheet",
                "--sample",
                str(sample_path),
                "--result",
                str(result_path),
            ],
        )

        assert outcome.exit_code == 0, outcome.output
        result_df = pd.read_csv(result_path)
        row = result_df.iloc[0]
        # Regression check: sanitization must not be discarded by the
        # search_report_text step that runs afterward.
        assert "Smith" not in row["ReportText"]
        assert row["FoundBiopsySide"] == "left"
        assert row["FoundBiopsyResult"] == "benign"
        assert row["FoundPathologyType"] == "carcinoma"

    def test_none_placeholder_replaced(self, tmp_path, config_path):
        sample_path = tmp_path / "sample.csv"
        pd.DataFrame(
            {
                "Accession": ["A1"],
                "ReportText": ["<NONE>"],
            }
        ).to_csv(sample_path, index=False)
        result_path = tmp_path / "result.csv"

        runner = CliRunner()
        outcome = runner.invoke(
            parse_report,
            [
                "--config",
                str(config_path),
                "spreadsheet",
                "--sample",
                str(sample_path),
                "--result",
                str(result_path),
            ],
        )

        assert outcome.exit_code == 0, outcome.output
        result_df = pd.read_csv(result_path)
        assert pd.isna(result_df.iloc[0]["ReportText"])

    def test_unreadable_sample_exits_with_error_instead_of_crashing(self, tmp_path, config_path):
        sample_path = tmp_path / "sample.parquet"
        sample_path.write_text("not a real parquet file", encoding="utf-8")
        result_path = tmp_path / "result.csv"

        runner = CliRunner()
        outcome = runner.invoke(
            parse_report,
            [
                "--config",
                str(config_path),
                "spreadsheet",
                "--sample",
                str(sample_path),
                "--result",
                str(result_path),
            ],
        )

        assert outcome.exit_code == 1
        assert "Could not read sample spreadsheet" in outcome.output
        assert not result_path.exists()
