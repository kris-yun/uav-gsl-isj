#!/usr/bin/env python3
"""Create immutable H01 static native-wind context views and their manifest."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from ctt_h01_wind_bank_io import sha256_file


SPLIT = {0: "train", 1: "test", 2: "test", 3: "train", 4: "validation",
         5: "train", 6: "train", 7: "validation", 8: "train", 9: "train"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--native-wind-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    if args.output_root.exists():
        raise SystemExit(f"REFUSE_OVERWRITE:{args.output_root}")
    sources = [args.native_wind_root / f"wind_iteration_{index}" for index in range(1, 11)]
    for source in sources:
        if not source.is_file():
            raise FileNotFoundError(source)
    args.output_root.mkdir(parents=True)
    contexts = []
    for context, source in enumerate(sources):
        directory = args.output_root / f"context_{context:02d}_{SPLIT[context]}"
        directory.mkdir()
        for slot in range(11):
            os.symlink(source.resolve(), directory / f"wind_iteration_{slot}")
        contexts.append({
            "context": context,
            "split": SPLIT[context],
            "original_iteration": context + 1,
            "original_path": str(source.resolve()),
            "wind_dir": str(directory.resolve()),
            "payload_sha256": sha256_file(source),
            "native_slots": list(range(11)),
        })
    manifest = {
        "contract": "CTT_H01_NATIVE_STATIC_WIND_CONTEXTS_V1",
        "construction": "context_c_repeats_original_iteration_c_plus_1_in_native_slots_0_through_10",
        "contexts": contexts,
    }
    target = args.output_root / "context_manifest.json"
    target.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"CTT_H01_NATIVE_WIND_CONTEXTS=PASS manifest_sha256={sha256_file(target)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
