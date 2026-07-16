from unittest.mock import MagicMock

from click.testing import CliRunner

import vega_tools.cli as cli_module
from vega_tools.cli import cli, main


class TestCliGroup:
    def test_help_lists_all_commands(self):
        runner = CliRunner()
        outcome = runner.invoke(cli, ["--help"])
        assert outcome.exit_code == 0
        for name in [
            "audit-series-by-study",
            "compare-projects",
            "parse-report",
            "philter",
            "spark-nlp",
            "validate-studies",
        ]:
            assert name in outcome.output

    def test_each_command_dispatches_via_group(self):
        runner = CliRunner()
        for name in [
            "audit-series-by-study",
            "compare-projects",
            "parse-report",
            "philter",
            "spark-nlp",
            "validate-studies",
        ]:
            outcome = runner.invoke(cli, [name, "--help"])
            assert outcome.exit_code == 0, f"{name}: {outcome.output}"

    def test_unknown_command_fails(self):
        runner = CliRunner()
        outcome = runner.invoke(cli, ["not-a-real-command"])
        assert outcome.exit_code != 0


class TestMain:
    def test_creates_data_directory_before_running_cli(self, monkeypatch):
        mock_create_directory = MagicMock()
        mock_cli = MagicMock()
        monkeypatch.setattr(cli_module, "create_directory", mock_create_directory)
        monkeypatch.setattr(cli_module, "cli", mock_cli)

        main()

        mock_create_directory.assert_called_once_with(cli_module.DATA_DIRECTORY)
        mock_cli.assert_called_once()
