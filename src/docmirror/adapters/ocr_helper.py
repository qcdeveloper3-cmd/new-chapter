from __future__ import annotations

import logging
from pathlib import Path

from docmirror.context import RunContext
from docmirror.ir.models import BBox, DocumentIR, Page

LOGGER = logging.getLogger(__name__)


class OCRFallbackAdapter:
    """Fallback analyzer placeholder for OCR/OpenCV assisted extraction."""

    def analyze(self, image_path: Path, context: RunContext) -> DocumentIR:
        LOGGER.info("Fallback OCR adapter stub active for %s", image_path)
        # TODO: Implement hybrid extraction:
        # - OCR text lines/runs
        # - contour-driven tables and checkboxes
        # - geometric normalization for final DOCX rendering
        page = Page(
            page_number=1,
            width_px=0,
            height_px=0,
            page_bbox=BBox(x=0, y=0, width=0, height=0),
            writing_direction="rtl",
        )
        return DocumentIR(
            source_image=str(image_path),
            pages=[page],
            metadata={"engine": "fallback_ocr", "status": "todo_stub"},
        )
