from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def test_health() -> None:
    with TestClient(app) as client:
        response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_docx_golden_flow(docx_fixture: Path) -> None:
    with TestClient(app) as client:
        with docx_fixture.open("rb") as handle:
            upload = client.post(
                "/api/templates/upload",
                files={
                    "file": (
                        "sample_internal_memo.docx",
                        handle,
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    )
                },
            )
        assert upload.status_code == 201, upload.text
        template_id = upload.json()["id"]

        analysis = client.post(f"/api/templates/{template_id}/analyze")
        assert analysis.status_code == 200, analysis.text
        assert {field["id"] for field in analysis.json()["manifest"]["fields"]} >= {
            "subject",
            "body",
        }

        draft = client.post(
            "/api/generations/draft",
            json={
                "template_id": template_id,
                "prompt": "ขออนุมัติจัดซื้อเครื่องสำรองไฟฟ้า 3 kVA จำนวน 1 เครื่อง",
            },
        )
        assert draft.status_code == 200, draft.text

        render = client.post(
            "/api/generations/render",
            json={
                "template_id": template_id,
                "generation_id": draft.json()["generation_id"],
                "prompt": "ขออนุมัติจัดซื้อเครื่องสำรองไฟฟ้า",
                "content": draft.json()["content"],
            },
        )
        assert render.status_code == 200, render.text
        download = client.get(render.json()["download_url"])
        assert download.status_code == 200
        assert download.content.startswith(b"PK")
