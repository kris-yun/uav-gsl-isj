#!/usr/bin/env python3
"""Frozen V2 hierarchical projection of CTRE carrier evidence to PMFS cells.

The scientific evidence is not recomputed here.  Carrier posteriors are loaded
byte-identically from the frozen V1 Stage-1 artifact.  V2 changes only the
resolution interface: CTRE replaces the carrier marginal while native PMFS
supplies the within-carrier conditional.  Native PMFS remains an independent
comparator; it is never multiplied into the frozen carrier likelihood.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import tempfile
from pathlib import Path
from typing import Any

import numpy as np

import evaluate_ctt_crosshouse_measured_pmfs_shadow as v1


CONTRACT = "CTT_CAUSAL_TEMPORAL_HIERARCHICAL_PROJECTION_V2"
PASS = "CTT_CAUSAL_TEMPORAL_HIERARCHICAL_PROJECTION_V2_PASS_TO_RUNTIME"
NO_GO = "CTT_CAUSAL_TEMPORAL_HIERARCHICAL_PROJECTION_V2_NO_GO"
INVALID = "CTT_CAUSAL_TEMPORAL_HIERARCHICAL_PROJECTION_V2_INVALID"
TOL = 1.0e-12
PRIMARY_MODES = ("ascending", "descending", "symmetric")
RANDOM_MODES = tuple(f"sha256_{index}" for index in range(16))
ALL_MODES = PRIMARY_MODES + RANDOM_MODES
# Source-label nulls are evaluated for all three preregistered primary
# endpoints.  The sixteen fixed random orders are deterministic sensitivity
# endpoints, not separately selected null hypotheses.
NULL_MODES = PRIMARY_MODES
METHOD_CHANNELS = (
    "identity_reconstruction",
    "conditional_only",
    "coarse_only",
    "full",
    "count_only",
    "stop_label_permute",
)


def sha256_file(path: Path) -> str:
    return v1.sha256_file(path)


def uniform_permutation(size: int, label: str) -> np.ndarray:
    """One deterministic draw from the full permutation distribution.

    Identity is deliberately allowed.  Rejecting identity separately inside
    each free-cell-count stratum would make two-member strata swap with
    probability one instead of the required one half and would invalidate the
    Monte Carlo randomisation null.
    """
    if size <= 0:
        raise ValueError("CTT_V2_PERMUTATION_SIZE_FAIL")
    seed = int.from_bytes(
        hashlib.sha256(("CTT-V2-SOURCE-LABEL-NULL|" + label).encode()).digest()[:8],
        "big",
    )
    return np.random.default_rng(seed).permutation(size)


def uniform_stratified_permutation(
    free_cells: np.ndarray, house: str, replicate: int
) -> np.ndarray:
    """Draw independently and uniformly within every equal-size stratum."""
    counts = np.asarray(free_cells, dtype=np.int64)
    result = np.arange(len(counts), dtype=np.int64)
    for value in sorted(set(int(item) for item in counts)):
        members = np.flatnonzero(counts == value)
        if len(members) < 2:
            continue
        local = uniform_permutation(
            len(members), f"STRATIFIED|{house}|{replicate}|{value}"
        )
        result[members] = members[local]
    return result


def _require_probability(value: np.ndarray, label: str) -> np.ndarray:
    array = np.asarray(value, dtype=np.float64)
    if (
        array.ndim != 1
        or len(array) == 0
        or not np.isfinite(array).all()
        or np.any(array < 0.0)
        or abs(float(np.sum(array)) - 1.0) > TOL
    ):
        raise ValueError(f"CTT_V2_PROBABILITY_CONTRACT_FAIL:{label}")
    return array


def carrier_marginal(
    cell_mass: np.ndarray, cell_to_carrier: np.ndarray, carrier_count: int
) -> np.ndarray:
    mass = _require_probability(cell_mass, "cell_mass")
    labels = np.asarray(cell_to_carrier, dtype=np.int64)
    if labels.shape != mass.shape or np.any(labels < 0) or np.any(labels >= carrier_count):
        raise ValueError("CTT_V2_CELL_TO_CARRIER_CONTRACT_FAIL")
    return np.bincount(labels, weights=mass, minlength=carrier_count).astype(np.float64)


def hierarchical_project(
    target_carrier: np.ndarray,
    native_cell: np.ndarray,
    cell_to_carrier: np.ndarray,
    *,
    label: str,
) -> dict[str, Any]:
    """Apply q(B) p_N(x|B), with an exact whole-update zero-mass fallback."""
    target = _require_probability(target_carrier, f"{label}:target_carrier")
    native = _require_probability(native_cell, f"{label}:native_cell")
    labels = np.asarray(cell_to_carrier, dtype=np.int64)
    native_carrier = carrier_marginal(native, labels, len(target))
    conflict = np.flatnonzero((native_carrier == 0.0) & (target > 0.0))
    if len(conflict):
        return {
            "cell": native.copy(),
            "native_carrier": native_carrier,
            "abstained": True,
            "reason": "ABSTAIN_NATIVE_CARRIER_ZERO_MASS",
            "conflict_carriers": conflict.astype(np.int64),
        }
    result = np.zeros_like(native)
    for carrier in range(len(target)):
        selected = labels == carrier
        if native_carrier[carrier] > 0.0:
            result[selected] = target[carrier] * native[selected] / native_carrier[carrier]
        elif target[carrier] != 0.0:
            raise AssertionError("CTT_V2_UNREACHABLE_ZERO_MASS_BRANCH")
    if abs(float(np.sum(result)) - 1.0) > TOL or np.any(result < 0.0):
        raise ValueError(f"CTT_V2_PROJECTED_MASS_FAIL:{label}")
    return {
        "cell": result,
        "native_carrier": native_carrier,
        "abstained": False,
        "reason": "PROJECTED",
        "conflict_carriers": np.empty(0, dtype=np.int64),
    }


def projection_invariants(
    target_carrier: np.ndarray,
    projected: dict[str, Any],
    native_cell: np.ndarray,
    cell_to_carrier: np.ndarray,
) -> dict[str, float]:
    target = _require_probability(target_carrier, "invariant_target")
    native = _require_probability(native_cell, "invariant_native")
    labels = np.asarray(cell_to_carrier, dtype=np.int64)
    output = _require_probability(projected["cell"], "invariant_projected")
    native_carrier = carrier_marginal(native, labels, len(target))
    if projected["abstained"]:
        return {
            "carrier_marginal_max_abs": 0.0,
            "within_carrier_conditional_max_abs": 0.0,
            "total_mass_abs": abs(float(np.sum(output)) - 1.0),
            "fail_closed_native_max_abs": float(np.max(np.abs(output - native))),
        }
    marginal = carrier_marginal(output, labels, len(target))
    conditional_max = 0.0
    for carrier in range(len(target)):
        if target[carrier] == 0.0 or native_carrier[carrier] == 0.0:
            continue
        selected = labels == carrier
        conditional_max = max(
            conditional_max,
            float(np.max(np.abs(
                output[selected] / target[carrier]
                - native[selected] / native_carrier[carrier]
            ))),
        )
    return {
        "carrier_marginal_max_abs": float(np.max(np.abs(marginal - target))),
        "within_carrier_conditional_max_abs": conditional_max,
        "total_mass_abs": abs(float(np.sum(output)) - 1.0),
        "fail_closed_native_max_abs": 0.0,
    }


def row_permutation_projection_max_abs(
    target_carrier: np.ndarray,
    native_cell: np.ndarray,
    cell_to_carrier: np.ndarray,
) -> float:
    labels = np.asarray(cell_to_carrier, dtype=np.int64)
    native = np.asarray(native_cell, dtype=np.float64)
    canonical = hierarchical_project(target_carrier, native, labels, label="row_canonical")["cell"]
    order = np.arange(len(native) - 1, -1, -1, dtype=np.int64)
    permuted = hierarchical_project(
        target_carrier, native[order], labels[order], label="row_reversed"
    )["cell"]
    restored = np.empty_like(permuted)
    restored[order] = permuted
    return float(np.max(np.abs(canonical - restored)))


def load_frozen_stage1(
    stage1_root: Path,
    prereg: dict[str, Any],
    supplied_manifest_sha256: str,
    v1_preregistration: Path,
    v1_evaluator: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    frozen = prereg["frozen_stage1"]
    manifest_path = stage1_root / "METHOD_POSTERIORS_MANIFEST.json"
    npz_path = stage1_root / "METHOD_POSTERIORS.npz"
    freeze_path = stage1_root / "INPUT_FREEZE.json"
    expected_manifest = frozen["method_posteriors_manifest_sha256"]
    if supplied_manifest_sha256 != expected_manifest:
        raise SystemExit("CTT_V2_EXTERNAL_STAGE1_MANIFEST_HASH_ARGUMENT_FAIL")
    if sha256_file(manifest_path) != expected_manifest:
        raise SystemExit("CTT_V2_EXTERNAL_STAGE1_MANIFEST_HASH_FAIL")
    if sha256_file(npz_path) != frozen["method_posteriors_npz_sha256"]:
        raise SystemExit("CTT_V2_STAGE1_NPZ_HASH_FAIL")
    if sha256_file(freeze_path) != frozen["input_freeze_sha256"]:
        raise SystemExit("CTT_V2_STAGE1_INPUT_FREEZE_HASH_FAIL")
    if sha256_file(v1_evaluator) != frozen["v1_evaluator_sha256"]:
        raise SystemExit("CTT_V2_V1_EVALUATOR_HASH_FAIL")
    if sha256_file(v1_preregistration) != frozen["v1_preregistration_sha256"]:
        raise SystemExit("CTT_V2_V1_PREREGISTRATION_HASH_FAIL")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (
        manifest.get("contract") != "CTT_CAUSAL_TEMPORAL_PMFS_SHADOW_STAGE1_V1"
        or manifest.get("status")
        != "ALL_150_METHOD_SCORES_AND_POSTERIORS_FROZEN_BEFORE_NATIVE_OR_TRUTH_READ"
        or int(manifest.get("records", -1)) != 150
        or manifest.get("verified_training_shards") != frozen["verified_train_shards"]
        or manifest.get("artifact_sha256") != frozen["method_posteriors_npz_sha256"]
        or manifest.get("preregistration_sha256") != frozen["v1_preregistration_sha256"]
        or manifest.get("evaluator_sha256") != frozen["v1_evaluator_sha256"]
        or manifest.get("input_freeze_sha256") != frozen["input_freeze_sha256"]
        or manifest.get("pretruth_posterior_sha256")
        != frozen["semantic_pretruth_posterior_sha256"]
        or tuple(manifest.get("array_keys", ())) != v1.STAGE1_ARRAY_KEYS
    ):
        raise SystemExit("CTT_V2_STAGE1_MANIFEST_CONTRACT_FAIL")

    records: list[dict[str, Any]] = []
    with np.load(npz_path, allow_pickle=False) as archive:
        expected_arrays = {
            f"{house}_{key}" for house in v1.HOUSES for key in v1.STAGE1_ARRAY_KEYS
        }
        if set(archive.files) != expected_arrays:
            raise SystemExit("CTT_V2_STAGE1_ARRAY_SET_FAIL")
        for item in manifest["metadata"]:
            house = item["house"]
            index = int(item["local_index"])
            record: dict[str, Any] = {
                key: value for key, value in item.items() if key != "local_index"
            }
            for key in v1.STAGE1_ARRAY_KEYS:
                record[key] = np.asarray(archive[f"{house}_{key}"][index], dtype=np.float64)
            records.append(record)
    if len(records) != 150:
        raise SystemExit("CTT_V2_STAGE1_RECORD_COUNT_FAIL")
    semantic = v1.pretruth_digest(records)
    if semantic != frozen["semantic_pretruth_posterior_sha256"]:
        raise SystemExit("CTT_V2_STAGE1_SEMANTIC_HASH_FAIL")
    return records, manifest


def _case_result(historical_root: Path, house: str, seed: int) -> tuple[dict[str, Any], str]:
    path = v1.historical_case_root(historical_root, house, seed) / "case_result.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    if not value.get("valid") or value.get("primary_metric") != "PMFS_ExpectedValue_top_5_percent":
        raise ValueError(f"CTT_V2_CASE_RESULT_FAIL:{house}:{seed}")
    return value, sha256_file(path)


def build_update_arms(
    record: dict[str, Any], mapping: dict[str, Any], support: dict[str, Any]
) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    native_cell = mapping["native_cell"]
    native_carrier = mapping["native_carrier"]
    labels = mapping["cell_to_source"]
    targets = {
        "identity_reconstruction": native_carrier,
        "conditional_only": np.asarray(record["q0_carrier"], dtype=np.float64),
        "full": np.asarray(record["method_carrier"], dtype=np.float64),
        "count_only": np.asarray(record["count_only_carrier"], dtype=np.float64),
        "stop_label_permute": np.asarray(record["stop_label_permute_carrier"], dtype=np.float64),
    }
    projected: dict[str, dict[str, Any]] = {
        name: hierarchical_project(target, native_cell, labels, label=name)
        for name, target in targets.items()
    }
    cells = {name: value["cell"] for name, value in projected.items()}
    cells["coarse_only"] = v1.carrier_to_cells(record["method_carrier"], mapping, support)

    invariant_rows = {
        name: projection_invariants(targets[name], projected[name], native_cell, labels)
        for name in targets
    }
    identity_max = float(np.max(np.abs(cells["identity_reconstruction"] - native_cell)))
    row_max = max(
        row_permutation_projection_max_abs(target, native_cell, labels)
        for target in targets.values()
    )
    invariant = {
        "identity_reconstruction_max_abs": identity_max,
        "carrier_marginal_max_abs": max(
            item["carrier_marginal_max_abs"] for item in invariant_rows.values()
        ),
        "within_carrier_conditional_max_abs": max(
            item["within_carrier_conditional_max_abs"] for item in invariant_rows.values()
        ),
        "total_mass_max_abs": max(
            [item["total_mass_abs"] for item in invariant_rows.values()]
            + [abs(float(np.sum(cells["coarse_only"])) - 1.0)]
        ),
        "fail_closed_native_max_abs": max(
            item["fail_closed_native_max_abs"] for item in invariant_rows.values()
        ),
        "cell_row_permutation_max_abs_after_restore": row_max,
        "abstained_arms": [name for name, item in projected.items() if item["abstained"]],
    }
    return cells, invariant


def evaluate(
    records: list[dict[str, Any]],
    historical_root: Path,
    support_all: dict[str, dict[str, Any]],
    prereg: dict[str, Any],
    frozen_v1_summary: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    updates: list[dict[str, Any]] = []
    final_internal: list[dict[str, Any]] = []
    case_cache: dict[tuple[str, int], tuple[dict[str, Any], str]] = {}
    comparator_hashes: dict[str, str] = {}
    invariant_max = {
        "identity_reconstruction_max_abs": 0.0,
        "carrier_marginal_max_abs": 0.0,
        "within_carrier_conditional_max_abs": 0.0,
        "total_mass_max_abs": 0.0,
        "fail_closed_native_max_abs": 0.0,
        "cell_row_permutation_max_abs_after_restore": 0.0,
    }
    abstained_updates: dict[str, int] = {name: 0 for name in METHOD_CHANNELS}

    for record in records:
        house, seed, update_id = record["house"], int(record["seed"]), int(record["update_id"])
        support = support_all[house]
        runtime = v1.runtime_root(historical_root, house, seed)
        native_path = runtime / "context_bank" / f"source_update_{update_id:04d}" / "source_posterior.csv"
        native_rows = v1.read_csv(native_path)
        comparator_hashes[f"{house}_seed{seed}_update{update_id}"] = sha256_file(native_path)
        mapping = v1.map_native_cells(native_rows, record["timing"], support)
        cell_fields, invariants = build_update_arms(record, mapping, support)
        for key in invariant_max:
            invariant_max[key] = max(invariant_max[key], float(invariants[key]))
        for arm in invariants["abstained_arms"]:
            abstained_updates[arm] = abstained_updates.get(arm, 0) + 1

        case_key = (house, seed)
        if case_key not in case_cache:
            case_cache[case_key] = _case_result(historical_root, house, seed)
        case, case_sha = case_cache[case_key]
        truth_xy = tuple(float(value) for value in case["truth_eval_only"])
        truth_source, truth_cell = v1.true_support_indices(
            truth_xy, record["timing"], native_rows, mapping, support
        )
        endpoints: dict[str, dict[str, float]] = {}
        for channel, cells in {"native": mapping["native_cell"], **cell_fields}.items():
            for mode in ALL_MODES:
                endpoints[f"{channel}_{mode}"] = v1.endpoint(
                    native_rows, cells, truth_xy, tie_mode=mode
                )
        row: dict[str, Any] = {
            "house": house,
            "seed": seed,
            "source_update_id": update_id,
            "source_update_time_s": float(record["update_time_s"]),
            "visible_physical_stops": len(record["visible_stops"]),
            "observed_hit_stops": int(record["observed_hit_stops"]),
            "truth_carrier_index": truth_source,
            "truth_carrier_id": support["carriers"][truth_source],
            "native_true_cell_rank": v1.rank_desc(mapping["native_cell"], truth_cell),
            "native_carrier_true_rank": v1.rank_desc(mapping["native_carrier"], truth_source),
            "full_carrier_true_rank": v1.rank_desc(record["method_carrier"], truth_source),
            "zero_mass_abstained_arms": ";".join(invariants["abstained_arms"]),
            **{key: float(value) for key, value in invariants.items() if key != "abstained_arms"},
        }
        for channel in ("native",) + METHOD_CHANNELS:
            for mode in ALL_MODES:
                endpoint = endpoints[f"{channel}_{mode}"]
                row[f"{channel}_{mode}_error_m"] = endpoint["error_m"]
                row[f"{channel}_{mode}_variance_m2"] = endpoint["variance_m2"]
                row[f"{channel}_{mode}_selected_variance_m2"] = endpoint["selected_variance_m2"]
        updates.append(row)
        if update_id == v1.SOURCE_UPDATES:
            parity = abs(endpoints["native_ascending"]["error_m"] - float(case["primary_error_m"]))
            invariant_max["native_final_endpoint_parity_max_abs_m"] = max(
                invariant_max.get("native_final_endpoint_parity_max_abs_m", 0.0), parity
            )
            final_internal.append({
                **record,
                **row,
                "truth_xy": truth_xy,
                "native_rows": native_rows,
                "mapping": mapping,
                "case_sha256": case_sha,
            })

    if len(updates) != 150 or len(final_internal) != 30:
        raise ValueError(f"CTT_V2_RECORD_COUNT_FAIL:{len(updates)}:{len(final_internal)}")

    # V2 is an interface-only replay over the exact V1 outcome inputs.  Do not
    # merely accept a directory with the same shape: bind every native PMFS
    # posterior and every truth-bearing case result to the hashes preserved in
    # the frozen V1 summary.
    frozen_inputs = frozen_v1_summary.get("input_hashes", {})
    if comparator_hashes != frozen_inputs.get("native_source_posteriors"):
        raise ValueError("CTT_V2_NATIVE_POSTERIOR_HASH_SET_FAIL")
    current_case_hashes = {
        f"{house}_seed{seed}": digest
        for (house, seed), (_, digest) in case_cache.items()
    }
    if current_case_hashes != frozen_inputs.get("case_results"):
        raise ValueError("CTT_V2_CASE_RESULT_HASH_SET_FAIL")

    null_rows, null_summary = evaluate_source_label_nulls(final_internal, support_all)
    final_rows = [
        {key: value for key, value in item.items()
         if not isinstance(value, (np.ndarray, list, dict, Path, tuple))}
        for item in final_internal
    ]
    diagnostics = {
        "invariant_maxima": invariant_max,
        "abstained_updates_by_arm": abstained_updates,
        "source_label_null": null_summary,
        "case_result_sha256": current_case_hashes,
        "native_source_posterior_sha256": comparator_hashes,
    }
    return updates, final_rows, null_rows, diagnostics


def evaluate_source_label_nulls(
    final_internal: list[dict[str, Any]], support_all: dict[str, dict[str, Any]]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    observed: dict[str, float] = {}
    native_error: dict[str, np.ndarray] = {}
    for mode in NULL_MODES:
        native = np.asarray([row[f"native_{mode}_error_m"] for row in final_internal])
        full = np.asarray([row[f"full_{mode}_error_m"] for row in final_internal])
        native_error[mode] = native
        observed[mode] = float((np.sum(native) - np.sum(full)) / np.sum(native))
    null_values = {
        family: {mode: np.empty(v1.NULL_REPLICATES, dtype=np.float64) for mode in NULL_MODES}
        for family in ("unrestricted", "free_count_stratified")
    }
    rows: list[dict[str, Any]] = []
    for replicate in range(v1.NULL_REPLICATES):
        errors = {
            family: {mode: [] for mode in NULL_MODES}
            for family in null_values
        }
        for item in final_internal:
            house = item["house"]
            support = support_all[house]
            maps = {
                "unrestricted": uniform_permutation(
                    len(support["carriers"]), f"UNRESTRICTED|{house}|{replicate}"
                ),
                "free_count_stratified": uniform_stratified_permutation(
                    support["free_cells"], house, replicate
                ),
            }
            for family, label_map in maps.items():
                target = v1.stable_softmax(
                    np.log(item["q0_carrier"]) + item["raw_score"][label_map]
                )
                projected = hierarchical_project(
                    target,
                    item["mapping"]["native_cell"],
                    item["mapping"]["cell_to_source"],
                    label=f"{family}_null",
                )["cell"]
                for mode in NULL_MODES:
                    errors[family][mode].append(v1.endpoint(
                        item["native_rows"], projected, item["truth_xy"], tie_mode=mode
                    )["error_m"])
        null_row: dict[str, Any] = {"replicate": replicate}
        for family in null_values:
            for mode in NULL_MODES:
                null_method = np.asarray(errors[family][mode], dtype=np.float64)
                value = float(
                    (np.sum(native_error[mode]) - np.sum(null_method))
                    / np.sum(native_error[mode])
                )
                null_values[family][mode][replicate] = value
                null_row[f"{family}_{mode}_pooled_relative_improvement"] = value
        rows.append(null_row)

    summary: dict[str, Any] = {"replicates": v1.NULL_REPLICATES, "families": {}}
    for family, modes in null_values.items():
        pvalues = {
            mode: float(
                (1 + np.count_nonzero(values >= observed[mode]))
                / (v1.NULL_REPLICATES + 1)
            )
            for mode, values in modes.items()
        }
        summary["families"][family] = {
            "empirical_upper_tail_p": pvalues,
            "maximum_primary_empirical_upper_tail_p": max(
                pvalues[mode] for mode in PRIMARY_MODES
            ),
        }
    return rows, summary


def _metrics(rows: list[dict[str, Any]], mode: str, channel: str) -> dict[str, Any]:
    native = np.asarray([row[f"native_{mode}_error_m"] for row in rows], dtype=np.float64)
    method = np.asarray([row[f"{channel}_{mode}_error_m"] for row in rows], dtype=np.float64)
    relative = np.divide(native - method, native, out=np.zeros_like(native), where=native > 0.0)
    catastrophe = (method > native + 1.0) & (method > 1.5 * native)
    native_collapse = (
        (native > 2.0)
        & (np.asarray([row[f"native_{mode}_variance_m2"] for row in rows]) < 1.0)
    )
    method_collapse = (
        (method > 2.0)
        & (np.asarray([row[f"{channel}_{mode}_variance_m2"] for row in rows]) < 1.0)
    )
    return {
        "pairs": len(rows),
        "native_total_error_m": float(np.sum(native)),
        "method_total_error_m": float(np.sum(method)),
        "native_mean_error_m": float(np.mean(native)),
        "method_mean_error_m": float(np.mean(method)),
        "pooled_relative_improvement": float((np.sum(native) - np.sum(method)) / np.sum(native)),
        "median_pair_relative_improvement": float(np.median(relative)),
        "improved_pairs": int(np.count_nonzero(method < native - TOL)),
        "tied_pairs": int(np.count_nonzero(np.abs(method - native) <= TOL)),
        "regressed_pairs": int(np.count_nonzero(method > native + TOL)),
        "catastrophic_regressions": int(np.count_nonzero(catastrophe)),
        "new_false_confident_collapses": int(np.count_nonzero(method_collapse & ~native_collapse)),
    }


def aggregate(
    updates: list[dict[str, Any]],
    final_rows: list[dict[str, Any]],
    diagnostics: dict[str, Any],
    prereg: dict[str, Any],
) -> dict[str, Any]:
    full = {mode: _metrics(final_rows, mode, "full") for mode in ALL_MODES}
    by_house = {
        house: {
            mode: _metrics([row for row in final_rows if row["house"] == house], mode, "full")
            for mode in ALL_MODES
        }
        for house in v1.HOUSES
    }
    controls = {
        channel: {mode: _metrics(final_rows, mode, channel) for mode in ALL_MODES}
        for channel in ("conditional_only", "coarse_only", "count_only", "stop_label_permute")
    }
    inv = diagnostics["invariant_maxima"]
    limits = prereg["invariants"]
    gate = prereg["hard_go_rules"]
    random_min_pooled = min(full[mode]["pooled_relative_improvement"] for mode in RANDOM_MODES)
    random_min_improved = min(full[mode]["improved_pairs"] for mode in RANDOM_MODES)
    all_mode_house_min = min(
        by_house[house][mode]["pooled_relative_improvement"]
        for house in v1.HOUSES for mode in ALL_MODES
    )
    rules = {
        "valid_updates_exactly": len(updates) == int(gate["valid_updates_exactly"]),
        "valid_final_pairs_exactly": len(final_rows) == int(gate["valid_final_pairs_exactly"]),
        "identity_reconstruction": inv["identity_reconstruction_max_abs"] <= float(limits["identity_reconstruction_max_abs"]),
        "carrier_marginal": inv["carrier_marginal_max_abs"] <= float(limits["carrier_marginal_max_abs"]),
        "within_carrier_conditional": inv["within_carrier_conditional_max_abs"] <= float(limits["within_carrier_conditional_max_abs"]),
        "total_mass": inv["total_mass_max_abs"] <= float(limits["total_mass_max_abs"]),
        "fail_closed_exact_native": inv["fail_closed_native_max_abs"] <= TOL,
        "cell_row_permutation": inv["cell_row_permutation_max_abs_after_restore"] <= float(limits["cell_row_permutation_max_abs_after_restore"]),
        "native_final_endpoint_parity": inv["native_final_endpoint_parity_max_abs_m"] <= float(limits["native_final_endpoint_parity_max_abs_m"]),
        "official_pooled_improvement": full["ascending"]["pooled_relative_improvement"] >= float(gate["official_pooled_relative_improvement_at_least"]),
        "reverse_pooled_improvement": full["descending"]["pooled_relative_improvement"] >= float(gate["reverse_pooled_relative_improvement_at_least"]),
        "symmetric_pooled_improvement": full["symmetric"]["pooled_relative_improvement"] >= float(gate["symmetric_pooled_relative_improvement_at_least"]),
        "random_tie_minimum_pooled_improvement": random_min_pooled >= float(gate["random_tie_minimum_pooled_relative_improvement_at_least"]),
        "official_improved_pairs": full["ascending"]["improved_pairs"] >= int(gate["official_improved_pairs_at_least"]),
        "reverse_improved_pairs": full["descending"]["improved_pairs"] >= int(gate["reverse_improved_pairs_at_least"]),
        "symmetric_improved_pairs": full["symmetric"]["improved_pairs"] >= int(gate["symmetric_improved_pairs_at_least"]),
        "random_tie_minimum_improved_pairs": random_min_improved >= int(gate["random_tie_minimum_improved_pairs_at_least"]),
        "each_house_each_tie_mode": all_mode_house_min >= float(gate["each_house_each_tie_mode_pooled_relative_improvement_at_least"]),
        "primary_median_pair_improvement": min(full[mode]["median_pair_relative_improvement"] for mode in PRIMARY_MODES) >= float(gate["median_pair_relative_improvement_each_primary_mode_at_least"]),
        "catastrophes_every_tie_mode": max(full[mode]["catastrophic_regressions"] for mode in ALL_MODES) <= int(gate["catastrophic_regressions_every_tie_mode_at_most"]),
        "new_false_confident_collapses": max(full[mode]["new_false_confident_collapses"] for mode in PRIMARY_MODES) <= int(gate["new_false_confident_collapses_every_primary_mode_at_most"]),
        "unrestricted_source_label_p": diagnostics["source_label_null"]["families"]["unrestricted"]["maximum_primary_empirical_upper_tail_p"] <= float(gate["unrestricted_source_label_empirical_p_at_most"]),
        "free_count_stratified_source_label_p": diagnostics["source_label_null"]["families"]["free_count_stratified"]["maximum_primary_empirical_upper_tail_p"] <= float(gate["free_count_stratified_source_label_empirical_p_at_most"]),
        "full_no_worse_than_conditional_only": all(full[mode]["method_total_error_m"] <= controls["conditional_only"][mode]["method_total_error_m"] + TOL for mode in ALL_MODES),
        "full_no_worse_than_count_only": all(full[mode]["method_total_error_m"] <= controls["count_only"][mode]["method_total_error_m"] + TOL for mode in ALL_MODES),
        "full_no_worse_than_stop_label_permute": all(full[mode]["method_total_error_m"] <= controls["stop_label_permute"][mode]["method_total_error_m"] + TOL for mode in ALL_MODES),
    }
    verdict = PASS if all(rules.values()) else NO_GO
    return {
        "verdict": verdict,
        "hard_pass_rules": rules,
        "overall": full,
        "by_house": by_house,
        "controls": controls,
        "fixed_random_tie_worst_case": {
            "minimum_pooled_relative_improvement": random_min_pooled,
            "minimum_improved_pairs": random_min_improved,
            "minimum_house_pooled_relative_improvement_all_modes": all_mode_house_min,
        },
        **diagnostics,
    }


def selftest() -> None:
    # The stratified Monte Carlo null must retain the full within-stratum
    # permutation law.  In particular, a two-member stratum must show both
    # identity and swap draws rather than being forced to swap every time.
    two_member_draws = {
        tuple(uniform_stratified_permutation(np.asarray([2, 2]), "H00", index))
        for index in range(64)
    }
    assert (0, 1) in two_member_draws and (1, 0) in two_member_draws
    stratified = uniform_stratified_permutation(
        np.asarray([1, 1, 2, 2, 3]), "H00", 0
    )
    assert np.array_equal(
        np.asarray([1, 1, 2, 2, 3])[stratified], np.asarray([1, 1, 2, 2, 3])
    )

    labels = np.asarray([0, 0, 1, 1], dtype=np.int64)
    native = np.asarray([0.1, 0.2, 0.3, 0.4], dtype=np.float64)
    target = np.asarray([0.6, 0.4], dtype=np.float64)
    projected = hierarchical_project(target, native, labels, label="selftest")
    assert not projected["abstained"]
    assert np.max(np.abs(carrier_marginal(projected["cell"], labels, 2) - target)) <= TOL
    expected = np.asarray([0.2, 0.4, 0.4 * 3.0 / 7.0, 0.4 * 4.0 / 7.0])
    assert np.max(np.abs(projected["cell"] - expected)) <= TOL
    identity = hierarchical_project(np.asarray([0.3, 0.7]), native, labels, label="identity")
    assert np.max(np.abs(identity["cell"] - native)) <= TOL
    assert row_permutation_projection_max_abs(target, native, labels) <= TOL

    zero_native = np.asarray([0.5, 0.5, 0.0, 0.0])
    conflict = hierarchical_project(target, zero_native, labels, label="zero_conflict")
    assert conflict["abstained"] and np.array_equal(conflict["cell"], zero_native)
    no_conflict = hierarchical_project(np.asarray([1.0, 0.0]), zero_native, labels, label="zero_both")
    assert not no_conflict["abstained"] and np.array_equal(no_conflict["cell"], zero_native)

    synthetic_mapping = {
        "native_cell": native,
        "native_carrier": np.asarray([0.3, 0.7]),
        "cell_to_source": labels,
    }
    synthetic_support = {"free_cells": np.asarray([2, 2])}
    synthetic_record = {
        "q0_carrier": np.asarray([0.5, 0.5]),
        "method_carrier": target,
        "count_only_carrier": np.asarray([0.7, 0.3]),
        "stop_label_permute_carrier": np.asarray([0.4, 0.6]),
    }
    arms, arm_invariants = build_update_arms(
        synthetic_record, synthetic_mapping, synthetic_support
    )
    assert set(arms) == set(METHOD_CHANNELS)
    assert np.max(np.abs(arms["identity_reconstruction"] - native)) <= TOL
    assert np.max(np.abs(carrier_marginal(arms["full"], labels, 2) - target)) <= TOL
    assert np.max(np.abs(
        carrier_marginal(arms["conditional_only"], labels, 2)
        - synthetic_record["q0_carrier"]
    )) <= TOL
    assert np.max(np.abs(
        arms["coarse_only"] - target[labels] / synthetic_support["free_cells"][labels]
    )) <= TOL
    assert max(
        float(value) for key, value in arm_invariants.items()
        if key != "abstained_arms"
    ) <= TOL

    rows = [{"cell_index": str(index), "x": str(index), "y": "0"} for index in range(40)]
    mass = np.zeros(40); mass[:4] = 0.25
    assert v1.endpoint(rows, mass, (0.0, 0.0), tie_mode="ascending")["estimate_x"] == 0.5
    assert v1.endpoint(rows, mass, (0.0, 0.0), tie_mode="descending")["estimate_x"] == 2.5
    assert v1.endpoint(rows, mass, (0.0, 0.0), tie_mode="symmetric")["estimate_x"] == 1.5
    for mode in RANDOM_MODES:
        assert math.isfinite(v1.endpoint(rows, mass, (0.0, 0.0), tie_mode=mode)["error_m"])

    # Synthetic artifact proves external manifest, byte hashes and semantic hash
    # are all independently enforced by the V2 loader.
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        v1_prereg = root / "v1_prereg.json"
        v1_prereg.write_text("{}\n", encoding="utf-8")
        freeze = root / "INPUT_FREEZE.json"
        freeze.write_text("{}\n", encoding="utf-8")
        synthetic: list[dict[str, Any]] = []
        for house in v1.HOUSES:
            source_count = v1.SOURCE_COUNTS[house]
            uniform = np.full(source_count, 1.0 / source_count)
            for seed in v1.SEEDS:
                for update_id in range(1, v1.SOURCE_UPDATES + 1):
                    record: dict[str, Any] = {
                        "house": house, "seed": seed, "update_id": update_id,
                        "update_time_s": float(update_id),
                        "visible_stops": np.arange(3 * update_id),
                        "observed_hit_stops": update_id,
                        "historical_measured_tape_exact_train_member_matches": 0,
                        "timing": {"grid_width": "1"},
                        "max_online_batch_abs": 0.0,
                    }
                    for key in v1.STAGE1_ARRAY_KEYS:
                        record[key] = uniform.copy()
                    synthetic.append(record)
        manifest = v1.write_stage1_artifact(
            root, synthetic, v1_prereg, Path(v1.__file__), 4936, sha256_file(freeze)
        )
        v2_prereg = {
            "frozen_stage1": {
                "records": 150,
                "verified_train_shards": 4936,
                "method_posteriors_npz_sha256": manifest["artifact_sha256"],
                "method_posteriors_manifest_sha256": sha256_file(root / "METHOD_POSTERIORS_MANIFEST.json"),
                "input_freeze_sha256": sha256_file(freeze),
                "semantic_pretruth_posterior_sha256": manifest["pretruth_posterior_sha256"],
                "v1_evaluator_sha256": sha256_file(Path(v1.__file__)),
                "v1_preregistration_sha256": sha256_file(v1_prereg),
            }
        }
        loaded, _ = load_frozen_stage1(
            root, v2_prereg,
            v2_prereg["frozen_stage1"]["method_posteriors_manifest_sha256"],
            v1_prereg, Path(v1.__file__),
        )
        assert len(loaded) == 150 and v1.pretruth_digest(loaded) == v1.pretruth_digest(synthetic)

    # Exercise every machine hard-rule key without touching real outcomes.
    repo = Path(__file__).resolve().parents[3]
    frozen_prereg = json.loads((
        repo / "docs" / "CTT_CAUSAL_TEMPORAL_HIERARCHICAL_PROJECTION_V2_PREREGISTRATION_20260831.json"
    ).read_text(encoding="utf-8"))
    fake_final: list[dict[str, Any]] = []
    for house in v1.HOUSES:
        for seed in v1.SEEDS:
            row: dict[str, Any] = {"house": house, "seed": seed}
            for mode in ALL_MODES:
                for channel, error in {
                    "native": 2.0,
                    "full": 1.0,
                    "conditional_only": 1.5,
                    "coarse_only": 1.5,
                    "count_only": 1.5,
                    "stop_label_permute": 1.5,
                }.items():
                    row[f"{channel}_{mode}_error_m"] = error
                    row[f"{channel}_{mode}_variance_m2"] = 2.0
            fake_final.append(row)
    fake_diagnostics = {
        "invariant_maxima": {
            "identity_reconstruction_max_abs": 0.0,
            "carrier_marginal_max_abs": 0.0,
            "within_carrier_conditional_max_abs": 0.0,
            "total_mass_max_abs": 0.0,
            "fail_closed_native_max_abs": 0.0,
            "cell_row_permutation_max_abs_after_restore": 0.0,
            "native_final_endpoint_parity_max_abs_m": 0.0,
        },
        "abstained_updates_by_arm": {},
        "source_label_null": {
            "families": {
                family: {"maximum_primary_empirical_upper_tail_p": 1.0 / 257.0}
                for family in ("unrestricted", "free_count_stratified")
            }
        },
    }
    synthetic_gate = aggregate([{} for _ in range(150)], fake_final, fake_diagnostics, frozen_prereg)
    assert synthetic_gate["verdict"] == PASS and all(synthetic_gate["hard_pass_rules"].values())
    print("CTT_CAUSAL_TEMPORAL_HIERARCHICAL_PROJECTION_V2_SELFTEST=PASS")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--run-freeze", type=Path)
    parser.add_argument("--run-freeze-sha256")
    parser.add_argument("--stage1-root", type=Path)
    parser.add_argument("--stage1-manifest-sha256")
    parser.add_argument("--historical-root", type=Path)
    parser.add_argument("--source-support", type=Path)
    parser.add_argument("--v1-preregistration", type=Path)
    parser.add_argument("--v1-evaluator", type=Path)
    parser.add_argument("--v1-summary", type=Path)
    parser.add_argument("--preregistration", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return 0
    required = (
        args.run_freeze, args.run_freeze_sha256,
        args.stage1_root, args.stage1_manifest_sha256, args.historical_root,
        args.source_support, args.v1_preregistration, args.v1_evaluator,
        args.v1_summary, args.preregistration, args.output,
    )
    if any(value is None for value in required):
        raise SystemExit("CTT_V2_REQUIRED_ARGUMENT_MISSING")
    if args.output.exists():
        raise SystemExit(f"CTT_V2_REFUSE_OVERWRITE:{args.output}")
    if sha256_file(args.run_freeze) != args.run_freeze_sha256:
        raise SystemExit("CTT_V2_EXTERNAL_RUN_FREEZE_HASH_FAIL")
    run_freeze = json.loads(args.run_freeze.read_text(encoding="utf-8"))
    if (
        run_freeze.get("contract") != f"{CONTRACT}_RUN_FREEZE"
        or run_freeze.get("status") != "FROZEN_BEFORE_V2_OUTCOME_READ"
    ):
        raise SystemExit("CTT_V2_RUN_FREEZE_CONTRACT_FAIL")
    evaluator_path = Path(__file__).resolve()
    if sha256_file(evaluator_path) != run_freeze.get("evaluator_sha256"):
        raise SystemExit("CTT_V2_EVALUATOR_RUN_FREEZE_HASH_FAIL")
    if sha256_file(args.preregistration) != run_freeze.get("preregistration_sha256"):
        raise SystemExit("CTT_V2_PREREGISTRATION_RUN_FREEZE_HASH_FAIL")
    if sha256_file(args.v1_summary) != run_freeze.get("v1_summary_sha256"):
        raise SystemExit("CTT_V2_V1_SUMMARY_RUN_FREEZE_HASH_FAIL")
    if str(args.historical_root.resolve()) != run_freeze.get("historical_root"):
        raise SystemExit("CTT_V2_HISTORICAL_ROOT_RUN_FREEZE_FAIL")
    if Path(v1.__file__).resolve() != args.v1_evaluator.resolve():
        raise SystemExit("CTT_V2_IMPORTED_V1_PATH_FAIL")

    prereg = json.loads(args.preregistration.read_text(encoding="utf-8"))
    if (
        prereg.get("contract") != CONTRACT
        or prereg.get("status")
        != "PREREGISTERED_BEFORE_V2_HIERARCHICAL_PROJECTION_OUTCOME_READ"
    ):
        raise SystemExit("CTT_V2_PREREGISTRATION_FAIL")
    if str(args.historical_root.resolve()) != prereg["scope"]["historical_root"]:
        raise SystemExit("CTT_V2_HISTORICAL_ROOT_PREREGISTRATION_FAIL")
    if sha256_file(args.source_support) != prereg["scope"]["region_support_manifest_sha256"]:
        raise SystemExit("CTT_V2_SOURCE_SUPPORT_HASH_FAIL")
    frozen_v1_summary = json.loads(args.v1_summary.read_text(encoding="utf-8"))
    if (
        frozen_v1_summary.get("contract") != "CTT_CAUSAL_TEMPORAL_PMFS_SHADOW_V1"
        or sha256_file(args.v1_summary) != prereg["preserved_v1"]["summary_sha256"]
    ):
        raise SystemExit("CTT_V2_FROZEN_V1_SUMMARY_CONTRACT_FAIL")
    records, stage1 = load_frozen_stage1(
        args.stage1_root, prereg, args.stage1_manifest_sha256,
        args.v1_preregistration, args.v1_evaluator,
    )
    support = v1.load_support(args.source_support)
    args.output.mkdir(parents=True)
    try:
        updates, final_rows, null_rows, diagnostics = evaluate(
            records, args.historical_root, support, prereg, frozen_v1_summary
        )
        result = aggregate(updates, final_rows, diagnostics, prereg)
    except Exception as error:
        (args.output / "VERDICT.txt").write_text(INVALID + "\n", encoding="utf-8")
        (args.output / "FIRST_ERROR.txt").write_text(
            f"{type(error).__name__}: {error}\n", encoding="utf-8"
        )
        raise
    report = {
        "contract": CONTRACT,
        "fixed_trajectory_development_only": True,
        "closed_loop_effectiveness_established": False,
        "gaden_runs": 0,
        "neural_training": False,
        "M1_or_M2_recomputed": False,
        "projection": prereg["hierarchical_projection"],
        **result,
        "input_hashes": {
            "preregistration": sha256_file(args.preregistration),
            "evaluator": sha256_file(Path(__file__)),
            "stage1_artifact": stage1["artifact_sha256"],
            "stage1_manifest": sha256_file(args.stage1_root / "METHOD_POSTERIORS_MANIFEST.json"),
            "source_support": sha256_file(args.source_support),
            "v1_evaluator": sha256_file(args.v1_evaluator),
            "v1_preregistration": sha256_file(args.v1_preregistration),
            "v1_summary": sha256_file(args.v1_summary),
            "run_freeze": sha256_file(args.run_freeze),
        },
    }
    with (args.output / "UPDATES.csv").open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=list(updates[0])); writer.writeheader(); writer.writerows(updates)
    with (args.output / "FINAL_PAIRS.csv").open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=list(final_rows[0])); writer.writeheader(); writer.writerows(final_rows)
    with (args.output / "SOURCE_LABEL_NULLS.csv").open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=list(null_rows[0])); writer.writeheader(); writer.writerows(null_rows)
    (args.output / "SUMMARY.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (args.output / "VERDICT.txt").write_text(result["verdict"] + "\n", encoding="utf-8")
    print(json.dumps({
        "verdict": result["verdict"],
        "overall": {mode: result["overall"][mode] for mode in PRIMARY_MODES},
        "by_house": {
            house: {mode: result["by_house"][house][mode] for mode in PRIMARY_MODES}
            for house in v1.HOUSES
        },
        "hard_pass_rules": result["hard_pass_rules"],
    }, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
