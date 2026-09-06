#!/usr/bin/env python3
"""Fail-closed provenance audit for existing CSTAR/GADEN raw realizations.

The auditor intentionally does not infer physical provenance from directory names.
A normalized claim is accepted only when it is bound to one or more immutable
text evidence files whose SHA-256 and required literal tokens are verified.

This tool qualifies raw realizations for *later* controlled data extraction. It
never turns a raw field into an M2 do(route) case by itself.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

CONTRACT = "CSTAR_RAW_REALIZATION_PROVENANCE_V1"
ENV_CONTRACT = "CSTAR_ENVIRONMENT_ALIGNMENT_AUDIT_V1"
SPLIT_CONTRACT = "CSTAR_RAW_REALIZATION_SPLITS_V1"
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
ALLOWED_EVIDENCE_KINDS = {
    "generator_config", "generation_command", "frozen_run_manifest",
    "simulation_metadata", "simulation_header", "transport_config",
    "release_config", "sensor_config",
}
FORBIDDEN_SOURCE_KINDS = {"directory_name_only", "inferred_from_result"}


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


def resolve(base: Path, value: Any, label: str) -> Path:
    require(isinstance(value, str) and value.strip(), f"CSTAR_PROV_BAD_PATH:{label}")
    p = Path(value)
    return p if p.is_absolute() else (base / p)


def require_sha(value: Any, label: str) -> str:
    require(isinstance(value, str) and SHA_RE.fullmatch(value) is not None,
            f"CSTAR_PROV_BAD_SHA:{label}:{value}")
    return value


def check_file(path: Path, expected: str, label: str) -> None:
    require(path.is_file(), f"CSTAR_PROV_FILE_MISSING:{label}:{path}")
    actual = sha256_file(path)
    require(actual == expected,
            f"CSTAR_PROV_HASH_MISMATCH:{label}:{actual}:{expected}:{path}")


def source_xyz(row: dict[str, Any]) -> tuple[float, float, float]:
    xyz = row.get("source_xyz_m")
    require(isinstance(xyz, list) and len(xyz) == 3,
            f"CSTAR_PROV_SOURCE_XYZ:{row.get('realization_id')}")
    vals = tuple(float(v) for v in xyz)
    require(all(math.isfinite(v) for v in vals),
            f"CSTAR_PROV_SOURCE_NONFINITE:{row.get('realization_id')}")
    return vals


def check_evidence(base: Path, item: dict[str, Any], rid: str) -> dict[str, Any]:
    required = ("kind", "path", "sha256", "required_literals")
    missing = [k for k in required if k not in item]
    require(not missing, f"CSTAR_PROV_EVIDENCE_FIELDS:{rid}:{missing}")
    kind = str(item["kind"])
    require(kind in ALLOWED_EVIDENCE_KINDS,
            f"CSTAR_PROV_EVIDENCE_KIND:{rid}:{kind}")
    p = resolve(base, item["path"], f"evidence:{rid}:{kind}")
    expected = require_sha(item["sha256"], f"evidence:{rid}:{kind}")
    check_file(p, expected, f"evidence:{rid}:{kind}")
    raw = p.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            fail(f"CSTAR_PROV_EVIDENCE_NOT_TEXT:{rid}:{kind}:{p}")
    literals = item["required_literals"]
    require(isinstance(literals, list) and literals,
            f"CSTAR_PROV_EVIDENCE_LITERALS:{rid}:{kind}")
    missing_literals = [str(x) for x in literals if str(x) not in text]
    require(not missing_literals,
            f"CSTAR_PROV_EVIDENCE_LITERAL_MISSING:{rid}:{kind}:{missing_literals[:8]}")
    return {"kind": kind, "path": str(p), "sha256": expected,
            "literal_count": len(literals)}


def fingerprint(value: Any, label: str) -> str:
    require(isinstance(value, str) and value.strip(), f"CSTAR_PROV_FINGERPRINT:{label}")
    return value.strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    require(data.get("contract") == CONTRACT,
            f"CSTAR_PROV_CONTRACT:{data.get('contract')}")
    for key in (
        "created_git_sha", "environment_alignment_audit_path",
        "environment_alignment_audit_sha256", "prerequisite_inventory_path",
        "prerequisite_inventory_sha256", "frozen_split_manifest_path",
        "frozen_split_manifest_sha256", "entries",
    ):
        require(key in data, f"CSTAR_PROV_TOP_FIELD:{key}")
    base = args.manifest.parent

    inv_path = resolve(base, data["prerequisite_inventory_path"], "prerequisite_inventory")
    inv_sha = require_sha(data["prerequisite_inventory_sha256"], "prerequisite_inventory")
    check_file(inv_path, inv_sha, "prerequisite_inventory")
    inv = json.loads(inv_path.read_text(encoding="utf-8"))
    require(inv.get("contract") == "CSTAR_CONTROLLED_PREREQUISITE_INVENTORY_V1",
            f"CSTAR_PROV_INVENTORY_CONTRACT:{inv.get('contract')}")
    inv_entries = inv.get("entries", [])
    require(isinstance(inv_entries, list) and inv_entries, "CSTAR_PROV_INVENTORY_EMPTY")
    require(all(e.get("payload_read") is False for e in inv_entries),
            "CSTAR_PROV_INVENTORY_ALREADY_PAYLOAD_READ")

    env_path = resolve(base, data["environment_alignment_audit_path"], "env_audit")
    env_sha = require_sha(data["environment_alignment_audit_sha256"], "env_audit")
    check_file(env_path, env_sha, "env_audit")
    env = json.loads(env_path.read_text(encoding="utf-8"))
    require(env.get("contract") == ENV_CONTRACT and env.get("pass") is True,
            "CSTAR_PROV_ENVIRONMENT_NOT_PASS")

    split_path = resolve(base, data["frozen_split_manifest_path"], "split_manifest")
    split_sha = require_sha(data["frozen_split_manifest_sha256"], "split_manifest")
    check_file(split_path, split_sha, "split_manifest")
    split = json.loads(split_path.read_text(encoding="utf-8"))
    require(split.get("contract") == SPLIT_CONTRACT,
            f"CSTAR_PROV_SPLIT_CONTRACT:{split.get('contract')}")
    require(split.get("status") == "FROZEN_BEFORE_PAYLOAD_READ",
            f"CSTAR_PROV_SPLIT_NOT_PREFROZEN:{split.get('status')}")
    require(split.get("frozen_from_inventory_sha256") == inv_sha,
            "CSTAR_PROV_SPLIT_INVENTORY_HASH_MISMATCH")
    split_records = {r["realization_id"]: r for r in split.get("records", [])}
    require(split_records, "CSTAR_PROV_SPLIT_RECORDS_EMPTY")
    inv_key = {(str(e["house"]).replace("House", "H"), str(e["config"]), str(e["resolved_realization_path"]))
               for e in inv_entries}
    split_key = {(str(r["house"]), str(r["config_id"]), str(r["resolved_realization_path"]))
                 for r in split_records.values()}
    require(inv_key == split_key, "CSTAR_PROV_SPLIT_INVENTORY_ENTRY_MISMATCH")

    entries = data["entries"]
    require(isinstance(entries, list) and entries, "CSTAR_PROV_NO_ENTRIES")
    seen: set[str] = set()
    normalized = []
    blocked = []
    for row in entries:
        require(isinstance(row, dict), "CSTAR_PROV_ENTRY_TYPE")
        for key in (
            "realization_id", "house", "geometry_identity", "config_id",
            "simulation_dir_path", "source_xyz_m", "gas_type_id",
            "source_authority", "release_fingerprint", "transport_fingerprint",
            "sensor_mechanism_fingerprint", "provenance_evidence",
        ):
            require(key in row, f"CSTAR_PROV_ENTRY_FIELD:{row.get('realization_id')}:{key}")
        rid = str(row["realization_id"])
        require(rid not in seen, f"CSTAR_PROV_DUP_REALIZATION:{rid}")
        seen.add(rid)
        sr = split_records.get(rid)
        require(sr is not None, f"CSTAR_PROV_NOT_IN_FROZEN_SPLIT:{rid}")
        house = str(row["house"])
        require(house == sr.get("house"), f"CSTAR_PROV_HOUSE_SPLIT_MISMATCH:{rid}")
        require(str(row["config_id"]) == sr.get("config_id"),
                f"CSTAR_PROV_CONFIG_SPLIT_MISMATCH:{rid}")
        require(str(row["simulation_dir_path"]) == sr.get("resolved_realization_path"),
                f"CSTAR_PROV_PATH_SPLIT_MISMATCH:{rid}")
        require(Path(row["simulation_dir_path"]).is_dir(),
                f"CSTAR_PROV_SIM_DIR_MISSING:{rid}:{row['simulation_dir_path']}")
        env_house = env.get("houses", {}).get(house)
        require(isinstance(env_house, dict) and env_house.get("pass") is True,
                f"CSTAR_PROV_ENV_HOUSE:{rid}:{house}")
        require(row["geometry_identity"] == env_house.get("geometry_identity"),
                f"CSTAR_PROV_GEOMETRY:{rid}")
        xyz = source_xyz(row)
        gas = str(row["gas_type_id"])
        authority = str(row["source_authority"])
        release = fingerprint(row["release_fingerprint"], f"release:{rid}")
        transport = fingerprint(row["transport_fingerprint"], f"transport:{rid}")
        sensor = fingerprint(row["sensor_mechanism_fingerprint"], f"sensor:{rid}")
        evidence = row["provenance_evidence"]
        require(isinstance(evidence, list) and evidence,
                f"CSTAR_PROV_NO_EVIDENCE:{rid}")
        checked = [check_evidence(base, item, rid) for item in evidence]
        entry_block = []
        if authority in FORBIDDEN_SOURCE_KINDS:
            entry_block.append("SOURCE_AUTHORITY_NOT_PHYSICAL")
        if authority not in ALLOWED_EVIDENCE_KINDS:
            entry_block.append("SOURCE_AUTHORITY_KIND_UNSUPPORTED")
        if not any(e["kind"] == authority for e in checked):
            entry_block.append("SOURCE_AUTHORITY_NOT_BOUND_TO_EVIDENCE")
        rec = {
            "realization_id": rid, "house": house,
            "geometry_identity": row["geometry_identity"],
            "config_id": str(row["config_id"]),
            "source_xyz_m": list(xyz), "gas_type_id": gas,
            "source_authority": authority,
            "release_fingerprint": release,
            "transport_fingerprint": transport,
            "sensor_mechanism_fingerprint": sensor,
            "evidence": checked, "blocked_reasons": entry_block,
            "entry_provenance_pass": not entry_block,
        }
        normalized.append(rec)
        if entry_block:
            blocked.append({"realization_id": rid, "reasons": entry_block})

    require(set(split_records) == seen,
            f"CSTAR_PROV_ENTRY_SET_MISMATCH:manifest={len(seen)}:split={len(split_records)}")

    groups: dict[tuple, list[dict[str, Any]]] = {}
    for r in normalized:
        key = (r["house"], r["geometry_identity"], tuple(r["source_xyz_m"]), r["gas_type_id"])
        groups.setdefault(key, []).append(r)

    pair_results = []
    qualified_transport_pairs = 0
    qualified_general_pairs = 0
    for key, rows in sorted(groups.items(), key=lambda kv: str(kv[0])):
        if len(rows) < 2:
            pair_results.append({"exact_source_key": str(key), "status": "BLOCKED_NO_PAIR",
                                 "realization_ids": [r["realization_id"] for r in rows]})
            continue
        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                a, b = rows[i], rows[j]
                reasons = []
                if not a["entry_provenance_pass"] or not b["entry_provenance_pass"]:
                    reasons.append("ENTRY_PROVENANCE_BLOCKED")
                changes = {
                    "release": a["release_fingerprint"] != b["release_fingerprint"],
                    "transport": a["transport_fingerprint"] != b["transport_fingerprint"],
                    "sensor": a["sensor_mechanism_fingerprint"] != b["sensor_mechanism_fingerprint"],
                }
                if not any(changes.values()):
                    reasons.append("NO_NUISANCE_DIFFERENCE")
                if reasons:
                    status = "BLOCKED_PROVENANCE"
                elif changes == {"release": False, "transport": True, "sensor": False}:
                    status = "QUALIFIED_M1_TRANSPORT_PAIR"
                    qualified_transport_pairs += 1
                else:
                    status = "QUALIFIED_M1_GENERAL_NUISANCE_PAIR"
                    qualified_general_pairs += 1
                pair_results.append({
                    "exact_source_key": str(key),
                    "realization_ids": [a["realization_id"], b["realization_id"]],
                    "changes": changes, "status": status, "reasons": reasons,
                })

    raw_route_eligible = [r["realization_id"] for r in normalized if r["entry_provenance_pass"]]
    qualified_group_keys = {p["exact_source_key"] for p in pair_results
                            if p.get("status") in {"QUALIFIED_M1_TRANSPORT_PAIR",
                                                   "QUALIFIED_M1_GENERAL_NUISANCE_PAIR"}}
    all_group_keys = {str(k) for k in groups}
    source_groups_per_house = {}
    qualified_groups_per_house = {}
    for k in groups:
        house = k[0]
        source_groups_per_house[house] = source_groups_per_house.get(house, 0) + 1
        if str(k) in qualified_group_keys:
            qualified_groups_per_house[house] = qualified_groups_per_house.get(house, 0) + 1
    houses = sorted(source_groups_per_house)
    all_groups_qualified = qualified_group_keys == all_group_keys
    house_source_diverse = all(source_groups_per_house[h] >= 2 for h in houses)
    house_groups_qualified = all(qualified_groups_per_house.get(h, 0) == source_groups_per_house[h]
                                 for h in houses)
    passed = bool(houses) and not blocked and all_groups_qualified and house_source_diverse and house_groups_qualified
    report = {
        "contract": "CSTAR_RAW_REALIZATION_PROVENANCE_AUDIT_V1",
        "pass": passed,
        "manifest_sha256": sha256_file(args.manifest),
        "prerequisite_inventory_sha256": inv_sha,
        "environment_alignment_audit_sha256": env_sha,
        "frozen_split_manifest_sha256": split_sha,
        "entry_count": len(normalized),
        "entry_provenance_pass_count": sum(r["entry_provenance_pass"] for r in normalized),
        "blocked_entries": blocked,
        "pair_results": pair_results,
        "qualified_m1_transport_pair_count": qualified_transport_pairs,
        "qualified_m1_general_nuisance_pair_count": qualified_general_pairs,
        "exact_source_group_count": len(all_group_keys),
        "qualified_exact_source_group_count": len(qualified_group_keys),
        "source_groups_per_house": source_groups_per_house,
        "qualified_groups_per_house": qualified_groups_per_house,
        "all_exact_source_groups_qualified": all_groups_qualified,
        "each_house_source_diverse": house_source_diverse,
        "each_house_all_groups_qualified": house_groups_qualified,
        "raw_realizations_eligible_for_future_truth_blind_route_extraction": raw_route_eligible,
        "qualified_m2_route_case_count": 0,
        "m2_status": "NOT_YET_ROUTE_CONTROLLED",
        "deployment_bank_free": True,
        "verdict": (
            "CSTAR_RAW_REALIZATION_PROVENANCE=PASS"
            if passed else "CSTAR_RAW_REALIZATION_PROVENANCE=BLOCKED"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(report["verdict"])
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
