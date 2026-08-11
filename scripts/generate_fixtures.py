from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app.services.fixtures import create_sample_docx, create_sample_xlsx


def main() -> None:
    fixture_dir = ROOT / "fixtures"
    docx_path = create_sample_docx(fixture_dir / "sample_internal_memo.docx")
    xlsx_path = create_sample_xlsx(fixture_dir / "sample_price_comparison.xlsx")
    print(f"Created {docx_path.relative_to(ROOT)}")
    print(f"Created {xlsx_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
