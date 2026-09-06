#!/usr/bin/env python3
"""Fail-closed CSTAR formal closed-loop authorization.

Authorization is intentionally stronger than checking ``contract`` and
``pass=true``. It validates required fields, scientific control identities,
referenced raw artifacts/checkpoints, cross-artifact hashes and the production
git identity. Any missing or unverifiable item is a hard failure.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
REPO_DEFAULT = HERE.parents[1]
SCHEMA_PATH = HERE / "CSTAR_REQUIRED_EVIDENCE_CONTRACTS_V1.json"
REQUIRED = {
    "m1": ("M1", "CSTAR_M1_CONTROLLED_CAUSAL_GATE_V1"),
    "m2": ("M2", "CSTAR_M2_SOURCE_DIVERSE_PREDICTIVE_GATE_V1"),
    "m3": ("M3", "CSTAR_M3_COUNTERFACTUAL_GATE_V1"),
    "models": ("MODELS", "CSTAR_FROZEN_MODEL_MANIFEST_V1"),
    "production": ("PRODUCTION", "CSTAR_PRODUCTION_MODE_MANIFEST_V1"),
    "smoke": ("SMOKE", "CSTAR_RUNTIME_SMOKE_V1"),
}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(cond: bool, code: str) -> None:
    if not cond:
        raise RuntimeError(code)


def require_fields(obj: dict, fields: list[str], label: str) -> None:
    missing = [field for field in fields if field not in obj]
    require(not missing, f"CSTAR_AUTH_MISSING_FIELDS:{label}:{','.join(missing)}")


def require_sha(value, label: str) -> str:
    require(isinstance(value, str) and bool(SHA256_RE.fullmatch(value)),
            f"CSTAR_AUTH_BAD_SHA256:{label}:{value}")
    return value


def require_git_sha(value, label: str) -> str:
    require(isinstance(value, str) and bool(GIT_SHA_RE.fullmatch(value)),
            f"CSTAR_AUTH_BAD_GIT_SHA:{label}:{value}")
    return value


def resolve_path(owner: Path, value, label: str) -> Path:
    require(isinstance(value, str) and value.strip() != "",
            f"CSTAR_AUTH_BAD_PATH:{label}")
    path = Path(value)
    if not path.is_absolute():
        path = owner.parent / path
    return path


def require_file_identity(owner: Path, obj: dict, path_field: str,
                          sha_field: str, label: str) -> Path:
    path = resolve_path(owner, obj.get(path_field), f"{label}:{path_field}")
    require(path.is_file(), f"CSTAR_AUTH_REFERENCED_FILE_MISSING:{label}:{path}")
    expected = require_sha(obj.get(sha_field), f"{label}:{sha_field}")
    actual = sha256_file(path)
    require(actual == expected,
            f"CSTAR_AUTH_REFERENCED_FILE_HASH_MISMATCH:{label}:{path}:{expected}:{actual}")
    return path


def load_schema() -> dict:
    require(SCHEMA_PATH.is_file(), f"CSTAR_AUTH_SCHEMA_MISSING:{SCHEMA_PATH}")
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    require(schema.get("contract") == "CSTAR_REQUIRED_EVIDENCE_CONTRACTS_V1",
            "CSTAR_AUTH_BAD_REQUIRED_EVIDENCE_SCHEMA")
    return schema


def load(path: Path, label: str, schema: dict) -> dict:
    require(path.is_file(), f"CSTAR_AUTH_MISSING:{label}:{path}")
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"CSTAR_AUTH_JSON:{label}:{exc}") from exc
    schema_key, expected = REQUIRED[label]
    require(obj.get("contract") == expected,
            f"CSTAR_AUTH_CONTRACT:{label}:{obj.get('contract')}:{expected}")
    require(obj.get("pass") is True,
            f"CSTAR_AUTH_NOT_PASS:{label}:{obj.get('verdict')}")
    spec = schema["artifacts"][schema_key]
    require_fields(obj, spec["required_top_level_fields"], label)
    return obj


def require_nonempty_results(value, label: str) -> None:
    if isinstance(value, dict):
        require(bool(value), f"CSTAR_AUTH_EMPTY_RESULTS:{label}")
    elif isinstance(value, list):
        require(len(value) > 0, f"CSTAR_AUTH_EMPTY_RESULTS:{label}")
    else:
        raise RuntimeError(f"CSTAR_AUTH_BAD_RESULTS_TYPE:{label}:{type(value).__name__}")


def validate_training_asset(owner: Path, value, label: str) -> None:
    require(isinstance(value, dict), f"CSTAR_AUTH_BAD_TRAINING_ASSET:{label}")
    require_fields(value, ["manifest_path", "manifest_sha256", "split_sha256"], label)
    require_file_identity(owner, value, "manifest_path", "manifest_sha256", label)
    require_sha(value["split_sha256"], f"{label}:split_sha256")


def validate_m1(path: Path, obj: dict, schema: dict) -> None:
    require(isinstance(obj.get("producer_version"), str) and obj["producer_version"],
            "CSTAR_AUTH_M1_PRODUCER_VERSION")
    require_git_sha(obj.get("git_sha"), "m1")
    validate_training_asset(path, obj["training_asset_identity"], "m1_training_asset")
    require_sha(obj["training_config_sha256"], "m1_training_config")
    require_sha(obj["checkpoint_sha256"], "m1_checkpoint")
    require_nonempty_results(obj["heldout_results"], "m1_heldout_results")
    controls = obj["causal_controls"]
    require(isinstance(controls, dict), "CSTAR_AUTH_M1_CONTROLS_TYPE")
    for field in schema["artifacts"]["M1"]["required_causal_control_fields"]:
        require(field in controls, f"CSTAR_AUTH_M1_CONTROL_MISSING:{field}")
        require(controls[field] is True, f"CSTAR_AUTH_M1_CONTROL_FAIL:{field}")
    require_file_identity(path, obj, "raw_result_manifest_path",
                          "raw_result_manifest_sha256", "m1_raw_results")


def validate_m2(path: Path, obj: dict, schema: dict) -> None:
    require(isinstance(obj.get("producer_version"), str) and obj["producer_version"],
            "CSTAR_AUTH_M2_PRODUCER_VERSION")
    require_git_sha(obj.get("git_sha"), "m2")
    validate_training_asset(path, obj["training_asset_identity"], "m2_training_asset")
    require_sha(obj["training_config_sha256"], "m2_training_config")
    require_sha(obj["checkpoint_sha256"], "m2_checkpoint")
    require_nonempty_results(obj["heldout_results"], "m2_heldout_results")
    baselines = obj["baselines"]
    require(isinstance(baselines, dict), "CSTAR_AUTH_M2_BASELINES_TYPE")
    for name in schema["artifacts"]["M2"]["required_baselines"]:
        require(name in baselines and isinstance(baselines[name], dict) and baselines[name],
                f"CSTAR_AUTH_M2_BASELINE_MISSING:{name}")
    route = obj["route_intervention_identity"]
    require(isinstance(route, dict), "CSTAR_AUTH_M2_ROUTE_IDENTITY_TYPE")
    require_fields(route, schema["artifacts"]["M2"]["required_route_identity_fields"],
                   "m2_route_identity")
    require(route["kind"] in {"decision_locked_planned_route", "controlled_open_loop_route"},
            f"CSTAR_AUTH_M2_ROUTE_KIND:{route['kind']}")
    require(route["decision_time_locked"] is True,
            "CSTAR_AUTH_M2_ROUTE_NOT_DECISION_LOCKED")
    require(route["future_policy_dependent_path_used"] is False,
            "CSTAR_AUTH_M2_RETROSPECTIVE_ADAPTIVE_PATH_FORBIDDEN")
    require(route["execution_deviation_reported"] is True,
            "CSTAR_AUTH_M2_EXECUTION_DEVIATION_NOT_REPORTED")
    require_file_identity(path, obj, "raw_result_manifest_path",
                          "raw_result_manifest_sha256", "m2_raw_results")


def validate_m3(path: Path, obj: dict) -> None:
    require(isinstance(obj.get("producer_version"), str) and obj["producer_version"],
            "CSTAR_AUTH_M3_PRODUCER_VERSION")
    require_git_sha(obj.get("git_sha"), "m3")
    require(isinstance(obj.get("cases"), int) and obj["cases"] > 0,
            "CSTAR_AUTH_M3_CASE_COUNT")
    require(isinstance(obj.get("real"), dict) and obj["real"],
            "CSTAR_AUTH_M3_REAL_RESULTS")
    require(isinstance(obj.get("destructive_route_law_shuffle"), dict)
            and obj["destructive_route_law_shuffle"],
            "CSTAR_AUTH_M3_SHUFFLE_RESULTS")
    require(obj.get("mechanism_destroyed_by_shuffle") is True,
            "CSTAR_AUTH_M3_SHUFFLE_DID_NOT_DESTROY_MECHANISM")
    require_file_identity(path, obj, "raw_result_manifest_path",
                          "raw_result_manifest_sha256", "m3_raw_results")


def validate_models(path: Path, obj: dict) -> None:
    require_git_sha(obj.get("git_sha"), "models")
    require_file_identity(path, obj, "m1_checkpoint", "m1_checkpoint_sha256", "m1_checkpoint")
    require_file_identity(path, obj, "m2_checkpoint", "m2_checkpoint_sha256", "m2_checkpoint")
    require_file_identity(path, obj, "training_config_path", "training_config_sha256", "training_config")
    require_file_identity(path, obj, "normalization_manifest_path",
                          "normalization_manifest_sha256", "normalization_manifest")
    require(isinstance(obj.get("input_schema_version"), str) and obj["input_schema_version"],
            "CSTAR_AUTH_MODEL_INPUT_SCHEMA_VERSION")


def validate_production(path: Path, obj: dict, models_path: Path, models: dict) -> None:
    git_sha = require_git_sha(obj.get("git_sha"), "production")
    require(obj.get("mode") == "cstar_v1", f"CSTAR_AUTH_PRODUCTION_MODE:{obj.get('mode')}")
    require(obj.get("model_manifest_sha256") == sha256_file(models_path),
            "CSTAR_AUTH_MODEL_MANIFEST_HASH_MISMATCH")
    require(isinstance(obj.get("runtime_inputs"), list) and obj["runtime_inputs"],
            "CSTAR_AUTH_RUNTIME_INPUTS")
    require(isinstance(obj.get("forbidden_runtime_inputs"), list)
            and obj["forbidden_runtime_inputs"], "CSTAR_AUTH_FORBIDDEN_INPUTS")
    require(isinstance(obj.get("fallback_policy"), dict) and obj["fallback_policy"],
            "CSTAR_AUTH_FALLBACK_POLICY")
    require(isinstance(obj.get("route_contract"), dict) and obj["route_contract"],
            "CSTAR_AUTH_ROUTE_CONTRACT")
    require_file_identity(path, obj, "production_artifact_path",
                          "production_artifact_sha256", "production_artifact")
    require(git_sha != "0" * 40, "CSTAR_AUTH_ZERO_PRODUCTION_GIT_SHA")


def validate_smoke(path: Path, obj: dict, production_path: Path, production: dict) -> None:
    require_git_sha(obj.get("git_sha"), "smoke")
    require(obj["git_sha"] == production["git_sha"], "CSTAR_AUTH_SMOKE_GIT_MISMATCH")
    require(obj.get("production_manifest_sha256") == sha256_file(production_path),
            "CSTAR_AUTH_PRODUCTION_MANIFEST_HASH_MISMATCH")
    zero_fields = [
        "future_read_violations", "truth_or_house_runtime_reads",
        "deployment_bank_queries", "invalid_route_count",
        "native_route_missing_when_feasible", "fallback_count",
    ]
    for field in zero_fields:
        require(type(obj.get(field)) is int and obj[field] == 0,
                f"CSTAR_AUTH_SMOKE_NONZERO_OR_BAD_TYPE:{field}:{obj.get(field)}")
    require(type(obj.get("decision_count")) is int and obj["decision_count"] > 0,
            "CSTAR_AUTH_SMOKE_NO_DECISIONS")
    for field in ("picr_calls", "phs_calls", "learned_cpo_calls"):
        require(type(obj.get(field)) is int and obj[field] > 0,
                f"CSTAR_AUTH_SMOKE_MODULE_NOT_EXERCISED:{field}:{obj.get(field)}")
    require(isinstance(obj.get("timing_summary"), dict) and obj["timing_summary"],
            "CSTAR_AUTH_SMOKE_TIMING_SUMMARY")
    require_file_identity(path, obj, "raw_audit_path", "raw_audit_sha256", "smoke_raw_audit")


def current_git_sha(repo_root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"], text=True
        ).strip()
    except Exception as exc:
        raise RuntimeError(f"CSTAR_AUTH_GIT_READ_FAILED:{repo_root}") from exc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--m1", type=Path, required=True)
    ap.add_argument("--m2", type=Path, required=True)
    ap.add_argument("--m3", type=Path, required=True)
    ap.add_argument("--models", type=Path, required=True)
    ap.add_argument("--production", type=Path, required=True)
    ap.add_argument("--smoke", type=Path, required=True)
    ap.add_argument("--repo-root", type=Path, default=REPO_DEFAULT)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    schema = load_schema()
    inputs = {name: getattr(args, name) for name in REQUIRED}
    loaded = {name: load(path, name, schema) for name, path in inputs.items()}

    validate_m1(args.m1, loaded["m1"], schema)
    validate_m2(args.m2, loaded["m2"], schema)
    validate_m3(args.m3, loaded["m3"])
    validate_models(args.models, loaded["models"])
    validate_production(args.production, loaded["production"], args.models, loaded["models"])
    validate_smoke(args.smoke, loaded["smoke"], args.production, loaded["production"])

    models = loaded["models"]
    m1 = loaded["m1"]
    m2 = loaded["m2"]
    production = loaded["production"]
    require(m1["checkpoint_sha256"] == models["m1_checkpoint_sha256"],
            "CSTAR_AUTH_M1_GATE_CHECKPOINT_MISMATCH")
    require(m2["checkpoint_sha256"] == models["m2_checkpoint_sha256"],
            "CSTAR_AUTH_M2_GATE_CHECKPOINT_MISMATCH")
    require(m1["training_config_sha256"] == models["training_config_sha256"],
            "CSTAR_AUTH_M1_TRAINING_CONFIG_MISMATCH")
    require(m2["training_config_sha256"] == models["training_config_sha256"],
            "CSTAR_AUTH_M2_TRAINING_CONFIG_MISMATCH")

    head = current_git_sha(args.repo_root)
    require(head == production["git_sha"],
            f"CSTAR_AUTH_REPO_HEAD_PRODUCTION_MISMATCH:{head}:{production['git_sha']}")

    report = {
        "contract": "CSTAR_FORMAL_CLOSED_LOOP_AUTHORIZATION_V1",
        "revision": "REVISE_BEFORE_EXECUTION_20260906",
        "pass": True,
        "formal_closed_loop_authorized": True,
        "authorized_git_sha": production["git_sha"],
        "authorized_matrix": {
            "houses": ["H01", "H02", "H03"],
            "seed": 12,
            "arms": ["A0", "F00", "F10", "F11"],
            "horizon_s": 240.0,
            "run_count": 12,
        },
        "inputs": {
            name: {
                "path": str(path.resolve()),
                "sha256": sha256_file(path),
                "contract": REQUIRED[name][1],
                "verdict": loaded[name].get("verdict"),
            }
            for name, path in inputs.items()
        },
        "required_evidence_schema_sha256": sha256_file(SCHEMA_PATH),
        "stop_after_matrix": True,
        "multiseed_authorized": False,
        "verdict": "CSTAR_FORMAL_CLOSED_LOOP_AUTHORIZED=TRUE",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(report["verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
