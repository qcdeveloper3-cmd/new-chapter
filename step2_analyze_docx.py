from __future__ import annotations

import argparse
import json
import logging
import re
import subprocess
import sys
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

W_NS_URI = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = f"{{{W_NS_URI}}}"
NS = {"w": W_NS_URI}

PERSIAN_ARABIC_DIGIT_TRANSLATION = str.maketrans(
    "0123456789",
    "0123456789",
)
PERSIAN_ARABIC_DIGIT_TRANSLATION.update(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))
PERSIAN_ARABIC_DIGIT_TRANSLATION.update(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))

DATE_RE = re.compile(r"^\d{1,4}[/-]\d{1,2}[/-]\d{1,4}$")
INT_RE = re.compile(r"^[+-]?\d+$")
FLOAT_RE = re.compile(r"^[+-]?\d+[.,]\d+$")
RANGE_RE = re.compile(r"(<=|>=|max|min|±|[+-]\s*\d| to |~)", re.IGNORECASE)
MEASUREMENT_RE = re.compile(r"\d+\s*(mm|cm|um|µm|nm|hrc|hv|kg|g|%)\b", re.IGNORECASE)
CODE_RE = re.compile(r"^[A-Za-z]{1,8}\s*[-/]?\s*\d[\w./-]*$")
SINGLE_LATIN_RE = re.compile(r"^[A-Za-z]$")
PLACEHOLDER_VALUES = {"-", "--", "---", "_", "*", "N/A", "n/a", "NA", "na"}


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def to_ascii_digits(text: str) -> str:
    return text.translate(PERSIAN_ARABIC_DIGIT_TRANSLATION)


def local_name(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def extract_text(element: ET.Element) -> str:
    lines: list[str] = []
    for paragraph in element.findall(".//w:p", NS):
        parts: list[str] = []
        for node in paragraph.iter():
            if node.tag == f"{W}t":
                if node.text:
                    parts.append(node.text)
            elif node.tag == f"{W}tab":
                parts.append("\t")
            elif node.tag == f"{W}br":
                parts.append("\n")
        paragraph_text = "".join(parts).strip()
        if paragraph_text:
            lines.append(paragraph_text)
    if lines:
        return "\n".join(lines).strip()

    raw = "".join((t.text or "") for t in element.findall(".//w:t", NS)).strip()
    return raw


def normalize_symbol_char(symbol_char: str) -> str:
    code = symbol_char.strip().upper()
    if code.startswith("0X"):
        code = code[2:]
    return code


def checkbox_state_for_symbol(font: str, symbol_char: str) -> bool | None:
    if "wingdings 2" not in font.lower():
        return None
    code = normalize_symbol_char(symbol_char)
    if code.endswith("A2"):
        return True
    if code.endswith("A3"):
        return False
    return None


def extract_symbols(element: ET.Element) -> list[dict[str, Any]]:
    symbols: list[dict[str, Any]] = []
    for symbol in element.findall(".//w:sym", NS):
        font = (symbol.attrib.get(f"{W}font") or "").strip()
        symbol_char = (symbol.attrib.get(f"{W}char") or "").strip()
        checkbox_state = checkbox_state_for_symbol(font, symbol_char)
        symbols.append(
            {
                "font": font,
                "char": normalize_symbol_char(symbol_char),
                "checkbox_state": checkbox_state,
                "is_checkbox_symbol": checkbox_state is not None,
            }
        )
    return symbols


def extract_key_values(text: str) -> list[dict[str, str]]:
    pairs: list[dict[str, str]] = []
    for raw_line in text.splitlines():
        line = normalize_space(raw_line)
        if not line:
            continue

        colon_positions = [pos for pos in (line.find(":"), line.find("：")) if pos > 0]
        if not colon_positions:
            continue
        split_at = min(colon_positions)
        key = line[:split_at].strip()
        value = line[split_at + 1 :].strip()
        if key:
            pairs.append({"key": key, "value": value})
    return pairs


def infer_text_type(value: str) -> str:
    normalized = normalize_space(value)
    if not normalized:
        return "empty"

    if normalized in PLACEHOLDER_VALUES:
        return "placeholder"

    ascii_digits = to_ascii_digits(normalized)
    lower = ascii_digits.lower()

    if lower in {"true", "false", "yes", "no"}:
        return "boolean"
    if DATE_RE.fullmatch(ascii_digits):
        return "date"
    if MEASUREMENT_RE.search(ascii_digits):
        return "measurement"
    if INT_RE.fullmatch(ascii_digits):
        return "integer"
    if FLOAT_RE.fullmatch(ascii_digits):
        return "float"
    if CODE_RE.fullmatch(ascii_digits):
        return "code"
    if RANGE_RE.search(ascii_digits) and any(ch.isdigit() for ch in ascii_digits):
        return "range_or_tolerance"
    if SINGLE_LATIN_RE.fullmatch(ascii_digits):
        return "enum"
    return "text"


def has_data_signal(row: dict[str, Any]) -> bool:
    values = [
        normalize_space(cell["text"])
        for cell in row["cells"]
        if normalize_space(cell["text"]) and infer_text_type(cell["text"]) != "placeholder"
    ]
    if len(values) < 2:
        return False
    inferred_types = [infer_text_type(value) for value in values]
    numeric_like = sum(
        1
        for value_type in inferred_types
        if value_type in {"integer", "float", "date", "measurement", "range_or_tolerance", "code"}
    )
    return numeric_like >= 1


def longest_contiguous_group(indices: list[int]) -> list[int]:
    if not indices:
        return []
    groups: list[list[int]] = [[indices[0]]]
    for idx in indices[1:]:
        if idx == groups[-1][-1] + 1:
            groups[-1].append(idx)
        else:
            groups.append([idx])
    return max(groups, key=len)


def infer_table_sections(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "dominant_row_pattern": [],
            "dominant_pattern_count": 0,
            "metadata_rows": [],
            "header_rows": [],
            "data_rows": [],
            "confidence": 0.0,
        }

    patterns = [tuple(cell["col_span"] for cell in row["cells"]) for row in rows]
    pattern_counts = Counter(patterns)
    dominant_pattern, dominant_pattern_count = pattern_counts.most_common(1)[0]
    dominant_rows = [idx for idx, pattern in enumerate(patterns) if pattern == dominant_pattern]
    dominant_group = longest_contiguous_group(dominant_rows)

    dense_threshold = max(8, int(len(dominant_pattern) * 0.6))
    layout_start = next(
        (idx for idx, row in enumerate(rows) if len(row["cells"]) >= dense_threshold),
        dominant_group[0] if dominant_group else 0,
    )

    data_start = None
    for idx in dominant_group:
        if has_data_signal(rows[idx]):
            data_start = idx
            break
    if data_start is None:
        data_start = dominant_group[0] if dominant_group else layout_start

    metadata_rows = list(range(0, min(layout_start, len(rows))))
    header_rows = list(range(layout_start, data_start)) if data_start > layout_start else []
    data_rows = [idx for idx in dominant_group if idx >= data_start]

    confidence = 0.0
    if rows:
        confidence = round(min(1.0, dominant_pattern_count / len(rows)), 3)

    return {
        "dominant_row_pattern": list(dominant_pattern),
        "dominant_pattern_count": dominant_pattern_count,
        "dominant_pattern_rows": dominant_rows,
        "dominant_contiguous_group": dominant_group,
        "layout_start_row": layout_start,
        "metadata_rows": metadata_rows,
        "header_rows": header_rows,
        "data_rows": data_rows,
        "confidence": confidence,
    }


def extract_label_candidates(text: str, expected_count: int) -> list[str]:
    if expected_count <= 0:
        return []
    candidates: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = [normalize_space(piece) for piece in re.split(r"\s{2,}", line) if normalize_space(piece)]
        if len(parts) == 1:
            slash_parts = [
                normalize_space(piece)
                for piece in re.split(r"[|/]+", line)
                if normalize_space(piece)
            ]
            if len(slash_parts) > 1:
                parts = slash_parts
        candidates.extend(parts)

    if len(candidates) >= expected_count:
        return candidates[:expected_count]
    return candidates


def annotate_vertical_merges(rows: list[dict[str, Any]]) -> None:
    by_row_slot: list[dict[tuple[int, int], dict[str, Any]]] = []
    for row in rows:
        slot_map: dict[tuple[int, int], dict[str, Any]] = {}
        for cell in row["cells"]:
            slot_map[(cell["col_start"], cell["col_span"])] = cell
        by_row_slot.append(slot_map)

    for row_index, row in enumerate(rows):
        for cell in row["cells"]:
            slot = (cell["col_start"], cell["col_span"])
            if cell["v_merge"] == "continue":
                anchor_row = None
                for prev_index in range(row_index - 1, -1, -1):
                    prev_cell = by_row_slot[prev_index].get(slot)
                    if prev_cell is None:
                        break
                    if prev_cell["v_merge"] != "continue":
                        anchor_row = prev_index
                        break
                cell["merge_anchor_row"] = anchor_row
                cell["row_span"] = 0
                continue

            span = 1
            for next_index in range(row_index + 1, len(rows)):
                next_cell = by_row_slot[next_index].get(slot)
                if not next_cell:
                    break
                if next_cell["v_merge"] != "continue":
                    break
                span += 1
            cell["merge_anchor_row"] = row_index if span > 1 else None
            cell["row_span"] = span


def slot_overlap(cell_a: tuple[int, int], cell_b: tuple[int, int]) -> bool:
    a_start, a_span = cell_a
    b_start, b_span = cell_b
    a_end = a_start + a_span - 1
    b_end = b_start + b_span - 1
    return max(a_start, b_start) <= min(a_end, b_end)


def collect_header_fragments(
    rows: list[dict[str, Any]],
    header_rows: list[int],
    slot: tuple[int, int],
) -> list[str]:
    fragments: list[str] = []
    for row_index in header_rows:
        row = rows[row_index]
        for cell in row["cells"]:
            if slot_overlap(slot, (cell["col_start"], cell["col_span"])):
                text = normalize_space(cell["text"])
                if text and text not in fragments:
                    fragments.append(text)
    return fragments


def find_cell_by_slot(cells: list[dict[str, Any]], slot: tuple[int, int]) -> dict[str, Any] | None:
    for cell in cells:
        if cell["col_start"] == slot[0] and cell["col_span"] == slot[1]:
            return cell
    return None


def infer_column_schema(
    rows: list[dict[str, Any]],
    sections: dict[str, Any],
    max_sample_values: int = 8,
) -> list[dict[str, Any]]:
    data_rows: list[int] = sections.get("data_rows", [])
    header_rows: list[int] = sections.get("header_rows", [])
    if not data_rows:
        return []

    template_row = rows[data_rows[0]]
    schema: list[dict[str, Any]] = []
    for index, template_cell in enumerate(template_row["cells"]):
        slot = (template_cell["col_start"], template_cell["col_span"])
        value_type_distribution: Counter[str] = Counter()
        sample_values: list[str] = []
        empty_cell_count = 0
        placeholder_count = 0
        checkbox_distribution: Counter[str] = Counter()

        for row_index in data_rows:
            row_cell = find_cell_by_slot(rows[row_index]["cells"], slot)
            if row_cell is None:
                continue
            value = normalize_space(row_cell["text"])
            if value:
                if value not in sample_values and len(sample_values) < max_sample_values:
                    sample_values.append(value)
                value_type = infer_text_type(value)
                value_type_distribution[value_type] += 1
                if value_type == "placeholder":
                    placeholder_count += 1
            else:
                empty_cell_count += 1

            for symbol in row_cell["symbols"]:
                state = symbol["checkbox_state"]
                if state is True:
                    checkbox_distribution["checked"] += 1
                elif state is False:
                    checkbox_distribution["unchecked"] += 1

        header_fragments = collect_header_fragments(rows, header_rows, slot)
        header_label = " | ".join(header_fragments)
        dominant_type = (
            value_type_distribution.most_common(1)[0][0]
            if value_type_distribution
            else "empty"
        )

        schema.append(
            {
                "column_index": index,
                "col_start": slot[0],
                "col_end": slot[0] + slot[1] - 1,
                "col_span": slot[1],
                "header_fragments": header_fragments,
                "header_label": header_label,
                "dominant_value_type": dominant_type,
                "value_type_distribution": dict(value_type_distribution),
                "sample_values": sample_values,
                "empty_cell_count": empty_cell_count,
                "placeholder_count": placeholder_count,
                "has_checkbox": bool(checkbox_distribution),
                "checkbox_distribution": dict(checkbox_distribution),
            }
        )
    return schema


def parse_table(table_element: ET.Element, table_index: int, body_block_index: int) -> dict[str, Any]:
    grid_columns = [
        int(grid_col.attrib.get(f"{W}w", "0") or 0)
        for grid_col in table_element.findall("./w:tblGrid/w:gridCol", NS)
    ]

    rows: list[dict[str, Any]] = []
    for row_index, tr in enumerate(table_element.findall("./w:tr", NS)):
        tr_pr = tr.find("./w:trPr", NS)
        grid_before = 0
        if tr_pr is not None:
            grid_before_element = tr_pr.find("./w:gridBefore", NS)
            if grid_before_element is not None:
                grid_before = int(grid_before_element.attrib.get(f"{W}val", "0") or 0)

        cursor = grid_before
        row_cells: list[dict[str, Any]] = []
        for cell_index, tc in enumerate(tr.findall("./w:tc", NS)):
            tc_pr = tc.find("./w:tcPr", NS)
            col_span = 1
            v_merge = None
            width_twips = None
            if tc_pr is not None:
                grid_span_el = tc_pr.find("./w:gridSpan", NS)
                if grid_span_el is not None:
                    col_span = int(grid_span_el.attrib.get(f"{W}val", "1") or 1)
                v_merge_el = tc_pr.find("./w:vMerge", NS)
                if v_merge_el is not None:
                    v_merge = v_merge_el.attrib.get(f"{W}val", "continue")
                tcw = tc_pr.find("./w:tcW", NS)
                if tcw is not None:
                    width_raw = tcw.attrib.get(f"{W}w")
                    if width_raw and width_raw.isdigit():
                        width_twips = int(width_raw)

            text = extract_text(tc)
            symbols = extract_symbols(tc)
            key_values = extract_key_values(text)
            inferred_type = infer_text_type(text)
            row_cells.append(
                {
                    "row_index": row_index,
                    "cell_index": cell_index,
                    "col_start": cursor,
                    "col_end": cursor + col_span - 1,
                    "col_span": col_span,
                    "v_merge": v_merge,
                    "width_twips": width_twips,
                    "row_span": 1,
                    "merge_anchor_row": None,
                    "text": text,
                    "text_lines": [line for line in text.splitlines() if line.strip()],
                    "symbols": symbols,
                    "key_values": key_values,
                    "inferred_type": inferred_type,
                    "contains_drawing": bool(tc.findall(".//w:drawing", NS)),
                }
            )
            cursor += col_span

        rows.append(
            {
                "row_index": row_index,
                "grid_before": grid_before,
                "cell_count": len(row_cells),
                "cells": row_cells,
                "total_col_span": grid_before + sum(cell["col_span"] for cell in row_cells),
                "non_empty_cell_count": sum(1 for cell in row_cells if normalize_space(cell["text"])),
                "symbol_count": sum(len(cell["symbols"]) for cell in row_cells),
                "checkbox_count": sum(
                    1
                    for cell in row_cells
                    for symbol in cell["symbols"]
                    if symbol["is_checkbox_symbol"]
                ),
            }
        )

    annotate_vertical_merges(rows)
    sections = infer_table_sections(rows)
    column_schema = infer_column_schema(rows, sections)

    checkbox_fields: list[dict[str, Any]] = []
    key_value_fields: list[dict[str, Any]] = []
    inferred_type_histogram: Counter[str] = Counter()
    for row in rows:
        for cell in row["cells"]:
            inferred_type_histogram[cell["inferred_type"]] += 1
            for key_value in cell["key_values"]:
                key_value_fields.append(
                    {
                        "table_index": table_index,
                        "row_index": row["row_index"],
                        "col_start": cell["col_start"],
                        "col_span": cell["col_span"],
                        "key": key_value["key"],
                        "value": key_value["value"],
                        "value_type": infer_text_type(key_value["value"]),
                    }
                )

            checkbox_symbols = [symbol for symbol in cell["symbols"] if symbol["is_checkbox_symbol"]]
            if checkbox_symbols:
                label_candidates = extract_label_candidates(cell["text"], len(checkbox_symbols))
                for symbol_index, symbol in enumerate(checkbox_symbols):
                    checkbox_fields.append(
                        {
                            "table_index": table_index,
                            "row_index": row["row_index"],
                            "col_start": cell["col_start"],
                            "col_span": cell["col_span"],
                            "symbol_index_in_cell": symbol_index,
                            "font": symbol["font"],
                            "char": symbol["char"],
                            "checked": symbol["checkbox_state"],
                            "label_candidate": (
                                label_candidates[symbol_index]
                                if symbol_index < len(label_candidates)
                                else None
                            ),
                            "cell_text": normalize_space(cell["text"]),
                        }
                    )

    return {
        "table_index": table_index,
        "body_block_index": body_block_index,
        "row_count": len(rows),
        "grid_column_count": len(grid_columns),
        "grid_column_widths_twips": grid_columns,
        "max_total_col_span": max((row["total_col_span"] for row in rows), default=0),
        "max_cell_count": max((row["cell_count"] for row in rows), default=0),
        "rows": rows,
        "sections": sections,
        "column_schema": column_schema,
        "checkbox_fields": checkbox_fields,
        "key_value_fields": key_value_fields,
        "inferred_type_histogram": dict(inferred_type_histogram),
    }


def parse_properties(xml_bytes: bytes) -> dict[str, str]:
    root = ET.fromstring(xml_bytes)
    output: dict[str, str] = {}
    for child in list(root):
        key = local_name(child.tag)
        value = (child.text or "").strip()
        if value:
            output[key] = value
    return output


def is_docx_package(path: Path) -> bool:
    if path.suffix.lower() != ".docx" or not path.exists():
        return False
    try:
        with zipfile.ZipFile(path) as docx_zip:
            return "word/document.xml" in docx_zip.namelist()
    except zipfile.BadZipFile:
        return False


def convert_doc_to_docx_via_win32com(doc_path: Path, out_docx_path: Path) -> None:
    try:
        import win32com.client  # type: ignore
    except Exception as exc:
        raise RuntimeError(f"win32com import failed: {type(exc).__name__}: {exc}") from exc

    word = None
    document = None
    try:
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        document = word.Documents.Open(
            str(doc_path.resolve()),
            ConfirmConversions=False,
            ReadOnly=True,
            AddToRecentFiles=False,
            Visible=False,
        )
        # 16 => wdFormatXMLDocument (.docx)
        document.SaveAs2(str(out_docx_path.resolve()), FileFormat=16)
    finally:
        if document is not None:
            document.Close(False)
        if word is not None:
            word.Quit()


def convert_doc_to_docx_via_powershell(doc_path: Path, out_docx_path: Path) -> None:
    doc_arg = str(doc_path.resolve()).replace("'", "''")
    out_arg = str(out_docx_path.resolve()).replace("'", "''")
    script = (
        "$ErrorActionPreference='Stop'; "
        "$word = New-Object -ComObject Word.Application; "
        "$word.Visible=$false; "
        "$word.DisplayAlerts=0; "
        f"$doc = $word.Documents.Open('{doc_arg}', $false, $true); "
        f"$doc.SaveAs2('{out_arg}', 16); "
        "$doc.Close($false); "
        "$word.Quit();"
    )
    command = ["powershell", "-NoProfile", "-NonInteractive", "-Command", script]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        stdout = (result.stdout or "").strip()
        message = stderr or stdout or f"exit code {result.returncode}"
        raise RuntimeError(f"PowerShell COM conversion failed: {message}")


def prepare_input_docx(
    input_path: Path,
    converted_dir: Path | None = None,
) -> tuple[Path, dict[str, Any]]:
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    suffix = input_path.suffix.lower()
    if suffix == ".docx":
        if not is_docx_package(input_path):
            raise ValueError(f"Input has .docx extension but is not a valid DOCX package: {input_path}")
        return input_path, {"source_format": "docx", "converted": False}

    if suffix != ".doc":
        raise ValueError(
            f"Unsupported input format '{suffix}'. Supported formats are .docx and .doc."
        )

    target_dir = converted_dir or (input_path.parent / "out" / "_converted")
    target_dir.mkdir(parents=True, exist_ok=True)
    out_docx_path = target_dir / f"{input_path.stem}.converted.docx"

    conversion_error: str | None = None
    try:
        convert_doc_to_docx_via_win32com(input_path, out_docx_path)
    except Exception as exc:
        conversion_error = f"win32com conversion failed: {type(exc).__name__}: {exc}"
        try:
            convert_doc_to_docx_via_powershell(input_path, out_docx_path)
            conversion_error = None
        except Exception as fallback_exc:
            conversion_error = (
                f"{conversion_error}; fallback failed: {type(fallback_exc).__name__}: {fallback_exc}"
            )

    if conversion_error:
        raise RuntimeError(
            "Unable to convert legacy .doc to .docx. "
            "Microsoft Word COM automation appears unavailable.\n"
            f"Details: {conversion_error}"
        )

    if not is_docx_package(out_docx_path):
        raise RuntimeError(f"Converted file is not a valid DOCX package: {out_docx_path}")

    return out_docx_path, {
        "source_format": "doc",
        "converted": True,
        "source_path": str(input_path),
        "converted_docx_path": str(out_docx_path),
    }


def analyze_with_docling(docx_path: Path) -> dict[str, Any]:
    try:
        from docling.document_converter import DocumentConverter
    except Exception as exc:  # pragma: no cover
        return {"available": False, "error": f"{type(exc).__name__}: {exc}"}

    logging.getLogger("docling").setLevel(logging.ERROR)
    try:
        result = DocumentConverter().convert(str(docx_path))
    except Exception as exc:  # pragma: no cover
        return {"available": True, "conversion_error": f"{type(exc).__name__}: {exc}"}

    document = result.document
    tables = list(getattr(document, "tables", []) or [])
    table_summaries: list[dict[str, Any]] = []
    for table_index, table in enumerate(tables):
        data = getattr(table, "data", None)
        table_cells = list(getattr(data, "table_cells", []) or [])
        non_empty = 0
        max_row = 0
        max_col = 0
        for cell in table_cells:
            if getattr(cell, "text", None):
                non_empty += 1
            end_row = getattr(cell, "end_row_offset_idx", None)
            end_col = getattr(cell, "end_col_offset_idx", None)
            if isinstance(end_row, int):
                max_row = max(max_row, end_row)
            if isinstance(end_col, int):
                max_col = max(max_col, end_col)
        table_summaries.append(
            {
                "table_index": table_index,
                "table_cell_count": len(table_cells),
                "non_empty_table_cell_count": non_empty,
                "estimated_row_count": max_row,
                "estimated_col_count": max_col,
            }
        )

    return {
        "available": True,
        "table_count": len(tables),
        "table_summaries": table_summaries,
    }


def analyze_docx(
    input_path: Path,
    use_docling: bool = True,
    converted_dir: Path | None = None,
) -> dict[str, Any]:
    analysis_docx_path, conversion_info = prepare_input_docx(
        input_path=input_path,
        converted_dir=converted_dir,
    )

    with zipfile.ZipFile(analysis_docx_path) as docx_zip:
        package_parts = docx_zip.namelist()
        if "word/document.xml" not in package_parts:
            raise ValueError("word/document.xml was not found in this .docx package.")
        document_xml = docx_zip.read("word/document.xml")

        core_properties = (
            parse_properties(docx_zip.read("docProps/core.xml"))
            if "docProps/core.xml" in package_parts
            else {}
        )
        app_properties = (
            parse_properties(docx_zip.read("docProps/app.xml"))
            if "docProps/app.xml" in package_parts
            else {}
        )

    root = ET.fromstring(document_xml)
    body = root.find("./w:body", NS)
    if body is None:
        raise ValueError("The document body was not found in word/document.xml.")

    block_sequence: list[dict[str, Any]] = []
    block_type_counts: Counter[str] = Counter()
    tables: list[dict[str, Any]] = []

    table_index = 0
    for block_index, child in enumerate(list(body)):
        block_type = local_name(child.tag)
        block_type_counts[block_type] += 1
        block_entry: dict[str, Any] = {"index": block_index, "type": block_type}

        if block_type == "tbl":
            table_data = parse_table(child, table_index=table_index, body_block_index=block_index)
            tables.append(table_data)
            block_entry["table_index"] = table_index
            block_entry["row_count"] = table_data["row_count"]
            block_entry["grid_column_count"] = table_data["grid_column_count"]
            table_index += 1
        elif block_type == "p":
            paragraph_text = normalize_space(extract_text(child))
            if paragraph_text:
                block_entry["text_preview"] = paragraph_text[:140]
        block_sequence.append(block_entry)

    all_checkbox_fields = [field for table in tables for field in table["checkbox_fields"]]
    all_key_value_fields = [field for table in tables for field in table["key_value_fields"]]
    all_type_counts: Counter[str] = Counter()
    for table in tables:
        all_type_counts.update(table["inferred_type_histogram"])

    symbol_counter: Counter[str] = Counter()
    symbol_fonts: Counter[str] = Counter()
    for table in tables:
        for row in table["rows"]:
            for cell in row["cells"]:
                for symbol in cell["symbols"]:
                    symbol_counter[symbol["char"]] += 1
                    symbol_fonts[symbol["font"]] += 1

    drawing_count = len(root.findall(".//w:drawing", NS))
    pict_count = len(root.findall(".//w:pict", NS))
    bookmark_count = len(root.findall(".//w:bookmarkStart", NS))

    analysis: dict[str, Any] = {
        "analysis_version": "1.0.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_document": str(input_path),
        "input_docx": str(analysis_docx_path),
        "input_format": input_path.suffix.lower().lstrip("."),
        "conversion": conversion_info,
        "package": {
            "part_count": len(package_parts),
            "parts": package_parts,
        },
        "document_properties": {
            "core": core_properties,
            "app": app_properties,
        },
        "structure": {
            "block_type_counts": dict(block_type_counts),
            "block_sequence": block_sequence,
            "drawing_count": drawing_count,
            "pict_count": pict_count,
            "bookmark_count": bookmark_count,
            "table_count": len(tables),
        },
        "tables": tables,
        "global_findings": {
            "checkbox_field_count": len(all_checkbox_fields),
            "key_value_field_count": len(all_key_value_fields),
            "inferred_type_histogram": dict(all_type_counts),
            "symbol_char_histogram": dict(symbol_counter),
            "symbol_font_histogram": dict(symbol_fonts),
            "checkbox_fields": all_checkbox_fields,
            "key_value_fields": all_key_value_fields,
        },
    }

    if use_docling:
        analysis["docling"] = analyze_with_docling(analysis_docx_path)
    else:
        analysis["docling"] = {"available": False, "error": "Disabled by --no-docling"}

    return analysis


def markdown_escape(text: str) -> str:
    return text.replace("|", "\\|")


def render_markdown_summary(analysis: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# DOCX Analysis Report: {analysis['input_document']}")
    lines.append("")
    lines.append(f"- Generated: {analysis['generated_at_utc']}")
    lines.append(f"- Analysis version: {analysis['analysis_version']}")
    lines.append(f"- Input format: {analysis['input_format']}")
    lines.append(f"- XML-analyzed DOCX: {analysis['input_docx']}")
    if analysis.get("conversion", {}).get("converted"):
        lines.append(f"- Conversion: {analysis['conversion']['source_path']} -> {analysis['conversion']['converted_docx_path']}")
    lines.append(f"- Tables detected: {analysis['structure']['table_count']}")
    lines.append(
        f"- Checkboxes detected: {analysis['global_findings']['checkbox_field_count']}"
    )
    lines.append(
        f"- Key-value fields detected: {analysis['global_findings']['key_value_field_count']}"
    )
    lines.append("")

    lines.append("## Structure")
    for block_type, count in analysis["structure"]["block_type_counts"].items():
        lines.append(f"- {block_type}: {count}")
    lines.append(f"- drawings: {analysis['structure']['drawing_count']}")
    lines.append(f"- pict nodes: {analysis['structure']['pict_count']}")
    lines.append(f"- bookmarks: {analysis['structure']['bookmark_count']}")
    lines.append("")

    lines.append("## Symbols")
    symbol_hist = analysis["global_findings"]["symbol_char_histogram"]
    if symbol_hist:
        for symbol_char, count in symbol_hist.items():
            lines.append(f"- {symbol_char}: {count}")
    else:
        lines.append("- none")
    lines.append("")

    for table in analysis["tables"]:
        lines.append(f"## Table {table['table_index']}")
        lines.append(f"- Body block index: {table['body_block_index']}")
        lines.append(f"- Row count: {table['row_count']}")
        lines.append(f"- Grid columns: {table['grid_column_count']}")
        lines.append(f"- Max row col-span: {table['max_total_col_span']}")
        lines.append(f"- Max physical cell count: {table['max_cell_count']}")

        sections = table["sections"]
        lines.append(
            "- Section inference:"
            f" metadata_rows={sections['metadata_rows']},"
            f" header_rows={sections['header_rows']},"
            f" data_rows={sections['data_rows']},"
            f" confidence={sections['confidence']}"
        )
        lines.append("")

        lines.append("### Inferred Column Schema")
        if table["column_schema"]:
            lines.append("| # | Col Range | Header | Type | Samples |")
            lines.append("|---|---|---|---|---|")
            for column in table["column_schema"]:
                samples = "; ".join(markdown_escape(value) for value in column["sample_values"][:3])
                header = markdown_escape(column["header_label"])
                col_range = f"{column['col_start']}-{column['col_end']}"
                lines.append(
                    f"| {column['column_index']} | {col_range} | {header} "
                    f"| {column['dominant_value_type']} | {samples} |"
                )
        else:
            lines.append("- no stable data schema inferred")
        lines.append("")

        lines.append("### Checkbox Fields")
        if table["checkbox_fields"]:
            for field in table["checkbox_fields"][:30]:
                state = (
                    "checked"
                    if field["checked"] is True
                    else "unchecked"
                    if field["checked"] is False
                    else "unknown"
                )
                label = field["label_candidate"] or "(no label)"
                lines.append(
                    f"- row {field['row_index']}, col {field['col_start']}: "
                    f"{label} -> {state} ({field['char']})"
                )
        else:
            lines.append("- none")
        lines.append("")

        lines.append("### Key-Value Fields")
        if table["key_value_fields"]:
            for field in table["key_value_fields"][:40]:
                lines.append(
                    f"- row {field['row_index']}, col {field['col_start']}: "
                    f"{field['key']} = {field['value']}"
                )
        else:
            lines.append("- none")
        lines.append("")

    docling = analysis.get("docling", {})
    lines.append("## Docling")
    if docling.get("available") is True and "conversion_error" not in docling:
        lines.append(f"- table_count: {docling.get('table_count', 0)}")
        for table in docling.get("table_summaries", []):
            lines.append(
                f"- table {table['table_index']}: cells={table['table_cell_count']}, "
                f"non_empty={table['non_empty_table_cell_count']}, "
                f"rows~={table['estimated_row_count']}, cols~={table['estimated_col_count']}"
            )
    elif docling.get("conversion_error"):
        lines.append(f"- conversion error: {docling['conversion_error']}")
    else:
        lines.append(f"- unavailable: {docling.get('error', 'not installed')}")

    return "\n".join(lines).rstrip() + "\n"


def write_outputs(analysis: dict[str, Any], output_dir: Path, stem: str) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{stem}.analysis.json"
    md_path = output_dir / f"{stem}.analysis.md"

    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(analysis, handle, ensure_ascii=False, indent=2)
    with md_path.open("w", encoding="utf-8") as handle:
        handle.write(render_markdown_summary(analysis))

    return json_path, md_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Analyze DOCX (or legacy DOC via auto-conversion) form structure and "
            "infer schema, value types, checkboxes, and key-value fields."
        )
    )
    parser.add_argument(
        "input_paths",
        nargs="*",
        help="Input file paths (.docx or .doc). If omitted, uses 9201.docx.",
    )
    parser.add_argument(
        "--output-dir",
        default="out",
        help="Directory for generated analysis files (default: out)",
    )
    parser.add_argument(
        "--converted-dir",
        default=None,
        help=(
            "Directory for temporary converted .docx files (used for .doc inputs). "
            "Default: <output-dir>/_converted"
        ),
    )
    parser.add_argument(
        "--no-docling",
        action="store_true",
        help="Disable optional Docling-based comparison.",
    )
    parser.add_argument(
        "--print-summary",
        action="store_true",
        help="Print compact summary to stdout.",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop immediately on first input failure.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_paths = [Path(path) for path in args.input_paths] if args.input_paths else [Path("9201.docx")]
    output_dir = Path(args.output_dir)
    converted_dir = Path(args.converted_dir) if args.converted_dir else (output_dir / "_converted")

    failures: list[tuple[Path, Exception]] = []
    for input_path in input_paths:
        try:
            analysis = analyze_docx(
                input_path=input_path,
                use_docling=not args.no_docling,
                converted_dir=converted_dir,
            )
            report_stem = input_path.stem if input_path.suffix.lower() == ".docx" else f"{input_path.stem}.doc"
            json_path, md_path = write_outputs(analysis, output_dir, report_stem)

            print(f"Analysis complete for: {input_path}")
            print(f"- JSON report: {json_path}")
            print(f"- Markdown report: {md_path}")

            if args.print_summary:
                sections = [
                    f"tables={analysis['structure']['table_count']}",
                    f"checkboxes={analysis['global_findings']['checkbox_field_count']}",
                    f"key_values={analysis['global_findings']['key_value_field_count']}",
                    f"docling_available={analysis.get('docling', {}).get('available', False)}",
                    f"converted={analysis.get('conversion', {}).get('converted', False)}",
                ]
                print("Summary: " + ", ".join(sections))
        except Exception as exc:
            failures.append((input_path, exc))
            print(f"Analysis failed for: {input_path}", file=sys.stderr)
            print(f"- Error: {type(exc).__name__}: {exc}", file=sys.stderr)
            if args.fail_fast:
                break

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
