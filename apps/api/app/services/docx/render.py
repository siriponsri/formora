from __future__ import annotations

import shutil
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from docx import Document

from app.schemas import BindingStrategy, TemplateManifest


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
        if binding.strategy != BindingStrategy.PLACEHOLDER:
            continue
        value = content.get(field.id)
        if value is None:
            if field.required:
                warnings.append(f"Required field '{field.label}' had no value.")
            value = ""
        replacements = replace_placeholder(document, binding.placeholder or "", value)
        if replacements == 0:
            warnings.append(f"Placeholder {binding.placeholder!r} was not found.")

    document.save(target)
    return warnings
