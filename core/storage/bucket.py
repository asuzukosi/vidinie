"""
r2 object storage, spoken to over the s3 api.
"""

import os
from pathlib import Path
from typing import Dict, Optional

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError

from core.utils.config_loader import config
from core.utils.logger import get_logger

logger = get_logger("storage.bucket")

_client = None


def enabled() -> bool:
    """true when r2 credentials are configured."""
    return bool(config.r2_bucket and config.r2_access_key_id and config.r2_secret_access_key)


def client():
    global _client
    if _client is None:
        _client = boto3.client(
            "s3",
            endpoint_url=config.r2_endpoint,
            aws_access_key_id=config.r2_access_key_id,
            aws_secret_access_key=config.r2_secret_access_key,
            region_name="auto",
            config=BotoConfig(signature_version="s3v4", retries={"max_attempts": 3}),
        )
    return _client


def remote_sizes(prefix: str) -> Dict[str, int]:
    """map of key to byte size for everything under prefix."""
    sizes: Dict[str, int] = {}
    paginator = client().get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=config.r2_bucket, Prefix=prefix):
        for item in page.get("Contents", []):
            sizes[item["Key"]] = item["Size"]
    return sizes


def upload(local_path: str, key: str) -> None:
    client().upload_file(local_path, config.r2_bucket, key)


def download(key: str, local_path: str) -> None:
    Path(local_path).parent.mkdir(parents=True, exist_ok=True)
    client().download_file(config.r2_bucket, key, local_path)


def delete(prefix: str) -> int:
    """delete every object under prefix. returns how many went."""
    keys = list(remote_sizes(prefix))
    for batch_start in range(0, len(keys), 1000):
        batch = keys[batch_start:batch_start + 1000]
        client().delete_objects(
            Bucket=config.r2_bucket,
            Delete={"Objects": [{"Key": key} for key in batch]},
        )
    return len(keys)


def signed_url(key: str, expires_in: int = 3600, filename: Optional[str] = None) -> Optional[str]:
    """time-limited download url, or none if the object is not there."""
    try:
        client().head_object(Bucket=config.r2_bucket, Key=key)
    except ClientError:
        logger.warning(f"no object at {key}")
        return None

    params = {"Bucket": config.r2_bucket, "Key": key}
    if filename:
        params["ResponseContentDisposition"] = f'attachment; filename="{filename}"'
    return client().generate_presigned_url("get_object", Params=params, ExpiresIn=expires_in)
