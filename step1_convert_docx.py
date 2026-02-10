from __future__ import annotations

import re
import logging
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

from docling.document_converter import DocumentConverter

W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def get_first_row_labels_with_docling(docx_path: Path) -> list[str]:
    """Read first-row labels from the first table using Docling."""
    logging.getLogger("docling").setLevel(logging.ERROR)
    result = DocumentConverter().convert(str(docx_path))
    if not result.document.tables:
        raise ValueError("No table found in document.")

    table = result.document.tables[0]
    first_row_cells = [
        cell
        for cell in table.data.table_cells
        if cell.start_row_offset_idx == 0 and cell.end_row_offset_idx == 1 and cell.text
    ]
    if not first_row_cells:
        raise ValueError("First row cells not found in Docling table output.")

    header_text = max((cell.text for cell in first_row_cells), key=len)
    lines = [line.strip() for line in header_text.splitlines() if line.strip()]
    if not lines:
        raise ValueError("First row text is empty.")

    label_line = lines[-1]
    labels = [part.strip() for part in re.split(r"\s{2,}", label_line) if part.strip()]
    if len(labels) < 4:
        raise ValueError(f"Expected 4 labels in first row, got {len(labels)}: {labels}")

    return labels[:4]


def get_first_row_checkbox_codes_from_xml(docx_path: Path) -> list[str]:
    """Extract first-row checkbox symbol codes from DOCX XML."""
    with zipfile.ZipFile(docx_path) as docx_zip:
        xml_data = docx_zip.read("word/document.xml")

    root = ET.fromstring(xml_data)
    first_row = root.find(f".//{W_NS}tbl/{W_NS}tr")
    if first_row is None:
        raise ValueError("Could not find the first table row in document.xml.")

    symbol_codes: list[str] = []
    for sym in first_row.findall(f".//{W_NS}sym"):
        font = (sym.attrib.get(f"{W_NS}font") or "").lower()
        code = (sym.attrib.get(f"{W_NS}char") or "").upper()
        if "wingdings 2" in font and code:
            symbol_codes.append(code)

    if len(symbol_codes) < 4:
        raise ValueError(
            f"Expected at least 4 checkbox symbols in first row, got {len(symbol_codes)}: {symbol_codes}"
        )

    return symbol_codes[:4]


def checkbox_code_to_bool(code: str) -> bool:
    """
    Map Wingdings-2 checkbox symbols to True/False.
    In this file, A2 means checked and A3 means unchecked.
    """
    normalized = code.upper()
    if normalized.endswith("A2"):
        return True
    if normalized.endswith("A3"):
        return False
    raise ValueError(f"Unknown checkbox symbol code: {code}")


def main() -> None:
    docx_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("9201.docx")
    if not docx_path.exists():
        raise FileNotFoundError(f"File not found: {docx_path}")

    labels = get_first_row_labels_with_docling(docx_path)
    codes = get_first_row_checkbox_codes_from_xml(docx_path)

    print(f"Document: {docx_path}")
    print("First-row checkbox values:")
    for label, code in zip(labels, codes):
        value = checkbox_code_to_bool(code)
        print(f"- {label}: {value} (symbol={code})")


if __name__ == "__main__":
    main()
