from __future__ import annotations

import logging
from pathlib import Path

from docmirror.context import RunContext
from docmirror.ir.models import BBox, DocumentIR, Page

LOGGER = logging.getLogger(__name__)


class DoclingAdapter:
    """Primary analyzer adapter placeholder.

    TODO: Integrate Docling's page layout, reading order, and table extraction
    into the IR with full Persian mixed-direction support.
    """

    def analyze(self, image_path: Path, context: RunContext) -> DocumentIR:
        try:
            import docling  # noqa: F401
        except ImportError as exc:  # pragma: no cover - depends on optional extra
            raise RuntimeError(
                "Docling is not installed. Install optional deps with: pip install -e .[analysis]"
            ) from exc

        LOGGER.info("Docling adapter stub active for %s", image_path)
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
            metadata={"engine": "docling", "status": "todo_stub"},
        )
