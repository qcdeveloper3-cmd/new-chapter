from __future__ import annotations

import logging
from pathlib import Path

from docmirror.adapters.ooxml_renderer import render_document
from docmirror.context import RunContext
from docmirror.ir.models import DocumentIR

LOGGER = logging.getLogger(__name__)


def run(context: RunContext, ir: DocumentIR, output_docx: Path | None = None) -> Path:
    target_docx = output_docx or (context.output_dir / f"{context.run_id}.docx")
    rendered = render_document(
        ir=ir,
        output_docx=target_docx,
        rtl_default=context.config.render.rtl_default,
    )
    LOGGER.info("DOCX rendered to %s", rendered)
    return rendered
