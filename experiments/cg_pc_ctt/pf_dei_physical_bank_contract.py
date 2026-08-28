#!/usr/bin/env python3
"""Validation contract for PF-DEI physical candidate forward banks.

This module does not generate GADEN simulations.  It validates that a materialized
bank really represents source-specific physical concentration on one complete
historical trajectory and that source/transport identities are stable.

Normative per-run NPZ payload:

- candidate_physical_ppm: [S,M,T], finite, non-negative physical ppm;
- sample_time_s: [T], strictly increasing;
- pose_xyz_m: [T,3], finite;
- source_xyz_m: [S,3], finite;
- geometry_prior: [S], non-negative and normalized after validation;
- source_id: [S], stable unique strings;
- transport_id: [M], stable unique strings;
- transport_seed: [M], integer seeds;
- scalar house, run_seed;
- scalar provenance hashes for source support, transport manifest, query binary,
  GADEN source/config/overlay and trajectory schedule.

Forbidden: true source, true_gas_ppm, localization error, ON/OFF outcome or any
performance-derived field.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping
import hashlib
import json
import numpy as np

FORBIDDEN_TOKENS = (
    "true_source", "source_truth", "true_gas_ppm", "localization_error",
    "final_error", "off_on_improvement", "performance_label",
)

REQUIRED_ARRAYS = (
    "candidate_physical_ppm", "sample_time_s", "pose_xyz_m", "source_xyz_m",
    "geometry_prior", "source_id", "transport_id", "transport_seed",
)

REQUIRED_SCALARS = (
    "house", "run_seed", "source_support_sha256", "transport_manifest_sha256",
    "trajectory_sha256", "query_binary_sha256", "gaden_source_sha256",
    "gaden_config_sha256", "overlay_sha256",
)


@dataclass(frozen=True)
class BankSummary:
    path: str
    house: str
    run_seed: int
    sources: int
    members: int
    samples: int
    min_ppm: float
    max_ppm: float
    bank_sha256: str


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _scalar_str(d: Mapping[str, np.ndarray], key: str) -> str:
    if key not in d:
        raise ValueError(f"missing scalar {key}")
    a = np.asarray(d[key])
    if a.size != 1:
        raise ValueError(f"{key} must be scalar")
    return str(a.reshape(-1)[0])


def _unique_strings(name: str, values, n: int) -> list[str]:
    a = np.asarray(values)
    if a.shape != (n,):
        raise ValueError(f"{name} must have shape ({n},)")
    out = [str(x) for x in a.tolist()]
    if any(not x for x in out) or len(set(out)) != n:
        raise ValueError(f"{name} must be non-empty and unique")
    return out


def validate_bank_mapping(d: Mapping[str, np.ndarray]) -> dict:
    lowered = {str(k).lower() for k in d.keys()}
    for token in FORBIDDEN_TOKENS:
        if any(token in key for key in lowered):
            raise ValueError(f"forbidden truth/performance field present: {token}")
    for key in REQUIRED_ARRAYS + REQUIRED_SCALARS:
        if key not in d:
            raise ValueError(f"missing required key {key}")

    x = np.asarray(d["candidate_physical_ppm"], dtype=np.float64)
    if x.ndim != 3 or min(x.shape) < 2 or not np.all(np.isfinite(x)):
        raise ValueError("candidate_physical_ppm must be finite [S,M,T] with all dimensions >=2")
    if np.any(x < -1e-12):
        raise ValueError("physical concentration cannot be materially negative")
    x = np.maximum(x, 0.0)
    S, M, T = x.shape

    t = np.asarray(d["sample_time_s"], dtype=np.float64)
    if t.shape != (T,) or not np.all(np.isfinite(t)) or not np.all(np.diff(t) > 0):
        raise ValueError("sample_time_s must be finite, strictly increasing and match T")
    pose = np.asarray(d["pose_xyz_m"], dtype=np.float64)
    if pose.shape != (T, 3) or not np.all(np.isfinite(pose)):
        raise ValueError("pose_xyz_m must be finite [T,3]")
    src = np.asarray(d["source_xyz_m"], dtype=np.float64)
    if src.shape != (S, 3) or not np.all(np.isfinite(src)):
        raise ValueError("source_xyz_m must be finite [S,3]")

    q0 = np.asarray(d["geometry_prior"], dtype=np.float64)
    if q0.shape != (S,) or np.any(q0 < 0) or not np.all(np.isfinite(q0)) or q0.sum() <= 0:
        raise ValueError("geometry_prior must be finite non-negative [S] with positive mass")
    q0 = q0 / q0.sum()

    source_id = _unique_strings("source_id", d["source_id"], S)
    transport_id = _unique_strings("transport_id", d["transport_id"], M)
    seeds = np.asarray(d["transport_seed"])
    if seeds.shape != (M,) or not np.issubdtype(seeds.dtype, np.integer):
        raise ValueError("transport_seed must be integer [M]")
    if len(set(int(v) for v in seeds.tolist())) != M:
        raise ValueError("transport_seed values must be distinct")

    house = _scalar_str(d, "house")
    run_seed = int(float(_scalar_str(d, "run_seed")))
    hashes = {}
    for key in REQUIRED_SCALARS[2:]:
        value = _scalar_str(d, key).lower()
        if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            raise ValueError(f"{key} must be a lowercase SHA-256 hex digest")
        hashes[key] = value

    return {
        "house": house, "run_seed": run_seed, "S": S, "M": M, "T": T,
        "source_id": source_id, "transport_id": transport_id,
        "geometry_prior": q0, "min_ppm": float(x.min()), "max_ppm": float(x.max()),
        **hashes,
    }


def validate_npz(path: Path) -> BankSummary:
    with np.load(path, allow_pickle=False) as d:
        meta = validate_bank_mapping(d)
    return BankSummary(
        path=str(path), house=meta["house"], run_seed=meta["run_seed"],
        sources=meta["S"], members=meta["M"], samples=meta["T"],
        min_ppm=meta["min_ppm"], max_ppm=meta["max_ppm"], bank_sha256=sha256_file(path),
    )


def assert_same_source_support(paths: list[Path]) -> None:
    """Require source index -> physical identity to be stable within each House.

    If a House legitimately uses different run-specific source supports, do not
    bypass this function; materialize and analyze those runs separately with an
    explicitly run-specific source-support contract instead.
    """
    by_house: dict[str, tuple[list[str], np.ndarray, str]] = {}
    for p in paths:
        with np.load(p, allow_pickle=False) as d:
            meta = validate_bank_mapping(d)
            ids = meta["source_id"]
            xyz = np.asarray(d["source_xyz_m"], dtype=np.float64)
            h = meta["source_support_sha256"]
        if meta["house"] not in by_house:
            by_house[meta["house"]] = (ids, xyz, h)
        else:
            ids0, xyz0, h0 = by_house[meta["house"]]
            if ids != ids0 or xyz.shape != xyz0.shape or np.max(np.abs(xyz - xyz0)) > 1e-12 or h != h0:
                raise ValueError(f"source-support identity drift within {meta['house']}")


def write_manifest(paths: list[Path], out_json: Path) -> None:
    rows = [validate_npz(p).__dict__ for p in paths]
    assert_same_source_support(paths)
    payload = {"contract": "PF_DEI_PHYSICAL_FORWARD_BANK_V1", "banks": rows}
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
