#!/usr/bin/env python3
"""Verify the frozen TNQC V5 implementation manifest against working-tree bytes.

Uses the Git blob object formula directly:
    sha1(b"blob " + len(content) + b"\0" + content)

This avoids depending on git status/index state and verifies exactly the file
bytes that the VM/Codex is about to execute.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--manifest",
        type=Path,
        default=Path("evidence/TNQC_V5_IMPLEMENTATION_MANIFEST_20260921.json"),
    )
    ap.add_argument("--root", type=Path, default=Path("."))
    args = ap.parse_args()

    root = args.root.resolve()
    manifest_path = args.manifest
    if not manifest_path.is_absolute():
        manifest_path = root / manifest_path
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    expected_contract = "TNQC_V5_IMPLEMENTATION_MANIFEST_V2_CPP_ENDPOINT_PARITY"
    if payload.get("contract") != expected_contract:
        raise SystemExit(
            f"TNQC manifest contract mismatch: {payload.get('contract')!r} "
            f"!= {expected_contract!r}"
        )
    if payload.get("house_300s_truth_used_before_freeze") is not False:
        raise SystemExit("TNQC manifest does not declare a pre-truth freeze")

    expected = payload.get("file_blob_sha")
    if not isinstance(expected, dict) or not expected:
        raise SystemExit("TNQC manifest has no file_blob_sha map")

    failures = []
    for rel, want in sorted(expected.items()):
        path = root / rel
        if not path.is_file():
            failures.append((rel, want, "MISSING"))
            continue
        got = git_blob_sha(path.read_bytes())
        if got != want:
            failures.append((rel, want, got))

    if failures:
        print("TNQC_MANIFEST_VERIFY_FAIL")
        for rel, want, got in failures:
            print(f"{rel}\n  expected={want}\n  actual={got}")
        raise SystemExit(4)

    print(
        "TNQC_MANIFEST_VERIFY_PASS "
        f"contract={payload['contract']} files={len(expected)}"
    )


if __name__ == "__main__":
    main()
