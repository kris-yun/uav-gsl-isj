#!/usr/bin/env python3
"""Materialize archived OFF runs into the frozen V4 truth-blind NPZ schema.

This adapter is deliberately outcome-blind with respect to localization.  It
reads only PMFS measurement/runtime artifacts needed to reconstruct one raw
source-update window:

* authoritative completed-block HIT/NOTHING messages from the action log;
* source-update wall-clock boundaries;
* movement/stationary pose state;
* the context-bank occupancy/wind snapshot; and
* the frozen truth-free keyed-member transport builder.

It never opens case results, final posteriors, ON performance, source truth,
route identifiers, or plume-seed metadata.  Full trace banks are streamed
through a temporary directory and removed after the small stop-level NPZ has
been verified, so the historical archive is never modified.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

import numpy as np

import ctt_bank_io
import v4_final_reference as v4


HOUSE_MAP = {"House01": "H01", "House02": "H02", "House03": "H03"}
ALLOWED_NPZ_KEYS = {
    "stop_probability", "stop_r", "rectangles", "geometry_prior",
    "house", "seed", "update_id", "context_id", "timesteps",
}
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
INFO_TIME_RE = re.compile(r"^\[INFO\] \[([0-9]+(?:\.[0-9]+)?)\]")


@dataclass(frozen=True)
class RunContract:
    house_long: str
    house: str
    seed: int
    run_root: Path
    runtime_root: Path
    context_bank: Path
    action_log: Path
    pose_trace: Path
    timing_file: Path
    max_updates_per_stop: int
    block_samples: int
    steps_source_update: int
    timesteps: int


@dataclass(frozen=True)
class ContextSpec:
    house: str
    house_long: str
    seed: int
    update_id: int
    context_id: str
    context_bank: Path
    stop_xy: tuple[tuple[float, float], ...]
    stop_r: tuple[float, ...]
    timesteps: int


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _scalar_param(text: str, key: str) -> int:
    match = re.search(rf"(?m)^\s*{re.escape(key)}\s*:\s*([0-9]+)\s*$", text)
    if not match:
        raise ValueError(f"missing frozen launch parameter {key}")
    return int(match.group(1))


def _discover_run(archive: Path, house_long: str, seed: int) -> RunContract:
    run_root = archive / house_long / f"seed{seed}" / "off"
    runtimes = sorted((run_root / "runtime").glob(f"{house_long}_seed{seed}_off_off"))
    if len(runtimes) != 1:
        raise ValueError(f"expected one OFF runtime, found {len(runtimes)}")
    runtime = runtimes[0]
    context_bank = runtime / "context_bank"
    action_logs = sorted((runtime / "ros_log").glob("gsl_actionserver_node_*.log"))
    launch_params = sorted((runtime / "tmp").glob("launch_params_*"))
    param_files = []
    for path in launch_params:
        text = path.read_text(encoding="utf-8", errors="replace")
        if "maxUpdatesPerStop:" in text and "iterationsToRecord:" in text:
            param_files.append((path, text))
    if len(action_logs) != 1 or len(param_files) != 1:
        raise ValueError(
            f"runtime provenance ambiguous: action_logs={len(action_logs)}, "
            f"parameter_files={len(param_files)}"
        )
    _, params = param_files[0]
    return RunContract(
        house_long=house_long,
        house=HOUSE_MAP[house_long],
        seed=seed,
        run_root=run_root,
        runtime_root=runtime,
        context_bank=context_bank,
        action_log=action_logs[0],
        pose_trace=runtime / "sim_pose_trace.csv",
        timing_file=context_bank / "source_update_timing.csv",
        max_updates_per_stop=_scalar_param(params, "maxUpdatesPerStop"),
        block_samples=_scalar_param(params, "measurement_block_samples"),
        steps_source_update=_scalar_param(params, "stepsSourceUpdate"),
        timesteps=_scalar_param(params, "iterationsToRecord"),
    )


def _completed_blocks(action_log: Path) -> list[tuple[float, int]]:
    rows: list[tuple[float, int]] = []
    pending_time: float | None = None
    for raw in action_log.read_text(encoding="utf-8", errors="replace").splitlines():
        line = ANSI_RE.sub("", raw)
        if "avg_gas=" in line:
            match = INFO_TIME_RE.search(line)
            if not match or pending_time is not None:
                raise ValueError("ambiguous completed-block average in action log")
            pending_time = float(match.group(1))
        elif "GAS HIT" in line or "NOTHING" in line:
            match = INFO_TIME_RE.search(line)
            if not match or pending_time is None:
                raise ValueError("hit/miss without one preceding completed block")
            rows.append((float(match.group(1)), 1 if "GAS HIT" in line else 0))
            pending_time = None
    if pending_time is not None or not rows:
        raise ValueError("incomplete or empty completed-block log")
    if any(rows[i][0] <= rows[i - 1][0] for i in range(1, len(rows))):
        raise ValueError("completed-block timestamps are not strictly increasing")
    return rows


def _stationary_stops(pose_trace: Path, minimum_samples: int) -> list[tuple[float, float]]:
    rows = _read_csv(pose_trace)
    segments: list[list[dict[str, str]]] = []
    current: list[dict[str, str]] = []
    for row in rows:
        if int(row["is_moving"]) == 0:
            current.append(row)
        elif current:
            segments.append(current)
            current = []
    if current:
        segments.append(current)
    stops: list[tuple[float, float]] = []
    for segment in segments:
        if len(segment) < minimum_samples:
            continue
        xy = np.asarray([[float(r["x"]), float(r["y"])] for r in segment], dtype=float)
        if np.max(np.linalg.norm(xy - xy[0], axis=1)) > 1e-6:
            raise ValueError("stationary pose segment drifts spatially")
        stops.append((float(xy[0, 0]), float(xy[0, 1])))
    if not stops:
        raise ValueError("no full physical stops in pose trace")
    return stops


def reconstruct_context_specs(run: RunContract) -> tuple[list[ContextSpec], dict[str, object]]:
    if run.max_updates_per_stop != 8:
        raise ValueError(f"maxUpdatesPerStop drift: {run.max_updates_per_stop}")
    if run.block_samples != 10:
        raise ValueError(f"measurement_block_samples drift: {run.block_samples}")
    if run.steps_source_update != 3:
        raise ValueError(f"stepsSourceUpdate drift: {run.steps_source_update}")
    if run.timesteps != 200:
        raise ValueError(f"iterationsToRecord drift: {run.timesteps}")

    blocks = _completed_blocks(run.action_log)
    stops = _stationary_stops(
        run.pose_trace, run.max_updates_per_stop * run.block_samples
    )
    timing = _read_csv(run.timing_file)
    specs: list[ContextSpec] = []
    previous_wall_end = -math.inf
    stop_cursor = 0
    used_blocks = 0
    for row in timing:
        update_id = int(row["source_update_id"])
        wall_start = float(row["wall_start_epoch"])
        window = [(t, y) for t, y in blocks if previous_wall_end < t <= wall_start]
        if len(window) == 0 or len(window) % run.max_updates_per_stop != 0:
            raise ValueError(
                f"update {update_id}: completed blocks {len(window)} not a positive multiple "
                f"of {run.max_updates_per_stop}"
            )
        stop_count = len(window) // run.max_updates_per_stop
        if stop_cursor + stop_count > len(stops):
            raise ValueError(f"update {update_id}: insufficient physical-stop segments")
        stop_xy = tuple(stops[stop_cursor: stop_cursor + stop_count])
        stop_r = tuple(
            float(sum(y for _, y in window[i:i + run.max_updates_per_stop])) /
            float(run.max_updates_per_stop)
            for i in range(0, len(window), run.max_updates_per_stop)
        )
        end_xy = np.asarray(stop_xy[-1])
        timing_xy = np.asarray([float(row["robot_x"]), float(row["robot_y"])])
        if np.linalg.norm(end_xy - timing_xy) > 0.02:
            raise ValueError(
                f"update {update_id}: final physical stop does not match update pose: "
                f"stop={end_xy.tolist()} update={timing_xy.tolist()}"
            )
        context_id = f"{run.house}_seed{run.seed}_update{update_id:04d}"
        specs.append(ContextSpec(
            house=run.house,
            house_long=run.house_long,
            seed=run.seed,
            update_id=update_id,
            context_id=context_id,
            context_bank=run.context_bank,
            stop_xy=stop_xy,
            stop_r=stop_r,
            timesteps=run.timesteps,
        ))
        stop_cursor += stop_count
        used_blocks += len(window)
        previous_wall_end = float(row["wall_end_epoch"])
    return specs, {
        "updates": len(specs),
        "used_completed_blocks": used_blocks,
        "physical_stops": stop_cursor,
        "trailing_completed_blocks": sum(t > previous_wall_end for t, _ in blocks),
        "trailing_full_pose_stops": max(0, len(stops) - stop_cursor),
    }


def _geometry_rows(snapshot: Path) -> list[dict[str, str]]:
    rows = _read_csv(snapshot / "measured_hit_probability.csv")
    required = {"grid_i", "grid_j", "x", "y", "occupancy"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError("measured-hit geometry schema mismatch")
    return rows


def geometry_signature(snapshot: Path) -> str:
    rows = _geometry_rows(snapshot)
    canonical = "\n".join(
        f"{r['grid_i']},{r['grid_j']},{r['x']},{r['y']},{r['occupancy']}"
        for r in rows
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def build_persistent_carriers(snapshot: Path, out_csv: Path) -> tuple[np.ndarray, np.ndarray]:
    rows = _geometry_rows(snapshot)
    cells = {(int(r["grid_i"]), int(r["grid_j"])): r for r in rows}
    width = max(i for i, _ in cells) + 1
    height = max(j for _, j in cells) + 1
    carriers: list[dict[str, object]] = []
    rectangles: list[tuple[int, int, int, int]] = []
    free_counts: list[int] = []
    for ox in range(0, width, 2):
        for oy in range(0, height, 2):
            sx, sy = min(2, width - ox), min(2, height - oy)
            free = [
                cells[(i, j)]
                for i in range(ox, ox + sx)
                for j in range(oy, oy + sy)
                if cells[(i, j)]["occupancy"] == "Free"
            ]
            if not free:
                continue
            x = float(np.mean([float(r["x"]) for r in free]))
            y = float(np.mean([float(r["y"]) for r in free]))
            carrier_id = f"quadtree_{ox}_{oy}_{sx}_{sy}"
            carriers.append({
                "carrier_index": len(carriers), "carrier_id": carrier_id,
                "x": format(x, ".17g"), "y": format(y, ".17g"),
                "free_cells": len(free),
            })
            rectangles.append((ox, oy, sx, sy))
            free_counts.append(len(free))
    if not carriers or sum(free_counts) != sum(r["occupancy"] == "Free" for r in rows):
        raise ValueError("persistent carrier partition does not cover free geometry exactly once")
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["carrier_index", "carrier_id", "x", "y", "free_cells"]
        )
        writer.writeheader()
        writer.writerows(carriers)
    prior = np.asarray(free_counts, dtype=float)
    prior /= prior.sum()
    return np.asarray(rectangles, dtype=np.int64), prior


def _validate_bank_carriers(bank: Path, expected: Path) -> None:
    got = _read_csv(bank / "carrier_manifest.csv")
    want = _read_csv(expected)
    if len(got) != len(want):
        raise ValueError("trace-bank carrier count mismatch")
    for a, b in zip(got, want):
        for key in ("carrier_index", "carrier_id", "free_cells"):
            if a[key] != b[key]:
                raise ValueError(f"trace-bank carrier mismatch at {key}")
        # The historical C++ exporter accumulated float32 cell coordinates;
        # the adapter averages their decimal CSV representations in float64.
        # Sub-micrometre differences are formatting/arithmetic only and are
        # far below either the 0.3 m cell size or a probability query boundary.
        if abs(float(a["x"]) - float(b["x"])) > 1e-6 or abs(float(a["y"]) - float(b["y"])) > 1e-6:
            raise ValueError("trace-bank carrier coordinate mismatch")


def _extract_stop_probability(bank: Path, stop_xy: tuple[tuple[float, float], ...]) -> np.ndarray:
    contract = json.loads((bank / "ctt_trace_bank_contract.json").read_text(encoding="utf-8"))
    if contract.get("contract") != "CTT_V13_TRUTH_FREE_TRACE_BANK_V1":
        raise ValueError("wrong trace-bank contract")
    if contract.get("source_truth_used") is not False:
        raise ValueError("trace bank is not truth-free")
    if int(contract.get("transport_members", -1)) != 8 or int(contract.get("timesteps", -1)) != 200:
        raise ValueError("trace-bank member/timestep contract drift")
    wind = _read_csv(bank / "estimated_wind.csv")
    free_idx = np.asarray([int(r["cell_index"]) for r in wind], dtype=np.int64)
    query_xy = np.asarray([[float(r["x"]), float(r["y"])] for r in wind], dtype=float)
    stop = np.asarray(stop_xy, dtype=float)
    selected: list[int] = []
    nearest_distance: list[float] = []
    for xy in stop:
        distance = np.linalg.norm(query_xy - xy[None, :], axis=1)
        k = int(np.argmin(distance))
        selected.append(int(free_idx[k]))
        nearest_distance.append(float(distance[k]))
    # All frozen House grids use 0.3 m cells.  This bound is stricter than half
    # the cell diagonal and catches an off-grid/obstacle stop without guessing.
    if max(nearest_distance, default=0.0) > 0.22:
        raise ValueError(f"physical stop does not map to a free PMFS cell: {nearest_distance}")
    carriers = _read_csv(bank / "carrier_manifest.csv")
    S, M, J = len(carriers), 8, len(selected)
    probability = np.empty((S, M, J), dtype=np.float64)
    for s in range(S):
        for m in range(M):
            _, freq, _ = ctt_bank_io.read_trace_fields(
                bank / "records" / f"carrier_{s:04d}_member_{m:02d}.cttbin",
                selected, expected_carrier=s, expected_member=m,
            )
            probability[s, m] = freq
    if not np.all(np.isfinite(probability)) or np.any((probability < 0) | (probability > 1)):
        raise ValueError("invalid stop probabilities reconstructed from trace bank")
    return probability


def _same_partition(a: np.ndarray, b: np.ndarray) -> bool:
    a = np.asarray(a)
    b = np.asarray(b)
    return np.array_equal(a[:, None] == a[None, :], b[:, None] == b[None, :])


def _decision_signature(dec: v4.M2Decision) -> tuple[object, ...]:
    mask = None if dec.selected_mask is None else tuple(bool(x) for x in dec.selected_mask)
    return bool(dec.accepted), str(dec.reason), mask


def validate_materialized_context(path: Path) -> dict[str, object]:
    with np.load(path, allow_pickle=False) as data:
        if set(data.files) != ALLOWED_NPZ_KEYS:
            raise ValueError(f"NPZ key contract mismatch: {sorted(data.files)}")
        p = np.asarray(data["stop_probability"], dtype=float)
        r = np.asarray(data["stop_r"], dtype=float)
        rect = np.asarray(data["rectangles"], dtype=np.int64)
        q0 = np.asarray(data["geometry_prior"], dtype=float)
        timesteps = int(data["timesteps"].item())
    base_build = v4.build_components(p, rect, timesteps)
    base_dec = v4.strict_loso_m2(p, r, base_build.labels, q0, timesteps)
    if np.min(base_build.c_eff_eigenvalues) <= 0:
        raise ValueError("effective covariance is not positive definite")

    rng = np.random.default_rng(20260828)
    source_perm = rng.permutation(p.shape[0])
    p_build = v4.build_components(p[source_perm], rect[source_perm], timesteps)
    p_dec = v4.strict_loso_m2(
        p[source_perm], r, p_build.labels, q0[source_perm], timesteps
    )
    inverse = np.argsort(source_perm)
    if not _same_partition(base_build.labels, p_build.labels[inverse]):
        raise ValueError("candidate permutation changes M1 partition")
    if bool(base_dec.accepted) != bool(p_dec.accepted) or base_dec.reason != p_dec.reason:
        raise ValueError("candidate permutation changes M2 verdict")
    if base_dec.selected_mask is not None:
        if p_dec.selected_mask is None or not np.array_equal(base_dec.selected_mask, p_dec.selected_mask[inverse]):
            raise ValueError("candidate permutation changes selected component")

    cal_perm = np.asarray([2, 0, 3, 1, 4, 5, 6, 7])
    cal_build = v4.build_components(p[:, cal_perm], rect, timesteps)
    if not _same_partition(base_build.labels, cal_build.labels):
        raise ValueError("calibration-member permutation changes M1 partition")

    score_perm = np.asarray([0, 1, 2, 3, 6, 4, 7, 5])
    score_build = v4.build_components(p[:, score_perm], rect, timesteps)
    score_dec = v4.strict_loso_m2(
        p[:, score_perm], r, score_build.labels, q0, timesteps
    )
    if _decision_signature(base_dec) != _decision_signature(score_dec):
        raise ValueError("scoring-member permutation changes M2 verdict")
    return {
        "components": int(len(np.unique(base_build.labels))),
        "accepted": bool(base_dec.accepted),
        "reason": str(base_dec.reason),
        "min_c_eff_eigenvalue": float(np.min(base_build.c_eff_eigenvalues)),
    }


def _find_reusable_bank(reuse_root: Path | None, spec: ContextSpec) -> Path | None:
    if reuse_root is None or spec.house != "H02":
        return None
    pattern = f"*_seed{spec.seed}_u{spec.update_id:04d}"
    matches = sorted((reuse_root / "banks").glob(pattern))
    if len(matches) > 1:
        raise ValueError(f"ambiguous reusable bank for {spec.context_id}")
    return matches[0] if matches else None


def _materialize_one(task: dict[str, object]) -> dict[str, object]:
    spec = ContextSpec(
        house=str(task["house"]), house_long=str(task["house_long"]),
        seed=int(task["seed"]), update_id=int(task["update_id"]),
        context_id=str(task["context_id"]), context_bank=Path(str(task["context_bank"])),
        stop_xy=tuple(tuple(float(v) for v in xy) for xy in task["stop_xy"]),
        stop_r=tuple(float(v) for v in task["stop_r"]), timesteps=int(task["timesteps"]),
    )
    carrier_manifest = Path(str(task["carrier_manifest"]))
    rectangles = np.asarray(task["rectangles"], dtype=np.int64)
    prior = np.asarray(task["geometry_prior"], dtype=float)
    output = Path(str(task["output"]))
    reusable = Path(str(task["reusable"])) if task.get("reusable") else None
    temporary: Path | None = None
    try:
        if reusable is not None:
            bank = reusable
            bank_source = "verified_reuse"
        else:
            work_root = Path(str(task["work_root"]))
            work_root.mkdir(parents=True, exist_ok=True)
            temporary = Path(tempfile.mkdtemp(prefix=f"{spec.context_id}_", dir=work_root))
            bank = temporary / "bank"
            command = [
                str(task["builder"]), str(spec.context_bank), str(carrier_manifest),
                str(bank), str(spec.update_id), "0",
            ]
            env = os.environ.copy()
            env["OMP_NUM_THREADS"] = "1"
            proc = subprocess.run(command, env=env, text=True, capture_output=True)
            if proc.returncode != 0:
                raise RuntimeError(
                    f"truth-free builder rc={proc.returncode}\nstdout={proc.stdout}\nstderr={proc.stderr}"
                )
            bank_source = "streamed_rebuild"
        _validate_bank_carriers(bank, carrier_manifest)
        probability = _extract_stop_probability(bank, spec.stop_xy)
        if probability.shape[0] != len(rectangles):
            raise ValueError("source count differs from persistent carrier geometry")
        output.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            output,
            stop_probability=probability,
            stop_r=np.asarray(spec.stop_r, dtype=np.float64),
            rectangles=rectangles,
            geometry_prior=prior,
            house=np.asarray(spec.house),
            seed=np.asarray(spec.seed, dtype=np.int64),
            update_id=np.asarray(spec.update_id, dtype=np.int64),
            context_id=np.asarray(spec.context_id),
            timesteps=np.asarray(spec.timesteps, dtype=np.int64),
        )
        check = validate_materialized_context(output)
        return {
            "context_id": spec.context_id, "house": spec.house, "seed": spec.seed,
            "update_id": spec.update_id, "status": "VALID", "reason": "",
            "physical_stops": len(spec.stop_r), "npz_path": str(output),
            "npz_sha256": _sha256(output), "bank_source": bank_source,
            **check,
        }
    except Exception as exc:  # evidence manifest must retain every failure
        if output.exists():
            output.unlink()
        return {
            "context_id": spec.context_id, "house": spec.house, "seed": spec.seed,
            "update_id": spec.update_id, "status": "INVALID",
            "reason": f"{type(exc).__name__}: {exc}", "physical_stops": len(spec.stop_r),
            "npz_path": "", "npz_sha256": "", "bank_source": "",
            "components": "", "accepted": "", "min_c_eff_eigenvalue": "",
        }
    finally:
        if temporary is not None and temporary.exists():
            shutil.rmtree(temporary)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--builder", type=Path, required=True)
    parser.add_argument("--reuse-root", type=Path)
    parser.add_argument("--houses", nargs="+", choices=sorted(HOUSE_MAP.values()), default=sorted(HOUSE_MAP.values()))
    parser.add_argument("--seeds", nargs="+", type=int, default=list(range(10)))
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--inventory-only", action="store_true")
    args = parser.parse_args()
    if any(seed < 0 or seed > 9 for seed in args.seeds):
        raise ValueError("this development adapter is frozen to seeds 0..9")
    if not args.builder.is_file():
        raise ValueError(f"missing truth-free builder: {args.builder}")

    args.output_root.mkdir(parents=True, exist_ok=True)
    carrier_root = args.output_root / "carriers"
    npz_root = args.output_root / "contexts"
    inventory: list[dict[str, object]] = []
    all_specs: list[ContextSpec] = []
    geometry: dict[str, tuple[Path, np.ndarray, np.ndarray, str]] = {}

    reverse_house = {short: long for long, short in HOUSE_MAP.items()}
    for house in args.houses:
        house_long = reverse_house[house]
        for seed in sorted(set(args.seeds)):
            try:
                run = _discover_run(args.archive_root, house_long, seed)
                specs, stats = reconstruct_context_specs(run)
                first_snapshot = run.context_bank / f"source_update_{specs[0].update_id:04d}"
                sig = geometry_signature(first_snapshot)
                if house not in geometry:
                    carrier_file = carrier_root / f"{house}_persistent_carriers.csv"
                    rectangles, prior = build_persistent_carriers(first_snapshot, carrier_file)
                    geometry[house] = (carrier_file, rectangles, prior, sig)
                elif geometry[house][3] != sig:
                    raise ValueError("House geometry changed across OFF runs")
                for spec in specs:
                    snapshot = spec.context_bank / f"source_update_{spec.update_id:04d}"
                    if geometry_signature(snapshot) != sig:
                        raise ValueError(f"{spec.context_id}: geometry changed across source updates")
                all_specs.extend(specs)
                inventory.append({
                    "house": house, "seed": seed, "status": "VALID_RUN", "reason": "",
                    **stats,
                })
            except Exception as exc:
                inventory.append({
                    "house": house, "seed": seed, "status": "INVALID_RUN",
                    "reason": f"{type(exc).__name__}: {exc}", "updates": 0,
                    "used_completed_blocks": 0, "physical_stops": 0,
                    "trailing_completed_blocks": 0, "trailing_full_pose_stops": 0,
                })

    inventory_file = args.output_root / "archive_inventory.csv"
    with inventory_file.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(inventory[0].keys()))
        writer.writeheader()
        writer.writerows(inventory)
    if args.inventory_only:
        print(json.dumps({
            "runs": len(inventory), "valid_runs": sum(r["status"] == "VALID_RUN" for r in inventory),
            "contexts": len(all_specs), "inventory": str(inventory_file),
        }, indent=2))
        return
    if any(r["status"] != "VALID_RUN" for r in inventory):
        raise ValueError("archive inventory contains invalid runs; see archive_inventory.csv")

    tasks: list[dict[str, object]] = []
    for spec in all_specs:
        carrier_file, rectangles, prior, _ = geometry[spec.house]
        reusable = _find_reusable_bank(args.reuse_root, spec)
        tasks.append({
            "house": spec.house, "house_long": spec.house_long, "seed": spec.seed,
            "update_id": spec.update_id, "context_id": spec.context_id,
            "context_bank": str(spec.context_bank), "stop_xy": spec.stop_xy,
            "stop_r": spec.stop_r, "timesteps": spec.timesteps,
            "carrier_manifest": str(carrier_file), "rectangles": rectangles.tolist(),
            "geometry_prior": prior.tolist(), "output": str(npz_root / f"{spec.context_id}.npz"),
            "reusable": "" if reusable is None else str(reusable),
            "work_root": str(args.work_root), "builder": str(args.builder),
        })

    rows: list[dict[str, object]] = []
    with ProcessPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        futures = {pool.submit(_materialize_one, task): task["context_id"] for task in tasks}
        for future in as_completed(futures):
            row = future.result()
            rows.append(row)
            print(json.dumps(row, sort_keys=True), flush=True)
    rows.sort(key=lambda r: (str(r["house"]), int(r["seed"]), int(r["update_id"])))
    manifest = args.output_root / "materialization_manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    summary = {
        "contract": "CG_PC_CTT_V4_TRUTHBLIND_MATERIALIZATION_V1",
        "truth_used": False,
        "localization_error_used": False,
        "runs": len(inventory),
        "valid_runs": sum(r["status"] == "VALID_RUN" for r in inventory),
        "contexts": len(rows),
        "valid_contexts": sum(r["status"] == "VALID" for r in rows),
        "invalid_contexts": sum(r["status"] != "VALID" for r in rows),
        "houses": {
            h: {
                "contexts": sum(r["house"] == h for r in rows),
                "valid": sum(r["house"] == h and r["status"] == "VALID" for r in rows),
                "invalid": sum(r["house"] == h and r["status"] != "VALID" for r in rows),
            }
            for h in sorted(set(str(r["house"]) for r in rows))
        },
        "inventory_csv": str(inventory_file),
        "manifest_csv": str(manifest),
    }
    (args.output_root / "materialization_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    if summary["invalid_contexts"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
