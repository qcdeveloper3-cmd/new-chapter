from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path


def discover_skills(skills_root: Path) -> list[Path]:
    if not skills_root.exists():
        return []
    return [
        path
        for path in sorted(skills_root.iterdir())
        if path.is_dir() and (path / "SKILL.md").exists()
    ]


def install_skill(source: Path, destination_root: Path, force: bool) -> tuple[str, str]:
    target = destination_root / source.name
    if target.exists():
        if not force:
            return source.name, "skipped (already exists)"
        shutil.rmtree(target)

    shutil.copytree(source, target)
    return source.name, "installed"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Install repository-scoped Codex skills into ~/.codex/skills."
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing installed skills.")
    parser.add_argument(
        "--dest",
        type=Path,
        default=None,
        help="Optional destination root (defaults to $CODEX_HOME/skills or ~/.codex/skills).",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    source_root = repo_root / ".codex" / "skills"

    codex_home = Path.home() / ".codex"
    env_codex_home = os.environ.get("CODEX_HOME")
    destination_root = args.dest or (
        Path(env_codex_home) / "skills" if env_codex_home else codex_home / "skills"
    )
    destination_root.mkdir(parents=True, exist_ok=True)

    skills = discover_skills(source_root)
    if not skills:
        print(f"No repository skills found in: {source_root}")
        return

    print(f"Installing {len(skills)} skill(s) into: {destination_root}")
    for skill in skills:
        name, status = install_skill(skill, destination_root, args.force)
        print(f"- {name}: {status}")


if __name__ == "__main__":
    main()
