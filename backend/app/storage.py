# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

# backend/app/storage.py
import io
from pathlib import Path
from datetime import timedelta
from composition.settings import settings

LOCAL_BASE = Path("backend/data/attachments")


def init_storage():
    if settings.storage_backend == "local":
        LOCAL_BASE.mkdir(parents=True, exist_ok=True)
    else:
        from minio import Minio
        client = _minio()
        if not client.bucket_exists(settings.minio_bucket):
            client.make_bucket(settings.minio_bucket)


def put_object(object_key: str, data: bytes, content_type: str):
    if settings.storage_backend == "local":
        path = LOCAL_BASE / object_key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    else:
        _minio().put_object(settings.minio_bucket, object_key, io.BytesIO(data), len(data), content_type=content_type)


def get_presigned_url(object_key: str, expires_seconds: int = 3600) -> str:
    if settings.storage_backend == "local":
        return f"/static/attachments/{object_key}"
    return _minio().presigned_get_object(settings.minio_bucket, object_key, expires=timedelta(seconds=expires_seconds))


def delete_object(object_key: str):
    if settings.storage_backend == "local":
        (LOCAL_BASE / object_key).unlink(missing_ok=True)
    else:
        _minio().remove_object(settings.minio_bucket, object_key)


def get_object_bytes(object_key: str) -> bytes:
    """Read an object from storage and return its raw bytes."""
    if settings.storage_backend == "local":
        return (LOCAL_BASE / object_key).read_bytes()

    response = _minio().get_object(settings.minio_bucket, object_key)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()


def _minio():
    from minio import Minio
    return Minio(settings.minio_endpoint, access_key=settings.minio_access_key, secret_key=settings.minio_secret_key, secure=settings.minio_secure)