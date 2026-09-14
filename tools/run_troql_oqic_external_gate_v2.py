#!/usr/bin/env python3
"""Run the frozen V2 TROQL/OQIC distributional-dominance gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

import run_troql_oqic_external_gate as kernel


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "experiments/troql_oqic_external_v2/POLICY_FREEZE.json"
DEVELOPMENT_PATH = ROOT / "experiments/troql_oqic_external_v2/DEVELOPMENT_GATE.json"
CONFIRMATION_PATH = ROOT / "experiments/troql_oqic_external_v2/CONFIRMATION_GATE.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def mann_whitney_greater(source: np.ndarray, nuisance: np.ndarray) -> dict[str, float]:
    """Return probability-of-superiority and tie-corrected one-sided p-value."""
    source = np.asarray(source, dtype=float)
    nuisance = np.asarray(nuisance, dtype=float)
    combined = np.concatenate([source, nuisance])
    ranks = kernel.midranks(combined)
    n_source = source.size
    n_nuisance = nuisance.size
    u_value = float(np.sum(ranks[:n_source]) - n_source * (n_source + 1) / 2.0)
    auc = u_value / float(n_source * n_nuisance)

    _, tie_counts = np.unique(combined, return_counts=True)
    tie_sum = float(np.sum(tie_counts**3 - tie_counts))
    total = n_source + n_nuisance
    variance = n_source * n_nuisance / 12.0 * (
        total + 1.0 - tie_sum / (total * (total - 1.0))
    )
    if variance <= 0.0:
        if np.all(combined == combined[0]):
            return {
                "u": u_value,
                "auc": auc,
                "z_continuity_corrected": 0.0,
                "one_sided_p": 0.5,
            }
        raise ValueError("TROQL_V2_NONPOSITIVE_U_VARIANCE")
    z_value = (u_value - n_source * n_nuisance / 2.0 - 0.5) / math.sqrt(variance)
    p_value = 0.5 * math.erfc(z_value / math.sqrt(2.0))
    return {
        "u": u_value,
        "auc": auc,
        "z_continuity_corrected": z_value,
        "one_sided_p": p_value,
    }


def summarize_dominance(
    source_margins: dict[str, np.ndarray],
    nuisance_margins: dict[str, np.ndarray],
    policy: dict[str, Any],
) -> dict[str, Any]:
    gate = policy["dominance_gate"]
    directions: dict[str, Any] = {}
    for direction in ("a_to_b", "b_to_a"):
        source = source_margins[direction]
        nuisance = nuisance_margins[direction]
        test = mann_whitney_greater(source, nuisance)
        positive_fraction = float(np.mean(source > 0.0))
        passed = (
            test["auc"] >= float(gate["minimum_auc_per_direction"])
            and test["one_sided_p"] <= float(gate["maximum_one_sided_p_per_direction"])
            and positive_fraction >= float(gate["minimum_positive_fraction_per_direction"])
        )
        directions[direction] = {
            **test,
            "source_positive_fraction": positive_fraction,
            "source_median_margin": float(np.median(source)),
            "nuisance_median_margin": float(np.median(nuisance)),
            "source_margins": [float(value) for value in source],
            "nuisance_margins": [float(value) for value in nuisance],
            "pass": passed,
        }
    return {
        "thresholds": {
            "minimum_auc_per_direction": gate["minimum_auc_per_direction"],
            "maximum_one_sided_p_per_direction": gate[
                "maximum_one_sided_p_per_direction"
            ],
            "minimum_positive_fraction_per_direction": gate[
                "minimum_positive_fraction_per_direction"
            ],
        },
        "directions": directions,
        "resolved": all(item["pass"] for item in directions.values()),
    }


def verify_frozen_inputs(policy: dict[str, Any], stage: str) -> dict[str, Any]:
    expected_kernel = policy["representation"]["kernel_sha256"]
    actual_kernel = sha256(ROOT / policy["representation"]["kernel"])
    if actual_kernel != expected_kernel:
        raise ValueError("TROQL_V2_REPRESENTATION_KERNEL_HASH_MISMATCH")
    provenance = kernel.verify_policy(policy, stage)
    provenance["representation_kernel_sha256"] = actual_kernel
    return provenance


def run_stage(policy: dict[str, Any], stage: str) -> dict[str, Any]:
    provenance = verify_frozen_inputs(policy, stage)
    loaded = kernel.load_stage_features(policy, stage)
    null_pair = tuple(policy["stages"][stage]["null_pair"])
    source_pair = tuple(policy["stages"][stage]["source_pair"])
    null_margins = kernel.pair_margins(
        loaded[null_pair[0]]["features"], loaded[null_pair[1]]["features"]
    )
    source_margins = kernel.pair_margins(
        loaded[source_pair[0]]["features"], loaded[source_pair[1]]["features"]
    )
    dominance = summarize_dominance(source_margins, null_margins, policy)
    passed = bool(dominance["resolved"])
    if stage == "development":
        verdict = (
            "TROQL_OQIC_V2_EXTERNAL_DEVELOPMENT_PASS_TO_CONFIRMATION"
            if passed
            else "TROQL_OQIC_V2_EXTERNAL_DEVELOPMENT_NO_GO"
        )
    else:
        verdict = (
            "TROQL_OQIC_MAIN_INNOVATION_PREMISE_PASS"
            if passed
            else "TROQL_OQIC_V2_EXTERNAL_CONFIRMATION_NO_GO"
        )
    result = {
        "schema": f"TROQL_OQIC_EXTERNAL_{stage.upper()}_GATE_V2",
        "stage": "untouched_confirmation" if stage == "confirmation" else stage,
        "policy_sha256": sha256(POLICY_PATH),
        "scorer_sha256": sha256(Path(__file__).resolve()),
        "provenance": provenance,
        "null_pair": list(null_pair),
        "source_pair": list(source_pair),
        "dominance_certificate": dominance,
        "input_shapes": {
            name: {key: value for key, value in item.items() if key != "features"}
            for name, item in loaded.items()
        },
        "gate_pass": passed,
        "verdict": verdict,
        "claim_boundary": {
            "bounded_cross_dataset_identifiability_mechanism": (
                "AUTHORIZED" if stage == "confirmation" and passed else "NOT_AUTHORIZED"
            ),
            "closed_loop_localization_improvement": "NOT_AUTHORIZED",
            "online_pmfs_deployment": "NOT_AUTHORIZED",
        },
    }
    if stage == "development":
        result["confirmation_opened"] = False
    return result


def verify_confirmation_preconditions(policy: dict[str, Any]) -> dict[str, Any]:
    if not DEVELOPMENT_PATH.exists():
        raise ValueError("TROQL_V2_DEVELOPMENT_GATE_MISSING")
    development = json.loads(DEVELOPMENT_PATH.read_text(encoding="utf-8"))
    if not development.get("gate_pass"):
        raise ValueError("TROQL_V2_DEVELOPMENT_NO_GO_CONFIRMATION_FORBIDDEN")
    if development["policy_sha256"] != sha256(POLICY_PATH):
        raise ValueError("TROQL_V2_POLICY_CHANGED_AFTER_DEVELOPMENT")
    if development["scorer_sha256"] != sha256(Path(__file__).resolve()):
        raise ValueError("TROQL_V2_SCORER_CHANGED_AFTER_DEVELOPMENT")
    if development["provenance"]["representation_kernel_sha256"] != sha256(
        ROOT / policy["representation"]["kernel"]
    ):
        raise ValueError("TROQL_V2_KERNEL_CHANGED_AFTER_DEVELOPMENT")
    return development


def selftest() -> None:
    nuisance = np.linspace(-0.02, 0.02, 20)
    source = np.linspace(0.20, 0.40, 20)
    strong = mann_whitney_greater(source, nuisance)
    if strong["auc"] != 1.0 or strong["one_sided_p"] >= 0.01:
        raise AssertionError("TROQL_V2_DOMINANCE_SELFTEST_FAILED")
    tied = mann_whitney_greater(np.ones(20), np.ones(20))
    if tied["auc"] != 0.5 or tied["one_sided_p"] < 0.49:
        raise AssertionError("TROQL_V2_TIE_SELFTEST_FAILED")
    print("TROQL_OQIC_V2_SELFTEST_PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["development", "confirmation"])
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return
    if not args.stage:
        parser.error("--stage is required unless --selftest is used")

    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    development = None
    if args.stage == "confirmation":
        development = verify_confirmation_preconditions(policy)
    result = run_stage(policy, args.stage)
    if development is not None:
        result["development_gate_sha256"] = sha256(DEVELOPMENT_PATH)

    output = args.out or (
        DEVELOPMENT_PATH if args.stage == "development" else CONFIRMATION_PATH
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": result["verdict"], "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()
