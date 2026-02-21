# Multi-Machine Setup

Use this flow after cloning the repo on a new machine.

## Option A: Local host setup

Windows:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap_dev.ps1 -InstallOptionalEngines -InstallVSCodeExtensions -ForceSkillOverwrite
```

Linux/macOS:

```bash
INSTALL_OPTIONAL_ENGINES=1 FORCE_SKILL_OVERWRITE=1 bash scripts/bootstrap_dev.sh
```

## Option B: Dev Container setup

1. Open repo in VS Code.
2. Run: `Dev Containers: Reopen in Container`.
3. Wait for `postCreateCommand` to finish.

## Verification

```bash
python -m docmirror --help
python .codex/skills/project-docling-engineer/scripts/run_quality_gate.py
```
