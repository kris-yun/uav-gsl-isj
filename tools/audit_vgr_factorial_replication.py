#!/usr/bin/env python3
"""Audit whether nominal VGR plume seeds are independent numeric replicates."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd


SIGNAL_COLUMNS = (
    "raw_gas_concentration_ppm",
    "processed_sensor_output_ppm",
)


def numeric_hash(frame: pd.DataFrame) -> str:
    values = np.ascontiguousarray(frame.loc[:, SIGNAL_COLUMNS].to_numpy(dtype=np.float64))
    return hashlib.sha256(values.tobytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    groups: dict[tuple[str, str, str], list[dict[str, object]]] = defaultdict(list)
    zero_hit_episodes = 0
    files = sorted(args.episodes.glob("*.csv"))
    for path in files:
        frame = pd.read_csv(path)
        source = str(frame["source_id"].iloc[0])
        wind = str(frame["wind_id"].iloc[0])
        route = str(frame["trajectory_id"].iloc[0])
        seed = int(frame["plume_seed"].iloc[0])
        hit_count = int(frame["gas_hit"].sum())
        zero_hit_episodes += int(hit_count == 0)
        groups[(source, wind, route)].append(
            {
                "file": path.name,
                "seed": seed,
                "rows": int(len(frame)),
                "gas_hits": hit_count,
                "signal_sha256": numeric_hash(frame),
            }
        )

    group_audits = []
    identical_groups = 0
    for (source, wind, route), records in sorted(groups.items()):
        unique_signal_hashes = len({str(record["signal_sha256"]) for record in records})
        identical = unique_signal_hashes == 1
        identical_groups += int(identical)
        group_audits.append(
            {
                "source_id": source,
                "wind_id": wind,
                "trajectory_id": route,
                "nominal_seed_count": len(records),
                "unique_signal_realizations": unique_signal_hashes,
                "signals_identical_across_nominal_seeds": identical,
                "records": records,
            }
        )

    independent_replication_pass = all(
        item["unique_signal_realizations"] == item["nominal_seed_count"]
        for item in group_audits
    )
    result = {
        "schema": "VGR_FACTORIAL_NUMERIC_REPLICATION_AUDIT_V1",
        "episode_count": len(files),
        "factorial_cell_count": len(group_audits),
        "zero_hit_episode_count": zero_hit_episodes,
        "identical_seed_triplet_count": identical_groups,
        "independent_numeric_replication_pass": independent_replication_pass,
        "verdict": (
            "VGR_FACTORIAL_INDEPENDENT_REPLICATION_PASS"
            if independent_replication_pass
            else "VGR_FACTORIAL_NOMINAL_SEEDS_ARE_NUMERIC_PSEUDOREPLICATES"
        ),
        "claim_boundary": {
            "development_diagnostic": "AUTHORIZED",
            "cross_fitted_session_calibration": (
                "AUTHORIZED" if independent_replication_pass else "NOT_AUTHORIZED"
            ),
            "untouched_main_innovation_confirmation": "NOT_AUTHORIZED",
        },
        "groups": group_audits,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in (
        "episode_count",
        "factorial_cell_count",
        "zero_hit_episode_count",
        "identical_seed_triplet_count",
        "independent_numeric_replication_pass",
        "verdict",
    )}, indent=2))


if __name__ == "__main__":
    main()
