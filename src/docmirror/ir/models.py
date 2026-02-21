from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Direction = Literal["rtl", "ltr", "auto"]
BlockType = Literal["paragraph", "header", "footer", "caption", "title", "other"]
ShapeType = Literal["line", "rectangle", "ellipse", "arrow", "polygon", "unknown"]


class BBox(BaseModel):
    x: float
    y: float
    width: float
    height: float
    rotation_deg: float = 0.0


class ElementStyle(BaseModel):
    font_name: str | None = None
    font_size_pt: float | None = None
    bold: bool | None = None
    italic: bool | None = None
    underline: bool | None = None
    color_hex: str | None = None


class TextSpan(BaseModel):
    text: str
    start: int = 0
    end: int = 0
    writing_direction: Direction = "auto"
    language: str | None = None
    style: ElementStyle | None = None


class PositionedElement(BaseModel):
    id: str
    bbox: BBox
    confidence: float | None = None


class Line(PositionedElement):
    text: str
    writing_direction: Direction = "auto"
    language: str | None = None
    spans: list[TextSpan] = Field(default_factory=list)


class Block(PositionedElement):
    block_type: BlockType = "paragraph"
    writing_direction: Direction = "auto"
    lines: list[Line] = Field(default_factory=list)


class Cell(PositionedElement):
    row: int
    col: int
    row_span: int = 1
    col_span: int = 1
    writing_direction: Direction = "auto"
    lines: list[Line] = Field(default_factory=list)


class Table(PositionedElement):
    n_rows: int
    n_cols: int
    writing_direction: Direction = "auto"
    cells: list[Cell] = Field(default_factory=list)


class Checkbox(PositionedElement):
    checked: bool
    label: str | None = None
    writing_direction: Direction = "auto"


class ImageElement(PositionedElement):
    source_path: str | None = None
    alt_text: str | None = None


class ShapeElement(PositionedElement):
    shape_type: ShapeType = "unknown"
    stroke_color_hex: str | None = None
    fill_color_hex: str | None = None
    stroke_width_pt: float | None = None


class Page(BaseModel):
    page_number: int
    width_px: int
    height_px: int
    dpi: int = 300
    writing_direction: Direction = "rtl"
    page_bbox: BBox = Field(default_factory=lambda: BBox(x=0, y=0, width=0, height=0))
    blocks: list[Block] = Field(default_factory=list)
    tables: list[Table] = Field(default_factory=list)
    checkboxes: list[Checkbox] = Field(default_factory=list)
    images: list[ImageElement] = Field(default_factory=list)
    shapes: list[ShapeElement] = Field(default_factory=list)
    reading_order: list[str] = Field(default_factory=list)


class DocumentIR(BaseModel):
    source_image: str
    pages: list[Page] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)
