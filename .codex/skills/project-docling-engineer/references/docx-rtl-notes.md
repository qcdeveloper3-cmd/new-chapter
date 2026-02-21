# DOCX RTL Notes

Use this reference when implementing `render-docx` for Persian/mixed-direction forms.

## Rules

- Keep textual content editable by default (native paragraphs/runs/tables).
- Apply paragraph-level RTL alignment for RTL content.
- Preserve mixed-direction runs by storing and using span-level direction metadata.
- Keep table structure semantic (real cells/merges), not visual-only drawings.

## Recommended Output Strategy

1. Build page-level containers in print-order.
2. Render tables first where they define layout.
3. Render text blocks/runs with direction and style.
4. Render checkboxes as editable markers with labels.
5. Use images/shapes only for elements that cannot be represented natively.

## Validation Targets

- Header/footer and fixed labels align with source print output.
- Cell text direction and alignment are correct for Persian fields.
- Checkboxes/symbols remain editable and correctly placed.
