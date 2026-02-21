from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def run(cmd: list[str], cwd: Path) -> None:
    print(f"\n$ {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run standard project quality checks.")
    parser.add_argument("--skip-mypy", action="store_true", help="Skip mypy.")
    parser.add_argument("--skip-pytest", action="store_true", help="Skip pytest.")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[4]
    python = repo_root / ".venv" / "Scripts" / "python.exe"
    if not python.exists():
        python = repo_root / ".venv" / "bin" / "python"

    if not python.exists():
        raise SystemExit("Virtual environment not found at .venv. Run bootstrap first.")

    run([str(python), "-m", "ruff", "check", "src", "tests"], cwd=repo_root)
    run([str(python), "-m", "ruff", "format", "--check", "src", "tests"], cwd=repo_root)

    if not args.skip_mypy:
        run([str(python), "-m", "mypy", "src"], cwd=repo_root)

    if not args.skip_pytest:
        run([str(python), "-m", "pytest"], cwd=repo_root)

    run([str(python), "-m", "unittest", "tests.test_cli_unittest", "-v"], cwd=repo_root)
    run([str(python), "-m", "docmirror", "--help"], cwd=repo_root)
    print("\nQuality gate passed.")


if __name__ == "__main__":
    main()
