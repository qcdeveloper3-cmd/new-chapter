from __future__ import annotations

from pathlib import Path

from docmirror.context import RunContext
from docmirror.stages import analyze as analyze_stage
from docmirror.stages import preprocess as preprocess_stage
from docmirror.stages import render_docx as render_docx_stage
from docmirror.stages import validate as validate_stage


def run(context: RunContext, input_image: Path) -> tuple[Path, Path, Path]:
    preprocessed_image = preprocess_stage.run(context=context, input_image=input_image)
    ir, ir_path = analyze_stage.run(context=context, preprocessed_image=preprocessed_image)
    docx_path = render_docx_stage.run(context=context, ir=ir)
    validation_report = validate_stage.run(
        context=context,
        source_image=input_image,
        output_docx=docx_path,
        ir_json=ir_path,
    )
    return docx_path, ir_path, validation_report
