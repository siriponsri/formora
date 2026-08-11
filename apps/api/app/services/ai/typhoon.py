from __future__ import annotations

import json
import re
from typing import Any

from openai import APIError, APITimeoutError, AsyncOpenAI
from pydantic import TypeAdapter, ValidationError

from app.config import Settings
from app.schemas import TemplateManifest

JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)
CONTENT_ADAPTER = TypeAdapter(dict[str, Any])


class AIProviderError(RuntimeError):
    pass


def parse_json_object(raw: str) -> dict[str, Any]:
    candidate = raw.strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?\s*", "", candidate, flags=re.IGNORECASE)
        candidate = re.sub(r"\s*```$", "", candidate)
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        match = JSON_OBJECT_RE.search(candidate)
        if not match:
            raise AIProviderError("The model response did not contain a JSON object.") from None
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise AIProviderError("The model returned malformed JSON.") from exc
    try:
        return CONTENT_ADAPTER.validate_python(parsed)
    except ValidationError as exc:
        raise AIProviderError("The model returned an invalid structured object.") from exc


class TyphoonAIProvider:
    def __init__(self, settings: Settings):
        if not settings.typhoon_api_key:
            raise AIProviderError(
                "AI_PROVIDER=typhoon requires TYPHOON_API_KEY. Use mock mode for offline work."
            )
        self.settings = settings
        self.client = AsyncOpenAI(
            api_key=settings.typhoon_api_key,
            base_url=settings.typhoon_base_url,
            timeout=45.0,
            max_retries=1,
        )

    async def _json_completion(self, system: str, user: str) -> dict[str, Any]:
        try:
            response = await self.client.chat.completions.create(
                model=self.settings.typhoon_text_model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.1,
                max_tokens=2500,
            )
        except (APITimeoutError, APIError) as exc:
            raise AIProviderError(
                "Typhoon request failed safely; no document was modified."
            ) from exc
        content = response.choices[0].message.content if response.choices else None
        if not content:
            raise AIProviderError("Typhoon returned an empty response.")
        return parse_json_object(content)

    async def infer_template_schema(
        self,
        *,
        template_id: str,
        name: str,
        file_type: str,
        original_file: str,
        document_map: dict[str, Any],
    ) -> TemplateManifest:
        payload = await self._json_completion(
            "You infer semantic fields from Office document maps. Return JSON only. "
            "Never invent a binding location that is absent from the map.",
            json.dumps(
                {
                    "task": "Create a TemplateManifest using placeholder bindings for DOCX or "
                    "explicit cell bindings for XLSX only when evidence is clear.",
                    "required_identity": {
                        "template_id": template_id,
                        "name": name,
                        "file_type": file_type,
                        "original_file": original_file,
                    },
                    "document_map": document_map,
                },
                ensure_ascii=False,
            ),
        )
        try:
            manifest = TemplateManifest.model_validate(payload)
        except ValidationError as exc:
            raise AIProviderError("Typhoon manifest failed validation.") from exc
        if manifest.template_id != template_id or manifest.file_type.value != file_type:
            raise AIProviderError("Typhoon changed locked template identity fields.")
        return manifest

    async def draft_document(self, *, prompt: str, schema: TemplateManifest) -> dict[str, Any]:
        payload = await self._json_completion(
            "You draft concise, professional Thai organizational documents. Return JSON only, "
            "with exactly the requested field IDs. Do not provide legal approval claims.",
            json.dumps(
                {
                    "request": prompt,
                    "fields": [
                        {
                            "id": field.id,
                            "label": field.label,
                            "required": field.required,
                            "content_type": field.content_type,
                        }
                        for field in schema.fields
                    ],
                },
                ensure_ascii=False,
            ),
        )
        allowed = {field.id for field in schema.fields}
        return {key: value for key, value in payload.items() if key in allowed}

    async def review_document(
        self, *, content: dict[str, Any], schema: TemplateManifest
    ) -> list[str]:
        return [
            f"Required field '{field.label}' is empty."
            for field in schema.fields
            if field.required and not content.get(field.id)
        ]
