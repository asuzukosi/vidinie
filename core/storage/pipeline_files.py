"""
sync a pipeline's working directory between the local disk and r2.

remotion renders from real files, so the local directory stays the place work
happens. r2 is what makes that directory survive a machine, so any worker can
pick up a pipeline that another machine started.
"""

import os
from pathlib import Path
from typing import List, Optional

from core.storage import bucket, media
from core.utils.logger import get_logger

logger = get_logger("storage.pipeline_files")

# copied into every pipeline directory from _base/, or rebuilt on demand
SKIP_DIRECTORIES = {"node_modules", "__pycache__", ".git", ".next"}


def _prefix(pipeline_id: str) -> str:
    return f"{pipeline_id}/"


def _local_directory(pipeline_id: str) -> Path:
    return media.root() / pipeline_id


def _local_files(root: Path) -> List[Path]:
    files = []
    for directory, subdirectories, filenames in os.walk(root):
        subdirectories[:] = [d for d in subdirectories if d not in SKIP_DIRECTORIES]
        files.extend(Path(directory) / name for name in filenames)
    return files


def push(pipeline_id: str) -> int:
    """upload anything r2 does not already hold at the same size."""
    if not bucket.enabled():
        return 0

    root = _local_directory(pipeline_id)
    if not root.exists():
        return 0

    already_there = bucket.remote_sizes(_prefix(pipeline_id))
    uploaded = 0
    for path in _local_files(root):
        key = media.key_for(str(path))
        if already_there.get(key) == path.stat().st_size:
            continue
        bucket.upload(str(path), key)
        uploaded += 1

    logger.info(f"pushed {uploaded} files for pipeline {pipeline_id}")
    return uploaded


def pull(pipeline_id: str) -> int:
    """download anything missing locally or a different size."""
    if not bucket.enabled():
        return 0

    root = _local_directory(pipeline_id)
    prefix = _prefix(pipeline_id)
    downloaded = 0
    for key, size in bucket.remote_sizes(prefix).items():
        path = root / key[len(prefix):]
        if path.exists() and path.stat().st_size == size:
            continue
        bucket.download(key, str(path))
        downloaded += 1

    logger.info(f"pulled {downloaded} files for pipeline {pipeline_id}")
    return downloaded


def remove(pipeline_id: str) -> int:
    if not bucket.enabled():
        return 0
    return bucket.delete(_prefix(pipeline_id))


def url_for(local_path: str, filename: Optional[str] = None) -> Optional[str]:
    """signed url for a file the pipeline produced."""
    return media.url_for(media.key_for(local_path), filename=filename)
