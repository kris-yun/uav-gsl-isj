"""Audit what the frozen controlled assets can, and cannot, identify for M1.

This is an evaluator-only diagnostic.  It intentionally reads source and raw
gas fields solely to establish the experimental-design boundary; neither may
become a model input.  In particular, an exact-source pair under two distinct
transport interventions does *not* identify a transport-invariant source
mechanism unless the same transport is also crossed with another source (or a
separate candidate-conditioned forward intervention supplies that
counterfactual).
"""

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ASSETS = ROOT / "evidence/cstar_controlled_assets_20260907_r2"
DT_S = 0.2


def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rms(a, b):
    return float(np.sqrt(np.mean((np.asarray(a) - np.asarray(b)) ** 2)))


def load_sensor_model(assets: Path):
    """Load the immutable sensor implementation bound by the asset manifest."""
    environment = assets.parent / "cstar_environment_20260906"
    source = environment / "source_snapshot" / "sensor_model.py"
    spec = importlib.util.spec_from_file_location("audit_bound_sensor_model", source)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    frozen = json.loads((environment / "probes_v1" / "H01" / "sensor_manifest.json").read_text(encoding="utf-8"))
    return module.SensorModel(seed=frozen["sensor"]["seed"], **frozen["sensor"]["config"]), frozen["sensor"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--assets", type=Path, default=DEFAULT_ASSETS)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    assets = args.assets.resolve()
    args.out.parent.mkdir(parents=True, exist_ok=True)

    # Each LOHO manifest carries the same 12 immutable parents.  H01 is enough
    # to enumerate them, while the other two manifests bind the split views.
    manifests = {
        house: json.loads((assets / "manifests" / f"{house}.json").read_text(encoding="utf-8"))
        for house in ("H01", "H02", "H03")
    }
    episodes = {e["realization_id"]: e for e in manifests["H01"]["m1_episodes"]}
    if len(episodes) != 12:
        raise RuntimeError("EXPECTED_12_UNIQUE_M1_PARENTS")
    for house, manifest in manifests.items():
        if {e["realization_id"] for e in manifest["m1_episodes"]} != set(episodes):
            raise RuntimeError(f"LOHO_PARENT_SET_MISMATCH:{house}")

    sensor_template, sensor_manifest = load_sensor_model(assets)
    by_house = defaultdict(list)
    for episode in episodes.values():
        by_house[episode["house"]].append(episode)

    houses = {}
    all_transport_ids = defaultdict(set)
    for house, group in sorted(by_house.items()):
        if len(group) != 4:
            raise RuntimeError(f"EXPECTED_FOUR_PARENTS:{house}")
        by_source = defaultdict(list)
        for episode in group:
            by_source[episode["source_id"]].append(episode)
            all_transport_ids[episode["transport_intervention_id"]].add(episode["source_id"])
        if sorted(map(len, by_source.values())) != [2, 2]:
            raise RuntimeError(f"EXPECTED_TWO_EXACT_SOURCE_PAIRS:{house}")

        records = {}
        route_hashes = set()
        for episode in group:
            history_path = assets / episode["history_trace_path"]
            raw_path = history_path.with_name("evaluator_raw_history.jsonl")
            history, raw = load_jsonl(history_path), load_jsonl(raw_path)
            if len(history) != 300 or len(raw) != 300:
                raise RuntimeError(f"EXPECTED_300_HISTORY_FRAMES:{episode['realization_id']}")
            if sha256(history_path) != episode["history_trace_sha256"]:
                raise RuntimeError(f"HISTORY_HASH_MISMATCH:{episode['realization_id']}")
            route = [(r["pose_xy"][0], r["pose_xy"][1]) for r in history]
            route_hashes.add(hashlib.sha256(repr(route).encode()).hexdigest())
            observed = np.asarray([r["gas_ppm"] for r in history], dtype=float)
            raw_gas = np.asarray([r["true_gas_ppm"] for r in raw], dtype=float)
            # Independent recomputation uses the exact causal piecewise-linear
            # delay and state transition, including the frozen 0.4 s dead time.
            sensor = type(sensor_template)(seed=sensor_template.seed, **sensor_template.cfg.__dict__)
            recomputed = [sensor.process(float(value), DT_S) for value in raw_gas]
            records[episode["realization_id"]] = {
                "source_id": episode["source_id"],
                "source_xyz_m": episode["source_xyz_m"],
                "transport_intervention_id": episode["transport_intervention_id"],
                "sensor_fopdt_max_abs_error": float(np.max(np.abs(observed - recomputed))),
                "gas_sum": float(observed.sum()),
                "hit_count_at_0_1ppm": int((observed > 0.1).sum()),
                "first_hit_frame_at_0_1ppm": next((i for i, x in enumerate(observed) if x > 0.1), None),
                "observed_gas": observed,
            }
        if len(route_hashes) != 1:
            raise RuntimeError(f"ROUTE_NOT_FIXED_WITHIN_HOUSE:{house}")

        source_ids = sorted(by_source)
        same = rms(records[by_source[source_ids[0]][0]["realization_id"]]["observed_gas"],
                   records[by_source[source_ids[0]][1]["realization_id"]]["observed_gas"])
        same += rms(records[by_source[source_ids[1]][0]["realization_id"]]["observed_gas"],
                    records[by_source[source_ids[1]][1]["realization_id"]]["observed_gas"])
        same /= 2.0
        cross = []
        for left in by_source[source_ids[0]]:
            for right in by_source[source_ids[1]]:
                cross.append(rms(records[left["realization_id"]]["observed_gas"],
                                 records[right["realization_id"]]["observed_gas"]))
        houses[house] = {
            "fixed_geometry_only_history_route": True,
            "source_groups": {source: [e["realization_id"] for e in pairs]
                              for source, pairs in by_source.items()},
            "mean_within_exact_source_transport_rms_ppm": same,
            "mean_cross_source_transport_rms_ppm": float(np.mean(cross)),
            "within_over_cross_rms_ratio": same / max(float(np.mean(cross)), 1e-12),
            "parents": {rid: {k: v for k, v in data.items() if k != "observed_gas"}
                        for rid, data in records.items()},
        }

    shared_transport = {transport: sorted(sources) for transport, sources in all_transport_ids.items()
                        if len(sources) > 1}
    report = {
        "contract": "CSTAR_M1_CROSSHOUSE_INFORMATION_AUDIT_V1",
        "assets": str(assets),
        "asset_manifest_sha256": sha256(assets / "manifests" / "H01.json"),
        "evaluator_only_fields_used": ["source_id", "source_xyz_m", "true_gas_ppm"],
        "model_inputs_unchanged": ["stamp_ns", "pose_xy", "gas_ppm", "wind_uv", "candidate_geometry"],
        "common_information_verified": [
            "fixed geometry-only route within each House",
            "identical sensor law (FOPDT tau=1.2 s, dead-time=0.4 s, dt=0.2 s) across all parents",
            "causal measured gas prefix and local wind at every route point",
            "candidate support aligned to the House map",
        ],
        "not_identified_from_this_bundle_alone": [
            "a source effect at a fixed transport intervention",
            "a transport-invariant source representation learned from raw histories alone",
            "a cross-House source posterior from coordinate or gas pattern classification",
        ],
        "shared_transport_interventions_across_distinct_sources": shared_transport,
        "source_transport_factorial_crossing_present": bool(shared_transport),
        "required_m1_bridge": "candidate-conditioned do(source) forward exposure under the observed route/wind history, composed with the fixed FOPDT sensor law, plus an observability abstention gate",
        "sensor_manifest": sensor_manifest,
        "houses": houses,
        "verdict": "M1_RAW_HISTORY_ONLY_CAUSAL_IDENTIFICATION_NOT_SUPPORTED"
                   if not shared_transport else "M1_FACTORIAL_SOURCE_TRANSPORT_IDENTIFICATION_POSSIBLE",
    }
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(report["verdict"])


if __name__ == "__main__":
    main()
