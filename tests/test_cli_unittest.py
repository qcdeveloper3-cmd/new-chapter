import unittest

from typer.testing import CliRunner

from docmirror.cli import app


class TestCLIHelp(unittest.TestCase):
    def test_cli_help_lists_required_subcommands(self) -> None:
        result = CliRunner().invoke(app, ["--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("preprocess", result.stdout)
        self.assertIn("analyze", result.stdout)
        self.assertIn("render-docx", result.stdout)
        self.assertIn("validate", result.stdout)
        self.assertIn("run-all", result.stdout)


if __name__ == "__main__":
    unittest.main()
