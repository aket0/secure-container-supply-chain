"""Tests for the CLI."""

import hashlib
import json
from pathlib import Path

import pytest

from app.cli import main


@pytest.fixture
def sample_file(tmp_path: Path) -> Path:
    p = tmp_path / "file.txt"
    p.write_bytes(b"test content")
    return p


class TestHashCommand:
    def test_hash_exits_0(self, tmp_path, capsys):
        p = tmp_path / "f.txt"
        p.write_bytes(b"data")
        rc = main(["hash", str(p)])
        assert rc == 0
        out = capsys.readouterr().out
        expected = hashlib.sha256(b"data").hexdigest()
        assert expected in out

    def test_hash_missing_file_exits_1(self, tmp_path):
        rc = main(["hash", str(tmp_path / "nope.txt")])
        assert rc == 1


class TestGenerateCommand:
    def test_generate_to_stdout(self, tmp_path, capsys):
        p = tmp_path / "f.txt"
        p.write_bytes(b"abc")
        rc = main(["generate", str(p), "--base-dir", str(tmp_path)])
        assert rc == 0
        data = json.loads(capsys.readouterr().out)
        assert "files" in data

    def test_generate_to_file(self, tmp_path):
        p = tmp_path / "f.txt"
        p.write_bytes(b"abc")
        out = tmp_path / "manifest.json"
        rc = main(["generate", str(p), "--base-dir", str(tmp_path), "--output", str(out)])
        assert rc == 0
        assert out.exists()
        data = json.loads(out.read_text())
        assert "files" in data


class TestVerifyCommand:
    def test_verify_valid_manifest_exits_0(self, tmp_path):
        p = tmp_path / "f.txt"
        p.write_bytes(b"hello")
        digest = hashlib.sha256(b"hello").hexdigest()
        manifest = tmp_path / "manifest.json"
        manifest.write_text(json.dumps({"files": {"f.txt": digest}}))
        rc = main(["verify", str(manifest), "--base-dir", str(tmp_path)])
        assert rc == 0

    def test_verify_tampered_exits_1(self, tmp_path):
        p = tmp_path / "f.txt"
        p.write_bytes(b"tampered!")
        manifest = tmp_path / "manifest.json"
        manifest.write_text(json.dumps({"files": {"f.txt": "0" * 64}}))
        rc = main(["verify", str(manifest), "--base-dir", str(tmp_path)])
        assert rc == 1
