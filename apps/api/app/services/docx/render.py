from __future__ import annotations

import shutil
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from docx import Document

from app.schemas import BindingStrategy, TemplateManifest
from app.services.docx.inspect import resolve_paragraph


class DocxRenderError(ValueError):
    """Raised when a DOCX manifest cannot be applied safely."""


def _paragraphs_in_table(table) -> Iterable:
    for row in table.rows:
        for cell in row.cells:
            yield from cell.paragraphs
            for nested_table in cell.tables:
                yield from _paragraphs_in_table(nested_table)


def _all_paragraphs(document: Document) -> Iterable:
    yield from document.paragraphs
    for table in document.tables:
        yield from _paragraphs_in_table(table)
    for section in document.sections:
        for story in (section.header, section.footer):
            yield from story.paragraphs
            for table in story.tables:
                yield from _paragraphs_in_table(table)


def _replace_first_across_runs(paragraph, placeholder: str, value: str) -> bool:
    runs = paragraph.runs
    if not runs:
        return False
    full_text = "".join(run.text for run in runs)
    start = full_text.find(placeholder)
    if start < 0:
        return False
    end = start + len(placeholder)

    spans: list[tuple[int, int]] = []
    cursor = 0
    for run in runs:
        next_cursor = cursor + len(run.text)
        spans.append((cursor, next_cursor))
        cursor = next_cursor

    start_run = next(i for i, (_, run_end) in enumerate(spans) if run_end > start)
    end_run = next(i for i, (run_start, run_end) in enumerate(spans) if run_start < end <= run_end)
    start_offset = start - spans[start_run][0]
    end_offset = end - spans[end_run][0]

    if start_run == end_run:
        original = runs[start_run].text
        runs[start_run].text = original[:start_offset] + value + original[end_offset:]
    else:
        prefix = runs[start_run].text[:start_offset]
        suffix = runs[end_run].text[end_offset:]
        runs[start_run].text = prefix + value
        for index in range(start_run + 1, end_run):
            runs[index].text = ""
        runs[end_run].text = suffix
    return True


def replace_placeholder(document: Document, placeholder: str, value: Any) -> int:
    replacement = "" if value is None else str(value)
    count = 0
    for paragraph in _all_paragraphs(document):
        while _replace_first_across_runs(paragraph, placeholder, replacement):
            count += 1
    return count


SEPARATOR_CHARS = " \t\r\n:：,，-–—"


def _run_spans(paragraph) -> tuple[str, list[tuple[Any, int, int]]]:
    text_parts: list[str] = []
    spans: list[tuple[Any, int, int]] = []
    cursor = 0
    for run in paragraph.runs:
        text = run.text or ""
        end = cursor + len(text)
        text_parts.append(text)
        spans.append((run, cursor, end))
        cursor = end
    return "".join(text_parts), spans


def _run_index_for_position(
    spans: list[tuple[Any, int, int]], position: int, *, prefer_next: bool
) -> int:
    for index, (_, start, end) in enumerate(spans):
        if start < position < end:
            return index
        if position == start:
            if prefer_next:
                return index
            if position > start:
                return index - 1
        if position == end and position > start:
            if prefer_next:
                continue
            return index
    if spans:
        return len(spans) - 1
    raise DocxRenderError("DOCX block paragraph has no writable runs.")


def _replace_text_range(paragraph, start: int, end: int, replacement: str) -> None:
    full_text, spans = _run_spans(paragraph)
    if start < 0 or end < start or end > len(full_text):
        raise DocxRenderError("DOCX replacement range is outside the paragraph text.")
    if not spans:
        raise DocxRenderError("DOCX block paragraph has no writable runs.")

    start_index = _run_index_for_position(spans, start, prefer_next=True)
    end_index = _run_index_for_position(spans, end, prefer_next=False)
    start_run, start_offset, _ = spans[start_index]
    end_run, end_offset, _ = spans[end_index]

    if start_index == end_index:
        local_start = start - start_offset
        local_end = end - start_offset
        start_run.text = (
            start_run.text[:local_start] + replacement + start_run.text[local_end:]
        )
        return

    start_local = start - start_offset
    end_local = end - end_offset
    start_run.text = start_run.text[:start_local] + replacement
    for index in range(start_index + 1, end_index):
        spans[index][0].text = ""
    end_run.text = end_run.text[end_local:]


def replace_after_anchor(paragraph, anchor: str, value: Any) -> None:
    full_text, _ = _run_spans(paragraph)
    anchor_start = full_text.find(anchor)
    if anchor_start < 0:
        raise DocxRenderError(f"Anchor {anchor!r} was not found in the reviewed DOCX block.")
    if full_text[:anchor_start].strip():
        raise DocxRenderError(f"Anchor {anchor!r} is not at the expected block position.")
    anchor_end = anchor_start + len(anchor)
    if anchor_end < len(full_text) and full_text[anchor_end] not in SEPARATOR_CHARS:
        raise DocxRenderError(f"Anchor {anchor!r} is not followed by a valid separator.")

    value_start = anchor_end
    while value_start < len(full_text) and full_text[value_start] in SEPARATOR_CHARS:
        value_start += 1
    replacement = "" if value is None else str(value)
    _replace_text_range(paragraph, value_start, len(full_text), replacement)


def render_docx(
    original_path: str | Path,
    output_path: str | Path,
    manifest: TemplateManifest,
    content: dict[str, Any],
) -> list[str]:
    source = Path(original_path)
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    document = Document(target)
    warnings: list[str] = []

    for field in manifest.fields:
        binding = field.binding
        value = content.get(field.id)
        if value is None:
            if field.required:
                warnings.append(f"Required field '{field.label}' had no value.")
            value = ""
        if binding.strategy == BindingStrategy.PLACEHOLDER:
            replacements = replace_placeholder(document, binding.placeholder or "", value)
            if replacements == 0:
                warnings.append(f"Placeholder {binding.placeholder!r} was not found.")
        elif binding.strategy == BindingStrategy.DOCX_BLOCK:
            if binding.mode != "after_anchor":
                raise DocxRenderError(
                    f"Unsupported DOCX block mode {binding.mode!r} for field '{field.id}'."
                )
            paragraph = resolve_paragraph(document, binding.block_id or "")
            if paragraph is None:
                raise DocxRenderError(
                    f"DOCX block_id {binding.block_id!r} could not be resolved."
                )
            replace_after_anchor(paragraph, binding.anchor or "", value)
        else:
            raise DocxRenderError(
                f"Unsupported DOCX binding strategy {binding.strategy.value!r} "
                f"for field '{field.id}'."
            )

    document.save(target)
    return warnings
