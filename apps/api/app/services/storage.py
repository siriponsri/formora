from __future__ import annotations

import json
import re
import shutil
import zipfile
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.config import Settings
from app.schemas import FileType

SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._\- ]+")


class LocalFileStorage:
    def __init__(self, settings: Settings):
        self.settings = settings
        settings.ensure_directories()

    @staticmethod
    def display_name(filename: str | None) -> str:
        cleaned = SAFE_NAME_RE.sub("_", Path(filename or "template").name).strip(" .")
        return cleaned[:180] or "template"

    @staticmethod
    def detect_file_type(filename: str | None) -> FileType:
        suffix = Path(filename or "").suffix.lower()
        if suffix == ".docx":
            return FileType.DOCX
        if suffix == ".xlsx":
            return FileType.XLSX
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only macro-free .docx and .xlsx templates are supported in POC v0.1.",
        )

    @staticmethod
    def validate_office_zip(path: Path, file_type: FileType) -> None:
        try:
            with zipfile.ZipFile(path) as package:
                names = set(package.namelist())
                required = "word/document.xml" if file_type == FileType.DOCX else "xl/workbook.xml"
                if required not in names:
                    raise ValueError(f"missing {required}")
                if any(name.startswith("../") or "/../" in name for name in names):
                    raise ValueError("unsafe ZIP path")
        except (zipfile.BadZipFile, ValueError) as exc:
            path.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail=f"Invalid Office file: {exc}") from exc

    async def save_upload(self, uploaded: UploadFile) -> tuple[str, str, FileType, Path]:
        file_type = self.detect_file_type(uploaded.filename)
        display_name = self.display_name(uploaded.filename)
        upload_id = str(uuid4())
        upload_path = self.settings.uploads_dir / f"{upload_id}.{file_type.value}"
        limit = self.settings.max_upload_mb * 1024 * 1024
        written = 0
        with upload_path.open("wb") as handle:
            while chunk := await uploaded.read(1024 * 1024):
                written += len(chunk)
                if written > limit:
                    handle.close()
                    upload_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=413, detail="Template exceeds upload size limit."
                    )
                handle.write(chunk)
        self.validate_office_zip(upload_path, file_type)

        template_id = str(uuid4())
        template_dir = self.settings.templates_dir / template_id
        template_dir.mkdir(parents=True, exist_ok=False)
        original_path = template_dir / f"original.{file_type.value}"
        shutil.copy2(upload_path, original_path)
        return template_id, display_name, file_type, original_path

    @staticmethod
    def write_json(path: Path, payload: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def read_json(path: str | Path | None) -> dict | None:
        if not path:
            return None
        target = Path(path)
        if not target.is_file():
            return None
        return json.loads(target.read_text(encoding="utf-8"))
