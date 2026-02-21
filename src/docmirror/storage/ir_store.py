from __future__ import annotations

from pathlib import Path

from docmirror.ir.models import DocumentIR


def save_ir(ir: DocumentIR, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(ir.model_dump_json(indent=2), encoding="utf-8")
    return path


def load_ir(path: Path) -> DocumentIR:
    return DocumentIR.model_validate_json(path.read_text(encoding="utf-8"))
