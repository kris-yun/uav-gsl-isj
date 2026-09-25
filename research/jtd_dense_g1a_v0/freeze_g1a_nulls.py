#!/usr/bin/env python3
"""Freeze exact domain-separated G1A derangements before dense scoring."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

N_FOLD, N_NULL, N_SOURCE, N_BLOCK, N_REF = 4, 200, 168, 4, 12


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--panel", type=Path, required=True)
    p.add_argument("--a0", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    if a.out.exists() and any(a.out.iterdir()):
        raise RuntimeError("refuse existing null-lock directory")
    audit = json.loads(a.a0.read_text(encoding="utf-8"))
    if audit["decision"] != "JTD_G1A_A0_COMPATIBLE":
        raise RuntimeError("A0 not compatible")
    with a.panel.open(newline="", encoding="utf-8") as f:
        panel = list(csv.DictReader(f, delimiter="\t"))
    assert len(panel) == N_SOURCE
    seeds = np.empty((N_FOLD, N_NULL, N_SOURCE, N_BLOCK), dtype=np.uint64)
    perm = np.empty((N_FOLD, N_NULL, N_SOURCE, N_BLOCK, N_REF), dtype=np.uint8)
    identity = np.arange(N_REF)
    used = set()
    for fold in range(N_FOLD):
        for null_id in range(N_NULL):
            for source, row in enumerate(panel):
                for block in range(1, 5):
                    key = f"uav-gsl-isj|JTD_G1A|fold={fold}|null_id={null_id}|source_id={row['source_id']}|block_id={block}|purpose=within_source_derangement"
                    seed = int.from_bytes(hashlib.sha256(key.encode("utf-8")).digest()[:8], "big")
                    if seed in used:
                        raise RuntimeError("SHA256 seed alias")
                    used.add(seed)
                    rng = np.random.default_rng(seed)
                    for _ in range(1000):
                        d = rng.permutation(N_REF)
                        if np.all(d != identity):
                            break
                    else:
                        raise RuntimeError("derangement failed")
                    seeds[fold, null_id, source, block-1] = seed
                    perm[fold, null_id, source, block-1] = d
        print(f"NULL_KEYS_FROZEN_FOLD {fold+1}/4", flush=True)
    a.out.mkdir(parents=True)
    np.save(a.out / "JTD_G1A_NULL_SEEDS.npy", seeds, allow_pickle=False)
    np.save(a.out / "JTD_G1A_NULL_DERANGEMENTS.npy", perm, allow_pickle=False)
    spec = {
        "algorithm": "SHA256 domain-separated tuple; first 8 digest bytes big-endian uint64 -> numpy default_rng -> G0 rejection-sampled derangement",
        "key_template": "uav-gsl-isj|JTD_G1A|fold={fold}|null_id={null_id}|source_id={source_id}|block_id={block}|purpose=within_source_derangement",
        "fold_range": [0, 3], "null_id_range": [0, 199], "source_ids": [r["source_id"] for r in panel],
        "block_id_range": [1, 4], "reference_order": "ascending zero-based replicate index excluding evaluation fold",
        "seed_shape": list(seeds.shape), "derangement_shape": list(perm.shape),
        "unique_seed_count": len(used), "a0_sha256": sha(a.a0), "panel_sha256": sha(a.panel),
        "seed_file_sha256": sha(a.out / "JTD_G1A_NULL_SEEDS.npy"),
        "derangement_file_sha256": sha(a.out / "JTD_G1A_NULL_DERANGEMENTS.npy"),
    }
    (a.out / "JTD_G1A_NULL_LOCK.json").write_text(json.dumps(spec, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print("JTD_G1A_NULL_LOCK_FROZEN", spec["derangement_file_sha256"], flush=True)


if __name__ == "__main__":
    main()
