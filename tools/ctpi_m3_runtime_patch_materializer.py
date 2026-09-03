#!/usr/bin/env python3
"""Materialize the complete CTPI M3 runtime patch from the frozen V2 body.

The checked-in V2 patch body is scientifically frozen and byte-identified by
SOURCE_SHA256.  It contains the complete hunk content but lacks the final LF
required by `git apply`.  This helper appends exactly one LF byte, verifies the
resulting COMPLETE_SHA256, and writes the complete patch to a fresh output.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

SOURCE_SHA256 = "a054a28c593f095956469e87713350e89baf3f30c94a9d23e8708b63379f4713"
COMPLETE_SHA256 = "96e1e425a7c4e6e97ad123c1d46e67120dc86574b3d3927a370e5b99d1020743"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def final_hunk_counts(text: str) -> tuple[int, int]:
    marker = "@@ -183,13 +186,124 @@"
    pos = text.rfind(marker)
    if pos < 0:
        raise RuntimeError("CTPI_M3_PATCH_FINAL_HUNK_HEADER")
    lines = text[pos:].splitlines()
    old_count = 0
    new_count = 0
    for line in lines[1:]:
        if line.startswith("@@ ") or line.startswith("--- ") or line.startswith("+++ "):
            break
        if line.startswith("-"):
            old_count += 1
        elif line.startswith("+"):
            new_count += 1
        else:
            old_count += 1
            new_count += 1
    return old_count, new_count


def materialize(source: Path, output: Path) -> None:
    source_bytes = source.read_bytes()
    if sha256(source_bytes) != SOURCE_SHA256:
        raise RuntimeError(f"CTPI_M3_PATCH_SOURCE_SHA:{sha256(source_bytes)}:{SOURCE_SHA256}")
    if source_bytes.endswith(b"\n"):
        raise RuntimeError("CTPI_M3_PATCH_SOURCE_UNEXPECTED_FINAL_LF")
    old_count, new_count = final_hunk_counts(source_bytes.decode("utf-8"))
    if (old_count, new_count) != (13, 124):
        raise RuntimeError(f"CTPI_M3_PATCH_FINAL_HUNK_COUNTS:{old_count}:{new_count}")
    complete = source_bytes + b"\n"
    if sha256(complete) != COMPLETE_SHA256:
        raise RuntimeError(f"CTPI_M3_PATCH_COMPLETE_SHA:{sha256(complete)}:{COMPLETE_SHA256}")
    if output.exists():
        raise RuntimeError(f"CTPI_M3_PATCH_OUTPUT_EXISTS:{output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(complete)
    print("CTPI_M3_RUNTIME_PATCH_MATERIALIZE=PASS")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    materialize(args.source.resolve(), args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
