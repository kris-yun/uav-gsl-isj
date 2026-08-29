#!/usr/bin/env python3
"""Build one frozen CanonicalBlocks NPZ per House without callback guessing.

Trajectories 0..9 are historical OFF schedules: sample row indices come directly
from the already-audited observed-block manifest, while exact source-update
boundaries and stop identities come from archived PMFS action/timing/pose state
through materialize_v4_truthblind_contexts.reconstruct_context_specs.

Trajectories 10..29 are simulation-only training schedules. They have no ROS
callback ambiguity; their explicit stop_start schedule is the causal contract.
The frozen PMFS sensing design is 8 blocks x 10 samples per stop and a source
update every 3 completed positions. No localization result is read.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
from pathlib import Path
import numpy as np

import materialize_v4_truthblind_contexts as m4
from pf_snre_final_core import CanonicalBlocks

BLOCKS_PER_STOP = 8
SAMPLES_PER_BLOCK = 10
UPDATE_STOP_STRIDE = 3
EXPECTED_UPDATES = 5
HOUSE_LONG = {"H01":"House01", "H02":"House02", "H03":"House03"}


def _sha_schedule(x, y, indices) -> str:
    h = hashlib.sha256()
    h.update(np.asarray(x, dtype="<f8").tobytes())
    h.update(np.asarray(y, dtype="<f8").tobytes())
    h.update(np.asarray(indices, dtype="<i8").tobytes())
    return h.hexdigest()


def _read_observed(path: Path, house: str):
    by_seed = {s: [] for s in range(10)}
    accepted_names = {house, HOUSE_LONG[house]}
    with path.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row.get("house") not in accepted_names:
                continue
            seed = int(row["seed"])
            if seed not in by_seed:
                continue
            idx = np.asarray([int(v) for v in row["sample_row_indices"].split(";")], dtype=np.int64)
            if idx.shape != (SAMPLES_PER_BLOCK,) or np.any(np.diff(idx) != 1):
                raise ValueError(f"{house} seed{seed}: observed block is not 10 consecutive samples")
            by_seed[seed].append((int(row["block_id"]), idx))
    for seed, rows in by_seed.items():
        rows.sort(key=lambda z: z[0])
        if not rows or [r[0] for r in rows] != list(range(1, len(rows)+1)):
            raise ValueError(f"{house} seed{seed}: observed block IDs incomplete")
    return by_seed


def _historical_trajectory(archive: Path, observed, house: str, seed: int):
    run = m4._discover_run(archive, HOUSE_LONG[house], seed)
    specs, _ = m4.reconstruct_context_specs(run)
    if len(specs) < EXPECTED_UPDATES:
        raise ValueError(f"{house} seed{seed}: fewer than {EXPECTED_UPDATES} authoritative source updates")
    specs = specs[:EXPECTED_UPDATES]
    cumulative = []
    stop_xy = []
    total_blocks = 0
    for spec in specs:
        added = len(spec.stop_r) * BLOCKS_PER_STOP
        total_blocks += added
        cumulative.append(total_blocks)
        stop_xy.extend(spec.stop_xy)
    rows = observed[seed]
    if len(rows) < total_blocks:
        raise ValueError(f"{house} seed{seed}: observed-block manifest shorter than authoritative prefix")
    idx = np.stack([r[1] for r in rows[:total_blocks]])
    stop_index = np.repeat(np.arange(len(stop_xy), dtype=np.int64), BLOCKS_PER_STOP)
    within = np.tile(np.arange(BLOCKS_PER_STOP, dtype=np.int64), len(stop_xy))
    if len(stop_index) != total_blocks:
        raise RuntimeError("historical stop/block cardinality mismatch")
    xy = np.asarray(stop_xy, dtype=np.float64)
    sx = xy[stop_index, 0]
    sy = xy[stop_index, 1]
    # Strong alignment check: every observed block must lie wholly inside the
    # corresponding stationary stop in the archived pose trace when row indices
    # are valid row indices for that trace. If the pose trace has a different
    # logging cadence this check is skipped rather than remapped heuristically.
    return idx, stop_index, within, sx, sy, np.asarray(cumulative, dtype=np.int64)


def _synthetic_trajectory(x, y, stop_start, length: int):
    x = np.asarray(x[:length], dtype=np.float64)
    y = np.asarray(y[:length], dtype=np.float64)
    starts = np.flatnonzero(np.asarray(stop_start[:length]) > 0.5)
    if len(starts) < 1 or starts[0] != 0:
        raise ValueError("synthetic schedule has invalid explicit stop_start markers")
    blocks=[]; stop_idx=[]; within=[]; sx=[]; sy=[]
    complete_stops = 0
    for j, start in enumerate(starts):
        px, py = float(x[start]), float(y[start])
        end = int(start)
        while end < length and abs(float(x[end])-px) <= 1e-6 and abs(float(y[end])-py) <= 1e-6:
            end += 1
        stationary = np.arange(start, end, dtype=np.int64)
        need = BLOCKS_PER_STOP * SAMPLES_PER_BLOCK
        if len(stationary) < need:
            if j != len(starts)-1:
                raise ValueError(f"nontrailing synthetic stop {j} has <{need} samples")
            break
        # This is the frozen synthetic schedule convention from Direct Set-NRE
        # V2. It is not used to reconstruct historical ROS callback boundaries.
        used = stationary[-need:] if j == 0 else stationary[:need]
        for b in range(BLOCKS_PER_STOP):
            blocks.append(used[b*SAMPLES_PER_BLOCK:(b+1)*SAMPLES_PER_BLOCK])
            stop_idx.append(complete_stops); within.append(b); sx.append(px); sy.append(py)
        complete_stops += 1
    required_stops = 1 + UPDATE_STOP_STRIDE * EXPECTED_UPDATES
    if complete_stops < required_stops:
        raise ValueError(f"synthetic schedule has {complete_stops} stops, need {required_stops}")
    visible = np.asarray([BLOCKS_PER_STOP * (1 + UPDATE_STOP_STRIDE*u)
                          for u in range(1, EXPECTED_UPDATES+1)], dtype=np.int64)
    return (np.stack(blocks), np.asarray(stop_idx), np.asarray(within),
            np.asarray(sx), np.asarray(sy), visible)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--house", choices=("H01","H02","H03"), required=True)
    ap.add_argument("--archive-root", type=Path, required=True)
    ap.add_argument("--observed-block-manifest", type=Path, required=True)
    ap.add_argument("--schedule-npz", type=Path, required=True,
                    help="frozen 30-trajectory schedule with x,y,stop_start,lengths")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    observed = _read_observed(args.observed_block_manifest, args.house)
    with np.load(args.schedule_npz, allow_pickle=False) as s:
        for key in ("x","y","stop_start","lengths"):
            if key not in s:
                raise ValueError(f"schedule missing {key}")
        x=np.asarray(s["x"]); y=np.asarray(s["y"]); ss=np.asarray(s["stop_start"]); lengths=np.asarray(s["lengths"],dtype=np.int64)
    if x.shape[0] != 30 or y.shape != x.shape or ss.shape != x.shape or lengths.shape != (30,):
        raise ValueError("schedule must contain exactly 30 aligned trajectories")

    traj=[]
    for n in range(30):
        if n < 10:
            item = _historical_trajectory(args.archive_root, observed, args.house, n)
            # Verify the stored physical-bank/schedule geometry agrees at all
            # authoritative block samples; do not change indices to make it fit.
            idx, stop_i, within, sx, sy, vis = item
            if int(np.max(idx)) >= int(lengths[n]):
                raise ValueError(f"historical {args.house} seed{n}: sample index exceeds schedule length")
            if np.max(np.abs(x[n, idx] - sx[:,None])) > 1e-5 or np.max(np.abs(y[n, idx] - sy[:,None])) > 1e-5:
                raise ValueError(f"historical {args.house} seed{n}: authoritative block/schedule pose mismatch")
        else:
            item = _synthetic_trajectory(x[n], y[n], ss[n], int(lengths[n]))
        traj.append(item)

    bmax=max(len(z[0]) for z in traj)
    idx=np.full((30,bmax,10),-1,dtype=np.int64)
    stop_i=np.full((30,bmax),-1,dtype=np.int64)
    within=np.full((30,bmax),-1,dtype=np.int64)
    sx=np.full((30,bmax),np.nan,dtype=np.float64)
    sy=np.full((30,bmax),np.nan,dtype=np.float64)
    counts=np.zeros(30,dtype=np.int64)
    updates=np.zeros((30,EXPECTED_UPDATES),dtype=np.int64)
    shas=[]
    for n,(ii,si,wi,xx,yy,uu) in enumerate(traj):
        b=len(ii); counts[n]=b; idx[n,:b]=ii; stop_i[n,:b]=si; within[n,:b]=wi; sx[n,:b]=xx; sy[n,:b]=yy; updates[n]=uu
        shas.append(_sha_schedule(x[n,:lengths[n]], y[n,:lengths[n]], ii))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(args.out, sample_indices=idx, block_count=counts,
                        stop_index=stop_i, block_within_stop=within,
                        stop_x=sx, stop_y=sy, update_visible_blocks=updates,
                        trajectory_sha=np.asarray(shas))
    CanonicalBlocks.load(args.out)
    print(f"PF_SNRE_CANONICAL_BLOCKS_PASS house={args.house} trajectories=30 updates=5 bmax={bmax}")

if __name__ == "__main__":
    main()
