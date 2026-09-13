"""
one rule for every object: the key is the path relative to outputs/.

so outputs/<pipeline_id>/public/audio/1.mp3 is at <pipeline_id>/public/audio/1.mp3,
and outputs/users/<user_id>/profile_picture.png is at users/<user_id>/profile_picture.png.
that keeps the /media route a straight lookup.
"""

from pathlib import Path
from typing import Optional

from core.storage import bucket
from core.utils.config_loader import config


def root() -> Path:
    return Path(str(config.output_directory))


def key_for(local_path: str) -> str:
    return Path(local_path).relative_to(root()).as_posix()


def local_path_for(key: str) -> Path:
    return root() / key


def push_file(local_path: str) -> None:
    """upload a single file the api wrote, so a worker can read it back."""
    if not bucket.enabled():
        return
    bucket.upload(local_path, key_for(local_path))


def url_for(relative_path: str, filename: Optional[str] = None) -> Optional[str]:
    if not bucket.enabled():
        return None
    return bucket.signed_url(relative_path, filename=filename)
