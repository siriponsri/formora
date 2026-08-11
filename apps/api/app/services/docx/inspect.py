from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path
from typing import Any

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH

ALIGNMENT_NAMES = {
    WD_ALIGN_PARAGRAPH.LEFT: "left",
    WD_ALIGN_PARAGRAPH.CENTER: "center",
    WD_ALIGN_PARAGRAPH.RIGHT: "right",
    WD_ALIGN_PARAGRAPH.JUSTIFY: "justify",
    WD_ALIGN_PARAGRAPH.DISTRIBUTE: "distribute",
}


def _length_emu(value: Any) -> int | None:
    return int(value) if value is not None else None


def _paragraph_map(paragraph, index: int) -> dict[str, Any]:
    return {
        "index": index,
        "text": paragraph.text,
        "style": paragraph.style.name if paragraph.style else None,
        "alignment": ALIGNMENT_NAMES.get(paragraph.alignment),
        "runs": [
            {
                "text": run.text,
                "bold": run.bold,
                "italic": run.italic,
                "underline": bool(run.underline) if run.underline is not None else None,
                "font_name": run.font.name,
                "font_size_pt": run.font.size.pt if run.font.size else None,
            }
            for run in paragraph.runs
        ],
    }


def _table_map(table, index: int) -> dict[str, Any]:
    return {
        "index": index,
        "style": table.style.name if table.style else None,
        "rows": [
            {
                "index": row_index,
                "cells": [
                    {
                        "index": cell_index,
                        "text": cell.text,
                        "paragraphs": [
                            _paragraph_map(paragraph, paragraph_index)
                            for paragraph_index, paragraph in enumerate(cell.paragraphs)
                        ],
                    }
                    for cell_index, cell in enumerate(row.cells)
                ],
            }
            for row_index, row in enumerate(table.rows)
        ],
    }


def _story_map(story) -> dict[str, Any]:
    return {
        "paragraphs": [
            _paragraph_map(paragraph, index) for index, paragraph in enumerate(story.paragraphs)
        ],
        "tables": [_table_map(table, index) for index, table in enumerate(story.tables)],
    }


def _package_summary(path: Path) -> dict[str, Any]:
    checksummed_prefixes = (
        "word/styles.xml",
        "word/theme/",
        "word/media/",
        "word/settings.xml",
    )
    with zipfile.ZipFile(path) as package:
        names = sorted(package.namelist())
        checksums = {
            name: hashlib.sha256(package.read(name)).hexdigest()
            for name in names
            if name == "word/styles.xml" or name.startswith(checksummed_prefixes[1:])
        }
    return {
        "part_count": len(names),
        "parts": names,
        "preservation_checksums": checksums,
        "media_count": sum(name.startswith("word/media/") for name in names),
    }


def inspect_docx(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    document = Document(source)
    sections = []
    headers = []
    footers = []
    for index, section in enumerate(document.sections):
        sections.append(
            {
                "index": index,
                "page_width_emu": _length_emu(section.page_width),
                "page_height_emu": _length_emu(section.page_height),
                "orientation": str(section.orientation).split(" (")[0],
                "top_margin_emu": _length_emu(section.top_margin),
                "right_margin_emu": _length_emu(section.right_margin),
                "bottom_margin_emu": _length_emu(section.bottom_margin),
                "left_margin_emu": _length_emu(section.left_margin),
                "header_distance_emu": _length_emu(section.header_distance),
                "footer_distance_emu": _length_emu(section.footer_distance),
            }
        )
        headers.append({"section_index": index, **_story_map(section.header)})
        footers.append({"section_index": index, **_story_map(section.footer)})

    return {
        "file_type": "docx",
        "filename": source.name,
        "page": {"sections": len(document.sections)},
        "paragraphs": [
            _paragraph_map(paragraph, index) for index, paragraph in enumerate(document.paragraphs)
        ],
        "tables": [_table_map(table, index) for index, table in enumerate(document.tables)],
        "sections": sections,
        "headers": headers,
        "footers": footers,
        "package": _package_summary(source),
    }
