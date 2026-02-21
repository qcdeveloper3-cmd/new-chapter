from __future__ import annotations

import json
import logging
from pathlib import Path

from docmirror.context import RunContext

LOGGER = logging.getLogger(__name__)


def run(
    context: RunContext,
    source_image: Path,
    output_docx: Path,
    ir_json: Path | None = None,
) -> Path:
    checks = {
        "source_exists": source_image.exists(),
        "docx_exists": output_docx.exists(),
        "docx_extension_ok": output_docx.suffix.lower() == ".docx",
        "ir_provided": bool(ir_json),
    }

    # TODO: implement structural and pixel-level validation:
    # - text overlap score
    # - bounding box drift metrics
    # - table and checkbox parity checks
    report = {
        "run_id": context.run_id,
        "source_image": str(source_image),
        "output_docx": str(output_docx),
        "ir_json": str(ir_json) if ir_json else None,
        "checks": checks,
        "status": "todo_stub",
    }

    report_path = context.debug_dir / f"{context.run_id}_validation.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    LOGGER.info("Validation report written to %s", report_path)
    return report_path
