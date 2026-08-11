from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db import TemplateORM
from app.schemas import TemplateManifest, TemplateRecord
from app.services.storage import LocalFileStorage


def get_template_or_404(session: Session, template_id: str) -> TemplateORM:
    template = session.get(TemplateORM, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found.")
    return template


def read_manifest(template: TemplateORM, storage: LocalFileStorage) -> TemplateManifest:
    payload = storage.read_json(template.manifest_path)
    if not payload:
        raise HTTPException(status_code=409, detail="Analyze and save the template manifest first.")
    return TemplateManifest.model_validate(payload)


def serialize_template(template: TemplateORM, storage: LocalFileStorage) -> TemplateRecord:
    manifest_payload = storage.read_json(template.manifest_path)
    analysis_payload = storage.read_json(template.analysis_path)
    return TemplateRecord(
        id=template.id,
        name=template.name,
        original_filename=template.original_filename,
        file_type=template.file_type,
        document_type=template.document_type,
        source_path=template.source_path,
        manifest_path=template.manifest_path,
        analysis_path=template.analysis_path,
        status=template.status,
        created_at=template.created_at,
        updated_at=template.updated_at,
        manifest=TemplateManifest.model_validate(manifest_payload) if manifest_payload else None,
        analysis=analysis_payload,
    )


def safe_output_path(path: str | None) -> Path:
    if not path:
        raise HTTPException(status_code=404, detail="Generated file is not available.")
    target = Path(path)
    if not target.is_file():
        raise HTTPException(status_code=404, detail="Generated file is missing from local storage.")
    return target
