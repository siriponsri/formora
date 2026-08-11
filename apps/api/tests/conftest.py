from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

TEST_DATA_DIR = Path(tempfile.mkdtemp(prefix="formora-tests-"))
os.environ["APP_ENV"] = "test"
os.environ["AI_PROVIDER"] = "mock"
os.environ["DATA_DIR"] = str(TEST_DATA_DIR)
os.environ["DATABASE_URL"] = ""

from app.config import get_settings  # noqa: E402
from app.db import init_db  # noqa: E402
from app.services.fixtures import create_sample_docx, create_sample_xlsx  # noqa: E402

get_settings.cache_clear()
init_db()


@pytest.fixture
def docx_fixture(tmp_path: Path) -> Path:
    return create_sample_docx(tmp_path / "memo.docx")


@pytest.fixture
def xlsx_fixture(tmp_path: Path) -> Path:
    return create_sample_xlsx(tmp_path / "comparison.xlsx")
