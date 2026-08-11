from __future__ import annotations

from typing import Any, Protocol

from app.schemas import TemplateManifest


class AIProvider(Protocol):
    async def infer_template_schema(
        self,
        *,
        template_id: str,
        name: str,
        file_type: str,
        original_file: str,
        document_map: dict[str, Any],
    ) -> TemplateManifest: ...

    async def draft_document(self, *, prompt: str, schema: TemplateManifest) -> dict[str, Any]: ...

    async def review_document(
        self, *, content: dict[str, Any], schema: TemplateManifest
    ) -> list[str]: ...
