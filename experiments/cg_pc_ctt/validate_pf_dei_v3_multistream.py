#!/usr/bin/env python3
"""Validate native PF-DEI V3 multistream output against schedule/reference files."""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path

import numpy as np

from pf_dei_v3_stream_format import read_multistream


def csv_length(path: Path) -> int:
    with path.open(newline="") as source:
        rows = csv.DictReader(source)
        return sum(1 for _ in rows)


def reference_ppm(path: Path) -> np.ndarray:
    with path.open(newline="") as source:
        rows = csv.DictReader(source)
        return np.asarray([float(row["physical_ppm"]) for row in rows], dtype=np.float32)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("schedules", nargs="+", type=Path)
    parser.add_argument("--reference-first", type=Path)
    args = parser.parse_args()

    trajectories = read_multistream(args.binary)
    if len(trajectories) != len(args.schedules):
        raise SystemExit("PF_DEI_V3_STREAM_TRAJECTORY_COUNT_MISMATCH")
    for index, (values, schedule) in enumerate(zip(trajectories, args.schedules, strict=True)):
        expected = csv_length(schedule)
        if values.size != expected:
            raise SystemExit(
                f"PF_DEI_V3_STREAM_SCHEDULE_LENGTH_MISMATCH index={index} "
                f"actual={values.size} expected={expected}"
            )

    reference_max_abs_diff = None
    if args.reference_first:
        expected = reference_ppm(args.reference_first)
        actual = trajectories[0]
        if not np.array_equal(actual, expected):
            reference_max_abs_diff = float(np.max(np.abs(actual - expected)))
            raise SystemExit(
                f"PF_DEI_V3_STREAM_REFERENCE_MISMATCH max_abs_diff={reference_max_abs_diff:.9g}"
            )
        reference_max_abs_diff = 0.0

    digest = hashlib.sha256(args.binary.read_bytes()).hexdigest()
    print(
        "PF_DEI_V3_MULTISTREAM_VALIDATION=PASS "
        f"trajectories={len(trajectories)} samples={sum(x.size for x in trajectories)} "
        f"reference_max_abs_diff={reference_max_abs_diff} sha256={digest}"
    )


if __name__ == "__main__":
    main()
