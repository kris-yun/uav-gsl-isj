#!/usr/bin/env python3
"""Create the pre-generation CTPI M2 CAL/CONFIRM RNG manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


CONTRACT = "CTPI_M2_OBSERVATION_PROVENANCE_V1"
DOMAIN_PREFIX = "CTPI_M2_OBSERVATION_V1"
HOUSES = ("H01", "H02", "H03")
SETS = ("M2_CAL", "M2_CONFIRM")
FORBIDDEN = frozenset((101, 211, 307, 401, 503, 601, 701, 809,
                       907, 1009, 1103, 1201, 5489))
BANK_SUMMARY_SHA256 = {
    "H01": "8bab8c2e5c39d091137beef5d2efe69eb2131be09c75efb1347f18411a776888",
    "H02": "f00daf24c70771d95f945de098fed29e17cc72a763b000bdd281038383bd2845",
    "H03": "736444246178d89432cfde5bc2f12699e7ec9d5600f2e11fa385e609fbfa68ab",
}


def derive_seed(dataset: str, house: str, index: int, occupied: set[int]) -> dict:
    retry = 0
    while True:
        domain = f"{DOMAIN_PREFIX}/{dataset}/{house}/{index:02d}"
        preimage = f"{domain}|retry={retry}"
        digest = hashlib.sha256(preimage.encode("ascii")).hexdigest()
        seed = int.from_bytes(bytes.fromhex(digest[:8]), "big")
        if seed != 0 and seed not in FORBIDDEN and seed not in occupied:
            occupied.add(seed)
            return {
                "set": dataset, "house": house, "index": index,
                "route_seed": index, "rng_domain": domain,
                "derivation_preimage": preimage, "derivation_sha256": digest,
                "uint32_seed": seed, "retry": retry,
            }
        retry += 1


def build_manifest() -> dict:
    occupied = set(FORBIDDEN)
    tapes = [
        derive_seed(dataset, house, index, occupied)
        for dataset in SETS for house in HOUSES for index in range(10)
    ]
    seeds = [item["uint32_seed"] for item in tapes]
    assert len(tapes) == 60 and len(set(seeds)) == 60
    assert not (set(seeds) & FORBIDDEN)
    cal = {item["uint32_seed"] for item in tapes if item["set"] == "M2_CAL"}
    confirm = {item["uint32_seed"] for item in tapes if item["set"] == "M2_CONFIRM"}
    assert not (cal & confirm)
    return {
        "contract": CONTRACT,
        "domain_prefix": DOMAIN_PREFIX,
        "predictive_bank_generation": False,
        "bank_summary_sha256": BANK_SUMMARY_SHA256,
        "forbidden_numeric_seeds": sorted(FORBIDDEN),
        "proof": {
            "new_seed_count": len(seeds),
            "all_new_numeric_seeds_unique": True,
            "cal_confirm_numeric_disjoint": True,
            "new_vs_predictive_and_default_numeric_disjoint": True,
            "cal_confirm_domain_disjoint": True,
        },
        "tapes": tapes,
    }


def canonical_bytes(payload: dict) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def selftest() -> None:
    left = canonical_bytes(build_manifest())
    right = canonical_bytes(build_manifest())
    assert left == right
    payload = json.loads(left)
    assert payload["tapes"][0]["rng_domain"].startswith(f"{DOMAIN_PREFIX}/M2_CAL/H01/")
    assert payload["tapes"][-1]["rng_domain"].startswith(f"{DOMAIN_PREFIX}/M2_CONFIRM/H03/")
    print("CTPI_M2_PROVENANCE_SELFTEST=PASS")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        selftest()
    if args.output:
        data = canonical_bytes(build_manifest())
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(data)
        digest = hashlib.sha256(data).hexdigest()
        args.output.with_suffix(args.output.suffix + ".sha256").write_text(
            f"{digest}  {args.output.name}\n", encoding="ascii"
        )
        print(f"CTPI_M2_PROVENANCE_MANIFEST={args.output}")
        print(f"CTPI_M2_PROVENANCE_SHA256={digest}")
    if not args.selftest and not args.output:
        parser.error("use --selftest and/or --output")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
