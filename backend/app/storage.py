# backend/app/storage.py
import io
from pathlib import Path
from datetime import timedelta
from advisor_pipeline.config.settings import settings

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


def _minio():
    from minio import Minio
    return Minio(settings.minio_endpoint, access_key=settings.minio_access_key, secret_key=settings.minio_secret_key, secure=settings.minio_secure)