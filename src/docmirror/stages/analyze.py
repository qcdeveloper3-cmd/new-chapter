from __future__ import annotations

import logging
from pathlib import Path

from docmirror.adapters.docling_adapter import DoclingAdapter
from docmirror.adapters.ocr_helper import OCRFallbackAdapter
from docmirror.context import RunContext
from docmirror.ir.models import DocumentIR
from docmirror.storage.ir_store import save_ir

LOGGER = logging.getLogger(__name__)


def run(context: RunContext, preprocessed_image: Path) -> tuple[DocumentIR, Path]:
    analyzer = DoclingAdapter()

    try:
        ir = analyzer.analyze(image_path=preprocessed_image, context=context)
    except Exception as exc:
        if not context.config.analysis.enable_fallback_ocr:
            raise
        LOGGER.warning("Docling analysis failed (%s). Falling back to OCR module.", exc)
        ir = OCRFallbackAdapter().analyze(image_path=preprocessed_image, context=context)

    ir_path = context.output_dir / f"{context.run_id}.ir.json"
    save_ir(ir=ir, path=ir_path)
    LOGGER.info("Analysis IR written to %s", ir_path)
    return ir, ir_path
