#!/usr/bin/env python3
"""A0 provenance audit and lossless canonicalization of frozen R0 observations."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np


BASE = "e527beea07c33cdbc362d156545409245f029968"
DECISION = "R0_PASS_STOCHASTIC_BENCHMARK_USABLE"
ITERATIONS = list(range(100, 551, 50))


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda: f.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def kv(path: Path) -> dict[str, str]:
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        key, value = line.split("\t", 1)
        result[key] = value
    return result


def audit(args: argparse.Namespace) -> dict:
    root = args.repo
    evidence = root / "evidence/stochastic_benchmark_refoundation/r0"
    protocol = root / "research/stochastic_benchmark_refoundation"
    gate = json.loads((evidence / "R0_RESULT.json").read_text(encoding="utf-8"))
    if gate["decision"] != DECISION or gate["panel_sources"] != 18 or gate["new_realizations_per_source"] != 16:
        raise ValueError("R0 PASS evidence drift")
    panel_path = protocol / "R0_SOURCE_PANEL_18.tsv"
    seed_path = protocol / "R0_SEED_MATRIX_18x16.tsv"
    artifact_path = evidence / "R0_ARTIFACT_SHA256.tsv"
    pool_code = protocol / "pool_r0_cube.py"
    contract_path = args.gate1a / "gate1a_contract.json"
    panel, seeds, artifacts = rows(panel_path), rows(seed_path), rows(artifact_path)
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if len(panel) != 18 or len(seeds) != 288 or len(artifacts) != 288:
        raise ValueError("R0 panel/seed/artifact count drift")
    if sorted(int(r["panel_index"]) for r in panel) != list(range(1, 19)):
        raise ValueError("R0 panel indexing drift")
    if contract["probe_operator"]["type"] != "avg_pool_2x2_then_sample" or contract["iteration_indices"] != ITERATIONS:
        raise ValueError("R0 observation operator or time ordering unproven")
    points = contract["probe_points"]
    if len(points) != 30 or any(int(p["native_x1_exclusive"]) - int(p["native_x0"]) != 2 or
                                int(p["native_y1_exclusive"]) - int(p["native_y0"]) != 2 for p in points):
        raise ValueError("R0 probe ordering/block contract drift")
    code_text = pool_code.read_text(encoding="utf-8")
    if "cube[:,x0:x1,y0:y1].mean(axis=(1,2))" not in code_text or "np.stack(vals,axis=1).astype(np.float64)" not in code_text:
        raise ValueError("R0 pooling implementation contract drift")
    source_ids = [r["source_id"] for r in sorted(panel, key=lambda x: int(x["panel_index"]))]
    if len(set(source_ids)) != 18 or len({int(r["rng_seed"]) for r in seeds}) != 288:
        raise ValueError("R0 source or seed uniqueness failure")
    by_key = {(r["source_id"], int(r["replicate"])): r for r in seeds}
    art_by_key = {(r["source_id"], int(r["replicate"])): r for r in artifacts}
    if len(by_key) != 288 or len(art_by_key) != 288:
        raise ValueError("duplicate R0 source/replicate row")
    x = np.empty((18, 16, 10, 30), dtype=np.float64)
    realization_ids = np.empty((18, 16), dtype="U32")
    raw_hashes, records = {}, []
    duplicate_hashes = {}
    for si, source_id in enumerate(source_ids):
        for ri in range(16):
            rep = ri + 1
            sr, ar = by_key[(source_id, rep)], art_by_key[(source_id, rep)]
            panel_index = si + 1
            seed = int(sr["rng_seed"])
            if int(sr["panel_index"]) != panel_index or int(ar["panel_index"]) != panel_index or int(ar["rng_seed"]) != seed:
                raise ValueError("R0 panel/seed/artifact mapping drift")
            if seed != 2026093000 + 16 * si + rep:
                raise ValueError("R0 seed formula drift")
            work = args.data / source_id / f"rep_{rep:02d}_seed_{seed}"
            cube_path = work / "spatial/concentration.npy"
            pooled_path = work / "pooled.npy"
            manifest_path = work / "manifest.tsv"
            manifest = kv(manifest_path)
            expected = {"panel_index": str(panel_index), "source_id": source_id,
                        "replicate": str(rep), "rng_seed": str(seed), "house": "House02",
                        "wind_name": "3,5-1_slow"}
            if any(manifest.get(k) != v for k, v in expected.items()):
                raise ValueError(f"R0 per-run metadata drift: {work}")
            cube_hash, pooled_hash = sha(cube_path), sha(pooled_path)
            if cube_hash != ar["concentration_sha256"] or pooled_hash != ar["pooled_sha256"]:
                raise ValueError(f"R0 raw/pooled hash mismatch: {work}")
            cube = np.load(cube_path, allow_pickle=False)
            pooled = np.load(pooled_path, allow_pickle=False)
            if cube.shape != (10, 83, 119) or pooled.shape != (10, 30):
                raise ValueError(f"R0 shape mismatch: {work}")
            if not np.isfinite(cube).all() or not np.isfinite(pooled).all() or (cube < 0).any() or (pooled < 0).any():
                raise ValueError(f"R0 invalid values: {work}")
            recomputed = np.stack([cube[:, int(p["native_x0"]):int(p["native_x1_exclusive"]),
                                         int(p["native_y0"]):int(p["native_y1_exclusive"])].mean(axis=(1, 2))
                                   for p in points], axis=1).astype(np.float64)
            if not np.array_equal(recomputed, pooled):
                raise ValueError(f"R0 ordered 10x30 re-extraction mismatch: {work}")
            x[si, ri] = pooled
            rid = f"rep_{rep:02d}_seed_{seed}"
            realization_ids[si, ri] = rid
            raw_hashes[str(cube_path)] = cube_hash
            raw_hashes[str(pooled_path)] = pooled_hash
            duplicate_hashes.setdefault(pooled_hash, []).append((source_id, rep))
            records.append({"source_id": source_id, "replicate": rep, "seed": seed,
                            "cube_sha256": cube_hash, "pooled_sha256": pooled_hash,
                            "cube_dtype": str(cube.dtype), "pooled_dtype": str(pooled.dtype)})
    same_hash = {h: ids for h, ids in duplicate_hashes.items() if len(ids) > 1}
    if same_hash:
        raise ValueError(f"duplicate full realization pooled hashes: {same_hash}")
    # Bit-identical pooled values would also have equal .npy hashes under this fixed format.
    cache = args.out / "cache/canonical_r0.npz"
    cache.parent.mkdir(parents=True, exist_ok=True)
    file_hashes = {str(p): sha(p) for p in (panel_path, seed_path, artifact_path, pool_code,
                                           contract_path, evidence / "R0_RESULT.json")}
    file_hashes.update(raw_hashes)
    source_xy = np.array([[float(r["x_m"]), float(r["y_m"])] for r in sorted(panel, key=lambda x: int(x["panel_index"]))])
    np.savez_compressed(cache, X=x, source_ids=np.array(source_ids), realization_ids=realization_ids,
                        source_xy=source_xy, time_index=np.arange(10), probe_index=np.arange(30),
                        time_iteration=np.array(ITERATIONS),
                        observable_name=np.array("raw_ppm_2x2_pooled_mean"), base_commit=np.array(BASE),
                        input_sha256_json=np.array(json.dumps(file_hashes, sort_keys=True)))
    with np.load(cache, allow_pickle=False) as recovered:
        if not np.array_equal(recovered["X"], x):
            raise ValueError("lossless canonical cache verification failed")
    audit_result = {
        "input_contract_pass": True,
        "base_commit": BASE,
        "r0_decision": DECISION,
        "n_sources": 18,
        "n_realizations_per_source": 16,
        "n_full_realizations": 288,
        "tensor_shape": [18, 16, 10, 30],
        "original_pooled_dtype": "float64",
        "time_axis": "axis 2, ordered GADEN iteration indices 100..550 step 50",
        "probe_axis": "axis 3, order of gate1a_contract.json probe_points",
        "observable_name": "raw_ppm_2x2_pooled_mean",
        "source_ids": source_ids,
        "source_xy": source_xy.tolist(),
        "realization_ids": realization_ids.tolist(),
        "seed_count_unique": 288,
        "duplicate_pooled_hash_groups": 0,
        "all_288_raw_cube_reextractions_exact": True,
        "nan_inf_count": 0,
        "input_file_sha256": file_hashes,
        "canonical_cache_sha256": sha(cache),
        "records": records,
    }
    return audit_result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--gate1a", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    try:
        result = audit(args)
    except Exception as exc:
        result = {"input_contract_pass": False, "base_commit": BASE, "error": str(exc)}
    dest = args.out / "audit"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "R0_INPUT_AUDIT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (dest / "R0_INPUT_AUDIT.md").write_text(
        "# JTD-G0 R0 input audit\n\n" +
        ("PASS: all 288 complete independent realizations exactly re-extracted from raw cubes.\n"
         if result["input_contract_pass"] else f"STOP: {result['error']}\n") +
        f"\nBase commit: `{BASE}`.\n" +
        ("Ordered 10x30 raw ppm is proven by Gate1A probe contract, R0 pooler, and exact raw-cube replay.\n"
         if result["input_contract_pass"] else "No JTD score was run.\n"), encoding="utf-8")
    if not result["input_contract_pass"]:
        raise SystemExit("JTD_G0_STOP_INPUT_CONTRACT_INVALID: " + result["error"])
    print("JTD_G0_A0_INPUT_AUDIT_PASS", result["canonical_cache_sha256"])


if __name__ == "__main__":
    main()
