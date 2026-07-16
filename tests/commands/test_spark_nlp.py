import subprocess
from unittest.mock import MagicMock

from click.testing import CliRunner

from vega_tools.commands import spark_nlp as spark_nlp_module
from vega_tools.commands.spark_nlp import spark_nlp


class TestSparkNlpCommand:
    def test_default_args_run_up_build(self, monkeypatch):
        mock_run = MagicMock(return_value=MagicMock(returncode=0))
        monkeypatch.setattr(spark_nlp_module.subprocess, "run", mock_run)

        runner = CliRunner()
        outcome = runner.invoke(spark_nlp, [])

        assert outcome.exit_code == 0, outcome.output
        mock_run.assert_called_once_with(
            ["docker", "compose", "up", "--build"],
            cwd=spark_nlp_module.SPARK_NLP_DIR,
            check=True,
        )

    def test_passthrough_args_replace_default(self, monkeypatch):
        mock_run = MagicMock(return_value=MagicMock(returncode=0))
        monkeypatch.setattr(spark_nlp_module.subprocess, "run", mock_run)

        runner = CliRunner()
        outcome = runner.invoke(spark_nlp, ["down"])

        assert outcome.exit_code == 0, outcome.output
        mock_run.assert_called_once_with(
            ["docker", "compose", "down"],
            cwd=spark_nlp_module.SPARK_NLP_DIR,
            check=True,
        )

    def test_multiple_passthrough_args(self, monkeypatch):
        mock_run = MagicMock(return_value=MagicMock(returncode=0))
        monkeypatch.setattr(spark_nlp_module.subprocess, "run", mock_run)

        runner = CliRunner()
        outcome = runner.invoke(spark_nlp, ["logs", "-f"])

        assert outcome.exit_code == 0, outcome.output
        mock_run.assert_called_once_with(
            ["docker", "compose", "logs", "-f"],
            cwd=spark_nlp_module.SPARK_NLP_DIR,
            check=True,
        )

    def test_docker_not_installed(self, monkeypatch):
        monkeypatch.setattr(
            spark_nlp_module.subprocess, "run",
            MagicMock(side_effect=FileNotFoundError()),
        )

        runner = CliRunner()
        outcome = runner.invoke(spark_nlp, [])

        assert outcome.exit_code == 1
        assert "docker is not installed" in outcome.output

    def test_called_process_error_propagates_exit_code(self, monkeypatch):
        monkeypatch.setattr(
            spark_nlp_module.subprocess, "run",
            MagicMock(side_effect=subprocess.CalledProcessError(returncode=5, cmd=["docker"])),
        )

        runner = CliRunner()
        outcome = runner.invoke(spark_nlp, [])

        assert outcome.exit_code == 5
