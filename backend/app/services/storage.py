from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

import aiofiles
from fastapi import UploadFile

from app.core.config import get_settings


async def save_upload(file: UploadFile, subdirectory: str = "uploads") -> tuple[Path, int, str]:
    settings = get_settings()
    base = Path(settings.upload_dir if subdirectory == "uploads" else settings.knowledge_dir)
    base.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "upload.bin").suffix.lower()
    if suffix not in settings.allowed_extensions:
        raise ValueError(f"File type {suffix} not allowed")

    dest_name = f"{uuid.uuid4().hex}{suffix}"
    dest = base / dest_name
    digest = hashlib.sha256()
    size = 0
    async with aiofiles.open(dest, "wb") as out:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > settings.max_upload_bytes:
                dest.unlink(missing_ok=True)
                raise ValueError("File exceeds maximum upload size")
            digest.update(chunk)
            await out.write(chunk)
    return dest, size, digest.hexdigest()
