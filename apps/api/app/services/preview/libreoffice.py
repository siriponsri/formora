from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.config import Settings

WINDOWS_CANDIDATES = (
    Path("C:/Program Files/LibreOffice/program/soffice.exe"),
    Path("C:/Program Files (x86)/LibreOffice/program/soffice.exe"),
)


@dataclass(slots=True)
class PreviewResult:
    available: bool
    status: str
    path: Path | None = None


def find_libreoffice(settings: Settings) -> Path | None:
    if settings.libreoffice_path:
        configured = Path(settings.libreoffice_path).expanduser()
        if configured.is_file():
            return configured
    discovered = shutil.which("soffice") or shutil.which("libreoffice")
    if discovered:
        return Path(discovered)
    return next((path for path in WINDOWS_CANDIDATES if path.is_file()), None)


def convert_to_pdf(
    source: str | Path, output_dir: str | Path, settings: Settings, timeout: int = 45
) -> PreviewResult:
    executable = find_libreoffice(settings)
    if not executable:
        return PreviewResult(False, "PDF preview unavailable; LibreOffice was not found.")
    source_path = Path(source)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    expected = destination / f"{source_path.stem}.pdf"
    try:
        completed = subprocess.run(
            [
                str(executable),
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(destination),
                str(source_path),
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return PreviewResult(True, f"PDF preview conversion failed safely: {type(exc).__name__}")
    if completed.returncode != 0 or not expected.is_file():
        return PreviewResult(True, "PDF preview conversion did not produce a file.")
    return PreviewResult(True, "PDF preview created.", expected)
