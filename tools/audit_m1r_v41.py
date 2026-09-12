#!/usr/bin/env python3
"""Produce the read-only M1R V4.1 implementation and replay-sufficiency audit.

This tool deliberately does not run PMFS and does not read any unexposed gas
payload.  It binds the historical seed-12 run to its preserved source snapshot,
checks the recorded artifacts for the fields required by an exact three-arm
replay, and preregisters data roles from metadata only.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HISTORICAL_COMMIT = "8dd5977"
STARTING_SHA = "c41fdb3833cc203550b760b36260a715fd7b99f3"
RUN_ROOT = ROOT / "evidence/cstar_cer_ratio_house123_seed12_20260908"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob(revision: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{revision}:{path}"], cwd=ROOT)


def blob_record(path: str) -> dict:
    payload = git_blob(HISTORICAL_COMMIT, path)
    return {
        "path": path,
        "preserved_commit": HISTORICAL_COMMIT,
        "git_blob": subprocess.check_output(
            ["git", "rev-parse", f"{HISTORICAL_COMMIT}:{path}"], cwd=ROOT, text=True
        ).strip(),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def read_csv_header(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8") as handle:
        return next(csv.reader(handle))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    source_paths = [
        "ros2_package/src/gsl_server/algorithms/PMFS/PMFS.cpp",
        "ros2_package/src/gsl_server/algorithms/PMFS/PMFS.hpp",
        "ros2_package/src/gsl_server/algorithms/PMFS/internal/Simulations.cpp",
        "ros2_package/src/gsl_server/algorithms/PMFS/internal/Simulations.hpp",
        "closed_loop/ctpi/run_ctpi_fasttrack_case_safe_20260903.sh",
        "closed_loop/ctpi/vgr_gsl_pmfs_ctpi_fasttrack.launch.py",
        "tools/cstar_run_cer_ratio_house123_seed12_20260908.sh",
    ]
    historical_cpp = git_blob(
        HISTORICAL_COMMIT,
        "ros2_package/src/gsl_server/algorithms/PMFS/internal/Simulations.cpp",
    ).decode("utf-8")
    historical_pmfs = git_blob(
        HISTORICAL_COMMIT, "ros2_package/src/gsl_server/algorithms/PMFS/PMFS.cpp"
    ).decode("utf-8")
    event_counts: dict[str, list[int]] = {}
    for house in ("H01", "H02", "H03"):
        log = (RUN_ROOT / f"{house}_seed12_M1R/launch.log").read_text(
            encoding="utf-8", errors="replace"
        )
        event_counts[house] = [
            int(value)
            for value in re.findall(r"CER contrastive context initialized: events=(\d+)", log)
        ]

    binary_hash = (RUN_ROOT / "ALGORITHM_SHA256.txt").read_text(encoding="utf-8").split()[0]
    manifest = {
        "contract": "M1R_IMPLEMENTATION_FREEZE_V41_20260912",
        "audit_starting_sha": STARTING_SHA,
        "historical_runtime_declared_source": "c62a54a+cer-ratio-working-tree",
        "historical_source_preservation_commit": HISTORICAL_COMMIT,
        "binding_basis": (
            "8dd5977 is the first repository commit that preserves the cer_ratio_m1 source and "
            "the nine historical run folders; the runtime manifest itself names an uncommitted tree"
        ),
        "historical_binary_sha256": binary_hash,
        "historical_binary_bytes_available": False,
        "source_files": [blob_record(path) for path in source_paths],
        "mode": {
            "pfdi_mode": "cer_ratio_m1",
            "event_evidence_enabled": True,
            "contrastive_ratio": True,
            "transport_replicas": 1,
            "sequential_assimilation": False,
            "physical_stop_only": False,
            "centered_log_odds": False,
        },
        "observation_law": {
            "recording_unit": "every completed internal measurement block",
            "physical_stop_factor_equivalence": False,
            "persistence": (
                "Normal(log1p(previous recorded block concentration), unit scale) threshold tail; "
                "previousConcentration is updated after every recorded block and reset to zero at each candidate score evaluation"
            ),
            "persistence_is_full_fopdt_latent_state": False,
            "source_probability": "candidate member hit-map probability at the recorded event cell, clipped to [1e-4,1-1e-4]",
            "context_probability": "arithmetic mean candidate hit-map probability at the event cell over the current first-level valid candidate set",
            "candidate_score": "product over recorded blocks of Bernoulli likelihood after logit(persistence)+logit(p_sim)-logit(p_context)",
            "posterior_path": "candidate sourceProb replaces the native first-level leaf score before native PMFS refinement/controller consumption",
        },
        "source_assertions": {
            "previous_concentration_updates_each_event": "previousConcentration = event.concentration;" in historical_cpp,
            "physical_stop_filter_present_for_historical_mode": "eventEvidencePhysicalStopOnly" in historical_pmfs,
            "historical_mode_records_each_measurement_block": "if (eventEvidenceEnabled)" in historical_pmfs,
        },
        "observed_event_counts_by_source_update": event_counts,
        "implementation_bound": "PASS_WITH_PROVENANCE_LIMIT",
        "provenance_limit": "the historical binary digest is recorded, but the binary bytes are not present in the preserved evidence tree",
    }
    write_json(ROOT / "evidence/m1r_freeze/M1R_IMPLEMENTATION_MANIFEST.json", manifest)

    required = {
        "event_history": "sensor_trace.csv",
        "robot_pose_history": "sim_pose_trace.csv",
        "action_history": "navigation_trace.csv",
        "source_estimate_summary": "source_estimate_trace.csv",
        "full_candidate_posterior_each_update": None,
        "candidate_event_p_sim": None,
        "event_p_context": None,
        "candidate_event_log_likelihood_increment": None,
        "true_source_rank_each_update": None,
        "random_transport_identity_each_candidate_update": None,
    }
    per_house = {}
    for house in ("H01", "H02", "H03"):
        folder = RUN_ROOT / f"{house}_seed12_M1R"
        presence = {}
        for field, filename in required.items():
            presence[field] = bool(filename and (folder / filename).is_file())
        presence["source_estimate_columns"] = read_csv_header(folder / "source_estimate_trace.csv")
        presence["sensor_columns"] = read_csv_header(folder / "sensor_trace.csv")
        per_house[house] = presence
    missing = [
        field
        for field in required
        if not all(per_house[h].get(field, False) for h in per_house)
    ]
    sufficiency = {
        "contract": "M1R_HISTORICAL_REPLAY_SUFFICIENCY_V41_20260912",
        "historical_run_root": str(RUN_ROOT.relative_to(ROOT)).replace("\\", "/"),
        "same_history_three_arm_requirement": True,
        "per_house": per_house,
        "missing_exact_replay_fields": missing,
        "historical_replay_sufficiency": "FAIL",
        "three_arm_exact_replay": "THREE_ARM_EXACT_REPLAY_NOT_IDENTIFIABLE_FROM_CURRENT_ARTIFACTS",
        "event_accounting_replay_identifiable": "NO",
        "event_accounting_verdict": "EVENT_ACCOUNTING_CAUSAL_EFFECT_NOT_IDENTIFIABLE_FROM_CURRENT_REPLAY",
        "no_approximate_reconstruction_used": True,
    }
    write_json(ROOT / "evidence/m1r_mechanism/HISTORICAL_REPLAY_SUFFICIENCY.json", sufficiency)
    write_json(
        ROOT / "evidence/m1r_mechanism/M1R_THREE_ARM_REPLAY.json",
        {
            "contract": "M1R_THREE_ARM_REPLAY_V41_20260912",
            "status": "NOT_IDENTIFIABLE",
            "result": "THREE_ARM_EXACT_REPLAY_NOT_IDENTIFIABLE_FROM_CURRENT_ARTIFACTS",
            "arms": {
                "M0": "persistence-only",
                "M1": "persistence plus absolute source",
                "M2": "persistence plus source/context contrast (historical M1R observation law)",
            },
            "reason": missing,
            "historical_closed_loop_gate_is_not_a_three_arm_replay": True,
            "historical_gate_path": "evidence/cstar_cer_ratio_house123_seed12_20260908/CSTAR_CER_RATIO_HOUSE123_SEED12_GATE.json",
        },
    )

    # All presently catalogued realizations have already appeared in development
    # inventories/screens.  Metadata-only role assignment therefore cannot truthfully
    # manufacture an untouched confirmation set.
    inventory_path = ROOT / "evidence/cstar_environment_20260906/CONTROLLED_PREREQUISITE_INVENTORY.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    records = []
    for entry in inventory["entries"]:
        records.append(
            {
                "house": entry["house"],
                "config": entry["config"],
                "gas_scenario": Path(entry["realization_path"]).name,
                "source_xyz_from_name_only": entry["source_xyz_from_name_only"],
                "wind_regime": "fast" if entry["config"].endswith("_fast") else "slow",
                "role": "DEVELOPMENT",
                "reason": "realization identity already present in prior project inventories/screens; virgin performance status cannot be certified",
                "performance_read_this_audit": False,
            }
        )
    split = {
        "contract": "M1R_CROSS_DOMAIN_SPLIT_PRECOMMIT_V41_20260912",
        "rule": "metadata-only; any asset previously used for method design, screening, or outcome inspection is DEVELOPMENT",
        "inventory_sha256": sha256(inventory_path),
        "records": records,
        "role_counts": {"DEVELOPMENT": len(records), "REPAIR": 0, "CONFIRMATION": 0},
        "confirmation_performance_read": False,
        "status": "FAIL_NO_CERTIFIABLY_UNTOUCHED_CONFIRMATION_ASSET",
        "constraint": "project instruction forbids adding Houses; no existing catalogued realization can be certified virgin",
    }
    write_json(ROOT / "evidence/m1r_cross_domain/CROSS_DOMAIN_SPLIT_PRECOMMIT.json", split)


if __name__ == "__main__":
    main()
