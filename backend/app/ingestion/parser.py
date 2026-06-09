from __future__ import annotations

from pathlib import Path

import fitz


def parse_document(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return parse_pdf(file_path)
    if suffix in {".txt", ".md"}:
        return file_path.read_text(encoding="utf-8")
    raise ValueError(f"Unsupported file type: {suffix}")


def parse_pdf(file_path: Path) -> str:
    document = fitz.open(file_path)
    pages = [page.get_text("text") for page in document]
    document.close()
    return "\n".join(page.strip() for page in pages if page.strip())

