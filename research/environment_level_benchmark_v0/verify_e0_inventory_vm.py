#!/usr/bin/env python3
"""Independent SHA and count checks for the read-only E0 inventory."""

import argparse
import csv
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

BASE = Path("/home/zyc")
SPECS = (
    ("CESS_D1R", BASE / "cess_d1r_reference_repo_20260925/evidence/causal_emergent_source_scale_v0/d1r/CESS_D1R_ARTIFACT_SHA256.tsv", 2688),
    ("R0", BASE / "r0_stochastic_benchmark_repo_20260924/evidence/stochastic_benchmark_refoundation/r0/R0_ARTIFACT_SHA256.tsv", 288),
    ("LSC_D0", BASE / "lsc_crosswind_d0_repo_20260925/evidence/local_stochastic_confusability_v0/crosswind_d0/LSC_CROSSWIND_D0_ARTIFACT_SHA256.tsv", 128),
)


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def table(path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    inventory = table(args.out / "E0_ENVIRONMENT_ASSET_INVENTORY.tsv")
    checked = {}
    for family, expected_path, expected_count in SPECS:
        observed = [r for r in inventory if r["family"] == family]
        expected = table(expected_path)
        assert len(observed) == len(expected) == expected_count, (family, len(observed), len(expected))
        lookup = {(r["source_id"], r["seed"]): r for r in observed}
        assert len(lookup) == expected_count
        for row in expected:
            key = (row["source_id"], row["rng_seed"])
            item = lookup[key]
            run = Path(item["path"])
            assert sha(run / "spatial/concentration.npy") == row["concentration_sha256"] == item["artifact_sha256"], key
            assert sha(run / "pooled.npy") == row["pooled_sha256"], key
        checked[family] = expected_count

    summary = json.loads((args.out / "E0_ENVIRONMENT_SUMMARY.json").read_text())
    per_env = Counter((r["house"], r["wind"]) for r in inventory)
    assert len(summary["environments"]) == 12
    assert sum(per_env.values()) == len(inventory) == summary["inventory_rows"]
    for env in summary["environments"]:
        assert per_env[(env["house"], env["wind"])] >= env["N_existing_independent_realizations_total"]
    report = {
        "verdict": "E0_INTEGRITY_PASS",
        "independent_SHA_inventory_families": checked,
        "concentration_and_pooled_files_verified": 2 * sum(checked.values()),
        "inventory_rows": len(inventory),
        "summary_environments": len(summary["environments"]),
        "inventory_sha256": sha(args.out / "E0_ENVIRONMENT_ASSET_INVENTORY.tsv"),
        "summary_sha256": sha(args.out / "E0_ENVIRONMENT_SUMMARY.json"),
        "new_plume_simulations": 0,
    }
    (args.out / "E0_INDEPENDENT_INTEGRITY.json").write_text(json.dumps(report, indent=2) + "\n")
    # Reconcile the audit's curated families against a filesystem-wide name
    # discovery. Other files are listed, not silently promoted to replicates.
    raw = subprocess.check_output(["find", str(BASE), "-type", "f", "-name", "iteration_0"], text=True).splitlines()
    cubes = subprocess.check_output(["find", str(BASE), "-type", "f", "-name", "concentration.npy"], text=True).splitlines()
    raw_roots = Counter(Path(p).relative_to(BASE).parts[0] for p in raw)
    cube_roots = Counter(Path(p).relative_to(BASE).parts[0] for p in cubes)
    coverage = {
        "raw_iteration0_total": len(raw),
        "raw_roots": dict(sorted(raw_roots.items())),
        "concentration_cube_total": len(cubes),
        "cube_roots": dict(sorted(cube_roots.items())),
        "counting_exclusions": {
            "SCTT_DISCOVERY_DATASET_V2_R2_20260817": "same named source/wind/seed cases as V2; mirror, not new realizations",
            "SCTT_DISCOVERY_DATASET_20260817": "five retained frames per oracle case; lacks D1R time indices",
            "hcmc_v1_independent_data_20260922/smoke": "runtime smoke cases, not formal independent data",
            "c0_5_cost_benchmark_20260923": "duration variants reuse seed 2026092301 and source/wind of C0.5 bank",
            "enva_vgr": "noncanonical environment outside E0 12-operator universe",
            "rmfe_*": "historical diagnostic raw assets without frozen source/seed/operator provenance; quarantined from independent counts",
            "*_repo_20260924/25": "Git worktree copies of tracked reference data, not new realizations",
        },
    }
    (args.out / "E0_DISCOVERY_COVERAGE.json").write_text(json.dumps(coverage, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
