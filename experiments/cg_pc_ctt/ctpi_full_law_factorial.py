#!/usr/bin/env python3
"""Truth-blind A0/F00/F01 factorial gate for the CTPI closed-loop candidate.

Stage 1 consumes the already-frozen V0.3 route-count laws and freezes:

* F00: CREL mean projection plus the frozen count likelihood;
* F01: CREL complete count law plus a categorical proper log score;
* every canonical non-identity source-law reassignment control.

Stage 2 verifies every Stage-1 hash before reading source truth or A0.  It
reports robot-task metrics but never runs GADEN, trains a model, or starts ROS.
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

from cpir_three_module_shadow import (
    HOUSES,
    SOURCE_UPDATES,
    BankHouse,
    endpoint,
    load_case,
    projection,
    read_csv,
    sha256_file,
)
from cpir_factorial_offline import (
    HORIZON_S,
    align_cell_mass,
    comparison,
    metric_record,
    paired_direction,
    time_to_threshold,
    trapezoid_auc,
)
from ctpi_closed_loop_core import f00_posterior, full_law_posterior
from ctpi_full_law_controls import canonical_cyclic_reassignment_indices


CONTRACT = "CTPI_FULL_LAW_FACTORIAL_V1"
UPSTREAM_CONTRACT = "CTPI_FULL_LAW_ORACLE_GATE_V0_3_IDEASPARK"
UPSTREAM_STATUS = "CTPI_FULL_LAW_SURFACES_FROZEN_BEFORE_TRUTH"
OUTPUT_ARMS = ("A0", "F00", "F01")
PAIR_TOL = 1.0e-12


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise RuntimeError(f"CTPI_EMPTY_CSV:{path.name}")
    with path.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _validate_prereg(path: Path) -> dict[str, Any]:
    value = _load_json(path)
    if value.get("contract") != CONTRACT:
        raise RuntimeError("CTPI_FACTORIAL_PREREG_CONTRACT")
    if value.get("houses") != list(HOUSES) or int(value.get("source_updates", -1)) != SOURCE_UPDATES:
        raise RuntimeError("CTPI_FACTORIAL_PREREG_SCOPE")
    if value.get("module_comparisons") != {"M1": "F00_vs_A0", "M2": "F01_vs_F00"}:
        raise RuntimeError("CTPI_FACTORIAL_PREREG_COMPARISONS")
    if value.get("m3_status") != "CLOSED_LOOP_ONLY_NOT_CLAIMED_OFFLINE":
        raise RuntimeError("CTPI_FACTORIAL_PREREG_M3_BOUNDARY")
    return value


def _verify_upstream(stage1_root: Path) -> tuple[dict[str, Any], Path]:
    manifest_path = stage1_root / "CTPI_STAGE1_MANIFEST.json"
    manifest = _load_json(manifest_path)
    if manifest.get("contract") != UPSTREAM_CONTRACT or manifest.get("status") != UPSTREAM_STATUS:
        raise RuntimeError("CTPI_FACTORIAL_UPSTREAM_CONTRACT")
    expected = manifest.get("semantic_freeze_sha256")
    payload = dict(manifest)
    payload.pop("semantic_freeze_sha256", None)
    actual = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    if expected != actual or manifest.get("truth_read") is not False:
        raise RuntimeError("CTPI_FACTORIAL_UPSTREAM_SEMANTIC_FREEZE")
    for name, digest in manifest.get("files", {}).items():
        candidate = stage1_root / name
        if not candidate.is_file() or sha256_file(candidate) != digest:
            raise RuntimeError(f"CTPI_FACTORIAL_UPSTREAM_FILE_HASH:{name}")
    return manifest, manifest_path


def stage1(upstream_root: Path, prereg_path: Path, output: Path) -> dict[str, Any]:
    prereg = _validate_prereg(prereg_path)
    upstream, upstream_manifest_path = _verify_upstream(upstream_root)
    output.mkdir(parents=True, exist_ok=False)
    house_meta: dict[str, Any] = {}
    for house in HOUSES:
        frozen = np.load(upstream_root / f"{house}_CTPI_STAGE1.npz")
        counts = np.asarray(frozen["counts"], dtype=np.int64)
        q0 = np.asarray(frozen["q0"], dtype=np.float64)
        carrier_ids = np.asarray(frozen["carrier_ids"], dtype=str)
        observed = np.asarray(frozen["observed_hit_count"], dtype=np.int64)
        visible = np.asarray(frozen["visible_count"], dtype=np.int64)
        upstream_f00 = np.asarray(frozen["f00"], dtype=np.float64)
        if counts.shape != (10 * SOURCE_UPDATES, len(q0), 8):
            raise RuntimeError(f"CTPI_FACTORIAL_COUNT_SHAPE:{house}:{counts.shape}")
        if observed.shape != (len(counts),) or visible.shape != observed.shape:
            raise RuntimeError(f"CTPI_FACTORIAL_OBSERVATION_SHAPE:{house}")
        f00 = np.empty_like(upstream_f00)
        f01 = np.empty_like(upstream_f00)
        control = np.empty((len(q0) - 1, len(counts), len(q0)), dtype=np.float64)
        for record in range(len(counts)):
            h = int(observed[record]); n = int(visible[record])
            f00[record] = f00_posterior(q0, counts[record], h, n)
            f01[record] = full_law_posterior(q0, counts[record], h, n)
            for shift in range(1, len(q0)):
                permutation = canonical_cyclic_reassignment_indices(carrier_ids, shift)
                control[shift - 1, record] = full_law_posterior(
                    q0, counts[record, permutation], h, n
                )
        parity = float(np.max(np.abs(f00 - upstream_f00)))
        if parity > 1.0e-12:
            raise RuntimeError(f"CTPI_FACTORIAL_F00_PARITY:{house}:{parity}")
        np.savez_compressed(
            output / f"{house}_CTPI_FACTORIAL.npz",
            carrier_ids=carrier_ids,
            q0=q0,
            carrier_cell_counts=np.asarray(frozen["carrier_cell_counts"], dtype=np.int64),
            cell_indices=np.asarray(frozen["cell_indices"], dtype=np.int64),
            cell_to_carrier=np.asarray(frozen["cell_to_carrier"], dtype=np.int64),
            seed=np.asarray(frozen["seed"], dtype=np.int64),
            update_id=np.asarray(frozen["update_id"], dtype=np.int64),
            update_time_s=np.asarray(frozen["update_time_s"], dtype=np.float64),
            observed_hit_count=observed,
            visible_count=visible,
            f00=f00,
            f01=f01,
            law_reassignment=control,
        )
        house_meta[house] = {
            "carrier_count": int(len(q0)),
            "canonical_nonidentity_controls": int(len(q0) - 1),
            "f00_upstream_max_abs": parity,
        }
        print(f"CTPI_FULL_LAW_FACTORIAL_STAGE1_{house}=PASS", flush=True)

    files = {p.name: sha256_file(p) for p in sorted(output.iterdir()) if p.is_file()}
    manifest = {
        "contract": CONTRACT,
        "status": "A0_F00_F01_AND_LAW_CONTROLS_FROZEN_BEFORE_TRUTH",
        "preregistration_sha256": sha256_file(prereg_path),
        "upstream_manifest_sha256": sha256_file(upstream_manifest_path),
        "upstream_semantic_freeze_sha256": upstream["semantic_freeze_sha256"],
        "inference_core_sha256": sha256_file(Path(__file__).with_name("ctpi_closed_loop_core.py")),
        "house_meta": house_meta,
        "files": files,
        "truth_read": False,
        "gaden_runs": 0,
        "neural_training": False,
        "closed_loop": False,
        "m3_evaluated": False,
        "preregistered_gate": prereg["gate"],
    }
    manifest["semantic_freeze_sha256"] = hashlib.sha256(
        json.dumps(manifest, sort_keys=True).encode("utf-8")
    ).hexdigest()
    _write_json(output / "CTPI_FACTORIAL_STAGE1_MANIFEST.json", manifest)
    return manifest


def _verify_stage1(stage1_root: Path, prereg_path: Path) -> dict[str, Any]:
    manifest_path = stage1_root / "CTPI_FACTORIAL_STAGE1_MANIFEST.json"
    manifest = _load_json(manifest_path)
    if manifest.get("contract") != CONTRACT or manifest.get("status") != "A0_F00_F01_AND_LAW_CONTROLS_FROZEN_BEFORE_TRUTH":
        raise RuntimeError("CTPI_FACTORIAL_STAGE1_CONTRACT")
    payload = dict(manifest)
    expected = payload.pop("semantic_freeze_sha256", None)
    actual = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    if expected != actual or manifest.get("truth_read") is not False:
        raise RuntimeError("CTPI_FACTORIAL_STAGE1_SEMANTIC_FREEZE")
    if manifest.get("preregistration_sha256") != sha256_file(prereg_path):
        raise RuntimeError("CTPI_FACTORIAL_STAGE1_PREREG_HASH")
    for name, digest in manifest.get("files", {}).items():
        candidate = stage1_root / name
        if not candidate.is_file() or sha256_file(candidate) != digest:
            raise RuntimeError(f"CTPI_FACTORIAL_STAGE1_FILE_HASH:{name}")
    return manifest


def _truth_indices(bank: BankHouse, case: Any, truth: tuple[float, float]) -> tuple[int, int]:
    ix = math.floor((truth[0] - float(case.timing["origin_x"])) / float(case.timing["cell_size"]))
    iy = math.floor((truth[1] - float(case.timing["origin_y"])) / float(case.timing["cell_size"]))
    native = int(ix + iy * int(case.timing["grid_width"]))
    if native not in bank.cell_to_stream:
        raise RuntimeError(f"CTPI_FACTORIAL_TRUTH_SUPPORT:{bank.house}:{case.seed}")
    row = int(bank.cell_to_stream[native])
    return int(bank.cell_to_carrier[row]), row


def evaluate(
    bank_root: Path,
    historical_root: Path,
    support_path: Path,
    prereg_path: Path,
    stage1_root: Path,
    output: Path,
) -> dict[str, Any]:
    prereg = _validate_prereg(prereg_path)
    manifest = _verify_stage1(stage1_root, prereg_path)
    support_rows = read_csv(support_path)
    output.mkdir(parents=True, exist_ok=False)
    update_rows: list[dict[str, Any]] = []
    case_rows: list[dict[str, Any]] = []
    control_rows: list[dict[str, Any]] = []
    a0_final_update5_max_abs = 0.0

    for house in HOUSES:
        bank = BankHouse.load(house, bank_root, support_rows)
        cases = [load_case(historical_root, house, seed, bank, strict_full_coverage=False)
                 for seed in range(10)]
        frozen = np.load(stage1_root / f"{house}_CTPI_FACTORIAL.npz")
        if list(frozen["carrier_ids"].astype(str)) != bank.carriers:
            raise RuntimeError(f"CTPI_FACTORIAL_CARRIER_ORDER:{house}")
        cell_rows = [
            {"cell_index": str(int(cell)), "x": str(float(x)), "y": str(float(y))}
            for cell, x, y in zip(bank.cell_indices, bank.cell_x, bank.cell_y)
        ]
        prior_cell = projection(bank.q0, bank.cell_to_carrier, bank.carrier_cell_counts)
        controls = np.asarray(frozen["law_reassignment"], dtype=np.float64)

        for case_index, case in enumerate(cases):
            native = _load_json(case.runtime.parent.parent / "case_result.json")
            truth = tuple(float(v) for v in native["truth_eval_only"])
            truth_carrier, truth_cell_row = _truth_indices(bank, case, truth)
            prior_metric = metric_record(
                bank, cell_rows, prior_cell, truth, truth_carrier, truth_cell_row
            )
            series: dict[str, list[dict[str, float]]] = {arm: [] for arm in OUTPUT_ARMS}
            control_series: list[list[dict[str, float]]] = [list() for _ in range(controls.shape[0])]
            a0_update5_cell: np.ndarray | None = None
            for update_index in range(SOURCE_UPDATES):
                record = case_index * SOURCE_UPDATES + update_index
                update_dir = case.runtime / "context_bank" / f"source_update_{update_index + 1:04d}"
                a0_cell = align_cell_mass(read_csv(update_dir / "source_posterior.csv"), bank)
                if update_index == SOURCE_UPDATES - 1:
                    a0_update5_cell = a0_cell.copy()
                cell_mass = {
                    "A0": a0_cell,
                    "F00": projection(
                        np.asarray(frozen["f00"][record], dtype=np.float64),
                        bank.cell_to_carrier, bank.carrier_cell_counts,
                    ),
                    "F01": projection(
                        np.asarray(frozen["f01"][record], dtype=np.float64),
                        bank.cell_to_carrier, bank.carrier_cell_counts,
                    ),
                }
                for arm in OUTPUT_ARMS:
                    item = metric_record(
                        bank, cell_rows, cell_mass[arm], truth, truth_carrier, truth_cell_row
                    )
                    series[arm].append(item)
                    update_rows.append({
                        "house": house,
                        "seed": case.seed,
                        "update_id": update_index + 1,
                        "update_time_s": float(case.update_times[update_index]),
                        "arm": arm,
                        **item,
                    })
                for shift_index in range(controls.shape[0]):
                    cell_mass = projection(
                        controls[shift_index, record], bank.cell_to_carrier, bank.carrier_cell_counts
                    )
                    control_series[shift_index].append(metric_record(
                        bank, cell_rows, cell_mass, truth, truth_carrier, truth_cell_row
                    ))

            if a0_update5_cell is None:
                raise RuntimeError(f"CTPI_FACTORIAL_A0_UPDATE5_MISSING:{house}:{case.seed}")
            a0_final_cell = align_cell_mass(
                read_csv(case.runtime.parent.parent / "final_posterior.csv"), bank
            )
            a0_final_update5_max_abs = max(
                a0_final_update5_max_abs,
                float(np.max(np.abs(a0_final_cell - a0_update5_cell))),
            )
            a0_final_metric = metric_record(
                bank, cell_rows, a0_final_cell, truth, truth_carrier, truth_cell_row
            )
            endpoint_delta = abs(a0_final_metric["error_m"] - float(native["primary_error_m"]))
            if endpoint_delta > 1.0e-8:
                raise RuntimeError(
                    f"CTPI_FACTORIAL_A0_ENDPOINT_PARITY:{house}:{case.seed}:{endpoint_delta}"
                )
            times = np.asarray(
                [0.0] + [float(v) for v in case.update_times] + [HORIZON_S], dtype=np.float64
            )
            for arm in OUTPUT_ARMS:
                final = a0_final_metric if arm == "A0" else series[arm][-1]
                errors = np.asarray(
                    [prior_metric["error_m"]] + [v["error_m"] for v in series[arm]] +
                    [final["error_m"]], dtype=np.float64
                )
                t2, reached = time_to_threshold(times, errors)
                case_rows.append({
                    "house": house,
                    "seed": case.seed,
                    "arm": arm,
                    "final_error_m": final["error_m"],
                    "error_auc_m_s": trapezoid_auc(times, errors),
                    "time_to_2m_s": t2,
                    "threshold_reached": int(reached),
                    "final_true_source_normalized_rank": final["true_source_normalized_rank"],
                    "final_posterior_entropy_nats": final["posterior_entropy_nats"],
                    "final_max_posterior_probability": final["max_posterior_probability"],
                })
            for shift_index, values in enumerate(control_series, start=1):
                errors = np.asarray(
                    [prior_metric["error_m"]] + [v["error_m"] for v in values] +
                    [values[-1]["error_m"]], dtype=np.float64
                )
                t2, reached = time_to_threshold(times, errors)
                control_rows.append({
                    "house": house,
                    "seed": case.seed,
                    "shift": shift_index,
                    "final_error_m": values[-1]["error_m"],
                    "error_auc_m_s": trapezoid_auc(times, errors),
                    "time_to_2m_s": t2,
                    "threshold_reached": int(reached),
                    "final_true_source_normalized_rank": values[-1]["true_source_normalized_rank"],
                })
        print(f"CTPI_FULL_LAW_FACTORIAL_STAGE2_{house}=PASS", flush=True)

    # One matched destructive-control summary per tape; no favorable shift is selected.
    control_median_rows: list[dict[str, Any]] = []
    for house in HOUSES:
        for seed in range(10):
            rows = [r for r in control_rows if r["house"] == house and int(r["seed"]) == seed]
            control_median_rows.append({
                "house": house,
                "seed": seed,
                "arm": "LAW_REASSIGNMENT_MEDIAN",
                **{name: float(np.median([float(r[name]) for r in rows])) for name in (
                    "final_error_m", "error_auc_m_s", "time_to_2m_s",
                    "final_true_source_normalized_rank",
                )},
            })
    comparison_rows = case_rows + control_median_rows
    metrics = (
        "final_error_m", "error_auc_m_s", "time_to_2m_s",
        "final_true_source_normalized_rank",
    )
    comparisons: dict[str, Any] = {}
    for label, left, right in (
        ("M1_F00_vs_A0", "A0", "F00"),
        ("M2_F01_vs_F00", "F00", "F01"),
        ("M2_CONTROL_F01_vs_LAW_REASSIGNMENT", "LAW_REASSIGNMENT_MEDIAN", "F01"),
    ):
        comparisons[label] = {
            metric: comparison(comparison_rows, left, right, metric) for metric in metrics
        }

    def eligible(label: str, names: tuple[str, ...]) -> list[str]:
        return [name for name in names if (
            comparisons[label][name]["clear_increment"] and
            comparisons[label][name]["cross_house_repeatable"]
        )]

    m1_selected = eligible(
        "M1_F00_vs_A0", ("final_error_m", "error_auc_m_s", "time_to_2m_s")
    )
    m1_final = comparisons["M1_F00_vs_A0"]["final_error_m"]
    m1_pass = bool(m1_selected and not m1_final["significant_worsening"] and
                   not m1_final["stable_reverse_houses"])

    m2_selected = eligible(
        "M2_F01_vs_F00", ("final_error_m", "error_auc_m_s", "time_to_2m_s")
    )
    m2_final = comparisons["M2_F01_vs_F00"]["final_error_m"]
    m2_rank = comparisons["M2_F01_vs_F00"]["final_true_source_normalized_rank"]
    control_selected = eligible(
        "M2_CONTROL_F01_vs_LAW_REASSIGNMENT", ("final_error_m", "error_auc_m_s")
    )
    control_rank = comparisons[
        "M2_CONTROL_F01_vs_LAW_REASSIGNMENT"
    ]["final_true_source_normalized_rank"]
    m2_pass = bool(
        m2_selected and
        not m2_final["significant_worsening"] and
        not m2_final["stable_reverse_houses"] and
        m2_rank["right_mean"] < m2_rank["left_mean"] and
        control_selected and
        control_rank["right_mean"] < control_rank["left_mean"]
    )
    offline_pass = bool(m1_pass and m2_pass)
    verdict = (
        "CTPI_M1_M2_OFFLINE_PASS_TO_RUNTIME_AND_M3_SMOKE"
        if offline_pass else "CTPI_FULL_LAW_FACTORIAL_NO_GO"
    )
    report = {
        "contract": CONTRACT,
        "status": "OFFLINE_FACTORIAL_COMPLETE",
        "verdict": verdict,
        "case_count": 30,
        "update_rows": len(update_rows),
        "gaden_runs": 0,
        "neural_training": False,
        "closed_loop": False,
        "a0_final_vs_update5_posterior_max_abs": a0_final_update5_max_abs,
        "module_gates": {
            "M1_CREL": {"pass": m1_pass, "selected_increment_metrics": m1_selected},
            "M2_FULL_LAW_PROPER_SCORE": {
                "pass": m2_pass,
                "selected_increment_metrics": m2_selected,
                "law_reassignment_increment_metrics": control_selected,
                "rank_same_direction": bool(m2_rank["right_mean"] < m2_rank["left_mean"]),
            },
            "M3_INFORMATION_ACTION": {
                "pass": False,
                "status": "CLOSED_LOOP_ONLY_NOT_EVALUATED_OFFLINE",
            },
        },
        "comparisons": comparisons,
        "stage1_manifest_sha256": sha256_file(
            stage1_root / "CTPI_FACTORIAL_STAGE1_MANIFEST.json"
        ),
        "preregistration_sha256": sha256_file(prereg_path),
        "gate": prereg["gate"],
    }
    _write_csv(output / "PER_UPDATE_METRICS.csv", update_rows)
    _write_csv(output / "CASE_METRICS.csv", case_rows)
    _write_csv(output / "LAW_REASSIGNMENT_CASES.csv", control_rows)
    _write_csv(output / "LAW_REASSIGNMENT_MEDIAN_CASES.csv", control_median_rows)
    _write_json(output / "SUMMARY.json", report)
    (output / "VERDICT.txt").write_text(verdict + "\n", encoding="utf-8")
    return report


def selftest() -> None:
    prior = np.asarray([0.5, 0.5])
    counts = np.asarray([[0, 0, 2, 2], [1, 1, 1, 1]])
    f00 = f00_posterior(prior, counts, 1, 2)
    f01 = full_law_posterior(prior, counts, 1, 2)
    np.testing.assert_allclose(f00, [0.5, 0.5], atol=1e-15)
    assert f01[1] > f01[0]
    left = np.asarray([3.0, 3.0, 3.0, 3.0, 3.0, 3.0])
    right = np.asarray([2.0, 2.0, 2.0, 2.0, 2.0, 2.0])
    assert paired_direction(left, right)["clear_increment"]
    print("CTPI_FULL_LAW_FACTORIAL_SELFTEST=PASS")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--stage", choices=("1", "2"))
    parser.add_argument("--upstream-stage1", type=Path)
    parser.add_argument("--bank-root", type=Path)
    parser.add_argument("--historical-root", type=Path)
    parser.add_argument("--support", type=Path)
    parser.add_argument("--prereg", type=Path)
    parser.add_argument("--stage1", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return 0
    if not args.stage or not args.prereg or not args.output:
        parser.error("--stage, --prereg and --output are required")
    if args.stage == "1":
        if not args.upstream_stage1:
            parser.error("--upstream-stage1 is required for stage 1")
        stage1(args.upstream_stage1, args.prereg, args.output)
    else:
        if not all((args.bank_root, args.historical_root, args.support, args.stage1)):
            parser.error("--bank-root, --historical-root, --support and --stage1 are required")
        evaluate(
            args.bank_root, args.historical_root, args.support,
            args.prereg, args.stage1, args.output,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
