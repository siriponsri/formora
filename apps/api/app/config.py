from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(REPOSITORY_ROOT / ".env")


def _resolve_path(raw: str, default: str) -> Path:
    value = Path(raw or default).expanduser()
    if not value.is_absolute():
        value = REPOSITORY_ROOT / value
    return value.resolve()


@dataclass(frozen=True, slots=True)
class Settings:
    app_env: str
    ai_provider: str
    typhoon_api_key: str
    typhoon_base_url: str
    typhoon_text_model: str
    typhoon_ocr_model: str
    data_dir: Path
    database_url: str
    libreoffice_path: str
    max_upload_mb: int

    @property
    def templates_dir(self) -> Path:
        return self.data_dir / "templates"

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def generated_dir(self) -> Path:
        return self.data_dir / "generated"

    @property
    def previews_dir(self) -> Path:
        return self.data_dir / "previews"

    @property
    def sqlite_url(self) -> str:
        configured = self.database_url.strip()
        if configured and configured != "sqlite:///./data/app.db":
            return configured
        return f"sqlite:///{(self.data_dir / 'app.db').as_posix()}"

    def ensure_directories(self) -> None:
        for path in (
            self.data_dir,
            self.templates_dir,
            self.uploads_dir,
            self.generated_dir,
            self.previews_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    provider = os.getenv("AI_PROVIDER", "mock").strip().lower()
    if provider not in {"mock", "typhoon"}:
        provider = "mock"
    return Settings(
        app_env=os.getenv("APP_ENV", "development"),
        ai_provider=provider,
        typhoon_api_key=os.getenv("TYPHOON_API_KEY", ""),
        typhoon_base_url=os.getenv("TYPHOON_BASE_URL", "https://api.opentyphoon.ai/v1"),
        typhoon_text_model=os.getenv("TYPHOON_TEXT_MODEL", "typhoon-v2.5-30b-a3b-instruct"),
        typhoon_ocr_model=os.getenv("TYPHOON_OCR_MODEL", "typhoon-ocr"),
        data_dir=_resolve_path(os.getenv("DATA_DIR", "./data"), "./data"),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./data/app.db"),
        libreoffice_path=os.getenv("LIBREOFFICE_PATH", ""),
        max_upload_mb=max(1, int(os.getenv("MAX_UPLOAD_MB", "20"))),
    )
