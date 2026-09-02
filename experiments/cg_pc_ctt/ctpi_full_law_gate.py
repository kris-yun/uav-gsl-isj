#!/usr/bin/env python3
"""CTPI V0.3 full-law truth-blind oracle gate.

This evaluator is designed to live in experiments/cg_pc_ctt beside the frozen
CPIR reference scripts.  Stage 1 reads only the historical measurement tapes,
the frozen exact-route bank, carrier geometry, and the already-frozen F00
Stage-1 artifact.  Stage 2 verifies Stage-1 hashes before opening source truth.

No GADEN invocation, ROS launch, neural training, SBI, or closed-loop action is
performed by this file.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

_PROJECT_IMPORT_ERROR: Exception | None = None
try:
    from cpir_three_module_shadow import (
        HOUSES,
        MEMBER_COUNT,
        SOURCE_UPDATES,
        THRESHOLD_PPM,
        BankHouse,
        carrier_scores,
        endpoint,
        load_case,
        projection,
        rank_desc,
        read_csv,
        sha256_file,
    )
    from cpir_factorial_offline import (
        ANALYSIS_STOP_COUNT,
        HORIZON_S,
        LOCALIZATION_THRESHOLD_M,
        normalized_rank,
        read_route_streams,
        trapezoid_auc,
        time_to_threshold,
    )
except ModuleNotFoundError as exc:
    # Keep --selftest portable.  Scientific Stage1/Stage2 still require the
    # exact frozen project reference scripts and will refuse to run without them.
    _PROJECT_IMPORT_ERROR = exc

from ctpi_full_law_core import (
    count_histograms,
    cramer_energy_units,
    cyclic_reassignment_indices,
    f00_mean_projection_numerator,
    integrated_excess_identification,
    mean_alias_distinct_pairs,
    observation_rps_robustness_depth,
    persistence_mass,
    route_member_counts,
    surface_area,
    surface_persistence,
    survivor_surface,
    transport_replacement_radius,
)
from ctpi_full_law_controls import (
    canonical_cyclic_reassignment_indices,
    transport_break_strength_for_permutation,
)
from ctpi_closed_loop_core import preserve_bitexact_reference

CONTRACT = "CTPI_FULL_LAW_ORACLE_GATE_V0_3_IDEASPARK"
PRIOR_CPIR_CONTRACT = "CPIR_FACTORIAL_OFFLINE_V1"
PRIOR_CPIR_STATUS = "F00_F01_F10_F11_FROZEN_BEFORE_A0_AND_TRUTH"
PAIR_TOL = 1.0e-12


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _verify_semantic_freeze(manifest: dict[str, Any]) -> None:
    expected = manifest.get("semantic_freeze_sha256")
    if not isinstance(expected, str):
        raise RuntimeError("CTPI_SEMANTIC_FREEZE_MISSING")
    payload = dict(manifest)
    payload.pop("semantic_freeze_sha256", None)
    actual = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    if actual != expected:
        raise RuntimeError(f"CTPI_SEMANTIC_FREEZE_HASH:{expected}:{actual}")


def _canonical_rank(values: np.ndarray) -> np.ndarray:
    """Average ranks, ascending, dependency-free; exact ties receive equal rank."""
    x = np.asarray(values, dtype=np.float64)
    if x.ndim != 1 or not np.isfinite(x).all():
        raise RuntimeError("CTPI_RANKDATA_INPUT")
    order = np.argsort(x, kind="mergesort")
    result = np.empty(len(x), dtype=np.float64)
    start = 0
    while start < len(x):
        end = start + 1
        while end < len(x) and x[order[end]] == x[order[start]]:
            end += 1
        rank = 0.5 * ((start + 1) + end)
        result[order[start:end]] = rank
        start = end
    return result


def spearman(x: np.ndarray, y: np.ndarray) -> float | None:
    a = np.asarray(x, dtype=np.float64)
    b = np.asarray(y, dtype=np.float64)
    if a.shape != b.shape or a.ndim != 1 or len(a) < 2:
        raise RuntimeError("CTPI_SPEARMAN_INPUT")
    ra = _canonical_rank(a)
    rb = _canonical_rank(b)
    sa = float(np.std(ra)); sb = float(np.std(rb))
    if sa == 0.0 or sb == 0.0:
        return None
    return float(np.corrcoef(ra, rb)[0, 1])


def _matched_area_top_set(score: np.ndarray, q0: np.ndarray, target_mass: float) -> np.ndarray:
    """F00 top-score set with q0 mass >= target; include every exact boundary tie."""
    s = np.asarray(score, dtype=np.float64)
    q = np.asarray(q0, dtype=np.float64)
    if s.ndim != 1 or q.shape != s.shape or np.any(q < 0.0) or not np.isfinite(s).all():
        raise RuntimeError("CTPI_MATCHED_F00_INPUT")
    q = q / float(np.sum(q))
    target = float(target_mass)
    if not 0.0 <= target <= 1.0 + 1e-12:
        raise RuntimeError("CTPI_MATCHED_F00_TARGET")
    if target <= 0.0:
        return np.zeros(len(s), dtype=np.bool_)
    # Determine the boundary score by descending score only; q0 is used only
    # for area accumulation, never as a tie breaker.
    levels = np.unique(s)[::-1]
    chosen = np.zeros(len(s), dtype=np.bool_)
    mass = 0.0
    for level in levels:
        tied = s == level
        chosen |= tied
        mass += float(np.sum(q[tied]))
        if mass + 1e-15 >= target:
            break
    return chosen


def _truth_carrier(bank: BankHouse, case: Any, truth: tuple[float, float]) -> int:
    origin_x = float(case.timing["origin_x"]); origin_y = float(case.timing["origin_y"])
    cell = float(case.timing["cell_size"]); width = int(case.timing["grid_width"])
    ix = math.floor((truth[0] - origin_x) / cell)
    iy = math.floor((truth[1] - origin_y) / cell)
    native = int(ix + iy * width)
    if native not in bank.cell_to_stream:
        raise RuntimeError(f"CTPI_TRUTH_SUPPORT:{bank.house}:{case.seed}:{native}")
    row = int(bank.cell_to_stream[native])
    return int(bank.cell_to_carrier[row])


def _cell_rows(bank: BankHouse) -> list[dict[str, str]]:
    return [
        {"cell_index": str(int(c)), "x": str(float(x)), "y": str(float(y))}
        for c, x, y in zip(bank.cell_indices, bank.cell_x, bank.cell_y)
    ]


def _validate_prereg(prereg_path: Path) -> dict[str, Any]:
    prereg = _load_json(prereg_path)
    if prereg.get("contract") != CONTRACT:
        raise RuntimeError("CTPI_PREREG_CONTRACT")
    method = prereg.get("method", {})
    if any(method.get(name) is not None for name in (
        "fixed_deletion_level", "dominance_margin", "likelihood_temperature", "jeffreys_smoothing"
    )):
        raise RuntimeError("CTPI_PREREG_HIDDEN_PARAMETER")
    assets = prereg.get("frozen_assets", {})
    if assets.get("houses") != list(HOUSES):
        raise RuntimeError("CTPI_PREREG_HOUSES")
    if int(assets.get("member_count_from_asset", -1)) != MEMBER_COUNT:
        raise RuntimeError("CTPI_PREREG_MEMBER_COUNT")
    if int(assets.get("source_updates_from_asset", -1)) != SOURCE_UPDATES:
        raise RuntimeError("CTPI_PREREG_UPDATES")
    if int(assets.get("analysis_stop_prefix_from_prior_contract", -1)) != ANALYSIS_STOP_COUNT:
        raise RuntimeError("CTPI_PREREG_STOPS")
    if not math.isclose(float(assets.get("sensor_event_threshold_ppm_from_prior_contract", -1.0)), THRESHOLD_PPM,
                        rel_tol=0.0, abs_tol=0.0):
        raise RuntimeError("CTPI_PREREG_SENSOR_THRESHOLD")
    return prereg


def _validate_prior_factorial(
    factorial_stage1: Path, prereg: dict[str, Any], bank_root: Path, support_path: Path,
) -> dict[str, Any]:
    assets = prereg["frozen_assets"]
    manifest_path = factorial_stage1 / "FACTORIAL_STAGE1_MANIFEST.json"
    if not manifest_path.is_file():
        raise RuntimeError("CTPI_PRIOR_FACTORIAL_MANIFEST_MISSING")
    if sha256_file(manifest_path) != assets["prior_factorial_stage1_manifest_sha256"]:
        raise RuntimeError("CTPI_PRIOR_FACTORIAL_MANIFEST_HASH")
    manifest = _load_json(manifest_path)
    if manifest.get("contract") != PRIOR_CPIR_CONTRACT or manifest.get("status") != PRIOR_CPIR_STATUS:
        raise RuntimeError("CTPI_PRIOR_FACTORIAL_CONTRACT")
    if manifest.get("semantic_freeze_sha256") != assets["prior_factorial_semantic_freeze_sha256"]:
        raise RuntimeError("CTPI_PRIOR_FACTORIAL_SEMANTIC_HASH")
    if manifest.get("preregistration_sha256") != assets["prior_cpir_prereg_sha256"]:
        raise RuntimeError("CTPI_PRIOR_FACTORIAL_PREREG_HASH")
    if sha256_file(support_path) != assets["support_manifest_sha256"]:
        raise RuntimeError("CTPI_SUPPORT_HASH")
    for name, digest in manifest.get("files", {}).items():
        path = factorial_stage1 / name
        if not path.is_file() or sha256_file(path) != digest:
            raise RuntimeError(f"CTPI_PRIOR_FACTORIAL_FILE_HASH:{name}")
    support_rows = read_csv(support_path)
    for house in HOUSES:
        bank = BankHouse.load(house, bank_root, support_rows)
        frozen = manifest.get("bank_hashes", {}).get(house, {})
        current = {
            "bank_summary_sha256": bank.summary_sha256,
            "cell_manifest_sha256": sha256_file(bank.root / "cell_manifest.csv"),
        }
        if frozen != current:
            raise RuntimeError(f"CTPI_FULLGRID_INTERFACE_HASH:{house}:{frozen}:{current}")
    return manifest


def _route_hash_check(route_root: Path, prereg: dict[str, Any]) -> None:
    assets = prereg["frozen_assets"]
    if sha256_file(route_root / "bank_summary.json") != assets["route_bank_summary_sha256"]:
        raise RuntimeError("CTPI_ROUTE_SUMMARY_HASH")
    if sha256_file(route_root / "bank_shard_manifest.csv") != assets["route_bank_manifest_sha256"]:
        raise RuntimeError("CTPI_ROUTE_MANIFEST_HASH")


def _build_route_raw_events(
    bank: BankHouse, cases: list[Any], route_root: Path,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Coverage-complete raw physical stop events only; no rejected sensor-state arm."""
    manifest_path = route_root / "bank_shard_manifest.csv"
    summary_path = route_root / "bank_summary.json"
    manifest = read_csv(manifest_path)
    summary = _load_json(summary_path)
    if summary.get("contract") != "PF_DEI_V3_HISTORICAL_NATIVE_BANK_V1":
        raise RuntimeError("CTPI_ROUTE_BANK_CONTRACT")
    rows = [row for row in manifest if row["house"] == bank.house and row["split"] == "train"]
    row_by_key = {(row["carrier_id"], int(row["member_id"])): row for row in rows}
    expected = {(carrier, member) for carrier in bank.carriers for member in range(MEMBER_COUNT)}
    if set(row_by_key) != expected:
        raise RuntimeError(f"CTPI_ROUTE_CARRIER_SET:{bank.house}")
    schedule_hashes = summary["trajectory_schedule_sha256"][bank.house + "_train"]
    schedule_lengths = summary["trajectory_lengths"][bank.house + "_train"]
    for case in cases:
        pose_path = case.runtime / "sim_pose_trace.csv"
        if (sha256_file(pose_path) != schedule_hashes[case.seed] or
                len(read_csv(pose_path)) != int(schedule_lengths[case.seed])):
            raise RuntimeError(f"CTPI_ROUTE_SCHEDULE:{bank.house}:{case.seed}")
    max_stops = max(len(case.stops) for case in cases)
    raw = np.zeros((len(cases), len(bank.carriers), MEMBER_COUNT, max_stops), dtype=np.bool_)
    values_checked = 0
    for carrier_index, carrier in enumerate(bank.carriers):
        for member in range(MEMBER_COUNT):
            row = row_by_key[(carrier, member)]
            streams = read_route_streams(route_root / row["relative_path"], row["sha256"])
            for case_index, case in enumerate(cases):
                physical = np.asarray(streams[case.seed][:1500], dtype=np.float32)
                if len(physical) != 1500:
                    raise RuntimeError(f"CTPI_ROUTE_TAPE_LENGTH:{bank.house}:{case.seed}")
                values_checked += len(physical)
                for stop_index, stop in enumerate(case.stops):
                    raw[case_index, carrier_index, member, stop_index] = bool(
                        np.max(physical[stop]) > THRESHOLD_PPM
                    )
            completed = carrier_index * MEMBER_COUNT + member + 1
            if completed % 500 == 0 or completed == len(bank.carriers) * MEMBER_COUNT:
                print(f"CTPI_ROUTE_RAW_PROGRESS={bank.house}:{completed}/{len(bank.carriers) * MEMBER_COUNT}", flush=True)
    return raw, {
        "contract": "CTPI_ROUTE_RAW_ONLY_INPUT_V1",
        "route_bank_summary_sha256": sha256_file(summary_path),
        "route_bank_manifest_sha256": sha256_file(manifest_path),
        "verified_shards": len(rows),
        "physical_values_consumed": values_checked,
        "schedule_hashes_verified": len(cases),
        "persistent_sensor_state_computed": False,
        "verdict": "CTPI_ROUTE_RAW_ONLY_INPUT_PASS",
    }


def stage1(
    bank_root: Path, historical_root: Path, support_path: Path, route_root: Path,
    factorial_stage1: Path, prereg_path: Path, output: Path,
) -> dict[str, Any]:
    prereg = _validate_prereg(prereg_path)
    _route_hash_check(route_root, prereg)
    prior_manifest = _validate_prior_factorial(factorial_stage1, prereg, bank_root, support_path)
    support_rows = read_csv(support_path)
    output.mkdir(parents=True, exist_ok=False)
    house_meta: dict[str, Any] = {}

    for house in HOUSES:
        bank = BankHouse.load(house, bank_root, support_rows)
        cases = [load_case(historical_root, house, seed, bank, strict_full_coverage=False)
                 for seed in range(10)]
        raw, route_audit = _build_route_raw_events(bank, cases, route_root)
        raw = raw[..., :ANALYSIS_STOP_COUNT]
        if raw.shape[:3] != (10, len(bank.carriers), MEMBER_COUNT):
            raise RuntimeError(f"CTPI_RAW_SHAPE:{house}:{raw.shape}")
        prior_npz = np.load(factorial_stage1 / f"{house}_FACTORIAL.npz")
        prior_f00 = np.asarray(prior_npz["f00"], dtype=np.float64)
        if prior_f00.shape != (50, len(bank.carriers)):
            raise RuntimeError(f"CTPI_PRIOR_F00_SHAPE:{house}:{prior_f00.shape}")
        if "carrier_ids" in prior_npz and list(prior_npz["carrier_ids"].astype(str)) != bank.carriers:
            raise RuntimeError(f"CTPI_PRIOR_F00_CARRIER_ORDER:{house}")

        rec_count = 50
        source_count = len(bank.carriers)
        counts_all = np.zeros((rec_count, source_count, MEMBER_COUNT), dtype=np.uint8)
        mean_num_all = np.zeros((rec_count, source_count), dtype=np.uint16)
        cramer_all = np.zeros((rec_count, source_count, source_count), dtype=np.uint16)
        t_radius_all = np.zeros((rec_count, source_count, source_count), dtype=np.uint8)
        o_depth_all = np.zeros_like(t_radius_all)
        rps_min_all = np.zeros((rec_count, source_count, MEMBER_COUNT), dtype=np.uint16)
        rps_max_all = np.zeros_like(rps_min_all)
        surface_all = np.zeros((rec_count, MEMBER_COUNT, MEMBER_COUNT, source_count), dtype=np.bool_)
        persistence_count_all = np.zeros((rec_count, source_count), dtype=np.uint8)
        persistence_mass_all = np.zeros((rec_count, source_count), dtype=np.float64)
        area_all = np.zeros((rec_count, MEMBER_COUNT, MEMBER_COUNT), dtype=np.float64)
        hard_pair_count = np.zeros(rec_count, dtype=np.uint32)
        mean_alias_pair_count = np.zeros(rec_count, dtype=np.uint32)
        f00_recomputed = np.zeros_like(prior_f00)
        f00_surface_all = np.zeros_like(surface_all)
        f00_persistence_count = np.zeros_like(persistence_count_all)
        f00_area_all = np.zeros_like(area_all)
        observed_hit_count = np.zeros(rec_count, dtype=np.uint8)
        update_time_s = np.zeros(rec_count, dtype=np.float64)
        seed_vec = np.zeros(rec_count, dtype=np.uint8)
        update_vec = np.zeros(rec_count, dtype=np.uint8)
        visible_count = np.zeros(rec_count, dtype=np.uint8)

        # Frozen F00 uses per-stop member mean with Jeffreys 1/2 smoothing.
        q_raw = (raw.sum(axis=2).astype(np.float64) + 0.5) / (MEMBER_COUNT + 1.0)
        record = 0
        for case_index, case in enumerate(cases):
            observed = np.asarray(case.observed_events[:ANALYSIS_STOP_COUNT], dtype=np.bool_)
            for update_id, visible in enumerate(case.visible, start=1):
                vis = np.asarray(visible, dtype=np.int64)
                if len(vis) > ANALYSIS_STOP_COUNT or not np.array_equal(vis, np.arange(len(vis))):
                    raise RuntimeError(f"CTPI_VISIBLE_PREFIX:{house}:{case.seed}:{update_id}:{vis.tolist()}")
                event_cube = raw[case_index][:, :, vis]
                h = int(np.count_nonzero(observed[vis]))
                n = int(len(vis))
                counts = route_member_counts(event_cube)
                hist = count_histograms(counts, n)
                cramer = cramer_energy_units(hist)
                t_radius = transport_replacement_radius(hist)
                alias = mean_alias_distinct_pairs(counts, cramer)
                o_depth, rps_lo, rps_hi = observation_rps_robustness_depth(counts, h, n)
                surface = survivor_surface(t_radius, o_depth, MEMBER_COUNT)
                persist = surface_persistence(surface)
                p_mass = persistence_mass(persist, bank.q0)
                area = surface_area(surface, bank.q0)

                _, f00 = carrier_scores(bank.q0, q_raw[case_index], observed, vis, "count_only")
                target_sets = np.zeros_like(surface)
                for rt in range(MEMBER_COUNT):
                    for ro in range(MEMBER_COUNT):
                        target_sets[rt, ro] = _matched_area_top_set(
                            f00, bank.q0, float(area[rt, ro])
                        )
                f00_area = surface_area(target_sets, bank.q0)

                mean_num = f00_mean_projection_numerator(counts)
                same_mean = mean_num[:, None] == mean_num[None, :]
                np.fill_diagonal(same_mean, False)

                counts_all[record] = counts.astype(np.uint8)
                mean_num_all[record] = mean_num.astype(np.uint16)
                cramer_all[record] = cramer.astype(np.uint16)
                t_radius_all[record] = t_radius.astype(np.uint8)
                o_depth_all[record] = o_depth.astype(np.uint8)
                rps_min_all[record] = rps_lo.astype(np.uint16)
                rps_max_all[record] = rps_hi.astype(np.uint16)
                surface_all[record] = surface
                persistence_count_all[record] = np.sum(surface, axis=(0, 1), dtype=np.uint8)
                persistence_mass_all[record] = p_mass
                area_all[record] = area
                hard_pair_count[record] = np.count_nonzero(np.triu(alias, 1))
                mean_alias_pair_count[record] = np.count_nonzero(np.triu(same_mean, 1))
                f00_recomputed[record] = f00
                f00_surface_all[record] = target_sets
                f00_persistence_count[record] = np.sum(target_sets, axis=(0, 1), dtype=np.uint8)
                f00_area_all[record] = f00_area
                observed_hit_count[record] = h
                update_time_s[record] = float(case.update_times[update_id - 1])
                seed_vec[record] = case.seed
                update_vec[record] = update_id
                visible_count[record] = n
                record += 1

        if record != rec_count:
            raise RuntimeError(f"CTPI_RECORD_COUNT:{house}:{record}")
        f00_frozen, parity = preserve_bitexact_reference(f00_recomputed, prior_f00)

        np.savez_compressed(
            output / f"{house}_CTPI_STAGE1.npz",
            carrier_ids=np.asarray(bank.carriers),
            q0=np.asarray(bank.q0, dtype=np.float64),
            carrier_cell_counts=np.asarray(bank.carrier_cell_counts, dtype=np.int64),
            cell_indices=np.asarray(bank.cell_indices, dtype=np.int64),
            cell_to_carrier=np.asarray(bank.cell_to_carrier, dtype=np.int64),
            counts=counts_all,
            f00_mean_numerator=mean_num_all,
            cramer_energy_units=cramer_all,
            transport_replacement_radius=t_radius_all,
            observation_rps_depth=o_depth_all,
            rps_min_numerator=rps_min_all,
            rps_max_numerator=rps_max_all,
            survivor_surface=surface_all,
            persistence_count=persistence_count_all,
            persistence_mass=persistence_mass_all,
            surface_area=area_all,
            mean_alias_distinct_pair_count=hard_pair_count,
            mean_alias_pair_count=mean_alias_pair_count,
            f00=f00_frozen,
            f00_matched_surface=f00_surface_all,
            f00_persistence_count=f00_persistence_count,
            f00_surface_area=f00_area_all,
            observed_hit_count=observed_hit_count,
            update_time_s=update_time_s,
            seed=seed_vec,
            update_id=update_vec,
            visible_count=visible_count,
        )
        house_meta[house] = {
            "carrier_count": source_count,
            "bank_summary_sha256": bank.summary_sha256,
            "cell_manifest_sha256": sha256_file(bank.root / "cell_manifest.csv"),
            "f00_max_abs_parity": parity,
            "f00_bitexact_reference_preserved": True,
            "route_audit": route_audit,
            "mean_alias_distinct_pairs_total": int(np.sum(hard_pair_count)),
            "contexts_with_mean_alias_distinct_pairs": int(np.count_nonzero(hard_pair_count)),
            "mean_alias_pairs_total": int(np.sum(mean_alias_pair_count)),
            "max_cramer_energy_units": int(np.max(cramer_all)),
            "max_transport_replacement_radius": int(np.max(t_radius_all)),
            "max_observation_rps_depth": int(np.max(o_depth_all)),
        }
        print(f"CTPI_FULL_LAW_STAGE1_{house}=PASS", flush=True)

    files = {path.name: sha256_file(path) for path in sorted(output.iterdir()) if path.is_file()}
    manifest = {
        "contract": CONTRACT,
        "status": "CTPI_FULL_LAW_SURFACES_FROZEN_BEFORE_TRUTH",
        "prereg_sha256": sha256_file(prereg_path),
        "support_sha256": sha256_file(support_path),
        "route_summary_sha256": sha256_file(route_root / "bank_summary.json"),
        "route_manifest_sha256": sha256_file(route_root / "bank_shard_manifest.csv"),
        "prior_factorial_manifest_sha256": sha256_file(factorial_stage1 / "FACTORIAL_STAGE1_MANIFEST.json"),
        "prior_factorial_semantic_freeze_sha256": prior_manifest["semantic_freeze_sha256"],
        "house_meta": house_meta,
        "method": prereg["method"],
        "files": files,
        "truth_read": False,
        "gaden_runs": 0,
        "neural_training": False,
        "closed_loop": False,
    }
    manifest["semantic_freeze_sha256"] = hashlib.sha256(
        json.dumps(manifest, sort_keys=True).encode("utf-8")
    ).hexdigest()
    _write_json(output / "CTPI_STAGE1_MANIFEST.json", manifest)
    return manifest

def _house_metrics(
    house: str, bank: BankHouse, cases: list[Any], frozen: Any,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    source_count = len(bank.carriers)
    if list(frozen["carrier_ids"].astype(str)) != bank.carriers:
        raise RuntimeError(f"CTPI_STAGE2_CARRIER_ORDER:{house}")
    q0 = np.asarray(frozen["q0"], dtype=np.float64)
    if np.max(np.abs(q0 - bank.q0)) > 1e-15:
        raise RuntimeError(f"CTPI_STAGE2_Q0:{house}")

    surface = np.asarray(frozen["survivor_surface"], dtype=np.bool_)
    persistence_count = np.asarray(frozen["persistence_count"], dtype=np.int64)
    persistence_mass_arr = np.asarray(frozen["persistence_mass"], dtype=np.float64)
    area = np.asarray(frozen["surface_area"], dtype=np.float64)
    f00 = np.asarray(frozen["f00"], dtype=np.float64)
    f00_surface = np.asarray(frozen["f00_matched_surface"], dtype=np.bool_)
    f00_persistence_count = np.asarray(frozen["f00_persistence_count"], dtype=np.int64)
    f00_area = np.asarray(frozen["f00_surface_area"], dtype=np.float64)
    mean_num = np.asarray(frozen["f00_mean_numerator"], dtype=np.int64)
    cramer = np.asarray(frozen["cramer_energy_units"], dtype=np.int64)
    t_radius = np.asarray(frozen["transport_replacement_radius"], dtype=np.int64)
    o_depth = np.asarray(frozen["observation_rps_depth"], dtype=np.int64)
    hard_pair_count = np.asarray(frozen["mean_alias_distinct_pair_count"], dtype=np.int64)
    seed_vec = np.asarray(frozen["seed"], dtype=np.int64)
    update_vec = np.asarray(frozen["update_id"], dtype=np.int64)
    update_time = np.asarray(frozen["update_time_s"], dtype=np.float64)

    truth_carriers: list[int] = []
    truths: dict[int, tuple[float, float]] = {}
    for case in cases:
        result_path = case.runtime.parent.parent / "case_result.json"
        native = _load_json(result_path)
        truth = tuple(float(v) for v in native["truth_eval_only"])
        truths[case.seed] = truth
        truth_carriers.append(_truth_carrier(bank, case, truth))
    if len(set(truth_carriers)) != 1:
        raise RuntimeError(f"CTPI_SOURCE_LABEL_UNIT_MISMATCH:{house}:{truth_carriers}")
    truth_carrier = truth_carriers[0]

    robustness_cells = float(MEMBER_COUNT * MEMBER_COUNT)
    mean_area = np.mean(area, axis=(1, 2))
    f00_mean_area = np.mean(f00_area, axis=(1, 2))
    j_by_source = np.mean(persistence_count / robustness_cells - mean_area[:, None], axis=0)
    f00_j_by_source = np.mean(f00_persistence_count / robustness_cells - f00_mean_area[:, None], axis=0)
    j_true = float(j_by_source[truth_carrier])
    f00_j_true = float(f00_j_by_source[truth_carrier])
    tail = float(np.sum(q0[j_by_source >= j_true - PAIR_TOL]))
    f00_tail = float(np.sum(q0[f00_j_by_source >= f00_j_true - PAIR_TOL]))

    rows: list[dict[str, Any]] = []
    ctpi_rank_values: list[float] = []
    f00_rank_values: list[float] = []
    ctpi_errors: dict[int, list[float]] = {seed: [] for seed in range(10)}
    f00_errors: dict[int, list[float]] = {seed: [] for seed in range(10)}
    cell_rows = _cell_rows(bank)
    prior_cell = projection(bank.q0, bank.cell_to_carrier, bank.carrier_cell_counts)
    prior_errors: dict[int, float] = {}
    truth_hard_alias_records = 0
    truth_hard_alias_pair_total = 0
    truth_hard_alias_persistence_margins: list[float] = []

    for case in cases:
        truth = truths[case.seed]
        prior_errors[case.seed] = float(endpoint(cell_rows, prior_cell, truth)["error_m"])

    for record in range(50):
        seed = int(seed_vec[record]); update_id = int(update_vec[record])
        truth = truths[seed]
        c_mass = persistence_mass_arr[record]
        f_mass = f00[record]
        c_rank = normalized_rank(c_mass, truth_carrier)
        f_rank = normalized_rank(f_mass, truth_carrier)
        c_cell = projection(c_mass, bank.cell_to_carrier, bank.carrier_cell_counts)
        f_cell = projection(f_mass, bank.cell_to_carrier, bank.carrier_cell_counts)
        c_err = float(endpoint(cell_rows, c_cell, truth)["error_m"])
        f_err = float(endpoint(cell_rows, f_cell, truth)["error_m"])
        ctpi_rank_values.append(c_rank); f00_rank_values.append(f_rank)
        ctpi_errors[seed].append(c_err); f00_errors[seed].append(f_err)

        truth_alias = (mean_num[record] == mean_num[record, truth_carrier]) & (
            cramer[record, truth_carrier] > 0
        )
        truth_alias[truth_carrier] = False
        alias_n = int(np.count_nonzero(truth_alias))
        truth_hard_alias_pair_total += alias_n
        truth_hard_alias_records += int(alias_n > 0)
        alias_margin = None
        if alias_n > 0:
            # F00's *physical* count-only likelihood is exactly tied inside
            # this class by Proposition 1.  Therefore use CTPI's unweighted
            # robustness-surface persistence (not q0-weighted mass) to test
            # whether the full-law mechanism actually resolves that tie in
            # the truth direction.  This is a mechanism diagnostic, not a
            # calibrated posterior comparison.
            true_persistence = float(persistence_count[record, truth_carrier] / robustness_cells)
            competitor_persistence = float(np.mean(
                persistence_count[record, truth_alias] / robustness_cells
            ))
            alias_margin = true_persistence - competitor_persistence
            truth_hard_alias_persistence_margins.append(alias_margin)

        rows.append({
            "house": house, "seed": seed, "update_id": update_id,
            "update_time_s": float(update_time[record]),
            "ctpi_true_persistence": float(persistence_count[record, truth_carrier] / robustness_cells),
            "ctpi_mean_surface_area": float(mean_area[record]),
            "ctpi_J": float(persistence_count[record, truth_carrier] / robustness_cells - mean_area[record]),
            "ctpi_true_source_normalized_rank": c_rank,
            "ctpi_error_m": c_err,
            "f00_true_persistence": float(f00_persistence_count[record, truth_carrier] / robustness_cells),
            "f00_mean_surface_area": float(f00_mean_area[record]),
            "f00_J": float(f00_persistence_count[record, truth_carrier] / robustness_cells - f00_mean_area[record]),
            "f00_true_source_normalized_rank": f_rank,
            "f00_error_m": f_err,
            "mean_alias_distinct_pair_count": int(hard_pair_count[record]),
            "truth_mean_alias_distinct_competitors": alias_n,
            "truth_hard_alias_ctpi_persistence_margin_vs_alias_mean": alias_margin,
        })

    # Mechanism control: reassign each complete P(K|S) to the wrong source identity.
    real_j = j_true
    controls = []
    carrier_ids = np.asarray(bank.carriers, dtype=str)
    for shift in range(1, source_count):
        # Define the destructive mapping in stable physical carrier-ID space,
        # not the incidental candidate-array order.
        pi = canonical_cyclic_reassignment_indices(carrier_ids, shift)
        control_persistence = persistence_count[:, pi]
        control_surface = np.take(surface, pi, axis=3)
        control_area = np.tensordot(control_surface.astype(np.float64), q0, axes=([3], [0]))
        control_j_by_source = np.mean(
            control_persistence / robustness_cells - np.mean(control_area, axis=(1, 2))[:, None],
            axis=0,
        )
        control_j = float(control_j_by_source[truth_carrier])
        b = float(np.mean([
            transport_break_strength_for_permutation(t_radius[record], pi, MEMBER_COUNT)
            for record in range(50)
        ]))
        controls.append({
            "shift": shift,
            "transport_break_strength": b,
            "J_true": control_j,
            "delta_J_real_minus_control": real_j - control_j,
        })
    informative = [row for row in controls if row["transport_break_strength"] > 0.0]
    control_mean = float(np.mean([row["J_true"] for row in informative])) if informative else None
    rho = spearman(
        np.asarray([row["transport_break_strength"] for row in informative]),
        np.asarray([row["delta_J_real_minus_control"] for row in informative]),
    ) if len(informative) >= 2 else None

    case_metrics = []
    for seed in range(10):
        case = cases[seed]
        times = np.asarray([0.0] + [float(v) for v in case.update_times] + [HORIZON_S], dtype=np.float64)
        c_err = np.asarray([prior_errors[seed]] + ctpi_errors[seed] + [ctpi_errors[seed][-1]], dtype=np.float64)
        f_err = np.asarray([prior_errors[seed]] + f00_errors[seed] + [f00_errors[seed][-1]], dtype=np.float64)
        c_t2, c_hit = time_to_threshold(times, c_err)
        f_t2, f_hit = time_to_threshold(times, f_err)
        case_metrics.append({
            "house": house, "seed": seed,
            "ctpi_error_auc_m_s": trapezoid_auc(times, c_err),
            "ctpi_time_to_2m_s": c_t2, "ctpi_reached_2m": int(c_hit),
            "ctpi_final_error_m": float(c_err[-1]),
            "f00_error_auc_m_s": trapezoid_auc(times, f_err),
            "f00_time_to_2m_s": f_t2, "f00_reached_2m": int(f_hit),
            "f00_final_error_m": float(f_err[-1]),
        })

    ctpi_rank_mean = float(np.mean(ctpi_rank_values))
    f00_rank_mean = float(np.mean(f00_rank_values))
    pareto_components = {
        "J_no_worse": j_true >= f00_j_true - PAIR_TOL,
        "tail_no_worse": tail <= f00_tail + PAIR_TOL,
        "rank_no_worse": ctpi_rank_mean <= f00_rank_mean + PAIR_TOL,
        "J_strict": j_true > f00_j_true + PAIR_TOL,
        "tail_strict": tail < f00_tail - PAIR_TOL,
        "rank_strict": ctpi_rank_mean < f00_rank_mean - PAIR_TOL,
    }
    house_pareto = bool(
        pareto_components["J_no_worse"] and pareto_components["tail_no_worse"] and
        pareto_components["rank_no_worse"] and
        (pareto_components["J_strict"] or pareto_components["tail_strict"] or pareto_components["rank_strict"])
    )
    summary = {
        "house": house,
        "truth_carrier_index": truth_carrier,
        "truth_carrier_id": bank.carriers[truth_carrier],
        "ctpi": {
            "J_H_true": j_true,
            "source_label_tail_mass": tail,
            "mean_true_source_normalized_rank": ctpi_rank_mean,
            "mean_true_persistence": float(np.mean(persistence_count[:, truth_carrier] / robustness_cells)),
            "mean_integrated_surface_area": float(np.mean(mean_area)),
        },
        "f00_matched": {
            "J_H_true": f00_j_true,
            "source_label_tail_mass": f00_tail,
            "mean_true_source_normalized_rank": f00_rank_mean,
            "mean_true_persistence": float(np.mean(f00_persistence_count[:, truth_carrier] / robustness_cells)),
            "mean_integrated_surface_area": float(np.mean(f00_mean_area)),
        },
        "strict_expressivity": {
            "mean_alias_distinct_pairs_total": int(np.sum(hard_pair_count)),
            "contexts_with_mean_alias_distinct_pairs": int(np.count_nonzero(hard_pair_count)),
            "truth_records_with_mean_alias_distinct_competitor": truth_hard_alias_records,
            "truth_mean_alias_distinct_competitors_total": truth_hard_alias_pair_total,
            "truth_hard_alias_mean_ctpi_persistence_margin": (
                float(np.mean(truth_hard_alias_persistence_margins))
                if truth_hard_alias_persistence_margins else None
            ),
            "truth_hard_alias_direct_mechanism_status": (
                "POSITIVE" if truth_hard_alias_persistence_margins and
                float(np.mean(truth_hard_alias_persistence_margins)) > PAIR_TOL
                else "NONPOSITIVE" if truth_hard_alias_persistence_margins
                else "NOT_IDENTIFIED"
            ),
        },
        "controls": {
            "count": len(controls),
            "informative_count": len(informative),
            "mean_informative_control_J": control_mean,
            "real_J_above_mean_informative_controls": bool(
                informative and control_mean is not None and j_true > control_mean + PAIR_TOL
            ),
            "break_strength_vs_degradation_spearman": rho,
            "positive_break_strength_vs_degradation": bool(rho is not None and rho > 0.0),
            "rows": controls,
        },
        "nontrivial": {
            "transport_distribution_separation": bool(np.any(t_radius > 0)),
            "observation_rps_preference": bool(np.any(o_depth > 0)),
            "max_transport_replacement_radius": int(np.max(t_radius)),
            "max_observation_rps_depth": int(np.max(o_depth)),
        },
        "pareto_vs_f00": {**pareto_components, "pass": house_pareto},
        "case_metrics": case_metrics,
    }
    return summary, rows


def _aggregate_truth_hard_alias_mechanism(
    house_summaries: dict[str, Any], houses: tuple[str, ...] | list[str] | None = None,
) -> dict[str, Any]:
    """Aggregate direct relevance of Proposition 1 without an effect-size cutoff.

    Only Houses containing at least one truth-involving exact-F00-mean/full-law-
    distinct context contribute.  Such Houses must not have a negative mean
    truth-vs-alias persistence margin, and the context-count-weighted pooled
    margin must be strictly positive.  If none exist, the mechanism's direct
    task relevance is NOT_IDENTIFIED rather than silently passed.
    """
    if houses is None:
        houses = list(house_summaries)
    alias_houses = [
        h for h in houses
        if int(house_summaries[h]["strict_expressivity"][
            "truth_records_with_mean_alias_distinct_competitor"
        ]) > 0
    ]
    weighted_num = 0.0
    weighted_den = 0
    no_house_negative = True
    for h in alias_houses:
        sx = house_summaries[h]["strict_expressivity"]
        n = int(sx["truth_records_with_mean_alias_distinct_competitor"])
        margin = float(sx["truth_hard_alias_mean_ctpi_persistence_margin"])
        weighted_num += n * margin
        weighted_den += n
        no_house_negative &= margin >= -PAIR_TOL
    pooled = weighted_num / weighted_den if weighted_den > 0 else None
    return {
        "houses": alias_houses,
        "observed": bool(alias_houses),
        "no_house_negative": bool(alias_houses and no_house_negative),
        "pooled_margin": pooled,
        "pooled_positive": bool(pooled is not None and pooled > PAIR_TOL),
    }

def stage2(
    bank_root: Path, historical_root: Path, support_path: Path,
    prereg_path: Path, stage1_root: Path, output: Path,
) -> dict[str, Any]:
    prereg = _validate_prereg(prereg_path)
    manifest_path = stage1_root / "CTPI_STAGE1_MANIFEST.json"
    manifest = _load_json(manifest_path)
    if manifest.get("contract") != CONTRACT or manifest.get("status") != "CTPI_FULL_LAW_SURFACES_FROZEN_BEFORE_TRUTH":
        raise RuntimeError("CTPI_STAGE1_CONTRACT")
    _verify_semantic_freeze(manifest)
    if manifest.get("prereg_sha256") != sha256_file(prereg_path):
        raise RuntimeError("CTPI_STAGE1_PREREG_HASH")
    if manifest.get("support_sha256") != sha256_file(support_path):
        raise RuntimeError("CTPI_STAGE1_SUPPORT_HASH")
    if manifest.get("support_sha256") != prereg["frozen_assets"]["support_manifest_sha256"]:
        raise RuntimeError("CTPI_STAGE1_SUPPORT_PREREG_HASH")
    for name, digest in manifest.get("files", {}).items():
        path = stage1_root / name
        if not path.is_file() or sha256_file(path) != digest:
            raise RuntimeError(f"CTPI_STAGE1_FILE_HASH:{name}")
    support_rows = read_csv(support_path)
    output.mkdir(parents=True, exist_ok=False)
    house_summaries = {}
    update_rows = []
    for house in HOUSES:
        bank = BankHouse.load(house, bank_root, support_rows)
        frozen_house = manifest.get("house_meta", {}).get(house, {})
        current_house = {
            "bank_summary_sha256": bank.summary_sha256,
            "cell_manifest_sha256": sha256_file(bank.root / "cell_manifest.csv"),
        }
        if any(frozen_house.get(k) != v for k, v in current_house.items()):
            raise RuntimeError(f"CTPI_STAGE2_BANK_INTERFACE_HASH:{house}:{frozen_house}:{current_house}")
        cases = [load_case(historical_root, house, seed, bank, strict_full_coverage=False)
                 for seed in range(10)]
        frozen = np.load(stage1_root / f"{house}_CTPI_STAGE1.npz")
        summary, rows = _house_metrics(house, bank, cases, frozen)
        house_summaries[house] = summary
        update_rows.extend(rows)
        print(f"CTPI_FULL_LAW_STAGE2_{house}=PASS", flush=True)

    # Pooled relative Gate; no arbitrary effect-size threshold is introduced.
    ctpi_j = np.asarray([house_summaries[h]["ctpi"]["J_H_true"] for h in HOUSES])
    f00_j = np.asarray([house_summaries[h]["f00_matched"]["J_H_true"] for h in HOUSES])
    ctpi_tail = np.asarray([house_summaries[h]["ctpi"]["source_label_tail_mass"] for h in HOUSES])
    f00_tail = np.asarray([house_summaries[h]["f00_matched"]["source_label_tail_mass"] for h in HOUSES])
    ctpi_rank = np.asarray([house_summaries[h]["ctpi"]["mean_true_source_normalized_rank"] for h in HOUSES])
    f00_rank = np.asarray([house_summaries[h]["f00_matched"]["mean_true_source_normalized_rank"] for h in HOUSES])

    alias_gate = _aggregate_truth_hard_alias_mechanism(house_summaries)

    rules = {
        "all_houses_positive_J": bool(np.all(ctpi_j > 0.0)),
        "all_houses_real_above_mean_informative_controls": bool(all(
            house_summaries[h]["controls"]["real_J_above_mean_informative_controls"] for h in HOUSES
        )),
        "all_houses_positive_break_strength_degradation_spearman": bool(all(
            house_summaries[h]["controls"]["positive_break_strength_vs_degradation"] for h in HOUSES
        )),
        "each_house_pareto_no_worse_f00_with_one_strict": bool(all(
            house_summaries[h]["pareto_vs_f00"]["pass"] for h in HOUSES
        )),
        "pooled_J_strict_better": bool(float(np.mean(ctpi_j)) > float(np.mean(f00_j)) + PAIR_TOL),
        "pooled_tail_strict_better": bool(float(np.mean(ctpi_tail)) < float(np.mean(f00_tail)) - PAIR_TOL),
        "pooled_rank_strict_better": bool(float(np.mean(ctpi_rank)) < float(np.mean(f00_rank)) - PAIR_TOL),
        "strict_expressivity_hard_pairs_all_houses": bool(all(
            house_summaries[h]["strict_expressivity"]["contexts_with_mean_alias_distinct_pairs"] > 0
            for h in HOUSES
        )),
        # Proposition 1 is only a load-bearing task mechanism if the truth
        # actually enters an F00-mean alias class somewhere.  When that occurs,
        # CTPI must break those exact physical-likelihood ties in the truth
        # direction on aggregate, with no House showing a negative mean margin.
        # No effect-size threshold is introduced: only sign is used.
        "truth_hard_alias_mechanism_observed": alias_gate["observed"],
        "truth_hard_alias_no_house_negative": alias_gate["no_house_negative"],
        "pooled_truth_hard_alias_margin_positive": alias_gate["pooled_positive"],
        "nontrivial_m2_m3_all_houses": bool(all(
            house_summaries[h]["nontrivial"]["transport_distribution_separation"] and
            house_summaries[h]["nontrivial"]["observation_rps_preference"] for h in HOUSES
        )),
    }
    go = bool(all(rules.values()))
    verdict = "CTPI_FULL_LAW_ORACLE_GO_TO_BANKFREE_M1_GATE" if go else "CTPI_FULL_LAW_ORACLE_NO_GO"

    with (output / "CTPI_UPDATE_ROWS.csv").open("w", newline="", encoding="utf-8") as f:
        if update_rows:
            writer = csv.DictWriter(f, fieldnames=list(update_rows[0]))
            writer.writeheader(); writer.writerows(update_rows)
    report = {
        "contract": CONTRACT,
        "status": "TRUTH_EVALUATION_COMPLETE",
        "verdict": verdict,
        "rules": rules,
        "pooled": {
            "ctpi_mean_J": float(np.mean(ctpi_j)), "f00_mean_J": float(np.mean(f00_j)),
            "ctpi_mean_source_label_tail": float(np.mean(ctpi_tail)),
            "f00_mean_source_label_tail": float(np.mean(f00_tail)),
            "ctpi_mean_true_source_rank": float(np.mean(ctpi_rank)),
            "f00_mean_true_source_rank": float(np.mean(f00_rank)),
            "truth_hard_alias_houses": alias_gate["houses"],
            "pooled_truth_hard_alias_ctpi_persistence_margin": alias_gate["pooled_margin"],
        },
        "houses": house_summaries,
        "stage1_manifest_sha256": sha256_file(manifest_path),
        "prereg_sha256": sha256_file(prereg_path),
        "gaden_runs": 0,
        "neural_training": False,
        "closed_loop": False,
    }
    _write_json(output / "CTPI_STAGE2_SUMMARY.json", report)
    (output / "VERDICT.txt").write_text(verdict + "\n", encoding="utf-8")
    return report


def selftest() -> None:
    # Matched-area tie handling.
    q = np.asarray([0.1, 0.2, 0.3, 0.4])
    score = np.asarray([4.0, 3.0, 3.0, 1.0])
    chosen = _matched_area_top_set(score, q, 0.25)
    assert np.array_equal(chosen, np.asarray([True, True, True, False]))
    # Spearman supports ties and detects positive monotone association.
    rho = spearman(np.asarray([0.0, 1.0, 1.0, 2.0]), np.asarray([0.0, 1.0, 2.0, 3.0]))
    assert rho is not None and rho > 0.0
    # Source reassignments have no fixed-point shift on the canonical cycle.
    for s in range(2, 40):
        for h in range(1, s):
            pi = cyclic_reassignment_indices(s, h)
            assert not np.any(pi == np.arange(s))
    # Destructive source-law mapping is invariant to candidate array order
    # when stable physical carrier IDs are carried with the array.
    labels = np.asarray(["k03", "k01", "k04", "k02"])
    pi1 = canonical_cyclic_reassignment_indices(labels, 1)
    order = np.asarray([2, 0, 3, 1])
    labels2 = labels[order]
    pi2 = canonical_cyclic_reassignment_indices(labels2, 1)
    pairs1 = {(labels[i], labels[pi1[i]]) for i in range(len(labels))}
    pairs2 = {(labels2[i], labels2[pi2[i]]) for i in range(len(labels2))}
    assert pairs1 == pairs2

    # Direct strict-expressivity task relevance is NOT_IDENTIFIED when truth
    # never enters a hard alias class; it requires nonnegative House means and
    # positive context-weighted pooled margin when such contexts do occur.
    test_houses = ("H01", "H02", "H03")
    empty = {
        h: {"strict_expressivity": {
            "truth_records_with_mean_alias_distinct_competitor": 0,
            "truth_hard_alias_mean_ctpi_persistence_margin": None,
        }} for h in test_houses
    }
    g0 = _aggregate_truth_hard_alias_mechanism(empty, test_houses)
    assert not g0["observed"] and g0["pooled_margin"] is None and not g0["pooled_positive"]
    pos = {
        "H01": {"strict_expressivity": {
            "truth_records_with_mean_alias_distinct_competitor": 2,
            "truth_hard_alias_mean_ctpi_persistence_margin": 0.10,
        }},
        "H02": {"strict_expressivity": {
            "truth_records_with_mean_alias_distinct_competitor": 1,
            "truth_hard_alias_mean_ctpi_persistence_margin": 0.04,
        }},
        "H03": empty["H03"],
    }
    gp = _aggregate_truth_hard_alias_mechanism(pos, test_houses)
    assert gp["observed"] and gp["no_house_negative"] and gp["pooled_positive"]
    assert abs(float(gp["pooled_margin"]) - 0.08) < 1e-12
    neg = dict(pos)
    neg["H02"] = {"strict_expressivity": {
        "truth_records_with_mean_alias_distinct_competitor": 1,
        "truth_hard_alias_mean_ctpi_persistence_margin": -0.01,
    }}
    gn = _aggregate_truth_hard_alias_mechanism(neg, test_houses)
    assert gn["observed"] and not gn["no_house_negative"]
    print("CTPI_FULL_LAW_ORACLE_GATE_SELFTEST=PASS")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--stage", choices=("stage1", "stage2"))
    parser.add_argument("--bank-root", type=Path)
    parser.add_argument("--historical-root", type=Path)
    parser.add_argument("--support-path", type=Path)
    parser.add_argument("--route-bank-root", type=Path)
    parser.add_argument("--factorial-stage1", type=Path)
    parser.add_argument("--prereg-path", type=Path)
    parser.add_argument("--stage1-root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.selftest:
        selftest(); return 0
    if _PROJECT_IMPORT_ERROR is not None:
        raise SystemExit(f"CTPI_PROJECT_REFERENCE_IMPORT_REQUIRED:{_PROJECT_IMPORT_ERROR}")
    required = (args.stage, args.bank_root, args.historical_root, args.support_path, args.prereg_path, args.output)
    if any(v is None for v in required):
        parser.error("--stage/--bank-root/--historical-root/--support-path/--prereg-path/--output required")
    if args.output.exists():
        raise SystemExit(f"CTPI_REFUSE_OVERWRITE:{args.output}")
    if args.stage == "stage1":
        if args.route_bank_root is None or args.factorial_stage1 is None:
            parser.error("Stage1 requires --route-bank-root and --factorial-stage1")
        result = stage1(
            args.bank_root, args.historical_root, args.support_path,
            args.route_bank_root, args.factorial_stage1, args.prereg_path, args.output,
        )
        print(json.dumps({"status": result["status"], "semantic_freeze_sha256": result["semantic_freeze_sha256"]}, indent=2))
    else:
        if args.stage1_root is None:
            parser.error("Stage2 requires --stage1-root")
        result = stage2(
            args.bank_root, args.historical_root, args.support_path,
            args.prereg_path, args.stage1_root, args.output,
        )
        print(json.dumps({"verdict": result["verdict"], "rules": result["rules"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
