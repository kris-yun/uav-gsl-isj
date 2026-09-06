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


def source_key(row: dict) -> tuple[float, float, float]:
    xyz = row["source_xyz_m"]
    require(isinstance(xyz, list) and len(xyz) == 3,
            f"CSTAR_ASSET_BAD_SOURCE_XYZ:{row.get('episode_id', row.get('decision_id'))}")
    vals = tuple(float(v) for v in xyz)
    require(all(math.isfinite(v) for v in vals), "CSTAR_ASSET_NONFINITE_SOURCE_XYZ")
    return vals


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    require(data.get("contract") == "CSTAR_CONTROLLED_CAUSAL_ASSET_V1",
            f"CSTAR_ASSET_BAD_CONTRACT:{data.get('contract')}")
    req_fields(data, contract["top_level_required"], "top")

    asset_root = resolve(args.manifest.parent, data["asset_root"], "asset_root")
    require(asset_root.is_dir(), f"CSTAR_ASSET_ROOT_MISSING:{asset_root}")
    splits = data["splits"]
    require(isinstance(splits, list) and len(splits) >= 2 and len(set(splits)) == len(splits),
            "CSTAR_ASSET_BAD_SPLITS")

    model_inputs = data["model_input_fields"]
    evaluator_only = data["evaluator_only_fields"]
    forbidden = data["forbidden_model_inputs"]
    require(isinstance(model_inputs, list) and isinstance(evaluator_only, list)
            and isinstance(forbidden, list), "CSTAR_ASSET_BAD_INPUT_FIELD_LISTS")
    forbidden_union = set(contract["forbidden_model_inputs"]) | set(forbidden)
    overlap = sorted(set(model_inputs) & forbidden_union)
    require(not overlap, f"CSTAR_ASSET_FORBIDDEN_MODEL_INPUTS:{','.join(overlap)}")

    m1_rows = data["m1_episodes"]
    require(isinstance(m1_rows, list) and m1_rows, "CSTAR_ASSET_NO_M1_EPISODES")
    m1_ids = set(); m1_by_source = {}; m1_source_by_split = {s:set() for s in splits}
    raw_sha_split = {}
    for row in m1_rows:
        require(isinstance(row, dict), "CSTAR_ASSET_BAD_M1_ROW")
        req_fields(row, contract["m1_episode_required_fields"], f"m1:{row.get('episode_id')}")
        eid = str(row["episode_id"])
        require(eid not in m1_ids, f"CSTAR_ASSET_DUP_M1_EPISODE:{eid}"); m1_ids.add(eid)
        split = row["split"]
        require(split in splits, f"CSTAR_ASSET_BAD_M1_SPLIT:{eid}:{split}")
        sk = source_key(row); m1_source_by_split[split].add(sk)
        require(row["candidate_domain_truth_independent"] is True,
                f"CSTAR_ASSET_M1_CANDIDATE_TRUTH_DEPENDENT:{eid}")
        require(row["sensor_state_kind"] in {"audited_fopdt_internal_state", "absent"},
                f"CSTAR_ASSET_M1_SENSOR_STATE_KIND:{eid}:{row['sensor_state_kind']}")
        hs = str(row["history_semantics"])
        require(hs == "causal_prefixes" or hs.startswith("bounded_causal_window_"),
                f"CSTAR_ASSET_M1_HISTORY_SEMANTICS:{eid}:{hs}")
        history_sha = check_file(asset_root, row, "history_trace_path", "history_trace_sha256", f"m1_history:{eid}")
        check_file(asset_root, row, "candidate_domain_path", "candidate_domain_sha256", f"m1_candidates:{eid}")
        old = raw_sha_split.get(history_sha)
        require(old is None or old == split,
                f"CSTAR_ASSET_RAW_HISTORY_SPLIT_LEAK:{eid}:{old}:{split}")
        raw_sha_split[history_sha] = split
        nuisance = (
            str(row["transport_intervention_id"]),
            str(row["release_intervention_id"]),
            str(row["sensor_intervention_id"]),
        )
        m1_by_source.setdefault((str(row["source_id"]), sk), set()).add(nuisance)

    underpaired = [key for key, nuis in m1_by_source.items() if len(nuis) < 2]
    require(not underpaired, f"CSTAR_ASSET_M1_SOURCE_WITHOUT_NUISANCE_PAIR:{underpaired[:5]}")
    for split, sources in m1_source_by_split.items():
        if any(row["split"] == split for row in m1_rows):
            require(len(sources) >= 2, f"CSTAR_ASSET_M1_NOT_SOURCE_DIVERSE:{split}:{len(sources)}")

    m2_rows = data["m2_route_cases"]
    require(isinstance(m2_rows, list) and m2_rows, "CSTAR_ASSET_NO_M2_ROUTE_CASES")
    m2_ids=set(); m2_source_by_split={s:set() for s in splits}; outcome_sha_split={}
    allowed=set(contract["m2_allowed_route_kinds"])
    for row in m2_rows:
        require(isinstance(row, dict), "CSTAR_ASSET_BAD_M2_ROW")
        req_fields(row, contract["m2_route_case_required_fields"], f"m2:{row.get('decision_id')}")
        did=str(row["decision_id"])
        require(did not in m2_ids, f"CSTAR_ASSET_DUP_M2_DECISION:{did}"); m2_ids.add(did)
        split=row["split"]
        require(split in splits, f"CSTAR_ASSET_BAD_M2_SPLIT:{did}:{split}")
        sk=source_key(row); m2_source_by_split[split].add(sk)
        require(row["route_kind"] in allowed,
                f"CSTAR_ASSET_M2_ROUTE_KIND:{did}:{row['route_kind']}")
        decision=float(row["decision_time_s"]); locked=float(row["route_locked_time_s"])
        require(math.isfinite(decision) and math.isfinite(locked) and locked <= decision,
                f"CSTAR_ASSET_M2_ROUTE_LOCK_TIME:{did}:{locked}:{decision}")
        require(row["route_locked_before_outcome"] is True,
                f"CSTAR_ASSET_M2_ROUTE_NOT_LOCKED:{did}")
        require(row["future_policy_dependent_path_used"] is False,
                f"CSTAR_ASSET_M2_RETROSPECTIVE_ADAPTIVE_PATH:{did}")
        require(row["execution_deviation_reported"] is True,
                f"CSTAR_ASSET_M2_EXECUTION_DEVIATION_MISSING:{did}")
        check_file(asset_root, row, "planned_route_path", "planned_route_sha256", f"m2_route:{did}")
        outcome_sha = check_file(asset_root, row, "outcome_trace_path", "outcome_trace_sha256", f"m2_outcome:{did}")
        old=outcome_sha_split.get(outcome_sha)
        require(old is None or old == split,
                f"CSTAR_ASSET_M2_OUTCOME_SPLIT_LEAK:{did}:{old}:{split}")
        outcome_sha_split[outcome_sha]=split

    for split, sources in m2_source_by_split.items():
        if any(row["split"] == split for row in m2_rows):
            require(len(sources) >= 2, f"CSTAR_ASSET_M2_NOT_SOURCE_DIVERSE:{split}:{len(sources)}")

    report = {
        "contract": "CSTAR_CONTROLLED_CAUSAL_ASSET_AUDIT_V1",
        "pass": True,
        "manifest_path": str(args.manifest.resolve()),
        "manifest_sha256": sha256_file(args.manifest),
        "contract_sha256": sha256_file(CONTRACT_PATH),
        "m1_episode_count": len(m1_rows),
        "m1_exact_source_count": len(m1_by_source),
        "m1_same_source_intervention_groups": len(m1_by_source),
        "m2_route_case_count": len(m2_rows),
        "m2_distinct_source_count": len({source_key(r) for r in m2_rows}),
        "formal_gate_authority": False,
        "verdict": "CSTAR_CONTROLLED_CAUSAL_ASSET_AUDIT=PASS",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print(report["verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
