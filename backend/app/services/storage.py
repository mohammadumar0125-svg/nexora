import hashlib
import os
import re
import uuid
from dataclasses import dataclass
from typing import Optional

from app.core.config import settings
from fastapi import HTTPException, status

ALLOWED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "text/csv": ".csv",
    "text/plain": ".txt",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "application/json": ".json",
}


@dataclass
class StoredObject:
    storage_key: str
    mime_type: str
    size_bytes: int
    sha256: str


def sanitize_filename(filename: str) -> str:
    base = os.path.basename(filename or "attachment")
    cleaned = re.sub(r"[^a-zA-Z0-9._-]", "_", base)
    return cleaned[:160] or "attachment"


def validate_upload(content: bytes, mime_type: str, max_bytes: Optional[int] = None) -> str:
    limit = max_bytes or settings.MAX_UPLOAD_BYTES
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")
    if len(content) > limit:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size ({limit // (1024 * 1024)} MB).",
        )
    normalized_mime = (mime_type or "").split(";")[0].strip().lower()
    if normalized_mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Allowed: PDF, CSV, TXT, PNG, JPG, JSON.",
        )
    # Basic magic-byte sanity verification for PDF / PNG / JPEG
    if normalized_mime == "application/pdf" and not content.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="File signature does not match PDF.")
    if normalized_mime == "image/png" and not content.startswith(b"\x89PNG"):
        raise HTTPException(status_code=400, detail="File signature does not match PNG.")
    if normalized_mime == "image/jpeg" and not content.startswith(b"\xff\xd8"):
        raise HTTPException(status_code=400, detail="File signature does not match JPEG.")

    return ALLOWED_MIME_TYPES[normalized_mime]


class LocalPrivateStorage:
    """Private tenant-partitioned local object store (used in local dev & tests)."""

    def __init__(self, root_dir: Optional[str] = None) -> None:
        self.root_dir = os.path.abspath(root_dir or settings.LOCAL_UPLOAD_DIR)
        os.makedirs(self.root_dir, exist_ok=True)

    def put_object(self, tenant_id: str, content: bytes, mime_type: str) -> StoredObject:
        ext = validate_upload(content, mime_type)
        tenant_dir = os.path.abspath(os.path.join(self.root_dir, str(tenant_id)))
        if not tenant_dir.startswith(self.root_dir + os.sep):
            raise HTTPException(status_code=400, detail="Invalid tenant storage path.")
        os.makedirs(tenant_dir, exist_ok=True)

        obj_name = f"{uuid.uuid4()}{ext}"
        full_path = os.path.abspath(os.path.join(tenant_dir, obj_name))
        if not full_path.startswith(tenant_dir + os.sep):
            raise HTTPException(status_code=400, detail="Invalid object key.")

        with open(full_path, "wb") as fh:
            fh.write(content)

        return StoredObject(
            storage_key=f"local://{tenant_id}/{obj_name}",
            mime_type=(mime_type or "").split(";")[0].strip().lower(),
            size_bytes=len(content),
            sha256=hashlib.sha256(content).hexdigest(),
        )

    def read_object(self, tenant_id: str, storage_key: str) -> bytes:
        prefix = f"local://{tenant_id}/"
        if not storage_key.startswith(prefix):
            raise HTTPException(status_code=403, detail="Cross-tenant file access denied.")
        rel_name = storage_key[len(prefix) :]
        if "/" in rel_name or ".." in rel_name:
            raise HTTPException(status_code=400, detail="Invalid storage key.")
        full_path = os.path.abspath(os.path.join(self.root_dir, str(tenant_id), rel_name))
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="File object not found in private storage.")
        with open(full_path, "rb") as fh:
            return fh.read()


class GCSStorageAdapter:
    """
    Production Google Cloud Storage adapter interface (private bucket IAM + signed access).
    Requires GCS_BUCKET_NAME & google-cloud-storage credentials when STORAGE_BACKEND=gcs.
    """

    def __init__(self, bucket_name: str) -> None:
        self.bucket_name = bucket_name

    def put_object(self, tenant_id: str, content: bytes, mime_type: str) -> StoredObject:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GCS backend selected but Google Cloud Storage client credentials are not configured.",
        )

    def read_object(self, tenant_id: str, storage_key: str) -> bytes:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GCS backend selected but Google Cloud Storage client credentials are not configured.",
        )


def get_storage_provider():
    if settings.STORAGE_BACKEND == "gcs" and settings.GCS_BUCKET_NAME:
        return GCSStorageAdapter(settings.GCS_BUCKET_NAME)
    return LocalPrivateStorage()
