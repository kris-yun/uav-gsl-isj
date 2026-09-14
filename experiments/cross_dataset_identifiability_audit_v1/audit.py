#!/usr/bin/env python3
"""Read-only audit of whether current artifacts identify cross-dataset source evidence."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_json(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def sha256(relative: str) -> str:
    digest = hashlib.sha256()
    with (ROOT / relative).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(relative: str):
    with (ROOT / relative).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    gate_path = "evidence/cstar_cer_ratio_house123_seed12_20260908/CSTAR_CER_RATIO_HOUSE123_SEED12_GATE.json"
    info_path = "evidence/m1r_post_nogo_diagnosis_20260913/INFORMATION_GATE.json"
    calibration_path = "evidence/cstar_m1_exact_counterfactual_calibration_audit_20260910.json"
    comparison_path = "evidence/m1r_mechanism/M1R_HISTORICAL_REPLICATION_COMPARISON.json"
    pairwise_path = "evidence/m1r_causal_repair_20260912/PAIRWISE_PREMISE.json"
    literature_search_path = "ideaspark_run/cross-dataset-identifiability-20260914/paper_search_2025_2026.json"
    attribution_path = "evidence/m1r_instrumented_20260912/H03_seed12_M1R/context_bank/contrastive_event_attribution.csv"
    sensor_path = "evidence/m1r_instrumented_20260912/H03_seed12_M1R/sensor_trace.csv"
    wind_path = "evidence/m1r_instrumented_20260912/H03_seed12_M1R/wind_trace.csv"
    scim_hpp_path = "ros2_package/src/gsl_server/SCIMCore.hpp"
    scim_cpp_path = "ros2_package/src/gsl_server/SCIMCore.cpp"
    simulation_path = "ros2_package/src/gsl_server/algorithms/PMFS/internal/Simulations.cpp"

    gate = load_json(gate_path)
    info = load_json(info_path)
    calibration = load_json(calibration_path)
    comparison = load_json(comparison_path)
    pairwise = load_json(pairwise_path)
    attribution = read_csv(attribution_path)
    sensor = read_csv(sensor_path)
    wind = read_csv(wind_path)

    h03 = gate["houses"]["H03"]
    a0 = h03["A0"]
    m1r = h03["M1R"]
    final_diag = info["h03_quadrature_response_support"]["updates"][-1]

    # One mobile sensor produces one spatial location per timestamp.  A local
    # 2-D PDE residual needs at least three non-collinear simultaneous points;
    # exact timestamp grouping is therefore a source-blind necessary gate.
    by_time: dict[str, set[tuple[str, str]]] = {}
    for row in sensor:
        by_time.setdefault(row["t_sim_s"], set()).add((row["x"], row["y"]))
    simultaneous_three_point_times = sum(len(points) >= 3 for points in by_time.values())

    attribution_members = sorted({row["member_index"] for row in attribution})
    attribution_candidates = sorted({row["candidate_id"] for row in attribution})
    attribution_updates = sorted({row["source_update_id"] for row in attribution}, key=int)
    attribution_events = sorted({row["event_index"] for row in attribution}, key=int)

    calibration_rank1 = sum(
        house["rank1_cases"] for house in calibration["by_house"].values()
    )
    calibration_commits = sum(
        house["commit_cases"] for house in calibration["by_house"].values()
    )

    scim_hpp = (ROOT / scim_hpp_path).read_text(encoding="utf-8")
    scim_cpp = (ROOT / scim_cpp_path).read_text(encoding="utf-8")
    simulations = (ROOT / simulation_path).read_text(encoding="utf-8")

    abstain_final = a0["final_error_m"]
    abstain_auc = a0["distance_auc_m_s"]
    strict_repair_pass = (
        abstain_final < a0["final_error_m"] and abstain_auc < a0["distance_auc_m_s"]
    )
    h03_comparison = comparison["houses"]["H03"]
    h03_pairwise_final = pairwise["houses"]["H03"]["updates"]["4"]

    source_points = final_diag["source_containing"]["points"]
    false_points = final_diag["strongest_false"]["points"]

    gate_files = {
        "sensing_150s": "experiments/sensing_support_upper_bound_v1/FINAL_GATE.json",
        "support_222_8s": "experiments/support_extension_mechanism_v1/FINAL_GATE.json",
        "aperture_5m": "experiments/aperture_extension_mechanism_v1/GEOMETRY_GATE.json",
        "observability_learning": "experiments/observability_learning_falsification_v1/FINAL_GATE.json",
        "active_observability": "experiments/active_observability_v1/FINAL_GATE.json",
    }

    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()

    output = {
        "schema": "CROSS_DATASET_IDENTIFIABILITY_AUDIT_V1",
        "git_head": head,
        "read_only": True,
        "protected_bank_consumed_or_regenerated": False,
        "literature_search_raw": {
            "path": literature_search_path,
            "sha256": sha256(literature_search_path),
            "year_range": "2025-2026",
            "limitations": [
                "Semantic Scholar and arXiv API requests returned HTTP 429",
                "DBLP request returned an SSL EOF error",
                "OpenAlex and Crossref results were retained and shortlisted records were checked on primary pages",
            ],
        },
        "h03_seed12_development_repair_gate": {
            "a0": {
                "final_error_m": a0["final_error_m"],
                "distance_auc_m_s": a0["distance_auc_m_s"],
            },
            "m1r": {
                "final_error_m": m1r["final_error_m"],
                "distance_auc_m_s": m1r["distance_auc_m_s"],
                "fixed_wrong_candidate_final_margin": final_diag[
                    "source_minus_false_log_mixture_margin"
                ],
                "new_replication_true_region_rank": "29/85",
                "new_replication_true_region_mass": h03_pairwise_final[
                    "source_region_binding"
                ]["native_true_leaf_mass"],
                "true_mass_source": "separate post-update posterior audit; absent from lightweight context bank",
                "truth_positive_events": max(
                    point["positive_events"] for point in source_points
                ),
                "truth_positive_zero_predictions_min": min(
                    point["positive_raw_probability_zero"] for point in source_points
                ),
                "strongest_false_positive_zero_predictions_max": max(
                    point["positive_raw_probability_zero"] for point in false_points
                ),
            },
            "identifiability_control_policy": "ABSTAIN_TO_A0_WHEN_REPLICATED_SOURCE_RESOLUTION_IS_UNAVAILABLE",
            "controlled_result": {
                "final_error_m": abstain_final,
                "distance_auc_m_s": abstain_auc,
                "strictly_improves_a0_on_both": strict_repair_pass,
                "improvement_vs_m1r": {
                    "final_error_m": m1r["final_error_m"] - abstain_final,
                    "distance_auc_m_s": m1r["distance_auc_m_s"] - abstain_auc,
                },
            },
            "trajectory_equivalence": {
                "historical_equivalence_proven": h03_comparison[
                    "historical_equivalence_proven"
                ],
                "observation_first_mismatch_row_1_based": h03_comparison[
                    "observation_sequence"
                ]["first_mismatch_row_1_based"],
                "pose_first_mismatch_row_1_based": h03_comparison[
                    "robot_pose_sequence"
                ]["first_mismatch_row_1_based"],
                "evidence_label": "NEW_INSTRUMENTED_DEVELOPMENT_REPLICATION",
            },
            "verdict": "H03_IDENTIFIABILITY_CONTROL_SAFETY_PASS_BUT_LOCALIZATION_REPAIR_NO_GO",
        },
        "necessary_information_gates": {
            "replicated_candidate_evidence": {
                "members": len(attribution_members),
                "candidates": len(attribution_candidates),
                "updates": len(attribution_updates),
                "events": len(attribution_events),
                "required_members_min": 2,
                "pass": len(attribution_members) >= 2,
                "reason": "one member cannot estimate transport-replicated source separation",
            },
            "local_pde_source_residual": {
                "sensor_rows": len(sensor),
                "unique_xy": len({(row["x"], row["y"]) for row in sensor}),
                "timestamps_with_three_spatial_points": simultaneous_three_point_times,
                "boundary_flux_observed": False,
                "zero_initial_field_certified": False,
                "pass": False,
                "reason": "no simultaneous spatial stencil and no boundary-flux/initial-condition contract",
            },
            "deployable_persistent_transport_provider": {
                "wind_rows": len(wind),
                "wind_columns": list(wind[0].keys()) if wind else [],
                "full_gmrf_field_history_present": False,
                "transport_members": len(attribution_members),
                "pass": False,
                "reason": "saved run contains receiver-local wind and one native member, not a causal full-field transport ensemble",
            },
            "exact_counterfactual_ranking": {
                "rank1_cases": calibration_rank1,
                "cases": sum(house["cases"] for house in calibration["by_house"].values()),
                "calibrated_commits": calibration_commits,
                "pass_as_ranking_only": calibration_rank1 == 12,
                "pass_as_calibrated_online_source_evidence": calibration_commits == 12,
                "verdict": calibration["verdict"],
            },
        },
        "octree_spatial_memory_audit": {
            "octree_token_in_pmfs_simulations": "octree" in simulations.lower(),
            "quadtree_token_in_pmfs_simulations": "quadtree" in simulations.lower(),
            "scim_explicitly_does_not_modify_pi_map": "without modifying pi_map" in scim_hpp,
            "scim_is_planner_state": "class SpatialInformationPlanner" in scim_hpp,
            "scim_uses_current_posterior_for_actions": "posterior.mapProbabilities()" in scim_cpp,
            "classification": "REPRESENTATION_OR_PLANNER_ABLATION_NOT_PRE_BAYES_SOURCE_INFORMATION",
        },
        "prior_bounded_gates": {
            name: {
                "path": path,
                "sha256": sha256(path),
                "payload": load_json(path),
            }
            for name, path in gate_files.items()
        },
        "decision_chain": {
            "IMPLEMENTATION": "M1R candidate-relative contrastive likelihood before Bayesian accumulation",
            "OBSERVED_FAILURE": "H03 endpoint worsened and the true-source response stayed outside predictive support while fixed false candidates dominated",
            "MISSING_THEORETICAL_PROPERTY": "observation-conditioned replicated source separation with a calibrated evidence-release rule",
            "ONE_NEXT_MECHANISM": "OBSERVATION_QUOTIENT_IDENTIFIABILITY_CERTIFICATE",
            "mechanism_scope": "project evidence only between resolution cells and abstain within unresolved cells; octree/quadtree is only the carrier representation",
        },
        "final_verdict": "NO_GO_NO_UNSEEN_SEED_CURRENT_DATA_DO_NOT_SUPPORT_CROSS_DATASET_LOCALIZATION_CLAIM",
        "claim_boundary": {
            "development_repair": "NO_GO",
            "new_replication": "NOT_RUN",
            "untouched_confirmation": "NOT_RUN",
            "cross_dataset_localization": "NOT_AUTHORIZED",
            "identifiability_audit_main_claim": "CANDIDATE_ONLY_REQUIRES_EXTERNAL_DATASET_VALIDATION",
        },
        "input_hashes": {
            path: sha256(path)
            for path in [
                gate_path,
                info_path,
                calibration_path,
                comparison_path,
                pairwise_path,
                literature_search_path,
                attribution_path,
                sensor_path,
                wind_path,
                scim_hpp_path,
                scim_cpp_path,
                simulation_path,
            ]
        },
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
