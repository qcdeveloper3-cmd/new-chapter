# Docling Implementation Guide

Use this reference when implementing or refining the `analyze` stage and engine adapters.

## Core Strategy

1. Keep Docling as the primary analyzer.
2. Convert Docling outputs into project IR (`Page`, `Block`, `Line`, `Table`, `Cell`, etc.).
3. Fall back to OCR/geometry helpers only when Docling confidence/coverage is insufficient.

## Practical Optioning

- Start with OCR enabled and table structure extraction enabled for scanned forms.
- Use accelerator options when available for predictable performance on larger workloads.
- Keep language hints explicit (`fa`, `en`) and propagate them into IR metadata.

## Mapping Priorities

1. Page geometry and reading order
2. Tables and merged-cell semantics
3. Text spans with direction metadata (RTL/LTR/auto)
4. Checkboxes and non-text marks
5. Shapes and lines needed for print fidelity

## Failure Policy

- Log exact reason when Docling path fails.
- Record fallback use in IR metadata.
- Keep fallback output schema-compatible with Docling output mapping.

## Anti-Patterns

- Do not return engine-specific structures beyond adapter boundaries.
- Do not silently drop unknown elements; map to generic `ShapeElement`/metadata placeholders.
- Do not mix OCR text into final output without confidence tracking.
