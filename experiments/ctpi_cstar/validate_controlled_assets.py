#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
CONTRACT_PATH = HERE / "CSTAR_CONTROLLED_CAUSAL_ASSET_CONTRACT_V1.json"
SHA_RE = re.compile(r"^[0-9a-f]{64}$")


def fail(code: str) -> None:
    raise RuntimeError(code)


def require(cond: bool, code: str) -> None:
    if not cond:
        fail(code)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def req_fields(obj: dict, fields: list[str], label: str) -> None:
    missing = [k for k in fields if k not in obj]
    require(not missing, f"CSTAR_ASSET_FIELDS_MISSING:{label}:{','.join(missing)}")


def resolve(base: Path, value, label: str) -> Path:
    require(isinstance(value, str) and value.strip() != "", f"CSTAR_ASSET_BAD_PATH:{label}")
    p = Path(value)
    return p if p.is_absolute() else base / p


def check_file(base: Path, row: dict, path_field: str, sha_field: str, label: str) -> str:
    p = resolve(base, row[path_field], f"{label}:{path_field}")
    require(p.is_file(), f"CSTAR_ASSET_FILE_MISSING:{label}:{p}")
    expected = row[sha_field]
    require(isinstance(expected, str) and SHA_RE.fullmatch(expected) is not None,
            f"CSTAR_ASSET_BAD_SHA:{label}:{sha_field}:{expected}")
    actual = sha256_file(p)
    require(actual == expected,
            f"CSTAR_ASSET_HASH_MISMATCH:{label}:{p}:{expected}:{actual}")
    return actual


def source_xyz(row: dict) -> tuple[float, float, float]:
    xyz = row["source_xyz_m"]
    require(isinstance(xyz, list) and len(xyz) == 3,
            f"CSTAR_ASSET_BAD_SOURCE_XYZ:{row.get('episode_id', row.get('decision_id'))}")
    vals = tuple(float(v) for v in xyz)
    require(all(math.isfinite(v) for v in vals), "CSTAR_ASSET_NONFINITE_SOURCE_XYZ")
    return vals


def source_key(row: dict) -> tuple[str, str, tuple[float, float, float]]:
    return str(row["house"]), str(row["geometry_identity"]), source_xyz(row)


def realization_key(row: dict) -> tuple[str, str, str]:
    rid = str(row["realization_id"])
    require(rid.strip() != "", "CSTAR_ASSET_EMPTY_REALIZATION_ID")
    return str(row["house"]), str(row["geometry_identity"]), rid


def bind_split(table: dict, key, split: str, code: str) -> None:
    old = table.get(key)
    require(old is None or old == split, f"{code}:{key}:{old}:{split}")
    table[key] = split


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    manifest_path = args.manifest.resolve()
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    require(data.get("contract") == "CSTAR_CONTROLLED_CAUSAL_ASSET_V1",
            f"CSTAR_ASSET_BAD_CONTRACT:{data.get('contract')}")
    req_fields(data, contract["top_level_required"], "top")

    # Formal controlled assets are subordinate to the already-passed three-House
    # environment alignment.  This closes the old geometry_identity-as-text loophole.
    env_path = resolve(manifest_path.parent, data["environment_alignment_audit_path"],
                       "environment_alignment_audit")
    require(env_path.is_file(), f"CSTAR_ASSET_ENV_AUDIT_MISSING:{env_path}")
    expected_env_sha = data["environment_alignment_audit_sha256"]
    require(isinstance(expected_env_sha, str) and SHA_RE.fullmatch(expected_env_sha) is not None,
            "CSTAR_ASSET_ENV_AUDIT_BAD_SHA")
    actual_env_sha = sha256_file(env_path)
    require(actual_env_sha == expected_env_sha,
            f"CSTAR_ASSET_ENV_AUDIT_HASH:{expected_env_sha}:{actual_env_sha}")
    env = json.loads(env_path.read_text(encoding="utf-8"))
    require(env.get("contract") == "CSTAR_ENVIRONMENT_ALIGNMENT_AUDIT_V1"
            and env.get("pass") is True
            and env.get("verdict") == "CSTAR_ENVIRONMENT_ALIGNMENT=PASS",
            "CSTAR_ASSET_ENVIRONMENT_NOT_ALIGNED")
    env_houses = env.get("houses")
    require(isinstance(env_houses, dict) and set(env_houses) == {"H01", "H02", "H03"},
            "CSTAR_ASSET_ENVIRONMENT_HOUSES")
    geometry_by_house = {
        h: str(env_houses[h]["geometry_identity"]) for h in ("H01", "H02", "H03")
    }

    # These references were previously required syntactically but not read.
    def bound_json(path_key, sha_key):
        check_file(manifest_path.parent, data, path_key, sha_key, path_key)
        return json.loads(resolve(manifest_path.parent, data[path_key], path_key).read_text(encoding="utf-8"))

    provenance = bound_json("raw_realization_provenance_audit_path", "raw_realization_provenance_audit_sha256")
    req_fields(data, ["wind_index_correction_audit_path", "wind_index_correction_audit_sha256"], "wind_correction")
    wind_correction = bound_json("wind_index_correction_audit_path", "wind_index_correction_audit_sha256")
    require(wind_correction.get("contract") == "CSTAR_NUMERIC_WIND_RUNTIME_CORRECTION_V1"
            and wind_correction.get("pass") is True
            and wind_correction.get("environment_audit_sha256") == actual_env_sha,
            "CSTAR_ASSET_WIND_CORRECTION_NOT_BOUND")
    frozen = bound_json("frozen_realization_split_path", "frozen_realization_split_sha256")
    require(provenance.get("contract") == "CSTAR_RAW_REALIZATION_PROVENANCE_AUDIT_V1"
            and provenance.get("pass") is True, "CSTAR_ASSET_PROVENANCE_NOT_PASS")
    require(provenance.get("environment_alignment_audit_sha256") == actual_env_sha,
            "CSTAR_ASSET_PROVENANCE_ENVIRONMENT_MISMATCH")
    require(provenance.get("frozen_split_manifest_sha256") == data["frozen_realization_split_sha256"],
            "CSTAR_ASSET_PROVENANCE_SPLIT_MISMATCH")
    require(frozen.get("contract") == "CSTAR_RAW_REALIZATION_SPLITS_V1", "CSTAR_ASSET_SPLIT_CONTRACT")
    held = data.get("outer_fold")
    require(held in {"H01", "H02", "H03"}, "CSTAR_ASSET_OUTER_FOLD_MISSING")
    fold = frozen["outer_folds"][held]
    roles = {rid: "train" for rid in fold["train_realization_ids"]}
    require(not set(roles) & set(fold["heldout_realization_ids"]), "CSTAR_ASSET_FROZEN_FOLD_LEAK")
    roles.update({rid: "heldout" for rid in fold["heldout_realization_ids"]})
    qualified = {e["realization_id"]: e for e in provenance["normalized_entries"] if e["entry_provenance_pass"]}
    require(set(roles) == set(qualified) and len(roles) == 12, "CSTAR_ASSET_PARENT_COVERAGE")
    for rid, entry in qualified.items():
        require((entry["house"] == held) == (roles[rid] == "heldout"), "CSTAR_ASSET_LOHO_CONTRADICTION")

    req_fields(data, ["route_freeze_path", "route_freeze_sha256", "route_freeze_git_sha"], "route_lock")
    route_freeze = bound_json("route_freeze_path", "route_freeze_sha256")
    require(data["route_freeze_sha256"] == "c3001aeb1a7b425e7b3354a55f0f17f47412dd7b45c1380de3b7ea7c186e199f"
            and data["route_freeze_git_sha"] == "d3fa825a2da06a308af6bb6398d5f5a43e5b701a",
            "CSTAR_ASSET_UNREGISTERED_ROUTE_FREEZE")
    allowed_routes = {r["sha256"]: (h, r["decision_time_s"]) for h, d in route_freeze["houses"].items()
                      for r in d["routes"]}
    sensor_identity = sha256_file(env_path.parent / "probes_v1/H01/sensor_manifest.json")
    geometry_manifest = json.loads((env_path.parent / "maps_v1/geometry_manifest.json").read_text())

    def check_parent(row):
        rid = row["realization_id"]
        require(rid in qualified and row["split"] == roles[rid], "CSTAR_ASSET_PARENT_FROZEN_ROLE")
        entry = qualified[rid]
        physical = entry["physical_claims"]
        require(row["house"] == entry["house"] and row["geometry_identity"] == entry["geometry_identity"]
                and row["source_xyz_m"] == physical["source_xyz_m"], "CSTAR_ASSET_PARENT_SOURCE_IDENTITY")
        require(row["transport_intervention_id"] == physical["transport_fingerprint"],
                "CSTAR_ASSET_PARENT_TRANSPORT_IDENTITY")

    asset_root = resolve(manifest_path.parent, data["asset_root"], "asset_root")
    require(asset_root.is_dir(), f"CSTAR_ASSET_ROOT_MISSING:{asset_root}")
    splits = data["splits"]
    require(set(splits) == {"train", "heldout"}, "CSTAR_ASSET_FROZEN_ROLE_NAMES")
    require(isinstance(splits, list) and len(splits) >= 2 and len(set(splits)) == len(splits),
            "CSTAR_ASSET_BAD_SPLITS")
    require(all(isinstance(s, str) and s.strip() for s in splits), "CSTAR_ASSET_EMPTY_SPLIT")

    model_inputs = data["model_input_fields"]
    evaluator_only = data["evaluator_only_fields"]
    forbidden = data["forbidden_model_inputs"]
    require(isinstance(model_inputs, list) and isinstance(evaluator_only, list)
            and isinstance(forbidden, list), "CSTAR_ASSET_BAD_INPUT_FIELD_LISTS")
    forbidden_union = set(contract["forbidden_model_inputs"]) | set(forbidden)
    overlap = sorted(set(model_inputs) & forbidden_union)
    require(not overlap, f"CSTAR_ASSET_FORBIDDEN_MODEL_INPUTS:{','.join(overlap)}")
    require(not set(model_inputs) & set(evaluator_only), "CSTAR_ASSET_EVALUATOR_INPUT_OVERLAP")

    # Shared split identity across M1 and M2.  Different prefixes/files from the
    # same physical realization cannot cross train/heldout merely because their
    # SHA-256 values differ.
    realization_split = {}
    raw_sha_split = {}

    m1_rows = data["m1_episodes"]
    require(isinstance(m1_rows, list) and m1_rows, "CSTAR_ASSET_NO_M1_EPISODES")
    m1_ids = set()
    m1_by_source = {}
    m1_source_by_split = {s: set() for s in splits}
    m1_count_by_split = {s: 0 for s in splits}
    for row in m1_rows:
        require(isinstance(row, dict), "CSTAR_ASSET_BAD_M1_ROW")
        req_fields(row, contract["m1_episode_required_fields"], f"m1:{row.get('episode_id')}")
        check_parent(row)
        require(row["release_intervention_id"] == qualified[row["realization_id"]]["physical_claims"]["release_fingerprint"],
                "CSTAR_ASSET_PARENT_RELEASE_IDENTITY")
        require(row["sensor_intervention_id"] == sensor_identity, "CSTAR_ASSET_SENSOR_IDENTITY")
        require(row["candidate_domain_sha256"] == geometry_manifest[row["house"]]["free_space_probe_csvs"][0]["sha256"],
                "CSTAR_ASSET_CANDIDATE_NOT_FROZEN_DOMAIN")
        eid = str(row["episode_id"])
        require(eid not in m1_ids, f"CSTAR_ASSET_DUP_M1_EPISODE:{eid}")
        m1_ids.add(eid)
        split = row["split"]
        require(split in splits, f"CSTAR_ASSET_BAD_M1_SPLIT:{eid}:{split}")
        m1_count_by_split[split] += 1
        house = str(row["house"])
        require(house in geometry_by_house, f"CSTAR_ASSET_M1_HOUSE:{eid}:{house}")
        geom = str(row["geometry_identity"])
        require(geom == geometry_by_house[house],
                f"CSTAR_ASSET_M1_GEOMETRY_IDENTITY:{eid}:{geom}:{geometry_by_house[house]}")
        sk = source_key(row)
        m1_source_by_split[split].add(sk)
        bind_split(realization_split, realization_key(row), split,
                   "CSTAR_ASSET_REALIZATION_SPLIT_LEAK")
        require(row["candidate_domain_truth_independent"] is True,
                f"CSTAR_ASSET_M1_CANDIDATE_TRUTH_DEPENDENT:{eid}")
        require(row["sensor_state_kind"] in {"audited_fopdt_internal_state", "absent"},
                f"CSTAR_ASSET_M1_SENSOR_STATE_KIND:{eid}:{row['sensor_state_kind']}")
        hs = str(row["history_semantics"])
        require(hs == "causal_prefixes" or hs.startswith("bounded_causal_window_"),
                f"CSTAR_ASSET_M1_HISTORY_SEMANTICS:{eid}:{hs}")
        start = float(row["history_start_s"])
        end = float(row["history_end_s"])
        require(math.isfinite(start) and math.isfinite(end) and 0 <= start < end,
                f"CSTAR_ASSET_M1_HISTORY_INTERVAL:{eid}:{start}:{end}")
        history_sha = check_file(asset_root, row, "history_trace_path", "history_trace_sha256",
                                 f"m1_history:{eid}")
        check_file(asset_root, row, "candidate_domain_path", "candidate_domain_sha256",
                   f"m1_candidates:{eid}")
        bind_split(raw_sha_split, ("history", history_sha), split,
                   "CSTAR_ASSET_RAW_HISTORY_SPLIT_LEAK")
        nuisance = (
            str(row["transport_intervention_id"]),
            str(row["release_intervention_id"]),
            str(row["sensor_intervention_id"]),
        )
        # Do not trust source_id naming to define an exact source pair.
        m1_by_source.setdefault((split, sk), set()).add(nuisance)

    underpaired = [key for key, nuis in m1_by_source.items() if len(nuis) < 2]
    require(not underpaired,
            f"CSTAR_ASSET_M1_SOURCE_WITHOUT_NUISANCE_PAIR:{underpaired[:5]}")
    for split in splits:
        require(m1_count_by_split[split] > 0, f"CSTAR_ASSET_M1_EMPTY_SPLIT:{split}")
        require(len(m1_source_by_split[split]) >= 2,
                f"CSTAR_ASSET_M1_NOT_SOURCE_DIVERSE:{split}:{len(m1_source_by_split[split])}")
    require({r["realization_id"] for r in m1_rows} == set(qualified), "CSTAR_ASSET_M1_MISSING_PARENT")
    m1_lookup = {r["episode_id"]: r for r in m1_rows}

    m2_rows = data["m2_route_cases"]
    require(isinstance(m2_rows, list) and m2_rows, "CSTAR_ASSET_NO_M2_ROUTE_CASES")
    m2_ids = set()
    m2_source_by_split = {s: set() for s in splits}
    m2_count_by_split = {s: 0 for s in splits}
    outcome_realization_split = {}
    allowed = set(contract["m2_allowed_route_kinds"])
    for row in m2_rows:
        require(isinstance(row, dict), "CSTAR_ASSET_BAD_M2_ROW")
        req_fields(row, contract["m2_route_case_required_fields"], f"m2:{row.get('decision_id')}")
        check_parent(row)
        require(row["episode_id"] in m1_lookup and
                m1_lookup[row["episode_id"]]["realization_id"] == row["realization_id"],
                "CSTAR_ASSET_M2_HISTORY_PARENT_MISMATCH")
        did = str(row["decision_id"])
        require(did not in m2_ids, f"CSTAR_ASSET_DUP_M2_DECISION:{did}")
        m2_ids.add(did)
        split = row["split"]
        require(split in splits, f"CSTAR_ASSET_BAD_M2_SPLIT:{did}:{split}")
        m2_count_by_split[split] += 1
        house = str(row["house"])
        require(house in geometry_by_house, f"CSTAR_ASSET_M2_HOUSE:{did}:{house}")
        geom = str(row["geometry_identity"])
        require(geom == geometry_by_house[house],
                f"CSTAR_ASSET_M2_GEOMETRY_IDENTITY:{did}:{geom}:{geometry_by_house[house]}")
        sk = source_key(row)
        m2_source_by_split[split].add(sk)
        bind_split(realization_split, realization_key(row), split,
                   "CSTAR_ASSET_REALIZATION_SPLIT_LEAK")
        outcome_rid = str(row["outcome_realization_id"])
        require(outcome_rid.strip() != "", f"CSTAR_ASSET_M2_EMPTY_OUTCOME_REALIZATION:{did}")
        require(outcome_rid == row["realization_id"], "CSTAR_ASSET_M2_OUTCOME_PARENT_MISMATCH")
        bind_split(realization_split, (house, geom, outcome_rid), split,
                   "CSTAR_ASSET_REALIZATION_SPLIT_LEAK")
        bind_split(outcome_realization_split, (house, geom, outcome_rid), split,
                   "CSTAR_ASSET_M2_OUTCOME_REALIZATION_SPLIT_LEAK")
        require(row["route_kind"] in allowed,
                f"CSTAR_ASSET_M2_ROUTE_KIND:{did}:{row['route_kind']}")
        decision = float(row["decision_time_s"])
        locked = float(row["route_locked_time_s"])
        require(math.isfinite(decision) and math.isfinite(locked) and locked <= decision,
                f"CSTAR_ASSET_M2_ROUTE_LOCK_TIME:{did}:{locked}:{decision}")
        require(row["route_locked_before_outcome"] is True,
                f"CSTAR_ASSET_M2_ROUTE_NOT_LOCKED:{did}")
        require(row["future_policy_dependent_path_used"] is False,
                f"CSTAR_ASSET_M2_RETROSPECTIVE_ADAPTIVE_PATH:{did}")
        require(row["execution_deviation_reported"] is True,
                f"CSTAR_ASSET_M2_EXECUTION_DEVIATION_MISSING:{did}")
        route_sha = check_file(asset_root, row, "planned_route_path", "planned_route_sha256",
                               f"m2_route:{did}")
        outcome_sha = check_file(asset_root, row, "outcome_trace_path", "outcome_trace_sha256",
                                 f"m2_outcome:{did}")
        # Geometry-only plans may be shared; outcomes and parent identities may not.
        require(allowed_routes.get(route_sha) == (house, decision), "CSTAR_ASSET_ROUTE_NOT_FROZEN")
        bind_split(raw_sha_split, ("outcome", outcome_sha), split,
                   "CSTAR_ASSET_M2_OUTCOME_SPLIT_LEAK")

    for split in splits:
        require(m2_count_by_split[split] > 0, f"CSTAR_ASSET_M2_EMPTY_SPLIT:{split}")
        require(len(m2_source_by_split[split]) >= 2,
                f"CSTAR_ASSET_M2_NOT_SOURCE_DIVERSE:{split}:{len(m2_source_by_split[split])}")

    report = {
        "contract": "CSTAR_CONTROLLED_CAUSAL_ASSET_AUDIT_V1",
        "pass": True,
        "manifest_path": str(manifest_path),
        "manifest_sha256": sha256_file(manifest_path),
        "contract_sha256": sha256_file(CONTRACT_PATH),
        "environment_alignment_audit_path": str(env_path.resolve()),
        "environment_alignment_audit_sha256": actual_env_sha,
        "raw_provenance_and_frozen_fold_verified": True,
        "wind_index_correction_audit_sha256": data["wind_index_correction_audit_sha256"],
        "route_freeze_git_sha": data["route_freeze_git_sha"],
        "outer_fold": held,
        "geometry_identity_by_house": geometry_by_house,
        "m1_episode_count": len(m1_rows),
        "m1_exact_source_count": len(m1_by_source),
        "m1_same_source_intervention_groups": len(m1_by_source),
        "m1_count_by_split": m1_count_by_split,
        "m2_route_case_count": len(m2_rows),
        "m2_distinct_source_count": len({source_key(r) for r in m2_rows}),
        "m2_count_by_split": m2_count_by_split,
        "unique_physical_realization_count": len(realization_split),
        "unique_outcome_realization_count": len(outcome_realization_split),
        "prefix_split_leakage_checked_by_realization_id": True,
        "formal_gate_authority": False,
        "verdict": "CSTAR_CONTROLLED_CAUSAL_ASSET_AUDIT=PASS",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(report["verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
