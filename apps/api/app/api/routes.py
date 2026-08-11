from __future__ import annotations

import json
import os
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_template_or_404,
    read_manifest,
    safe_output_path,
    serialize_template,
)
from app.config import get_settings
from app.db import GenerationORM, TemplateORM, get_db, utc_now
from app.schemas import (
    ConfigStatus,
    DraftRequest,
    DraftResult,
    FileType,
    GenerationRecord,
    RenderRequest,
    RenderResult,
    TemplateManifest,
    TemplateRecord,
)
from app.services.ai import build_ai_provider
from app.services.ai.typhoon import AIProviderError
from app.services.docx.inspect import inspect_docx
from app.services.docx.render import render_docx
from app.services.preview.libreoffice import convert_to_pdf, find_libreoffice
from app.services.storage import LocalFileStorage
from app.services.xlsx.inspect import inspect_xlsx
from app.services.xlsx.render import render_xlsx

router = APIRouter(prefix="/api")


def _storage() -> LocalFileStorage:
    return LocalFileStorage(get_settings())


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "formora-api", "version": "0.1.0"}


@router.get("/config/status", response_model=ConfigStatus)
def config_status() -> ConfigStatus:
    settings = get_settings()
    settings.ensure_directories()
    return ConfigStatus(
        app_env=settings.app_env,
        ai_provider=settings.ai_provider,
        typhoon_configured=bool(settings.typhoon_api_key),
        libreoffice_available=find_libreoffice(settings) is not None,
        data_directory_writable=os.access(settings.data_dir, os.W_OK),
        max_upload_mb=settings.max_upload_mb,
        text_model=settings.typhoon_text_model,
        ocr_model=settings.typhoon_ocr_model,
    )


@router.post("/templates/upload", response_model=TemplateRecord, status_code=201)
async def upload_template(
    file: UploadFile = File(...),
    name: str | None = Form(default=None),
    session: Session = Depends(get_db),
) -> TemplateRecord:
    storage = _storage()
    template_id, display_name, file_type, original_path = await storage.save_upload(file)
    now = utc_now()
    record = TemplateORM(
        id=template_id,
        name=(name or Path(display_name).stem).strip() or "Untitled template",
        original_filename=display_name,
        file_type=file_type.value,
        document_type="unknown",
        source_path=str(original_path),
        status="uploaded",
        created_at=now,
        updated_at=now,
    )
    session.add(record)
    session.commit()
    return serialize_template(record, storage)


@router.post("/templates/{template_id}/analyze", response_model=TemplateRecord)
async def analyze_template(
    template_id: str,
    session: Session = Depends(get_db),
) -> TemplateRecord:
    storage = _storage()
    record = get_template_or_404(session, template_id)
    source = Path(record.source_path)
    document_map = inspect_docx(source) if record.file_type == "docx" else inspect_xlsx(source)
    try:
        provider = build_ai_provider(get_settings())
        manifest = await provider.infer_template_schema(
            template_id=record.id,
            name=record.name,
            file_type=record.file_type,
            original_file=source.name,
            document_map=document_map,
        )
    except AIProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    template_dir = source.parent
    analysis_path = template_dir / "analysis.json"
    manifest_path = template_dir / "manifest.json"
    storage.write_json(analysis_path, document_map)
    storage.write_json(manifest_path, manifest.model_dump(mode="json"))
    record.analysis_path = str(analysis_path)
    record.manifest_path = str(manifest_path)
    record.document_type = manifest.document_type
    record.status = "analyzed" if manifest.fields else "needs_review"
    record.updated_at = utc_now()
    session.commit()
    return serialize_template(record, storage)


@router.get("/templates", response_model=list[TemplateRecord])
def list_templates(session: Session = Depends(get_db)) -> list[TemplateRecord]:
    storage = _storage()
    records = session.scalars(select(TemplateORM).order_by(TemplateORM.created_at.desc())).all()
    return [serialize_template(record, storage) for record in records]


@router.get("/templates/{template_id}", response_model=TemplateRecord)
def get_template(template_id: str, session: Session = Depends(get_db)) -> TemplateRecord:
    return serialize_template(get_template_or_404(session, template_id), _storage())


@router.put("/templates/{template_id}/manifest", response_model=TemplateRecord)
def save_manifest(
    template_id: str,
    manifest: TemplateManifest,
    session: Session = Depends(get_db),
) -> TemplateRecord:
    storage = _storage()
    record = get_template_or_404(session, template_id)
    if manifest.template_id != template_id:
        raise HTTPException(status_code=422, detail="Manifest template_id cannot be changed.")
    if manifest.file_type.value != record.file_type:
        raise HTTPException(status_code=422, detail="Manifest file_type cannot be changed.")
    manifest.original_file = Path(record.source_path).name
    manifest_path = Path(record.source_path).parent / "manifest.json"
    storage.write_json(manifest_path, manifest.model_dump(mode="json"))
    record.manifest_path = str(manifest_path)
    record.name = manifest.name
    record.document_type = manifest.document_type
    record.status = "ready" if manifest.fields else "needs_review"
    record.updated_at = utc_now()
    session.commit()
    return serialize_template(record, storage)


@router.post("/generations/draft", response_model=DraftResult)
async def draft_generation(
    request: DraftRequest,
    session: Session = Depends(get_db),
) -> DraftResult:
    record = get_template_or_404(session, request.template_id)
    manifest = read_manifest(record, _storage())
    try:
        provider = build_ai_provider(get_settings())
        content = await provider.draft_document(prompt=request.prompt, schema=manifest)
        warnings = await provider.review_document(content=content, schema=manifest)
    except AIProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    generation_id = str(uuid4())
    generation = GenerationORM(
        id=generation_id,
        template_id=record.id,
        prompt=request.prompt,
        semantic_json=json.dumps(content, ensure_ascii=False),
        status="drafted",
    )
    session.add(generation)
    session.commit()
    return DraftResult(
        generation_id=generation_id,
        template_id=record.id,
        content=content,
        warnings=warnings,
    )


@router.post("/generations/render", response_model=RenderResult)
def render_generation(
    request: RenderRequest,
    session: Session = Depends(get_db),
) -> RenderResult:
    settings = get_settings()
    storage = _storage()
    template = get_template_or_404(session, request.template_id)
    manifest = read_manifest(template, storage)
    generation_id = request.generation_id or str(uuid4())
    generation = session.get(GenerationORM, generation_id)
    if generation and generation.template_id != template.id:
        raise HTTPException(status_code=409, detail="Generation belongs to another template.")
    if not generation:
        generation = GenerationORM(
            id=generation_id,
            template_id=template.id,
            prompt=request.prompt,
            semantic_json="{}",
            status="drafted",
        )
        session.add(generation)

    output_path = settings.generated_dir / f"{generation_id}.{template.file_type}"
    if template.file_type == FileType.DOCX:
        warnings = render_docx(template.source_path, output_path, manifest, request.content)
    else:
        warnings = render_xlsx(template.source_path, output_path, manifest, request.content)

    preview = convert_to_pdf(output_path, settings.previews_dir, settings)
    generation.prompt = request.prompt or generation.prompt
    generation.semantic_json = json.dumps(request.content, ensure_ascii=False)
    generation.output_path = str(output_path)
    generation.preview_path = str(preview.path) if preview.path else None
    generation.preview_status = preview.status
    generation.status = "rendered"
    session.commit()

    return RenderResult(
        generation_id=generation_id,
        template_id=template.id,
        status="rendered",
        file_type=FileType(template.file_type),
        download_url=f"/api/files/{generation_id}",
        preview_url=f"/api/files/{generation_id}?kind=preview" if preview.path else None,
        preview_status=preview.status,
        warnings=warnings,
    )


@router.get("/generations/{generation_id}", response_model=GenerationRecord)
def get_generation(generation_id: str, session: Session = Depends(get_db)) -> GenerationRecord:
    generation = session.get(GenerationORM, generation_id)
    if not generation:
        raise HTTPException(status_code=404, detail="Generation not found.")
    return GenerationRecord.model_validate(generation)


@router.get("/files/{generation_id}")
def download_file(
    generation_id: str,
    kind: str = "output",
    session: Session = Depends(get_db),
) -> FileResponse:
    generation = session.get(GenerationORM, generation_id)
    if not generation:
        raise HTTPException(status_code=404, detail="Generation not found.")
    path = safe_output_path(
        generation.preview_path if kind == "preview" else generation.output_path
    )
    media_type = (
        "application/pdf"
        if path.suffix.lower() == ".pdf"
        else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if path.suffix.lower() == ".docx"
        else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    return FileResponse(
        path, media_type=media_type, filename=f"formora-{generation_id}{path.suffix}"
    )
