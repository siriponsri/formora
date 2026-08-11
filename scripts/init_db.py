from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app.config import get_settings
from app.db import init_db

if __name__ == "__main__":
    settings = get_settings()
    settings.ensure_directories()
    init_db()
    print(f"SQLite ready at {settings.sqlite_url}")
