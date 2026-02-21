from __future__ import annotations

from pathlib import Path
from typing import Protocol

from docmirror.context import RunContext
from docmirror.ir.models import DocumentIR


class Preprocessor(Protocol):
    def run(self, context: RunContext, input_image: Path) -> Path: ...


class Analyzer(Protocol):
    def analyze(self, image_path: Path, context: RunContext) -> DocumentIR: ...


class DocxRenderer(Protocol):
    def render(self, ir: DocumentIR, output_docx: Path, context: RunContext) -> Path: ...


class Validator(Protocol):
    def validate(
        self,
        source_image: Path,
        output_docx: Path,
        context: RunContext,
    ) -> Path: ...
