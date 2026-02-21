# Implementation Playbook

Use this when adding non-trivial features to the pipeline.

## 1. Clarify target behavior

- Define acceptance criteria tied to output files and quality constraints.
- Confirm if the request prioritizes visual fidelity, editability, or both.

## 2. Stage-scoped design

- Place logic in one stage at a time (`preprocess`, `analyze`, `render-docx`, `validate`).
- Add/update interfaces when introducing a new engine or fallback.

## 3. Data-contract first

- Extend IR models before extending adapters.
- Keep IR backward-compatible where possible; document breaking changes.

## 4. Implement thin slice

- Deliver one vertical path from CLI -> stage -> adapter -> artifact.
- Add TODO only for scoped deferred work.

## 5. Verify and report

- Run lint/type/tests/smoke checks.
- Record known limitations and next changes needed.
