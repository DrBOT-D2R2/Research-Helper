from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import re

from fastapi import HTTPException, UploadFile, status

from ..config import settings


ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md"}
SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


async def validate_upload(file: UploadFile) -> bytes:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing filename.")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {suffix}",
        )

    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty files are not allowed.")

    if len(payload) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds the 10 MB MVP upload limit.",
        )

    return payload


def sanitize_filename(filename: str) -> str:
    stem = SAFE_FILENAME_RE.sub("-", Path(filename).stem).strip("-") or "document"
    return f"{stem}{Path(filename).suffix.lower()}"


def compute_checksum(payload: bytes) -> str:
    return sha256(payload).hexdigest()

