#!/usr/bin/env python3
"""Build a compact, source-blind M5 L1 transition bundle from exported frames.

The raw filament-frame CSV may contain millions of rows and remains external.
This script:
- reconstructs exact save-step mapping and birth-step pseudo-IDs;
- validates identity invariants fail-closed;
- computes exact 3-D nearest-obstacle context from OccupancyGrid3D.csv;
- emits only a deterministic pseudo-ID hash sample of transitions;
- preserves B0 and exported B3 residuals.

No source coordinate or plume concentration truth is used.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt

from recover_filament_pseudo_ids import (
    infer_age_updates,
    pseudo_birth_step,
    release_schedule,
    save_step_schedule,
    sigma_table,
)

DT = 0.1
SAVE_DT = 0.5
RATE_HZ = 7.0
SIGMA0 = 10.0
GAMMA = 15.0
SIM_TIME = 1000.0
EXPECTED_FRAMES = 1803
SIGMA_ATOL = 5e-5


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def parse_occupancy(path: Path):
    with path.open("r", encoding="utf-8", errors="replace") as f:
        header = [next(f).strip() for _ in range(4)]
        mn = [float(x) for x in header[0].split()[1:]]
        mx = [float(x) for x in header[1].split()[1:]]
        dims = [int(x) for x in header[2].split()[1:]]
        cell = float(header[3].split()[1])
        nx, ny, nz = dims
        arr = np.full((nz, nx, ny), 255, dtype=np.uint8)
        z = 0
        x = 0
        for line in f:
            s = line.strip()
            if not s:
                continue
            if s == ";":
                z += 1
                x = 0
                continue
            if z >= nz or x >= nx:
                raise ValueError(f"occupancy layout overflow z={z} x={x}")
            vals = np.fromstring(s, sep=" ", dtype=np.int64)
            if vals.size != ny:
                raise ValueError(f"occupancy y count {vals.size} != {ny} at z={z} x={x}")
            arr[z, x, :] = vals.astype(np.uint8)
            x += 1
    if np.any(arr == 255):
        raise ValueError("occupancy has uninitialized cells")
    return {
        "min_xyz": mn,
        "max_xyz": mx,
        "dims_xyz": dims,
        "cell_m": cell,
        "state_zxy": arr,
    }


def wall_context(occ):
    free = occ["state_zxy"] == 0
    # OOB is a wall too: pad with blocked cells.
    pad = np.pad(free, 1, mode="constant", constant_values=False)
    dist, nearest = distance_transform_edt(
        pad,
        sampling=(occ["cell_m"], occ["cell_m"], occ["cell_m"]),
        return_indices=True,
    )
    # Strip padding but keep nearest indices in padded coordinates.
    return free, dist[1:-1, 1:-1, 1:-1], nearest[:, 1:-1, 1:-1, 1:-1]


def wall_at(cell_x, cell_y, cell_z, occ, dist, nearest):
    nx, ny, nz = occ["dims_xyz"]
    if not (0 <= cell_x < nx and 0 <= cell_y < ny and 0 <= cell_z < nz):
        return (float("nan"), 0.0, 0.0, 0.0)
    d = float(dist[cell_z, cell_x, cell_y])
    # nearest array points into PADDED coordinates.
    nzp = int(nearest[0, cell_z, cell_x, cell_y])
    nxp = int(nearest[1, cell_z, cell_x, cell_y])
    nyp = int(nearest[2, cell_z, cell_x, cell_y])
    czp, cxp, cyp = cell_z + 1, cell_x + 1, cell_y + 1
    vx = (nxp - cxp) * occ["cell_m"]
    vy = (nyp - cyp) * occ["cell_m"]
    vz = (nzp - czp) * occ["cell_m"]
    n = math.sqrt(vx * vx + vy * vy + vz * vz)
    if n > 0:
        vx, vy, vz = vx / n, vy / n, vz / n
    return d, vx, vy, vz


def keep_id(pid: int, mod: int) -> bool:
    # Stable Knuth multiplicative integer hash; no Python hash randomization.
    u = (int(pid) * 2654435761) & 0xFFFFFFFF
    return (u % mod) == 0


def cast_row(r):
    ints = {
        "frame", "iteration", "physics_step", "row", "wind_index",
        "cell_x", "cell_y", "cell_z", "stencil27",
        "pred_alive", "next_step",
    }
    out = {}
    for k, v in r.items():
        if k in ints:
            out[k] = int(v)
        else:
            out[k] = float(v)
    return out


TRANSITION_FIELDS = [
    "label", "pseudo_id", "birth_step",
    "frame0", "frame1", "step0", "step1", "delta_s",
    "age_updates0", "age_updates1",
    "x0", "y0", "z0", "sigma0",
    "x1", "y1", "z1", "sigma1",
    "wind_x0", "wind_y0", "wind_z0", "wind_speed0",
    "wind_x1", "wind_y1", "wind_z1", "wind_speed1",
    "wind_index0", "wind_index1",
    "cell_x0", "cell_y0", "cell_z0", "stencil27_0",
    "wall_dist_m", "wall_dir_x", "wall_dir_y", "wall_dir_z",
    "dx", "dy", "dz",
    "b0_res_x", "b0_res_y", "b0_res_z",
    "b3_pred_alive", "b3_pred_x", "b3_pred_y", "b3_pred_z", "b3_pred_sigma",
    "b3_res_x", "b3_res_y", "b3_res_z",
    "wind_turn_cos",
]

DISAPPEAR_FIELDS = [
    "label", "pseudo_id", "birth_step", "last_frame", "last_step",
    "x", "y", "z", "sigma", "wind_x", "wind_y", "wind_z",
    "cell_x", "cell_y", "cell_z", "stencil27", "next_frame", "next_step",
]


def transition_row(label, pid, prev, cur, age0, age1, occ, dist, nearest):
    dt = float(cur["physics_step"] - prev["physics_step"]) * DT
    dx = cur["x"] - prev["x"]
    dy = cur["y"] - prev["y"]
    dz = cur["z"] - prev["z"]
    b0x = dx - prev["wind_x"] * dt
    b0y = dy - prev["wind_y"] * dt
    b0z = dz - prev["wind_z"] * dt
    wd, wx, wy, wz = wall_at(
        prev["cell_x"], prev["cell_y"], prev["cell_z"], occ, dist, nearest
    )
    s0 = math.sqrt(prev["wind_x"] ** 2 + prev["wind_y"] ** 2 + prev["wind_z"] ** 2)
    s1 = math.sqrt(cur["wind_x"] ** 2 + cur["wind_y"] ** 2 + cur["wind_z"] ** 2)
    turn = (
        (prev["wind_x"] * cur["wind_x"] + prev["wind_y"] * cur["wind_y"] + prev["wind_z"] * cur["wind_z"])
        / (s0 * s1)
        if s0 > 0 and s1 > 0
        else float("nan")
    )
    if prev["pred_alive"]:
        r3x = cur["x"] - prev["pred_x"]
        r3y = cur["y"] - prev["pred_y"]
        r3z = cur["z"] - prev["pred_z"]
    else:
        r3x = r3y = r3z = float("nan")
    return {
        "label": label,
        "pseudo_id": pid,
        "birth_step": pid,
        "frame0": prev["frame"],
        "frame1": cur["frame"],
        "step0": prev["physics_step"],
        "step1": cur["physics_step"],
        "delta_s": dt,
        "age_updates0": age0,
        "age_updates1": age1,
        "x0": prev["x"], "y0": prev["y"], "z0": prev["z"], "sigma0": prev["sigma"],
        "x1": cur["x"], "y1": cur["y"], "z1": cur["z"], "sigma1": cur["sigma"],
        "wind_x0": prev["wind_x"], "wind_y0": prev["wind_y"], "wind_z0": prev["wind_z"], "wind_speed0": s0,
        "wind_x1": cur["wind_x"], "wind_y1": cur["wind_y"], "wind_z1": cur["wind_z"], "wind_speed1": s1,
        "wind_index0": prev["wind_index"], "wind_index1": cur["wind_index"],
        "cell_x0": prev["cell_x"], "cell_y0": prev["cell_y"], "cell_z0": prev["cell_z"],
        "stencil27_0": prev["stencil27"],
        "wall_dist_m": wd, "wall_dir_x": wx, "wall_dir_y": wy, "wall_dir_z": wz,
        "dx": dx, "dy": dy, "dz": dz,
        "b0_res_x": b0x, "b0_res_y": b0y, "b0_res_z": b0z,
        "b3_pred_alive": prev["pred_alive"],
        "b3_pred_x": prev["pred_x"], "b3_pred_y": prev["pred_y"],
        "b3_pred_z": prev["pred_z"], "b3_pred_sigma": prev["pred_sigma"],
        "b3_res_x": r3x, "b3_res_y": r3y, "b3_res_z": r3z,
        "wind_turn_cos": turn,
    }


def process(args):
    saves = save_step_schedule(SIM_TIME, DT, SAVE_DT)
    if len(saves) != EXPECTED_FRAMES:
        raise RuntimeError(f"internal save schedule {len(saves)} != {EXPECTED_FRAMES}")
    sigma_tab = sigma_table(SIGMA0, GAMMA, DT, 10050)
    releases = release_schedule(RATE_HZ, DT, saves[-1][0] + 2)
    if max(releases) > 1:
        raise RuntimeError("release contract no longer unique")
    valid_birth_steps = {i for i, n in enumerate(releases) if n == 1}

    occ = parse_occupancy(args.occupancy)
    _, dist, nearest = wall_context(occ)

    args.out_dir.mkdir(parents=True, exist_ok=False)
    transitions_path = args.out_dir / f"{args.label}_transitions.csv.gz"
    disappear_path = args.out_dir / f"{args.label}_disappearances.csv.gz"

    total_obs = 0
    bad_sigma = 0
    invalid_birth = 0
    duplicate_ids = 0
    order_fail = 0
    reappear = 0
    age_progress_fail = 0
    frames_seen = 0
    all_transition_count = 0
    sampled_transition_count = 0
    sampled_disappear_count = 0

    prev_ids = set()
    prev_sampled = {}
    dead = set()
    sigma_cache = {}

    current_frame = None
    frame_rows = []
    frame_ids = []

    def age_for_sigma(s):
        key = float(s)
        if key not in sigma_cache:
            try:
                sigma_cache[key] = infer_age_updates(key, sigma_tab, atol=SIGMA_ATOL)
            except ValueError:
                sigma_cache[key] = None
        return sigma_cache[key]

    with gzip.open(transitions_path, "wt", newline="") as tf, gzip.open(
        disappear_path, "wt", newline=""
    ) as df:
        tw = csv.DictWriter(tf, fieldnames=TRANSITION_FIELDS)
        dw = csv.DictWriter(df, fieldnames=DISAPPEAR_FIELDS)
        tw.writeheader()
        dw.writeheader()

        def flush_frame(frame, rows):
            nonlocal frames_seen, total_obs, bad_sigma, invalid_birth
            nonlocal duplicate_ids, order_fail, reappear, age_progress_fail
            nonlocal prev_ids, prev_sampled, dead
            nonlocal all_transition_count, sampled_transition_count, sampled_disappear_count
            if frame is None:
                return
            if frame >= len(saves):
                raise RuntimeError(f"frame index {frame} exceeds save schedule")
            expected_step = saves[frame][0]
            ids = []
            sampled = {}
            ages = {}
            for r in rows:
                total_obs += 1
                if r["physics_step"] != expected_step:
                    raise RuntimeError(
                        f"frame {frame} physics_step {r['physics_step']} != {expected_step}"
                    )
                age = age_for_sigma(r["sigma"])
                if age is None:
                    bad_sigma += 1
                    continue
                pid = pseudo_birth_step(expected_step, r["sigma"], sigma_tab)
                if pid not in valid_birth_steps:
                    invalid_birth += 1
                ids.append(pid)
                ages[pid] = age
                if keep_id(pid, args.sample_mod):
                    sampled[pid] = r

            if len(ids) != len(set(ids)):
                duplicate_ids += len(ids) - len(set(ids))
            if any(b <= a for a, b in zip(ids, ids[1:])):
                order_fail += 1

            curr_ids = set(ids)
            reappear += len(curr_ids & dead)

            if frames_seen > 0:
                matched = prev_ids & curr_ids
                all_transition_count += len(matched)
                for pid in sorted(set(prev_sampled) & set(sampled)):
                    p = prev_sampled[pid]
                    q = sampled[pid]
                    age0 = age_for_sigma(p["sigma"])
                    age1 = ages[pid]
                    expected_age1 = age0 + (q["physics_step"] - p["physics_step"])
                    if age1 != expected_age1:
                        age_progress_fail += 1
                        continue
                    tw.writerow(
                        transition_row(args.label, pid, p, q, age0, age1, occ, dist, nearest)
                    )
                    sampled_transition_count += 1

                disappeared = prev_ids - curr_ids
                dead.update(disappeared)
                next_step = expected_step
                for pid in sorted(set(prev_sampled) & disappeared):
                    p = prev_sampled[pid]
                    dw.writerow(
                        {
                            "label": args.label,
                            "pseudo_id": pid,
                            "birth_step": pid,
                            "last_frame": p["frame"],
                            "last_step": p["physics_step"],
                            "x": p["x"], "y": p["y"], "z": p["z"], "sigma": p["sigma"],
                            "wind_x": p["wind_x"], "wind_y": p["wind_y"], "wind_z": p["wind_z"],
                            "cell_x": p["cell_x"], "cell_y": p["cell_y"], "cell_z": p["cell_z"],
                            "stencil27": p["stencil27"],
                            "next_frame": frame,
                            "next_step": next_step,
                        }
                    )
                    sampled_disappear_count += 1

            prev_ids = curr_ids
            prev_sampled = sampled
            frames_seen += 1

        with args.frames.open("r", newline="") as f:
            rd = csv.DictReader(f)
            required = {
                "frame", "iteration", "physics_step", "x", "y", "z", "sigma",
                "wind_index", "wind_x", "wind_y", "wind_z",
                "cell_x", "cell_y", "cell_z", "stencil27",
                "pred_alive", "pred_x", "pred_y", "pred_z", "pred_sigma",
                "next_step", "delta_s",
            }
            if not required.issubset(rd.fieldnames or []):
                raise RuntimeError(f"frame CSV missing {sorted(required-set(rd.fieldnames or []))}")
            for raw in rd:
                r = cast_row(raw)
                fidx = r["frame"]
                if current_frame is None:
                    current_frame = fidx
                if fidx != current_frame:
                    flush_frame(current_frame, frame_rows)
                    if fidx != current_frame + 1:
                        raise RuntimeError(f"non-contiguous frame {current_frame}->{fidx}")
                    current_frame = fidx
                    frame_rows = []
                frame_rows.append(r)
            flush_frame(current_frame, frame_rows)

    match_rate = 1.0 - bad_sigma / max(total_obs, 1)
    decision = (
        frames_seen == EXPECTED_FRAMES
        and match_rate >= 0.9999
        and invalid_birth == 0
        and duplicate_ids == 0
        and order_fail == 0
        and reappear == 0
        and age_progress_fail == 0
        and sampled_transition_count > 0
    )

    manifest = {
        "label": args.label,
        "source_blind": True,
        "frames_csv": str(args.frames),
        "frames_csv_sha256": sha256(args.frames),
        "occupancy_sha256": sha256(args.occupancy),
        "sample_mod": args.sample_mod,
        "selection": "((birth_step*2654435761)&0xffffffff)%sample_mod==0",
        "frozen_contract": {
            "dt_s": DT,
            "save_dt_s": SAVE_DT,
            "rate_hz": RATE_HZ,
            "sigma0_cm": SIGMA0,
            "gamma_cm2_s": GAMMA,
            "sim_time_s": SIM_TIME,
            "expected_frames": EXPECTED_FRAMES,
        },
        "validation": {
            "frames_seen": frames_seen,
            "total_filament_observations": total_obs,
            "sigma_age_match_rate": match_rate,
            "bad_sigma": bad_sigma,
            "invalid_birth_step": invalid_birth,
            "duplicate_pseudo_ids": duplicate_ids,
            "order_failures": order_fail,
            "reappearances": reappear,
            "age_progression_failures": age_progress_fail,
            "all_transition_count": all_transition_count,
            "sampled_transition_count": sampled_transition_count,
            "sampled_disappearance_count": sampled_disappear_count,
        },
        "outputs": {
            "transitions": transitions_path.name,
            "transitions_sha256": sha256(transitions_path),
            "disappearances": disappear_path.name,
            "disappearances_sha256": sha256(disappear_path),
        },
        "decision": "TRAJECTORY_INTERFACE_PASS" if decision else "INVALID_DATA_INTERFACE",
    }
    (args.out_dir / f"{args.label}_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n"
    )
    print(json.dumps(manifest, indent=2))
    if not decision:
        raise SystemExit(2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", type=Path, required=True)
    ap.add_argument("--occupancy", type=Path, required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--sample-mod", type=int, default=32)
    args = ap.parse_args()
    if args.sample_mod < 1:
        raise ValueError("--sample-mod must be >=1")
    process(args)


if __name__ == "__main__":
    main()
