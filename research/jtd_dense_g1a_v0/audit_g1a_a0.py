#!/usr/bin/env python3
"""Read-only G1A compatibility audit of the frozen D1R raw bank."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np


EXPECTED = {
    "source_bank": "0e835c3a3d0f4651f9c4aa87b28a34892589cfb073a73daf6a84896d081824fb",
    "contract": "68121bc9225646e37fcf0233e769b694d9dbaec382723f45b8e80ffc73cea334",
    "panel": "5df11712dd0e7dbef6e454c8d146427407644b9f27245c447479185ab2129d8e",
    "inventory": "3540c6a734c7d7c4714793bd504ae246277d2563eff9346514d3f9d761372b1d",
    "tensor": "b21a089cb015ace71a448db58bd7a2f1fee25e9a8431cbb56728f48ca39573d9",
    "binary": "4127b9ba4f42186ba2d6d33c84fba8d4b92749da59b83750fa4847dbd9957ce1",
    "occupancy": "9402690152be4568ced8f2256e9098d82691aaaa1f22a1887eeac55d0e5d098d",
    "wind_iteration_1": "54d7bc338ea681611f66004a3230f29feffc495446814607141b0623ef1dd9a8",
    "extractor": "206cc92384866dcb7d966c6f8f9ec87862e15c7fee460a43c04014b58e3cae91",
}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def main() -> None:
    p = argparse.ArgumentParser()
    for name in ("bank-root", "package-root", "r0-panel", "r0-audit", "binary", "occupancy", "wind-iteration-1", "extractor", "out"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    pkg = a.package_root
    files = {
        "source_bank": pkg / "repo/source_bank.tsv",
        "contract": pkg / "repo/gate1a_contract.json",
        "panel": pkg / "repo/CESS_D1R_PANEL_168.tsv",
        "inventory": pkg / "repo/CESS_D1R_ARTIFACT_SHA256.tsv",
        "tensor": pkg / "data/reference_168x16x10x30.npy",
        "binary": a.binary,
        "occupancy": a.occupancy,
        "wind_iteration_1": a.wind_iteration_1,
        "extractor": a.extractor,
    }
    checks = []
    for name, path in files.items():
        actual = sha(path)
        checks.append({"item": name, "path": str(path), "sha256": actual, "expected_sha256": EXPECTED[name], "pass": actual == EXPECTED[name]})
    panel = rows(files["panel"])
    inventory = rows(files["inventory"])
    r0_panel = rows(a.r0_panel)
    r0_audit = json.loads(a.r0_audit.read_text(encoding="utf-8"))
    contract = json.loads(files["contract"].read_text(encoding="utf-8"))
    tensor = np.load(files["tensor"], allow_pickle=False, mmap_mode="r")
    assert len(panel) == 168 and len(inventory) == 2688
    assert tensor.shape == (168, 16, 10, 30) and tensor.dtype == np.float64
    assert contract["iteration_indices"] == list(range(100, 551, 50)) and len(contract["probe_points"]) == 30
    assert r0_audit["input_contract_pass"] and r0_audit["all_288_raw_cube_reextractions_exact"]
    assert r0_audit["original_pooled_dtype"] == "float64"
    assert r0_audit["input_file_sha256"]["/home/zyc/bigreen_gate1a_exact_20260924/gate1a_contract.json"] == EXPECTED["contract"]
    assert len({r["source_id"] for r in panel}) == 168
    assert {(int(r["pmfs_i"]), int(r["pmfs_j"])) for r in panel} == {(i, j) for i in range(1, 25) for j in range(12, 19)}
    assert {float(r["z_m"]) for r in panel} == {0.2}
    r0_ids = {r["source_id"] for r in r0_panel}
    overlap = sorted(r0_ids & {r["source_id"] for r in panel})
    assert len(overlap) == 1 and overlap == ["pmfs_23_16"]
    seen_seed, seen_cube, seen_pooled = set(), set(), set()
    exact_pool = exact_tensor = 0
    for i, source in enumerate(panel):
        assert int(source["panel_index"]) == i
        for rep in range(1, 17):
            inv = inventory[16*i + rep - 1]
            seed = 2026105000 + 16*i + rep
            assert (int(inv["panel_index"]), inv["source_id"], int(inv["replicate"]), int(inv["rng_seed"])) == (i, source["source_id"], rep, seed)
            work = a.bank_root / source["source_id"] / f"rep_{rep:02d}_seed_{seed}"
            cube_path, pooled_path, meta_path = work / "spatial/concentration.npy", work / "pooled.npy", work / "manifest.tsv"
            cube_hash, pooled_hash = sha(cube_path), sha(pooled_path)
            assert cube_hash == inv["concentration_sha256"] and pooled_hash == inv["pooled_sha256"]
            assert cube_hash not in seen_cube and pooled_hash not in seen_pooled and seed not in seen_seed
            seen_cube.add(cube_hash); seen_pooled.add(pooled_hash); seen_seed.add(seed)
            meta = dict(line.rstrip("\n").split("\t", 1) for line in meta_path.read_text(encoding="utf-8").splitlines())
            expected_meta = {"panel_index": str(i), "source_id": source["source_id"], "replicate": str(rep), "rng_seed": str(seed),
                             "house": "House02", "wind": "3,5-1_slow", "binary_sha256": EXPECTED["binary"],
                             "occupancy_sha256": EXPECTED["occupancy"], "w2_iteration1_sha256": EXPECTED["wind_iteration_1"],
                             "extractor_sha256": EXPECTED["extractor"], "source_bank_sha256": EXPECTED["source_bank"],
                             "gate1a_contract_sha256": EXPECTED["contract"]}
            assert all(meta.get(k) == v for k, v in expected_meta.items())
            assert np.allclose(np.array([float(v) for v in meta["source_xyz_m"].split(",")]),
                               np.array([float(source[k]) for k in ("x_m", "y_m", "z_m")]), atol=1e-12, rtol=0)
            cube = np.load(cube_path, allow_pickle=False)
            pooled = np.load(pooled_path, allow_pickle=False)
            assert cube.shape == (10, 83, 119) and pooled.shape == (10, 30) and pooled.dtype == np.float64
            assert np.isfinite(cube).all() and np.isfinite(pooled).all() and (cube >= 0).all() and (pooled >= 0).all()
            repooled = np.stack([cube[:, int(q["native_x0"]):int(q["native_x1_exclusive"]),
                                      int(q["native_y0"]):int(q["native_y1_exclusive"])].mean(axis=(1,2))
                                 for q in contract["probe_points"]], axis=1).astype(np.float64)
            assert np.array_equal(repooled, pooled)
            exact_pool += 1
            assert np.array_equal(pooled, tensor[i, rep-1])
            exact_tensor += 1
        if (i+1) % 24 == 0:
            print(f"A0_AUDITED_SOURCES {i+1}/168", flush=True)
    report = {
        "decision": "JTD_G1A_A0_COMPATIBLE" if all(x["pass"] for x in checks) else "JTD_G1A_DATA_CONTRACT_STOP",
        "checks": checks,
        "source_count": len(panel), "realizations_per_source": 16, "total_realizations": len(inventory),
        "unique_seed_count": len(seen_seed), "unique_cube_hash_count": len(seen_cube), "unique_pooled_hash_count": len(seen_pooled),
        "raw_cube_repool_exact_count": exact_pool, "pooled_tensor_exact_count": exact_tensor,
        "r0_g0_panel_intersection_ids": overlap,
        "r0_g0_panel_intersection_count": len(overlap),
        "observation_contract_sha256": EXPECTED["contract"],
        "time_indices": contract["iteration_indices"], "probe_count": len(contract["probe_points"]),
        "observable_name": "raw_ppm_2x2_pooled_mean",
        "model_contract": "G0 five two-time blocks, StandardScaler + PCA2/block, source OAS, jitter 1e-10*max(1,trace(cov)/d)",
        "r0_audit_sha256": sha(a.r0_audit), "r0_panel_sha256": sha(a.r0_panel),
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(report["decision"], flush=True)
    if report["decision"] != "JTD_G1A_A0_COMPATIBLE":
        raise SystemExit(30)


if __name__ == "__main__":
    main()
