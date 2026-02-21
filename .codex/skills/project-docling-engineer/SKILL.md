---
name: project-docling-engineer
description: Engineer robust Python document-processing systems for this repository. Use when tasks involve Docling-first analysis, OCR/table fallback design, editable DOCX generation, RTL/LTR mixed text handling, project scaffolding, CI/tooling setup, or implementation planning and execution that must prioritize correctness, maintainability, and practical delivery.
---

# Project Docling Engineer

## Overview

Plan and implement production-grade changes for Python + Docling + DOCX workflows in this repo. Prioritize architecture clarity, testability, and staged delivery over quick but fragile code.

## Workflow

1. Confirm target outcomes and acceptance criteria before writing code.
2. Inspect current state first (`tree`, `rg`, config, tests, CI).
3. Propose minimal viable architecture changes with explicit tradeoffs.
4. Implement in thin vertical slices:
   - keep stage boundaries clean (`preprocess`, `analyze`, `render-docx`, `validate`)
   - use interfaces/adapters for engines and fallbacks
   - keep IR stable and version-aware
5. Add verification with every slice:
   - unit tests for pure logic and schema
   - CLI smoke tests for orchestration
   - artifact checks for deterministic outputs
6. Report residual risks and clear next steps.

## Implementation Rules

- Keep modules cohesive; avoid monolithic stage files.
- Preserve editability in DOCX output: prefer native paragraphs/tables/checkbox-like symbols before raster overlays.
- Preserve geometry explicitly in IR; avoid lossy implicit conversions.
- Treat mixed-direction text as first-class: store direction metadata on lines/spans/cells.
- Make fallback behavior explicit and observable in logs/metadata.
- Avoid hidden global state; pass context/config through stage boundaries.

## Quality Gates

- Run lint/format/type/test before finalizing:
  - `ruff check src tests`
  - `ruff format --check src tests`
  - `mypy src`
  - `pytest`
- Run CLI smoke checks:
  - `python -m docmirror --help`
  - `python -m docmirror run-all <sample.jpg> -o out`
- Validate that logs and debug artifacts are generated in configured paths.

## Use Bundled References

- For Docling integration details and option selection: read `references/docling-implementation-guide.md`.
- For engineering behavior and delivery checks: read `references/engineering-checklist.md`.
- For DOCX/RTL implementation notes: read `references/docx-rtl-notes.md`.

## Use Bundled Script

- `scripts/run_quality_gate.py` runs the standard local quality checks in one command.

## Output Expectations

- Deliver concrete code changes, validation evidence, and a short risk list.
- Do not stop at abstract advice when implementation is feasible.
