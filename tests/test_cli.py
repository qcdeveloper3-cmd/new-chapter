from typer.testing import CliRunner

from docmirror.cli import app

runner = CliRunner()


def test_cli_help_lists_required_subcommands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "preprocess" in result.stdout
    assert "analyze" in result.stdout
    assert "render-docx" in result.stdout
    assert "validate" in result.stdout
    assert "run-all" in result.stdout
