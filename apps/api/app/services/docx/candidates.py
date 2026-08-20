"""Conservative, local field-candidate detection for inspected DOCX maps."""

from __future__ import annotations

import re
from collections.abc import Iterator
from typing import Any, TypedDict


class FieldCandidate(TypedDict):
    field_id: str
    label: str
    block_id: str
    anchor: str
    confidence: float
    source_text: str


_ANCHORS: tuple[tuple[str, str], ...] = (
    ("เรื่อง", "subject"),
    ("เรียน", "recipient"),
    ("วันที่", "date"),
    ("ที่", "document_number"),
)
_ANCHOR_PATTERN = re.compile(
    r"^\s*(เรื่อง|เรียน|วันที่|ที่)(?=$|[\s:：,，\-–—])"
)
_THAI_MONTHS = (
    "มกราคม",
    "กุมภาพันธ์",
    "มีนาคม",
    "เมษายน",
    "พฤษภาคม",
    "มิถุนายน",
    "กรกฎาคม",
    "สิงหาคม",
    "กันยายน",
    "ตุลาคม",
    "พฤศจิกายน",
    "ธันวาคม",
)
_DATE_EVIDENCE = re.compile(r"\d|" + "|".join(_THAI_MONTHS))
_DOCUMENT_NUMBER_EVIDENCE = re.compile(r"\d|/")


def _iter_table_paragraphs(table: dict[str, Any]) -> Iterator[dict[str, Any]]:
    for row in table.get("rows", []):
        for cell in row.get("cells", []):
            yield from cell.get("paragraphs", [])
            for nested_table in cell.get("tables", []):
                yield from _iter_table_paragraphs(nested_table)


def iter_document_paragraphs(document_map: dict[str, Any]) -> Iterator[dict[str, Any]]:
    yield from document_map.get("paragraphs", [])
    for table in document_map.get("tables", []):
        yield from _iter_table_paragraphs(table)
    for story_name in ("headers", "footers"):
        for story in document_map.get(story_name, []):
            yield from story.get("paragraphs", [])
            for table in story.get("tables", []):
                yield from _iter_table_paragraphs(table)


def document_block_map(document_map: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        paragraph["block_id"]: paragraph
        for paragraph in iter_document_paragraphs(document_map)
        if isinstance(paragraph.get("block_id"), str)
    }


def is_valid_anchor(text: str, anchor: str) -> bool:
    match = _ANCHOR_PATTERN.match(text)
    if match is None or match.group(1) != anchor:
        return False
    field_id = dict(_ANCHORS)[anchor]
    value = text[match.end() :].strip(" \t:：,，-–—")
    return _has_required_evidence(field_id, value)


def _has_required_evidence(field_id: str, value: str) -> bool:
    if field_id == "date":
        return bool(_DATE_EVIDENCE.search(value))
    if field_id == "document_number":
        return bool(_DOCUMENT_NUMBER_EVIDENCE.search(value))
    return bool(value.strip())


def detect_candidates(document_map: dict[str, Any]) -> list[FieldCandidate]:
    """Return deterministic candidates supported by explicit Thai anchors.

    Anchors must begin a paragraph and be followed by a separator and value.
    The returned block IDs come directly from the inspected paragraph records.
    """

    candidates: list[FieldCandidate] = []
    anchor_fields = dict(_ANCHORS)
    for paragraph in iter_document_paragraphs(document_map):
        text = paragraph.get("text")
        block_id = paragraph.get("block_id")
        if not isinstance(text, str) or not isinstance(block_id, str):
            continue
        match = _ANCHOR_PATTERN.match(text)
        if match is None:
            continue
        label = match.group(1)
        field_id = anchor_fields[label]
        value = text[match.end() :].strip(" \t:：,，-–—")
        if not _has_required_evidence(field_id, value):
            continue
        candidates.append(
            {
                "field_id": field_id,
                "label": label,
                "block_id": block_id,
                "anchor": label,
                "confidence": 0.99,
                "source_text": text,
            }
        )
    return candidates


detect_field_candidates = detect_candidates
