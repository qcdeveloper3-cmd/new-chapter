# Tooling Research Notes (Feb 21, 2026)

This note captures what was reviewed and what was adopted in this repository setup.

## 1) Docling-first analysis strategy

Sources reviewed:

- Docling examples index: <https://docling-project.github.io/docling/examples/>
- Docling OCR + pipeline options examples: <https://docling-project.github.io/docling/examples/full_page_ocr/> and <https://docling-project.github.io/docling/examples/custom_convert/>
- Docling model/service catalog: <https://docling-project.github.io/docling/concepts/models/>

Key decisions applied:

- Keep Docling as the primary analyzer path.
- Keep fallback analyzers behind adapter boundaries.
- Preserve table/text direction metadata in IR for later DOCX rendering.

## 2) VS Code Python integration

Sources reviewed:

- Python settings reference: <https://code.visualstudio.com/docs/python/settings-reference>
- Python testing in VS Code: <https://code.visualstudio.com/docs/python/testing>
- Python linting in VS Code: <https://code.visualstudio.com/docs/python/linting>
- Python formatting in VS Code: <https://code.visualstudio.com/docs/python/formatting>
- Python Environments extension update: <https://devblogs.microsoft.com/python/python-in-visual-studio-code-october-2025-release/>

Key decisions applied:

- Added workspace Python interpreter, testing, and lint/format settings.
- Added extension recommendations for Python, Pylance, Ruff, Containers, and GitHub Actions.
- Added launch/tasks for fast local loops.

## 3) CI and portability

Sources reviewed:

- GitHub Action `setup-python` (version + pip cache): <https://github.com/actions/setup-python>
- Dev Container docs and overview: <https://code.visualstudio.com/docs/devcontainers/containers> and <https://containers.dev/>

Key decisions applied:

- Added GitHub workflow for lint/tests/CLI smoke.
- Added `.devcontainer` with OCR/system dependencies and post-create bootstrap.
- Added bootstrap scripts for Windows and Linux/macOS.

## 4) Local quality gates

Sources reviewed:

- pre-commit docs: <https://pre-commit.com/>
- Ruff docs: <https://docs.astral.sh/ruff/>

Key decisions applied:

- Added `.pre-commit-config.yaml`.
- Added Ruff and mypy configuration in `pyproject.toml`.
- Added reusable quality gate script in project skill resources.
