#!/usr/bin/env python3
"""Freeze outcome-independent destruction maps for the CTT M2 V2 premise Gate."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


CONTRACT = "CTT_M2_FIXED_U_PROSPECTIVE_K_NULL_MAPS_V2"
REPLICATES = 256
SOURCE_COUNT = 210
PREDICTIVE_K_COUNT = 6
ROUTES = (4004, 4005)
STOP_COUNT = 10
SEEDS = {
    "observation_source_association": 2026083001,
    "candidate_stop_association": 2026083002,
    "predictive_K_identity": 2026083003,
    "candidate_permutation_invariance": 2026083004,
}


def nonidentity_permutation(rng: np.random.Generator, size: int) -> list[int]:
    identity = np.arange(size)
    for _ in range(1000):
        candidate = rng.permutation(size)
        if not np.array_equal(candidate, identity):
            return [int(value) for value in candidate]
    raise RuntimeError("CTT_M2_NULL_MAP_NONIDENTITY_EXHAUSTED")


def build_payload() -> dict:
    source_rng = np.random.Generator(np.random.PCG64(SEEDS["observation_source_association"]))
    stop_rng = np.random.Generator(np.random.PCG64(SEEDS["candidate_stop_association"]))
    k_rng = np.random.Generator(np.random.PCG64(SEEDS["predictive_K_identity"]))
    invariant_rng = np.random.Generator(
        np.random.PCG64(SEEDS["candidate_permutation_invariance"])
    )
    source_maps = [
        nonidentity_permutation(source_rng, SOURCE_COUNT) for _ in range(REPLICATES)
    ]
    stop_maps = []
    k_maps = []
    for _ in range(REPLICATES):
        stop_maps.append({
            str(route): nonidentity_permutation(stop_rng, STOP_COUNT)
            for route in ROUTES
        })
        k_maps.append({
            str(route): [
                nonidentity_permutation(k_rng, PREDICTIVE_K_COUNT)
                for _ in range(STOP_COUNT)
            ]
            for route in ROUTES
        })
    return {
        "contract": CONTRACT,
        "status": "FROZEN_BEFORE_MATERIALIZATION_NO_OUTCOME_READ",
        "numpy_bit_generator": "PCG64",
        "replicates": REPLICATES,
        "source_count": SOURCE_COUNT,
        "predictive_K_count": PREDICTIVE_K_COUNT,
        "routes": list(ROUTES),
        "stop_count_by_route": {str(route): STOP_COUNT for route in ROUTES},
        "seeds": SEEDS,
        "observation_source_association": source_maps,
        "candidate_stop_association": stop_maps,
        "predictive_K_identity": k_maps,
        "candidate_permutation_invariance": nonidentity_permutation(
            invariant_rng, SOURCE_COUNT
        ),
    }


def validate(payload: dict) -> None:
    if payload.get("contract") != CONTRACT or payload.get("replicates") != REPLICATES:
        raise ValueError("CTT_M2_NULL_MAP_CONTRACT")
    identity_source = list(range(SOURCE_COUNT))
    identity_stop = list(range(STOP_COUNT))
    identity_k = list(range(PREDICTIVE_K_COUNT))
    if len(payload["observation_source_association"]) != REPLICATES:
        raise ValueError("CTT_M2_NULL_MAP_SOURCE_COUNT")
    for mapping in payload["observation_source_association"]:
        if sorted(mapping) != identity_source or mapping == identity_source:
            raise ValueError("CTT_M2_NULL_MAP_SOURCE_PERMUTATION")
    for family in payload["candidate_stop_association"]:
        for route in ROUTES:
            mapping = family[str(route)]
            if sorted(mapping) != identity_stop or mapping == identity_stop:
                raise ValueError("CTT_M2_NULL_MAP_STOP_PERMUTATION")
    for family in payload["predictive_K_identity"]:
        for route in ROUTES:
            maps = family[str(route)]
            if len(maps) != STOP_COUNT:
                raise ValueError("CTT_M2_NULL_MAP_K_STOP_COUNT")
            for mapping in maps:
                if sorted(mapping) != identity_k or mapping == identity_k:
                    raise ValueError("CTT_M2_NULL_MAP_K_PERMUTATION")
    invariant = payload["candidate_permutation_invariance"]
    if sorted(invariant) != identity_source or invariant == identity_source:
        raise ValueError("CTT_M2_NULL_MAP_INVARIANCE")


def canonical_bytes(payload: dict) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    payload = build_payload()
    validate(payload)
    encoded = canonical_bytes(payload)
    digest = hashlib.sha256(encoded).hexdigest()
    if args.selftest:
        second = canonical_bytes(build_payload())
        if encoded != second:
            raise AssertionError("CTT_M2_NULL_MAP_NONDETERMINISTIC")
        print(f"CTT_M2_FIXED_U_TRANSPORT_NULL_MAP_SELFTEST=PASS sha256={digest}")
        return 0
    if args.output is None:
        parser.error("--output is required unless --selftest is used")
    if args.output.exists():
        raise SystemExit(f"CTT_M2_NULL_MAP_REFUSE_OVERWRITE:{args.output}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(encoded)
    print(f"CTT_M2_FIXED_U_TRANSPORT_NULL_MAP_FREEZE=PASS sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
