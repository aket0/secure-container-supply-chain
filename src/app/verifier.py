"""File integrity verifier using SHA-256."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


class IntegrityError(Exception):
    pass


def compute_sha256(path: Path | str) -> str:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_manifest(manifest_path: Path | str, base_dir: Path | str = ".") -> dict:
    """
    Verify file integrity against a JSON manifest.

    Manifest format:
        {"files": {"relative/path": "sha256hex", ...}}
    """
    manifest_path = Path(manifest_path)
    base_dir = Path(base_dir)

    with manifest_path.open(encoding="utf-8") as f:
        manifest = json.load(f)

    results: dict[str, dict] = {}
    for rel_path, expected_hash in manifest.get("files", {}).items():
        full_path = base_dir / rel_path
        try:
            actual = compute_sha256(full_path)
            ok = actual == expected_hash
            results[rel_path] = {"ok": ok, "expected": expected_hash, "actual": actual}
        except FileNotFoundError:
            results[rel_path] = {"ok": False, "expected": expected_hash, "actual": None, "error": "missing"}

    return results


def generate_manifest(paths: list[Path | str], base_dir: Path | str = ".") -> dict:
    base_dir = Path(base_dir)
    files = {}
    for p in paths:
        p = Path(p)
        rel = p.relative_to(base_dir) if p.is_absolute() else p
        full = base_dir / rel
        files[str(rel)] = compute_sha256(full)
    return {"files": files}
