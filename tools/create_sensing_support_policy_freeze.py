#!/usr/bin/env python3
"""Create the pre-response policy freeze and deterministic hash manifest."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


def sha256_file(path: Path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--starting-sha", required=True)
    parser.add_argument("--policy-parent-sha", required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = repo / "experiments/active_observability_v1/candidates/CANDIDATE_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    native_audit_path = repo / "experiments/active_observability_v1/CANDIDATE_NATIVE_GEOMETRY_AUDIT.json"
    native_audit = json.loads(native_audit_path.read_text(encoding="utf-8"))
    query_precheck_path = out_dir / "QUERY_PATH_PRECHECK.json"
    if not query_precheck_path.is_file():
        raise FileNotFoundError(query_precheck_path)
    query_precheck = json.loads(query_precheck_path.read_text(encoding="utf-8"))
    if query_precheck.get("status") != "PASS":
        raise RuntimeError("query-path precheck did not pass")
    code_paths = [
        repo / "tools/query_sensing_support_design_routes.py",
        repo / "tools/audit_sensing_support_upper_bound.py",
        repo / "tools/score_sensing_support_upper_bound.py",
        repo / "tools/query_synchronized_pair_from_raw_cache.py",
        repo / "tools/merge_sensing_support_query_summaries.py",
    ]
    route_files = []
    maximum_midpoint_error = 0.0
    maximum_separation_error = 0.0
    for item in manifest["candidates"]:
        route_dir = repo / "experiments/active_observability_v1/candidates" / item["route_id"]
        for filename in ("CENTER.csv", "PLUS.csv", "MINUS.csv"):
            path = route_dir / filename
            route_files.append({"path": path.relative_to(repo).as_posix(), "sha256": sha256_file(path)})
        with (route_dir / "CENTER.csv").open(newline="", encoding="utf-8") as stream:
            center_rows = list(csv.DictReader(stream))
        with (route_dir / "PLUS.csv").open(newline="", encoding="utf-8") as stream:
            plus_all = list(csv.DictReader(stream))
        with (route_dir / "MINUS.csv").open(newline="", encoding="utf-8") as stream:
            minus_all = list(csv.DictReader(stream))
        for wind in ("W_fast", "W_slow"):
            plus_rows = [row for row in plus_all if row["wind_id"] == wind]
            minus_rows = [row for row in minus_all if row["wind_id"] == wind]
            for center, plus, minus in zip(center_rows, plus_rows, minus_rows):
                c = [float(center[key]) for key in ("x", "y", "z")]
                p = [float(plus[key]) for key in ("x", "y", "z")]
                m = [float(minus[key]) for key in ("x", "y", "z")]
                maximum_midpoint_error = max(maximum_midpoint_error, *(abs((p[i] + m[i]) / 2.0 - c[i]) for i in range(3)))
                maximum_separation_error = max(maximum_separation_error, abs(math.dist(p, m) - 2.0))
    policy = {
        "schema": "SENSING_SUPPORT_MEASUREMENT_POLICY_FREEZE_V1",
        "frozen_before_aggregate_source_separation_scoring": True,
        "execution_starting_sha": args.starting_sha,
        "policy_parent_commit_sha": args.policy_parent_sha,
        "pre_response_route_freeze_sha": "6d5ea8fc0e67990f7750c7e86b010368dda88221",
        "continuation_contract": {
            "path": "docs/CODEX_SENSING_SUPPORT_UPPER_BOUND_V1_20260914.md",
            "sha256": sha256_file(repo / "docs/CODEX_SENSING_SUPPORT_UPPER_BOUND_V1_20260914.md"),
        },
        "candidate_manifest": {"path": manifest_path.relative_to(repo).as_posix(), "sha256": sha256_file(manifest_path)},
        "candidate_route_files": route_files,
        "pre_response_integrity": {
            "candidate_hash_failures": sum(
                item["sha256"] != next(
                    candidate[key] for candidate in manifest["candidates"] if candidate["route_id"] in item["path"]
                    for key, filename in (("center_sha256", "CENTER.csv"), ("plus_sha256", "PLUS.csv"), ("minus_sha256", "MINUS.csv"))
                    if item["path"].endswith(filename)
                )
                for item in route_files
            ),
            "maximum_midpoint_coordinate_error": maximum_midpoint_error,
            "maximum_separation_error_m": maximum_separation_error,
            "native_geometry_audit": {
                "path": native_audit_path.relative_to(repo).as_posix(),
                "sha256": sha256_file(native_audit_path),
                "total_endpoint_samples": native_audit["total_endpoint_samples"],
                "total_pairs": native_audit["total_pairs"],
                "total_failures": native_audit["total_failures"],
                "all_pass": native_audit["all_pass"],
                "binding_rule": "candidate byte hashes identical to the inputs of the frozen native GADEN audit",
            },
            "query_path_precheck": {
                "path": query_precheck_path.relative_to(repo).as_posix(),
                "sha256": sha256_file(query_precheck_path),
                "status": query_precheck["status"],
                "plus_query_valid_finite": query_precheck["plus_query_valid_finite"],
                "minus_query_valid_finite": query_precheck["minus_query_valid_finite"],
                "non_design_wind_queried": query_precheck["non_design_wind_queried"],
            },
        },
        "code": [{"path": path.relative_to(repo).as_posix(), "sha256": sha256_file(path)} for path in code_paths],
        "frozen_conditions": {
            "house": "House02",
            "sources": ["S_truth", "S_k01", "S_k10", "S_k22"],
            "design_winds": ["W_fast", "W_slow"],
            "held_wind_response_access": "FORBIDDEN_IN_THIS_STAGE",
            "route_ids": [f"AO_{index:02d}" for index in range(12)],
            "altitude_m": 0.4,
            "speed_mps": 0.35,
            "duration_s": 150.0,
            "cadence_s": 0.2,
            "separation_m": 2.0,
            "fopdt": {"dead_s": 0.4, "rise_s": 1.2, "recovery_s": 1.2, "dt_s": 0.2},
        },
        "configurations": {
            "C0": {"name": "S1_CENTER_PROCESSED_FOPDT", "channels": ["center_processed"], "role": "reference"},
            "C1": {"name": "S1_CENTER_RAW_ORACLE", "channels": ["center_raw"], "role": "oracle_diagnostic"},
            "C2": {"name": "D2_TWO_CHANNEL_PROCESSED_FOPDT", "channels": ["plus_processed", "minus_processed"], "ordered": True, "difference": False, "role": "deployable_candidate"},
            "C3": {"name": "D2_TWO_CHANNEL_RAW_ORACLE", "channels": ["plus_raw", "minus_raw"], "ordered": True, "difference": False, "role": "oracle_diagnostic"},
        },
        "gates": {
            "rank": 3,
            "rank_tolerance": "numpy matrix_rank default",
            "sigma3_sigma1_minimum": 0.05,
            "q_energy_minimum": 0.01,
            "q_energy_windows_s": [5.0, 10.0],
            "q_energy_psd_roundoff_rule": "clamp negative ratio to zero only",
            "exact_source_pair_collisions": 0,
            "hit_floor_ppm": 0.1,
            "minimum_exposed_temporal_thirds_per_source": 2,
            "two_channel_exposure": "union of plus and minus above hit floor; also report plus, minus, union, overlap",
            "route_pass": "all gates pass in both design winds",
        },
        "route_ranking_lexicographic": [
            "number of design winds with numerical rank 3",
            "worst-design-wind sigma3/sigma1",
            "worst-design-wind maximum corrected Q_energy over frozen 5 s and 10 s windows",
            "minimum source exposure count and minimum number of exposed temporal thirds",
            "lower total absolute heading change",
            "route_id",
        ],
        "new_gaden": False,
        "posterior_used": False,
        "likelihood_used": False,
    }
    freeze_path = out_dir / "MEASUREMENT_POLICY_FREEZE.json"
    freeze_path.write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")
    hash_targets = [manifest_path, native_audit_path, query_precheck_path, *code_paths, *[repo / item["path"] for item in route_files], freeze_path]
    lines = [f"{sha256_file(path)}  {path.relative_to(repo).as_posix()}" for path in sorted(hash_targets, key=lambda p: p.relative_to(repo).as_posix())]
    (out_dir / "PRE_RESPONSE_SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"policy": str(freeze_path), "hash_entries": len(lines), "status": "PASS"}))


if __name__ == "__main__":
    main()
