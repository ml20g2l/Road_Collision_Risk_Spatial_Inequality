import hashlib
from pathlib import Path

import pytest

import src.download_sources as module
from src.download_sources import Source, download, sha256


def test_sha256_matches_hashlib(tmp_path: Path) -> None:
    path = tmp_path / "sample.txt"
    path.write_bytes(b"road-risk")
    assert sha256(path) == hashlib.sha256(b"road-risk").hexdigest()


def test_download_from_local_uri_is_atomic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source_file = tmp_path / "upstream.csv"
    source_file.write_text("a,b\n1,2\n", encoding="utf-8")
    monkeypatch.setattr(module, "ROOT", tmp_path / "project")
    source = Source("fixture", source_file.as_uri(), "data/raw/file.csv", sha256(source_file), "test")
    record = download(source, retries=1)
    assert record["status"] == "downloaded"
    assert source.path.read_bytes() == source_file.read_bytes()
    assert not source.path.with_suffix(".csv.part").exists()


def test_existing_verified_download_is_reused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(module, "ROOT", tmp_path)
    target = tmp_path / "data/raw/file.csv"
    target.parent.mkdir(parents=True)
    target.write_text("ok", encoding="utf-8")
    source = Source("fixture", "https://invalid.example", "data/raw/file.csv", sha256(target), "test")
    assert download(source)["status"] == "reused"


def test_checksum_mismatch_fails_and_removes_partial(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source_file = tmp_path / "upstream.csv"
    source_file.write_text("changed", encoding="utf-8")
    monkeypatch.setattr(module, "ROOT", tmp_path / "project")
    source = Source("fixture", source_file.as_uri(), "data/raw/file.csv", "0" * 64, "test")
    with pytest.raises(ValueError, match="Checksum mismatch"):
        download(source, retries=1)
    assert not source.path.exists()
    assert not source.path.with_suffix(".csv.part").exists()
