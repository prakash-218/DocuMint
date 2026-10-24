"""
File storage for attachments: a Railway Bucket (S3-compatible) in production,
a local folder otherwise.

Railway bucket variables (reference them on the web and worker services):
    S3_BUCKET=${{Bucket.BUCKET}}  S3_ENDPOINT=${{Bucket.ENDPOINT}}  S3_REGION=${{Bucket.REGION}}
    S3_ACCESS_KEY_ID=${{Bucket.ACCESS_KEY_ID}}  S3_SECRET_ACCESS_KEY=${{Bucket.SECRET_ACCESS_KEY}}
Without S3_BUCKET, files go under STORAGE_DIR (default ./var/storage).
"""

import os
import re
import threading
from pathlib import Path

_local = threading.local()


def _safe_key(key: str) -> str:
    parts = [re.sub(r'[^A-Za-z0-9._-]+', '_', p).strip('.') or '_' for p in key.replace('\\', '/').split('/') if p]
    return '/'.join(parts)


def _s3():
    client = getattr(_local, 'client', None)
    if client is None:
        import boto3
        from botocore.config import Config
        client = _local.client = boto3.client(
            's3', endpoint_url=os.getenv('S3_ENDPOINT') or None, region_name=os.getenv('S3_REGION') or 'auto',
            aws_access_key_id=os.getenv('S3_ACCESS_KEY_ID'), aws_secret_access_key=os.getenv('S3_SECRET_ACCESS_KEY'),
            config=Config(s3={'addressing_style': os.getenv('S3_ADDRESSING_STYLE', 'virtual')},
                          retries={'max_attempts': 3}))
    return client


def using_bucket() -> bool:
    return bool(os.getenv('S3_BUCKET'))


def _root() -> Path:
    return Path(os.getenv('STORAGE_DIR', 'var/storage'))


def put(key: str, data: bytes, content_type: str = 'application/octet-stream') -> str:
    key = _safe_key(key)
    if using_bucket():
        _s3().put_object(Bucket=os.environ['S3_BUCKET'], Key=key, Body=data, ContentType=content_type)
    else:
        path = _root() / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return key


def get(key: str) -> bytes:
    if using_bucket():
        return _s3().get_object(Bucket=os.environ['S3_BUCKET'], Key=key)['Body'].read()
    return (_root() / key).read_bytes()


def delete(key: str):
    try:
        if using_bucket():
            _s3().delete_object(Bucket=os.environ['S3_BUCKET'], Key=key)
        else:
            (_root() / key).unlink(missing_ok=True)
    except Exception:       # a missing file must never block deleting the record
        pass


def check() -> bool:
    """For the health check: can we reach the bucket?"""
    if not using_bucket():
        return _root().exists() or True
    _s3().head_bucket(Bucket=os.environ['S3_BUCKET'])
    return True
