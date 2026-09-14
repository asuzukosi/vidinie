"""
durable storage for the files a pipeline produces.

bucket.py           talks to r2 over the s3 api
media.py            maps a local path under outputs/ to its object key
pipeline_files.py   syncs outputs/<pipeline_id>/ to and from the bucket

with no r2 credentials configured every call is a no-op, so a single-machine
setup keeps working off the local disk alone.
"""

from core.storage import bucket, media
from core.storage.pipeline_files import pull, push, remove, url_for

__all__ = ["bucket", "media", "pull", "push", "remove", "url_for"]
