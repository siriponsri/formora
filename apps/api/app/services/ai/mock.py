from __future__ import annotations

import json
import re
from typing import Any

from app.schemas import (
    BindingStrategy,
    FileType,
    TemplateBinding,
    TemplateField,
    TemplateManifest,
)

PLACEHOLDER_RE = re.compile(r"\{\{\s*([a-zA-Z][a-zA-Z0-9_\-]*)\s*\}\}")
THAI_LABELS = {
    "subject": "เรื่อง",
    "recipient": "เรียน",
    "body": "เนื้อหา",
    "signer_name": "ชื่อผู้ลงนาม",
    "signer_title": "ตำแหน่งผู้ลงนาม",
    "project_name": "ชื่อโครงการ",
    "vendor_a_price": "ราคาผู้เสนอ A",
    "vendor_b_price": "ราคาผู้เสนอ B",
    "vendor_c_price": "ราคาผู้เสนอ C",
}


class MockAIProvider:
    async def infer_template_schema(
        self,
        *,
        template_id: str,
        name: str,
        file_type: str,
        original_file: str,
        document_map: dict[str, Any],
    ) -> TemplateManifest:
        fields: list[TemplateField] = []
        if file_type == FileType.DOCX:
            serialized = json.dumps(document_map, ensure_ascii=False)
            seen: set[str] = set()
            for field_id in PLACEHOLDER_RE.findall(serialized):
                if field_id in seen:
                    continue
                seen.add(field_id)
                fields.append(
                    TemplateField(
                        id=field_id,
                        label=THAI_LABELS.get(field_id, field_id.replace("_", " ").title()),
                        required=True,
                        content_type="rich_text" if field_id == "body" else "short_text",
                        binding=TemplateBinding(
                            strategy=BindingStrategy.PLACEHOLDER,
                            placeholder=f"{{{{{field_id}}}}}",
                        ),
                    )
                )
        return TemplateManifest(
            template_id=template_id,
            name=PathLikeName.without_suffix(name),
            file_type=FileType(file_type),
            original_file=original_file,
            document_type="internal_memo" if "memo" in name.lower() else "generic_document",
            fields=fields,
        )

    async def draft_document(self, *, prompt: str, schema: TemplateManifest) -> dict[str, Any]:
        samples = {
            "subject": "ขออนุมัติดำเนินการตามรายละเอียดที่เสนอ",
            "recipient": "ผู้อำนวยการ",
            "body": (
                "ตามที่หน่วยงานมีความจำเป็นต้องดำเนินการเพื่อสนับสนุนการปฏิบัติงาน "
                f"โดยมีรายละเอียดจากคำขอว่า “{prompt.strip()}”\n\n"
                "จึงเรียนมาเพื่อโปรดพิจารณาอนุมัติ ทั้งนี้ ผู้จัดทำจะตรวจสอบรายละเอียด "
                "งบประมาณ และข้อกำหนดที่เกี่ยวข้องก่อนนำไปใช้เป็นเอกสารทางการ"
            ),
            "signer_name": "ผู้จัดทำเอกสาร",
            "signer_title": "ตำแหน่ง",
            "project_name": prompt.strip()[:120] or "โครงการตัวอย่าง",
            "vendor_a_price": 45000,
            "vendor_b_price": 46500,
            "vendor_c_price": 47200,
        }
        return {
            field.id: samples.get(field.id, f"ข้อมูลตัวอย่างสำหรับ {field.label}")
            for field in schema.fields
        }

    async def review_document(
        self, *, content: dict[str, Any], schema: TemplateManifest
    ) -> list[str]:
        return [
            f"กรุณาตรวจสอบข้อมูลในช่อง “{field.label}”"
            for field in schema.fields
            if field.required and not content.get(field.id)
        ]


class PathLikeName:
    @staticmethod
    def without_suffix(name: str) -> str:
        return name.rsplit(".", 1)[0].replace("_", " ").strip() or "Untitled template"
