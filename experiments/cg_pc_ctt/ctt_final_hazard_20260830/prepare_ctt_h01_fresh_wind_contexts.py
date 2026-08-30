#!/usr/bin/env python3
"""Prepare CTT H01 fresh wind contexts (logical 10..15) from the three unused
GADEN configs.

Each fresh context repeats a single genuinely-unused frame into native slots
0..10, mirroring the frozen CTT_H01_NATIVE_STATIC_WIND_CONTEXTS_V1 construction
but with a distinct contract name and context indices 10..15.  No old field is
copied, rotated, perturbed, or noise-injected: every fresh payload is a
byte-level conversion of an independent House01 CFD wind frame.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path


# frozen fresh mapping (logical ID -> config, frame) from FRESH_WIND_INVENTORY
FRESH_MAP = {
    10: {"config": "1,3-2,4_fast", "frame": 1, "split": "test"},
    11: {"config": "1,3-2,4_slow", "frame": 1, "split": "test"},
    12: {"config": "2,4-1_slow", "frame": 1, "split": "test"},
    13: {"config": "1,3-2,4_fast", "frame": 10, "split": "test"},
    14: {"config": "1,3-2,4_slow", "frame": 10, "split": "closed_loop"},
    15: {"config": "2,4-1_slow", "frame": 10, "split": "closed_loop"},
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wind-csv-root", type=Path, required=True,
                        help="House01 wind_simulations directory")
    parser.add_argument("--environment", type=Path, required=True)
    parser.add_argument("--converter", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--convert-root", type=Path, required=True,
                        help="where converted wind_iteration dirs are written")
    args = parser.parse_args()
    if args.output_root.exists():
        raise SystemExit(f"REFUSE_OVERWRITE:{args.output_root}")

    # convert each required config once
    converted: dict[str, Path] = {}
    for logical in sorted(FRESH_MAP):
        cfg = FRESH_MAP[logical]["config"]
        if cfg in converted:
            continue
        out = args.convert_root / cfg.replace(",", "_")
        if not out.exists():
            prefix = args.wind_csv_root / cfg / cfg
            subprocess.run([str(args.converter), str(args.environment), str(prefix), str(out)],
                           check=True)
        converted[cfg] = out

    args.output_root.mkdir(parents=True)
    contexts = []
    for logical in sorted(FRESH_MAP):
        spec = FRESH_MAP[logical]
        source = converted[spec["config"]] / f"wind_iteration_{spec['frame']}"
        if not source.is_file():
            raise FileNotFoundError(source)
        directory = args.output_root / f"context_{logical:02d}_{spec['split']}"
        directory.mkdir()
        for slot in range(11):
            os.symlink(source.resolve(), directory / f"wind_iteration_{slot}")
        contexts.append({
            "context": logical,
            "split": spec["split"],
            "source_config": spec["config"],
            "source_frame": spec["frame"],
            "original_path": str(source.resolve()),
            "wind_dir": str(directory.resolve()),
            "payload_sha256": sha256_file(source),
            "native_slots": list(range(11)),
        })
    manifest = {
        "contract": "CTT_H01_FRESH_STATIC_WIND_CONTEXTS_V1",
        "construction": "context_10_15_repeats_single_unused_frame_in_native_slots_0_through_10",
        "contexts": contexts,
    }
    target = args.output_root / "context_manifest.json"
    target.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"CTT_H01_FRESH_WIND_CONTEXTS=PASS manifest_sha256={sha256_file(target)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
