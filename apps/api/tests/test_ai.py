from __future__ import annotations

import pytest

from app.services.ai.typhoon import AIProviderError, parse_json_object


def test_json_parser_accepts_fenced_object() -> None:
    assert parse_json_object('```json\n{"subject": "ทดสอบ"}\n```') == {"subject": "ทดสอบ"}


def test_json_parser_rejects_malformed_output() -> None:
    with pytest.raises(AIProviderError):
        parse_json_object("This is not structured JSON")
