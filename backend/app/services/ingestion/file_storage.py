from __future__ import annotations

from pathlib import Path
from uuid import uuid4


def generate_document_id() -> str:
    return f"doc_{uuid4().hex[:12]}"


def build_stored_filename(*, document_id: str, original_filename: str) -> str:
    return f"{document_id}_{original_filename}"


def resolve_upload_dir(upload_dir: Path | str) -> Path:
    path = Path(upload_dir)
    if not path.is_absolute():
        backend_root = Path(__file__).resolve().parents[3]
        path = backend_root / path
    return path


def ensure_upload_dir(upload_dir: Path) -> None:
    upload_dir.mkdir(parents=True, exist_ok=True)


def save_upload_file(
    *,
    upload_dir: Path,
    document_id: str,
    original_filename: str,
    content: bytes,
) -> Path:
    ensure_upload_dir(upload_dir)
    stored_name = build_stored_filename(
        document_id=document_id,
        original_filename=original_filename,
    )
    destination = upload_dir / stored_name
    destination.write_bytes(content)
    return destination
