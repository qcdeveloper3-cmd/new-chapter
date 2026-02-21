# DocMirror CLI Scaffold

Scaffold for a Python CLI that converts a structured JPG/JPEG document image into a mirrored editable DOCX.

Status: architecture-first skeleton with stage wiring, IR schema, config, logging, and tests. Core extraction and high-fidelity rendering are marked with `TODO`.

## Goals

- Mirror the source form visually as closely as possible in DOCX print output.
- Keep generated output editable (text, tables, checkboxes, symbols/images where possible).
- Support RTL Persian and mixed RTL/LTR content.
- Use Docling as the primary analysis engine with fallback helpers (OpenCV/OCR/OOXML logic).

## Project Layout

```text
.
├── artifacts/
│   ├── debug/
│   └── logs/
├── config/
│   └── default.yaml
├── fixtures/
│   └── sample_forms/
├── src/
│   └── docmirror/
│       ├── adapters/
│       ├── ir/
│       ├── stages/
│       ├── storage/
│       ├── __main__.py
│       ├── cli.py
│       ├── config.py
│       ├── context.py
│       ├── interfaces.py
│       └── logging_utils.py
├── tests/
│   ├── fixtures/
│   └── test_cli.py
└── pyproject.toml
```

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
```

Optional extras:

```bash
pip install -e .[analysis,fallback]
```

## Bootstrap (Recommended)

Windows:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap_dev.ps1 -InstallOptionalEngines -ForceSkillOverwrite -InstallVSCodeExtensions
```

Linux/macOS:

```bash
INSTALL_OPTIONAL_ENGINES=1 FORCE_SKILL_OVERWRITE=1 bash scripts/bootstrap_dev.sh
```

What bootstrap does:

- Creates `.venv` if missing.
- Installs package and dev dependencies.
- Optionally installs analysis/fallback engines.
- Installs pre-commit hooks.
- Installs repo-bundled Codex skills into `~/.codex/skills`.

## CLI Usage

Default config file: `config/default.yaml` (if present).

```bash
docmirror --help
docmirror preprocess path\to\form.jpg -o out
docmirror analyze path\to\form.jpg -o out
docmirror render-docx out\20260221T000000Z.ir.json -o out
docmirror validate path\to\form.jpg out\20260221T000000Z.docx -o out
docmirror run-all path\to\form.jpg -o out
```

## Engineering Workflow

- Lint: `.\.venv\Scripts\python -m ruff check src tests`
- Format check: `.\.venv\Scripts\python -m ruff format --check src tests`
- Type check: `.\.venv\Scripts\python -m mypy src`
- Tests: `.\.venv\Scripts\python -m pytest`
- CLI smoke: `.\.venv\Scripts\python -m docmirror --help`
- One-command gate: `.\.venv\Scripts\python .codex\skills\project-docling-engineer\scripts\run_quality_gate.py`

## VS Code + GitHub Integration

- VS Code workspace settings: `.vscode/settings.json`
- Recommended extensions: `.vscode/extensions.json`
- Dev tasks: `.vscode/tasks.json`
- Debug launch configs: `.vscode/launch.json`
- Dev Container: `.devcontainer/devcontainer.json`
- GitHub CI: `.github/workflows/ci.yml`
- Pre-commit hooks: `.pre-commit-config.yaml`
- Codex project skill: `.codex/skills/project-docling-engineer/SKILL.md`

## Stage Responsibilities

- `preprocess`: image cleanup pipeline boundary (deskew/denoise/perspective correction).
- `analyze`: Docling-first analysis and fallback extraction into IR.
- `render-docx`: IR to editable DOCX generation.
- `validate`: structural and visual checks between source image and DOCX.
- `run-all`: orchestrates all stages in sequence.

## Notes

- The IR models are in `src/docmirror/ir/models.py`.
- Logging writes to `artifacts/logs` and debug artifacts to `artifacts/debug` under the selected output directory.
- Implementation-heavy parts are intentionally deferred and marked with `TODO`.
- Tooling and implementation guidance from web research is documented in `docs/tooling-research-notes.md`.
- Cross-machine setup is documented in `docs/multi-machine-setup.md`.
