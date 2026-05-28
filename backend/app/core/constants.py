from typing import FrozenSet

# ---------------------------------------------------------------------------
# Upload size limits
# ---------------------------------------------------------------------------
MAX_UPLOAD_SIZE_BYTES: int = 20 * 1024 * 1024  # 20 MB

# ---------------------------------------------------------------------------
# Allowed MIME types  →  mapped to canonical label for logging/errors
# ---------------------------------------------------------------------------
ALLOWED_MIME_TYPES: dict[str, str] = {
    "application/pdf": "PDF",
    "text/plain": "TXT",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "DOCX",
    "image/png": "PNG",
    "image/jpeg": "JPEG",
}

# ---------------------------------------------------------------------------
# Allowed file extensions (lowercase, with leading dot)
# ---------------------------------------------------------------------------
ALLOWED_EXTENSIONS: FrozenSet[str] = frozenset(
    {".pdf", ".txt", ".docx", ".png", ".jpg", ".jpeg"}
)
