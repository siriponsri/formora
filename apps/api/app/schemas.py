from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FileType(StrEnum):
    DOCX = "docx"
    XLSX = "xlsx"


class BindingStrategy(StrEnum):
    PLACEHOLDER = "placeholder"
    CELL = "cell"


class TemplateBinding(BaseModel):
    strategy: BindingStrategy
    placeholder: str | None = None
    cell: str | None = None
    sheet: str | None = None

    @model_validator(mode="after")
    def validate_strategy_payload(self) -> TemplateBinding:
        if self.strategy == BindingStrategy.PLACEHOLDER and not self.placeholder:
            raise ValueError("placeholder binding requires a placeholder value")
        if self.strategy == BindingStrategy.CELL and not self.cell:
            raise ValueError("cell binding requires a cell coordinate")
        return self


class TemplateField(BaseModel):
    id: str = Field(min_length=1, pattern=r"^[a-zA-Z][a-zA-Z0-9_\-]*$")
    label: str = Field(min_length=1)
    required: bool = True
    content_type: str = "text"
    binding: TemplateBinding


class TemplateManifest(BaseModel):
    template_id: str
    name: str = Field(min_length=1)
    file_type: FileType
    original_file: str
    document_type: str = "generic_document"
    fields: list[TemplateField] = Field(default_factory=list)


class TemplateRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    original_filename: str
    file_type: FileType
    document_type: str
    source_path: str
    manifest_path: str | None = None
    analysis_path: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime
    manifest: TemplateManifest | None = None
    analysis: dict[str, Any] | None = None


class GenerationRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    template_id: str
    prompt: str
    semantic_content: dict[str, Any]
    output_path: str | None = None
    preview_path: str | None = None
    preview_status: str | None = None
    status: str
    created_at: datetime


class DraftRequest(BaseModel):
    template_id: str
    prompt: str = Field(min_length=1, max_length=10_000)


class DraftResult(BaseModel):
    generation_id: str
    template_id: str
    content: dict[str, Any]
    warnings: list[str] = Field(default_factory=list)


class RenderRequest(BaseModel):
    template_id: str
    content: dict[str, Any]
    prompt: str = ""
    generation_id: str | None = None


class RenderResult(BaseModel):
    generation_id: str
    template_id: str
    status: str
    file_type: FileType
    download_url: str
    preview_url: str | None = None
    preview_status: str | None = None
    warnings: list[str] = Field(default_factory=list)


class ValidationIssue(BaseModel):
    field_id: str | None = None
    level: str = "warning"
    message: str


class ConfigStatus(BaseModel):
    app_env: str
    ai_provider: str
    typhoon_configured: bool
    libreoffice_available: bool
    data_directory_writable: bool
    max_upload_mb: int
    text_model: str
    ocr_model: str
