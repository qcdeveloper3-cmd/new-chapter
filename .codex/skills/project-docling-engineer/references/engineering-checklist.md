# Engineering Checklist

Use this checklist before and after each non-trivial implementation.

## Before Coding

- Confirm acceptance criteria and expected artifacts.
- Inspect current tests/config/CI to avoid regressions.
- Choose the smallest architecture change that solves the requested problem.

## During Coding

- Keep boundaries explicit: CLI -> stages -> adapters -> storage.
- Prefer pure functions and typed models for transformation logic.
- Add logs that explain decision points and fallback paths.
- Add TODOs only for genuinely deferred work with clear scope.

## Before Finalizing

- Run lint, format checks, type checks, tests, and CLI smoke.
- Verify output paths and artifact generation.
- Summarize what was implemented, what is deferred, and known risks.

## Decision Heuristics

- If complexity grows unexpectedly, split into an interface + adapter.
- If logic is repetitive across stages, centralize utility code.
- If uncertainty is high, create a thin proof path first, then iterate.
