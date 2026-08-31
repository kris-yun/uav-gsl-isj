#!/usr/bin/env python3
"""Fail-closed verifier for a frozen CPIR full-grid lookup bank.

This verifier is deliberately separate from the CPIR score implementation.  It
checks provenance, layout, headers, sizes, and hashes before a runtime launch;
it does not change any scientific parameter or posterior calculation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys


MAGIC = b"PFV3STR1"
TIME_COUNT = 1500
MEMBER_COUNT = 8


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fail(message: str) -> "NoReturn":
    raise RuntimeError(message)


def read_world_header(path: Path) -> tuple[int, list[int]]:
    with path.open("rb") as source:
        header = source.read(12)
        if len(header) != 12 or header[:8] != MAGIC:
            fail(f"BAD_MAGIC:{path}")
        count = struct.unpack_from("<I", header, 8)[0]
        raw = source.read(4 * count)
    if len(raw) != 4 * count:
        fail(f"TRUNCATED_LENGTH_TABLE:{path}")
    return count, list(struct.unpack(f"<{count}I", raw))


def verify_world(path: Path, cell_count: int) -> int:
    count, lengths = read_world_header(path)
    if count != cell_count:
        fail(f"CELL_COUNT:{path}:{count}:{cell_count}")
    if any(length != TIME_COUNT for length in lengths):
        fail(f"TIME_LENGTH:{path}")
    expected = 12 + 4 * cell_count + 4 * cell_count * TIME_COUNT
    actual = path.stat().st_size
    if actual != expected:
        fail(f"SIZE:{path}:{actual}:{expected}")
    return actual


def expected_hash(path_arg: str | None, stored: str, label: str) -> None:
    if not path_arg:
        return
    path = Path(path_arg)
    if not path.is_file():
        fail(f"INPUT_MISSING:{label}:{path}")
    actual = sha256_file(path)
    if actual != stored:
        fail(f"INPUT_HASH:{label}:{actual}:{stored}")


def parse_file_manifest(root: Path) -> dict[str, tuple[int, str]]:
    path = root / "FILE_SHA256.tsv"
    if not path.is_file():
        fail("FILE_SHA256_MISSING")
    result: dict[str, tuple[int, str]] = {}
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        fields = line.split("\t")
        if len(fields) != 3:
            fail(f"FILE_SHA256_ROW:{line_no}")
        rel, size_text, digest = fields
        rel_path = Path(rel)
        if rel_path.is_absolute() or ".." in rel_path.parts:
            fail(f"FILE_SHA256_PATH:{line_no}")
        try:
            size = int(size_text)
        except ValueError:
            fail(f"FILE_SHA256_SIZE:{line_no}")
        if size < 0 or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            fail(f"FILE_SHA256_DIGEST:{line_no}")
        if rel in result:
            fail(f"FILE_SHA256_DUPLICATE:{rel}")
        result[rel] = (size, digest)
    if not result:
        fail("FILE_SHA256_EMPTY")
    return result


def verify_cell_manifest(root: Path, summary: dict) -> None:
    path = root / "cell_manifest.csv"
    if not path.is_file():
        fail("CELL_MANIFEST_MISSING")
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "stream_ordinal,native_cell_index,x,y":
        fail("CELL_MANIFEST_HEADER")
    native: set[int] = set()
    for expected_ordinal, line in enumerate(lines[1:]):
        fields = line.split(",")
        if len(fields) != 4:
            fail(f"CELL_MANIFEST_ROW:{expected_ordinal}")
        try:
            ordinal = int(fields[0])
            index = int(fields[1])
            float(fields[2])
            float(fields[3])
        except ValueError:
            fail(f"CELL_MANIFEST_VALUE:{expected_ordinal}")
        if ordinal != expected_ordinal or index < 0 or index in native:
            fail(f"CELL_MANIFEST_ORDER_OR_DUP:{expected_ordinal}")
        native.add(index)
    if len(native) != int(summary.get("cell_count", -1)):
        fail(f"CELL_MANIFEST_COUNT:{len(native)}:{summary.get('cell_count')}")


def verify_bank(args: argparse.Namespace) -> dict:
    root = args.root.resolve()
    if not root.is_dir():
        fail(f"ROOT_MISSING:{root}")
    if (root / "IN_PROGRESS").exists():
        fail("IN_PROGRESS_PRESENT")
    summary_path = root / "bank_summary.json"
    if not summary_path.is_file():
        fail("BANK_SUMMARY_MISSING")
    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"BANK_SUMMARY_JSON:{exc}")
    required = {
        "contract", "house", "carrier_count", "member_count", "cell_count",
        "time_count", "file_count", "total_bytes", "cell_manifest_sha256",
        "cell_csv_sha256", "placement_manifest_sha256", "native_binary_sha256", "environment_sha256",
        "observation_realization_sha256", "wind_iteration_hashes", "verdict",
    }
    missing = sorted(required.difference(summary))
    if missing:
        fail("BANK_SUMMARY_FIELDS:" + ",".join(missing))
    if summary["contract"] != "CPIR_FULLGRID_LOOKUP_V1":
        fail(f"CONTRACT:{summary['contract']}")
    if args.house and summary["house"] != args.house:
        fail(f"HOUSE:{summary['house']}:{args.house}")
    if summary["verdict"] != "CPIR_FULLGRID_LOOKUP_PASS":
        fail(f"VERDICT:{summary['verdict']}")
    if int(summary["member_count"]) != MEMBER_COUNT or int(summary["time_count"]) != TIME_COUNT:
        fail("MEMBER_OR_TIME_COUNT")
    if args.carrier_count is not None and int(summary["carrier_count"]) != args.carrier_count:
        fail(f"CARRIER_COUNT:{summary['carrier_count']}:{args.carrier_count}")
    if args.cell_count is not None and int(summary["cell_count"]) != args.cell_count:
        fail(f"CELL_COUNT_SUMMARY:{summary['cell_count']}:{args.cell_count}")

    verify_cell_manifest(root, summary)
    manifest = parse_file_manifest(root)
    files = sorted((root / "worlds").glob("member_*/*.bin"))
    if len(files) != int(summary["file_count"]) or len(files) != len(manifest):
        fail(f"FILE_COUNT:{len(files)}:{summary['file_count']}:{len(manifest)}")
    expected_total = 0
    for path in files:
        rel = path.relative_to(root).as_posix()
        if rel not in manifest:
            fail(f"FILE_NOT_IN_MANIFEST:{rel}")
        expected_size, expected_digest = manifest[rel]
        size = verify_world(path, int(summary["cell_count"]))
        if size != expected_size:
            fail(f"MANIFEST_SIZE:{rel}:{size}:{expected_size}")
        digest = sha256_file(path)
        if digest != expected_digest:
            fail(f"MANIFEST_HASH:{rel}:{digest}:{expected_digest}")
        expected_total += size
    if expected_total != int(summary["total_bytes"]):
        fail(f"TOTAL_BYTES:{expected_total}:{summary['total_bytes']}")

    member_ids = sorted(path.name for path in (root / "worlds").glob("member_*"))
    expected_members = [f"member_{i:02d}" for i in range(MEMBER_COUNT)]
    if member_ids != expected_members:
        fail(f"MEMBER_DIRS:{member_ids}")
    carriers = sorted(path.stem for path in (root / "worlds" / "member_00").glob("*.bin"))
    if len(carriers) != int(summary["carrier_count"]):
        fail("CARRIER_SET_COUNT")
    for member in expected_members:
        member_carriers = sorted(path.stem for path in (root / "worlds" / member).glob("*.bin"))
        if member_carriers != carriers:
            fail(f"CARRIER_RECTANGLE:{member}")

    expected_hash(args.cell_csv, summary["cell_csv_sha256"], "cell_csv")
    expected_hash(args.placement_manifest, summary["placement_manifest_sha256"], "placement_manifest")
    expected_hash(args.native_binary, summary["native_binary_sha256"], "native_binary")
    expected_hash(args.environment, summary["environment_sha256"], "environment")
    expected_hash(args.observation_realization, summary["observation_realization_sha256"], "observation_realization")
    if args.wind_dir:
        wind_dir = Path(args.wind_dir)
        stored_wind = summary["wind_iteration_hashes"]
        if not wind_dir.is_dir():
            fail(f"WIND_DIR_MISSING:{wind_dir}")
        actual_names = sorted(path.name for path in wind_dir.glob("wind_iteration_*") if path.is_file())
        if sorted(stored_wind) != actual_names:
            fail("WIND_ITERATION_SET")
        for name in actual_names:
            digest = sha256_file(wind_dir / name)
            if digest != stored_wind[name]:
                fail(f"WIND_HASH:{name}")

    return {
        "verdict": "CPIR_LOOKUP_INTEGRITY_PASS",
        "root": str(root),
        "house": summary["house"],
        "carrier_count": int(summary["carrier_count"]),
        "member_count": int(summary["member_count"]),
        "cell_count": int(summary["cell_count"]),
        "time_count": int(summary["time_count"]),
        "file_count": len(files),
        "total_bytes": expected_total,
        "bank_summary_sha256": sha256_file(summary_path),
        "file_manifest_sha256": sha256_file(root / "FILE_SHA256.tsv"),
        "cell_manifest_sha256": sha256_file(root / "cell_manifest.csv"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--house")
    parser.add_argument("--carrier-count", type=int)
    parser.add_argument("--cell-count", type=int)
    parser.add_argument("--cell-csv")
    parser.add_argument("--placement-manifest")
    parser.add_argument("--native-binary")
    parser.add_argument("--environment")
    parser.add_argument("--observation-realization")
    parser.add_argument("--wind-dir")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        report = verify_bank(args)
    except (OSError, RuntimeError, ValueError, struct.error) as exc:
        print(f"CPIR_LOOKUP_INTEGRITY_FAIL:{exc}", file=sys.stderr)
        return 2
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
