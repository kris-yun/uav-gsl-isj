#!/usr/bin/env python3
"""Freeze realization provenance before any independent endpoint is run."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


HOUSE = {
    "H01": {
        "house": "House01",
        "backend": "raw_house1_snapshot",
        "scenario_id": "H01_cfg_2_4_1_fast",
        "config_id": "2,4-1_fast",
        "source_position": [-0.40, -2.90, -0.30],
        "start_position": [-3.17, -1.75, 0.30],
    },
    "H02": {
        "house": "House02",
        "backend": "gaden_player",
        "scenario_id": "H02_cfg_3_5_1_fast",
        "config_id": "3,5-1_fast",
        "source_position": [0.00, -1.00, 0.20],
        "start_position": [-0.50, -2.50, 0.30],
    },
    "H03": {
        "house": "House03",
        "backend": "gaden_player",
        "scenario_id": "H03_cfg_1-2_5_fast",
        "config_id": "1-2,5_fast",
        "source_position": [-0.45, 1.90, -0.10],
        "start_position": [2.00, 0.00, 0.30],
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def content_hash(files: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in files:
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(sha256(path).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze-template", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--pmfs-binary", type=Path, required=True)
    parser.add_argument("--launch", type=Path, required=True)
    parser.add_argument("--hcmc-code", type=Path, required=True)
    parser.add_argument("--generator-binary", type=Path, required=True)
    parser.add_argument("--generator-source-diff", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    freeze = json.loads(args.freeze_template.read_text(encoding="utf-8"))
    for path in (
        args.pmfs_binary,
        args.launch,
        args.hcmc_code,
        args.generator_binary,
        args.generator_source_diff,
    ):
        if not path.is_file():
            raise FileNotFoundError(path)

    finalized = []
    for entry in freeze["realizations"]:
        case_id = entry["case_id"]
        short = case_id[:3]
        meta = HOUSE[short]
        case_root = args.data_root / case_id
        matches = sorted(case_root.glob("FilamentSimulation_gasType_10_sourcePosition_*"))
        if len(matches) != 1:
            raise RuntimeError(f"{case_id}: expected one realization, found {len(matches)}")
        realization = matches[0]
        frames = sorted(
            realization.glob("iteration_*"),
            key=lambda path: int(path.name.split("_", 1)[1].split(".", 1)[0]),
        )
        indices = [int(path.name.split("_", 1)[1].split(".", 1)[0]) for path in frames]
        if len(frames) < 1501 or indices != list(range(len(indices))):
            raise RuntimeError(f"{case_id}: invalid contiguous frame range")
        generation_manifest = case_root / "generation_manifest.txt"
        finalized.append(
            {
                **entry,
                **meta,
                "gas_realization_directory": str(realization),
                "gas_realization_content_sha256": content_hash(frames),
                "generation_manifest_sha256": sha256(generation_manifest),
                "available_iteration_range": [indices[0], indices[-1]],
                "available_iteration_count": len(indices),
                "replay_policy": "seeded_time_replay; offset=(7919*(navigation_seed+1))%max(1,max_iteration-1)",
                "wind_config": f"canonical {meta['house']} {meta['config_id']} wind_iteration_0..10",
                "sensor_model": "fopdt_tau1p2_dead0p4_noise0",
                "pmfs_binary_sha256": sha256(args.pmfs_binary),
                "launch_sha256": sha256(args.launch),
                "hcmc_code_sha256": sha256(args.hcmc_code),
                "generator_binary_sha256": sha256(args.generator_binary),
                "generator_source_diff_sha256": sha256(args.generator_source_diff),
                "discovery_used_this_realization": False,
                "independence_classification": "NEW_STOCHASTIC_GADEN_PLUME_REALIZATION",
            }
        )
    freeze["realizations"] = finalized
    freeze["freeze_state"] = "PRE_ENDPOINT_PROVENANCE_FROZEN"
    freeze["selection_timestamp_utc"] = datetime.now(timezone.utc).isoformat()
    freeze["endpoint_seen_at_freeze"] = False
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(freeze, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("HCMC_V1_PRE_ENDPOINT_PROVENANCE_FREEZE_PASS")


if __name__ == "__main__":
    main()
