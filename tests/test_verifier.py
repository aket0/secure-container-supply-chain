"""Tests for the integrity verifier."""

import hashlib
import json
from pathlib import Path

import pytest

from app.verifier import compute_sha256, generate_manifest, verify_manifest


@pytest.fixture
def sample_file(tmp_path: Path) -> Path:
    p = tmp_path / "sample.txt"
    p.write_bytes(b"hello world\n")
    return p


@pytest.fixture
def known_hash() -> str:
    return hashlib.sha256(b"hello world\n").hexdigest()


class TestComputeSha256:
    def test_known_content(self, sample_file, known_hash):
        assert compute_sha256(sample_file) == known_hash

    def test_empty_file(self, tmp_path):
        p = tmp_path / "empty.bin"
        p.write_bytes(b"")
        assert compute_sha256(p) == hashlib.sha256(b"").hexdigest()

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            compute_sha256(tmp_path / "nope.txt")

    def test_different_content_different_hash(self, tmp_path):
        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        a.write_bytes(b"aaa")
        b.write_bytes(b"bbb")
        assert compute_sha256(a) != compute_sha256(b)

    def test_accepts_string_path(self, sample_file):
        assert compute_sha256(str(sample_file)) == compute_sha256(sample_file)


class TestGenerateManifest:
    def test_generates_correct_hashes(self, tmp_path, sample_file, known_hash):
        manifest = generate_manifest([sample_file], base_dir=tmp_path)
        assert "files" in manifest
        assert manifest["files"]["sample.txt"] == known_hash

    def test_multiple_files(self, tmp_path):
        files = []
        for name in ("a.txt", "b.txt", "c.txt"):
            p = tmp_path / name
            p.write_bytes(name.encode())
            files.append(p)
        manifest = generate_manifest(files, base_dir=tmp_path)
        assert len(manifest["files"]) == 3

    def test_empty_list(self, tmp_path):
        manifest = generate_manifest([], base_dir=tmp_path)
        assert manifest == {"files": {}}


class TestVerifyManifest:
    def _write_manifest(self, tmp_path: Path, content: dict) -> Path:
        p = tmp_path / "manifest.json"
        p.write_text(json.dumps(content), encoding="utf-8")
        return p

    def test_valid_manifest_all_ok(self, tmp_path, sample_file, known_hash):
        manifest_path = self._write_manifest(tmp_path, {"files": {"sample.txt": known_hash}})
        results = verify_manifest(manifest_path, base_dir=tmp_path)
        assert results["sample.txt"]["ok"] is True

    def test_tampered_file_fails(self, tmp_path, sample_file):
        good_hash = compute_sha256(sample_file)
        sample_file.write_bytes(b"tampered content!")
        manifest_path = self._write_manifest(tmp_path, {"files": {"sample.txt": good_hash}})
        results = verify_manifest(manifest_path, base_dir=tmp_path)
        assert results["sample.txt"]["ok"] is False

    def test_missing_file_fails(self, tmp_path):
        manifest_path = self._write_manifest(
            tmp_path, {"files": {"missing.txt": "abc123"}}
        )
        results = verify_manifest(manifest_path, base_dir=tmp_path)
        assert results["missing.txt"]["ok"] is False
        assert results["missing.txt"].get("error") == "missing"

    def test_wrong_hash_fails(self, tmp_path, sample_file):
        manifest_path = self._write_manifest(
            tmp_path, {"files": {"sample.txt": "0" * 64}}
        )
        results = verify_manifest(manifest_path, base_dir=tmp_path)
        assert results["sample.txt"]["ok"] is False

    def test_roundtrip_generate_then_verify(self, tmp_path):
        files = []
        for name in ("a.txt", "b.bin"):
            p = tmp_path / name
            p.write_bytes(name.encode() * 100)
            files.append(p)
        manifest = generate_manifest(files, base_dir=tmp_path)
        manifest_path = self._write_manifest(tmp_path, manifest)
        results = verify_manifest(manifest_path, base_dir=tmp_path)
        assert all(r["ok"] for r in results.values())
