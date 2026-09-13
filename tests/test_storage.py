"""
the sync is what lets the api and the worker run on different machines,
so it gets a round trip against an in-memory s3.
"""

import os
import shutil
from pathlib import Path

import boto3
import pytest
from moto import mock_aws


@pytest.fixture
def pipeline_directory(tmp_path, monkeypatch):
    """a configured bucket, an empty outputs/, and the modules pointed at both."""
    for name, value in {
        "R2_ACCOUNT_ID": "account", "R2_BUCKET": "test-bucket",
        "R2_ACCESS_KEY_ID": "key", "R2_SECRET_ACCESS_KEY": "secret",
        "AWS_ACCESS_KEY_ID": "key", "AWS_SECRET_ACCESS_KEY": "secret",
        "AWS_DEFAULT_REGION": "us-east-1",
    }.items():
        monkeypatch.setenv(name, value)

    with mock_aws():
        from core.storage import bucket
        from core.utils.config_loader import config

        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket="test-bucket")

        monkeypatch.setattr(config, "output_directory", tmp_path)
        monkeypatch.setattr(config, "r2_bucket", "test-bucket")
        monkeypatch.setattr(config, "r2_access_key_id", "key")
        monkeypatch.setattr(config, "r2_secret_access_key", "secret")
        monkeypatch.setattr(bucket, "_client", client)
        yield tmp_path


def _write(path: Path, contents: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents)


def test_push_skips_node_modules_and_repeats_cheaply(pipeline_directory):
    from core.storage import pipeline_files

    _write(pipeline_directory / "pipe1" / "public" / "sources" / "doc.pdf", "pdf")
    _write(pipeline_directory / "pipe1" / "public" / "audio.mp3", "audio")
    _write(pipeline_directory / "pipe1" / "node_modules" / "junk" / "big.js", "x" * 5000)

    assert pipeline_files.push("pipe1") == 2
    assert pipeline_files.push("pipe1") == 0


def test_another_machine_can_restore_the_directory(pipeline_directory):
    from core.storage import pipeline_files

    _write(pipeline_directory / "pipe1" / "public" / "sources" / "doc.pdf", "pdf")
    pipeline_files.push("pipe1")

    shutil.rmtree(pipeline_directory / "pipe1")
    assert pipeline_files.pull("pipe1") == 1
    assert (pipeline_directory / "pipe1" / "public" / "sources" / "doc.pdf").read_text() == "pdf"
    assert pipeline_files.pull("pipe1") == 0


def test_signed_url_points_at_the_file_and_is_none_when_absent(pipeline_directory):
    from core.storage import media, pipeline_files

    video = pipeline_directory / "pipe1" / "result" / "video.mp4"
    _write(video, "mp4")
    pipeline_files.push("pipe1")

    assert "pipe1/result/video.mp4" in pipeline_files.url_for(str(video))
    assert media.url_for("pipe1/missing.mp4") is None


def test_remove_clears_the_prefix(pipeline_directory):
    from core.storage import bucket, pipeline_files

    _write(pipeline_directory / "pipe1" / "a.txt", "a")
    _write(pipeline_directory / "pipe1" / "b.txt", "b")
    pipeline_files.push("pipe1")

    assert pipeline_files.remove("pipe1") == 2
    assert bucket.remote_sizes("pipe1/") == {}


def test_everything_no_ops_without_credentials(pipeline_directory, monkeypatch):
    from core.storage import bucket, pipeline_files
    from core.utils.config_loader import config

    _write(pipeline_directory / "pipe1" / "a.txt", "a")
    monkeypatch.setattr(config, "r2_bucket", None)

    assert not bucket.enabled()
    assert pipeline_files.push("pipe1") == 0
    assert pipeline_files.pull("pipe1") == 0
    assert pipeline_files.remove("pipe1") == 0
