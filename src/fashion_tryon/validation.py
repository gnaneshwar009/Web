from __future__ import annotations

from pathlib import Path

from fastapi import UploadFile

SUPPORTED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def validate_image_filename(filename: str | None) -> str:
    suffix = Path(filename or "image.jpg").suffix.lower() or ".jpg"
    if suffix not in SUPPORTED_IMAGE_SUFFIXES:
        raise ValueError(f"Unsupported image type '{suffix}'. Use jpg, jpeg, png, or webp.")
    return suffix


def validate_prompt(prompt: str) -> str:
    normalized = " ".join(prompt.strip().split())
    if len(normalized) < 6:
        raise ValueError("Prompt is too short. Describe colour, garment type, and design details.")
    if len(normalized) > 900:
        raise ValueError("Prompt is too long. Keep the outfit description under 900 characters.")
    return normalized


async def read_limited_upload(file: UploadFile, max_mb: int) -> bytes:
    content = await file.read()
    max_bytes = max_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise ValueError(f"Upload is too large. Maximum size is {max_mb} MB.")
    return content
