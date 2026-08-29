#!/usr/bin/env python3
"""Materialize the frozen three-House PF-SNRE dataset from existing physical banks.

This program NEVER runs GADEN and never reconstructs sensing blocks heuristically.
It consumes already-materialized physical concentration banks plus an authoritative
CanonicalBlocks NPZ and advances the frozen persistent sensor on each COMPLETE
0.2 s trajectory before any block slicing.

Input JSON contract PF_SNRE_MATERIALIZATION_INPUT_V1:
{
  "contract": "PF_SNRE_MATERIALIZATION_INPUT_V1",
  "houses": {
    "H01": {
      "carriers": "/abs/or/relative/H01_carriers.json",
      "blocks": "/.../H01_canonical_blocks.npz",
      "placement_manifest": "/.../H01_source_member_placements.csv",
      "banks": [
        {"trajectory_index":0, "path":"/.../bank.npz"}, ... 30 entries ...
      ]
    }, ... H02,H03 ...
  }
}

Each bank is the existing PF_DEI_PHYSICAL_FORWARD_BANK_V1 per-run NPZ with all
12 frozen nuisance members. Member identity is selected by transport_seed, not
by array position.

Placement CSV columns: source_id,transport_seed,x,y,z. Every (source,member)
combination must occur exactly once. x/y must equal an exact free-cell center of
the declared carrier. This is used ONLY to define synthetic reserved truth; no
historical localization truth or outcome is read.
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
import time
import numpy as np

from pf_dei_physical_bank_contract import validate_bank_mapping
from pf_dei_inverse_sensor_reference import FrozenSensorInverseConfig
from pf_snre_final_core import CanonicalBlocks, sha256
from pf_snre_spatial_eval import load_carrier_cells

TRAIN_SEEDS = (101, 211, 307, 401, 503, 601, 701, 809)
RESERVED_SEEDS = (907, 1009, 1103, 1201)
ALL_SEEDS = TRAIN_SEEDS + RESERVED_SEEDS
EXPECTED_TRAJECTORIES = 30
DT_S = 0.2


def _resolve(base: Path, value: str) -> Path:
    p = Path(value)
    return p if p.is_absolute() else (base / p).resolve()


def _forward_sensor_same_length(physical: np.ndarray, dt_s: float = DT_S) -> np.ndarray:
    """Vectorized frozen persistent sensor; output sample k is M[k] for C timeline k."""
    x = np.asarray(physical, dtype=np.float64)
    if x.ndim < 1 or x.shape[-1] < 3 or np.any(x < -1e-12) or not np.all(np.isfinite(x)):
        raise ValueError("physical ppm must be finite nonnegative [...,T]")
    x = np.maximum(x, 0.0)
    cfg = FrozenSensorInverseConfig()
    ratio = cfg.dead_time_s / dt_s
    delay = int(round(ratio))
    if not np.isclose(ratio, delay, rtol=0.0, atol=1e-12):
        raise ValueError("frozen sensor dead-time/cadence contract drift")
    alpha = float(np.exp(-dt_s / cfg.tau_s))
    state = np.full(x.shape[:-1], cfg.initial_state_ppm, dtype=np.float64)
    out = np.empty_like(x, dtype=np.float32)
    for k in range(x.shape[-1]):
        delayed = cfg.initial_input_ppm if k < delay else x[..., k - delay]
        state = alpha * state + (1.0 - alpha) * delayed
        measured = cfg.baseline + cfg.gain * state
        if np.any(measured < cfg.saturation_min_ppm) or np.any(measured > cfg.saturation_max_ppm):
            measured = np.clip(measured, cfg.saturation_min_ppm, cfg.saturation_max_ppm)
        out[..., k] = measured.astype(np.float32)
    return out


def _load_placements(path: Path) -> dict[tuple[str, int], np.ndarray]:
    rows = []
    if path.suffix.lower() == ".csv":
        with path.open(newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
    elif path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = payload["placements"] if isinstance(payload, dict) else payload
    else:
        raise ValueError("placement manifest must be CSV or JSON")
    required = {"source_id", "transport_seed", "x", "y", "z"}
    out = {}
    for row in rows:
        if not required.issubset(row):
            raise ValueError(f"placement row missing {sorted(required - set(row))}")
        key = (str(row["source_id"]), int(row["transport_seed"]))
        if key in out:
            raise ValueError(f"duplicate placement {key}")
        xyz = np.asarray([float(row["x"]), float(row["y"]), float(row["z"])], dtype=np.float64)
        if not np.all(np.isfinite(xyz)):
            raise ValueError(f"nonfinite placement {key}")
        out[key] = xyz
    return out


def _validate_placement_geometry(carriers_path: Path, placements, source_ids):
    ids, _, _, cells, ptr = load_carrier_cells(carriers_path)
    if not np.array_equal(ids.astype(str), np.asarray(source_ids).astype(str)):
        raise ValueError("placement/carrier source order mismatch")
    reserved_xy = np.empty((len(ids), len(RESERVED_SEEDS), 2), dtype=np.float64)
    for s, sid in enumerate(ids.astype(str)):
        legal_xy = cells[ptr[s]:ptr[s + 1]]
        for seed in ALL_SEEDS:
            key = (sid, int(seed))
            if key not in placements:
                raise ValueError(f"missing source/member placement {key}")
            xy = placements[key][:2]
            d = np.linalg.norm(legal_xy - xy[None, :], axis=1)
            if not np.any(d <= 1e-8):
                raise ValueError(f"placement XY is not an exact free-cell center: {key} {xy.tolist()}")
        for j, seed in enumerate(RESERVED_SEEDS):
            reserved_xy[s, j] = placements[(sid, seed)][:2]
    return reserved_xy


def _bank_indices(d, expected_house: str, expected_source_ids):
    meta = validate_bank_mapping(d)
    if meta["house"] != expected_house:
        raise ValueError(f"bank House {meta['house']} != {expected_house}")
    if list(meta["source_id"]) != list(expected_source_ids):
        raise ValueError("bank source identity/order mismatch")
    seeds = np.asarray(d["transport_seed"], dtype=np.int64)
    if not set(ALL_SEEDS).issubset(set(int(v) for v in seeds.tolist())):
        raise ValueError(f"bank lacks frozen train/reserved seeds; got {seeds.tolist()}")
    index = {int(v): i for i, v in enumerate(seeds.tolist())}
    return meta, np.asarray([index[s] for s in TRAIN_SEEDS]), np.asarray([index[s] for s in RESERVED_SEEDS])


def materialize_house(house: str, spec: dict, base: Path, out: Path) -> dict:
    carriers = _resolve(base, spec["carriers"])
    blocks_path = _resolve(base, spec["blocks"])
    placements_path = _resolve(base, spec["placement_manifest"])
    banks = sorted(spec["banks"], key=lambda r: int(r["trajectory_index"]))
    if [int(r["trajectory_index"]) for r in banks] != list(range(EXPECTED_TRAJECTORIES)):
        raise ValueError(f"{house}: banks must cover trajectory_index 0..29 exactly once")
    blocks = CanonicalBlocks.load(blocks_path)
    if len(blocks.block_count) != EXPECTED_TRAJECTORIES:
        raise ValueError(f"{house}: canonical block manifest must have exactly 30 trajectories")

    ids, _, q0, _, _ = load_carrier_cells(carriers)
    placements = _load_placements(placements_path)
    reserved_xy = _validate_placement_geometry(carriers, placements, ids)

    first_path = _resolve(base, banks[0]["path"])
    with np.load(first_path, allow_pickle=False) as d:
        meta0, _, _ = _bank_indices(d, house, ids.astype(str).tolist())
        S = int(meta0["S"])
    lengths = []
    bank_paths = []
    bank_hashes = []
    for row in banks:
        p = _resolve(base, row["path"])
        with np.load(p, allow_pickle=False) as d:
            meta, _, _ = _bank_indices(d, house, ids.astype(str).tolist())
            t = np.asarray(d["sample_time_s"], dtype=np.float64)
            if len(t) != int(meta["T"]):
                raise ValueError("bank T/time mismatch")
            dt = np.diff(t)
            if not np.allclose(dt, DT_S, rtol=0.0, atol=1e-9):
                raise ValueError(f"{house} trajectory {row['trajectory_index']}: cadence !=0.2 s")
            lengths.append(int(meta["T"]))
        bank_paths.append(p)
        bank_hashes.append(sha256(p))
    Tmax = max(lengths)
    house_out = out / house
    house_out.mkdir(parents=True, exist_ok=True)
    train_path = house_out / f"{house}_measured_train8.npy"
    reserved_path = house_out / f"{house}_measured_reserved4.npy"
    train = np.lib.format.open_memmap(train_path, mode="w+", dtype=np.float32,
                                      shape=(S, len(TRAIN_SEEDS), EXPECTED_TRAJECTORIES, Tmax))
    reserved = np.lib.format.open_memmap(reserved_path, mode="w+", dtype=np.float32,
                                         shape=(S, len(RESERVED_SEEDS), EXPECTED_TRAJECTORIES, Tmax))
    train[:] = 0.0
    reserved[:] = 0.0

    for n, p in enumerate(bank_paths):
        with np.load(p, allow_pickle=False) as d:
            _, ti, ri = _bank_indices(d, house, ids.astype(str).tolist())
            physical = np.asarray(d["candidate_physical_ppm"], dtype=np.float64)
            T = physical.shape[-1]
            measured = _forward_sensor_same_length(physical, DT_S)
            train[:, :, n, :T] = measured[:, ti, :]
            reserved[:, :, n, :T] = measured[:, ri, :]
            # Canonical block indices must fit the unpadded physical timeline.
            bc = int(blocks.block_count[n])
            if int(np.max(blocks.sample_indices[n, :bc])) >= T:
                raise ValueError(f"{house} trajectory {n}: canonical block index exceeds physical bank")
    train.flush(); reserved.flush()
    del train, reserved

    # Synthetic reserved generating XY is member-specific but trajectory-independent
    # under the frozen source/member physical field contract. Replicate over N.
    truth = np.repeat(reserved_xy[:, :, None, :], EXPECTED_TRAJECTORIES, axis=2)
    truth_path = house_out / f"{house}_reserved_source_xy.npy"
    np.save(truth_path, truth.astype(np.float64))
    lengths_path = house_out / f"{house}_trajectory_lengths.npy"
    np.save(lengths_path, np.asarray(lengths, dtype=np.int64))

    # Copy by value, not symlink, so the final dataset package has immutable block bytes.
    with np.load(blocks_path, allow_pickle=False) as b:
        blocks_copy = house_out / f"{house}_canonical_blocks.npz"
        np.savez_compressed(blocks_copy, **{k: np.asarray(b[k]) for k in b.files})
    carriers_copy = house_out / f"{house}_carriers.json"
    carriers_copy.write_text(carriers.read_text(encoding="utf-8"), encoding="utf-8")

    row = {
        "house": house,
        "measured": str(train_path.relative_to(out)),
        "reserved_measured": str(reserved_path.relative_to(out)),
        "reserved_source_xy": str(truth_path.relative_to(out)),
        "trajectory_lengths": str(lengths_path.relative_to(out)),
        "blocks": str(blocks_copy.relative_to(out)),
        "carriers": str(carriers_copy.relative_to(out)),
        "source_count": S,
        "trajectory_count": EXPECTED_TRAJECTORIES,
        "train_transport_seeds": list(TRAIN_SEEDS),
        "reserved_transport_seeds": list(RESERVED_SEEDS),
        "input_bank_sha256": bank_hashes,
        "input_blocks_sha256": sha256(blocks_path),
        "input_carriers_sha256": sha256(carriers),
        "input_placement_sha256": sha256(placements_path),
        "output_measured_sha256": sha256(train_path),
        "output_reserved_measured_sha256": sha256(reserved_path),
        "output_reserved_source_xy_sha256": sha256(truth_path),
        "sensor_forward": "full_timeline_persistent_dt0.2_tau1.2_deadtime0.4_gain1_baseline0",
        "gaden_runs": 0,
    }
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-manifest", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    started = time.monotonic()
    spec = json.loads(args.input_manifest.read_text(encoding="utf-8"))
    if spec.get("contract") != "PF_SNRE_MATERIALIZATION_INPUT_V1":
        raise ValueError("wrong input materialization contract")
    if set(spec.get("houses", {})) != {"H01", "H02", "H03"}:
        raise ValueError("input manifest must contain exactly H01,H02,H03")
    args.out.mkdir(parents=True, exist_ok=True)
    base = args.input_manifest.parent
    houses = {h: materialize_house(h, spec["houses"][h], base, args.out)
              for h in ("H01", "H02", "H03")}
    dataset = {
        "contract": "PF_SNRE_MULTI_HOUSE_DATASET_V1",
        "houses": {h: {k: v for k, v in row.items() if k in ("measured", "carriers", "blocks")}
                   for h, row in houses.items()},
        "provenance": houses,
        "input_manifest_sha256": sha256(args.input_manifest),
        "wall_time_s": time.monotonic() - started,
        "gaden_runs": 0,
    }
    path = args.out / "pf_snre_multi_house_dataset.json"
    path.write_text(json.dumps(dataset, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PF_SNRE_MULTI_HOUSE_DATASET_MATERIALIZED " + json.dumps({
        "manifest": str(path), "manifest_sha256": sha256(path),
        "wall_time_s": dataset["wall_time_s"], "gaden_runs": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
