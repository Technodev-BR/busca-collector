from __future__ import annotations

from collector.core.settings import Settings
from collector.storage.local import LocalStorage
from collector.storage.s3 import S3Storage
from collector.storage.storage import Storage


def configure_storage(settings: Settings) -> Storage:
    if not settings.s3_enabled:
        return LocalStorage(root_path=settings.data_dir)

    import boto3
    from botocore.config import Config

    # Endpoint custom (MinIO/LocalStack) exige path-style addressing.
    config = Config(s3={"addressing_style": "path"}) if settings.s3_endpoint_url else None
    client = boto3.client(
        "s3",
        region_name=settings.s3_region,
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        config=config,
    )
    return S3Storage(client=client, bucket=settings.s3_bucket or "")


__all__ = ["LocalStorage", "S3Storage", "Storage", "configure_storage"]
