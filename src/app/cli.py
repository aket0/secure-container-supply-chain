"""CLI entry point."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .verifier import compute_sha256, generate_manifest, verify_manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="verifier", description="File integrity verifier")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_hash = sub.add_parser("hash", help="Compute SHA-256 of a file")
    p_hash.add_argument("file")

    p_gen = sub.add_parser("generate", help="Generate a manifest for given files")
    p_gen.add_argument("files", nargs="+")
    p_gen.add_argument("--base-dir", default=".")
    p_gen.add_argument("--output", "-o", default="-")

    p_verify = sub.add_parser("verify", help="Verify files against a manifest")
    p_verify.add_argument("manifest")
    p_verify.add_argument("--base-dir", default=".")

    args = parser.parse_args(argv)

    if args.cmd == "hash":
        try:
            digest = compute_sha256(args.file)
            print(f"{digest}  {args.file}")
            return 0
        except FileNotFoundError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1

    if args.cmd == "generate":
        manifest = generate_manifest([Path(f) for f in args.files], args.base_dir)
        out = json.dumps(manifest, indent=2)
        if args.output == "-":
            print(out)
        else:
            Path(args.output).write_text(out, encoding="utf-8")
            print(f"Manifest written to {args.output}")
        return 0

    if args.cmd == "verify":
        results = verify_manifest(args.manifest, args.base_dir)
        failures = [p for p, r in results.items() if not r["ok"]]
        for path, result in results.items():
            status = "OK" if result["ok"] else "FAIL"
            print(f"[{status}] {path}")
        if failures:
            print(f"\n{len(failures)} verification failure(s).", file=sys.stderr)
            return 1
        print(f"\nAll {len(results)} files verified.")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
