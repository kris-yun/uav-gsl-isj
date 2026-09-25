#!/usr/bin/env python3
"""Write immutable NPG-G0 provenance, interpretation and SHA256 inventories."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            value.update(block)
    return value.hexdigest()


def inventory(path: Path, items: dict[str, Path]) -> None:
    lines = ["role\tbytes\tsha256\tpath"]
    for role, file in sorted(items.items()):
        lines.append(f"{role}\t{file.stat().st_size}\t{digest(file)}\t{file}")
    path.write_bytes(("\n".join(lines) + "\n").encode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--bank", type=Path, required=True)
    args = parser.parse_args()
    repo, bank = args.repo.resolve(), args.bank.resolve()
    folder = repo / "evidence/neural_population_geometry_v0/g0"
    result = json.loads((folder / "NPG_G0_RESULT.json").read_text(encoding="utf-8"))
    checked = json.loads((folder / "NPG_G0_INDEPENDENT_RECOMPUTATION.json").read_text(encoding="utf-8"))
    lock = json.loads((folder / "NPG_G0_PRE_RUN_LOCK.json").read_text(encoding="utf-8"))
    if result["decision"] != checked["decision"] or checked["independent_recomputation"] != "PASS":
        raise RuntimeError("independent recomputation incomplete")
    if lock["input_sha256"] != digest(bank) or lock["code_sha256"] != digest(repo / "research/neural_population_geometry_v0/npg_g0.py"):
        raise RuntimeError("frozen scorer or bank drift")
    note = f"""# NPG-G0 reference-only decision

Frozen decision: `{result['decision']}`. This is a zero-plume House02 reference-bank test of a new mother-theory mapping. JTD-E2 STOP remains unchanged.

The 84 disjoint 0.3 m source pairs show benefit heterogeneity: {result['positive_utility_pairs']} positive and {result['negative_utility_pairs']} negative A/B-mean interaction utilities. G0-1 passes.

GEOMETRY versus AUDIT utility: Spearman {result['geometry_spearman']:+.6f}, pair-bootstrap 95% interval {result['geometry_spearman_ci95']}. Split A {result['geometry_spearman_split']['A']:+.6f}; Split B {result['geometry_spearman_split']['B']:+.6f}. G0-2 fails.

GEOMETRY has a lower mean squared prediction error than INNER_CV by {result['mse_advantage_inner_cv_minus_geometry']:+.6f}, interval {result['mse_advantage_ci95']}; G0-3 passes. This does not establish prospective benefit-sign selection: balanced accuracy is {result['geometry_balanced_accuracy']:.6f} for GEOMETRY versus {result['inner_cv_balanced_accuracy']:.6f} for INNER_CV. G0-4 fails. G0-5 passes ({sum(row['mean_mse_advantage_inner_cv_minus_geometry'] > 0 for row in result['macro_band_advantages'])}/4 bands).

The frozen decision is STOP because G0-2 and G0-4 fail. No predictor, transform, alpha grid, pair set, or threshold was revised after AUDIT utility was revealed. No G1 method-development stage, E2 target, H01 DEV, House03, neural network or closed loop was run.

Independent audit refit the 336 AUDIT pair models and 840 held-out geometry/scalar predictions, recomputed all 10,000 pair-bootstrap draws, and reproduced every gate.
"""
    (folder / "NPG_G0_VERDICT_NOTE.md").write_bytes(note.encode("utf-8"))
    provenance = {
        "branch": "research/neural-population-geometry-g0-20260925",
        "pre_run_lock_commit": "80c4c8837a381a395d4c51d54174d18be1baa564",
        "pre_run_portability_fix_before_audit": True,
        "pre_run_lock_sha256": digest(folder / "NPG_G0_PRE_RUN_LOCK.json"),
        "decision": result["decision"],
        "source_count": 168,
        "pair_count": 84,
        "new_plume_runs": 0,
        "scorer_changed_after_audit": False,
        "independent_recomputation": checked["independent_recomputation"],
        "sealed_data_read": False,
    }
    (folder / "NPG_G0_PROVENANCE.json").write_bytes((json.dumps(provenance, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    inputs = {
        "frozen_reference_bank_168x16x10x30": bank,
        "D1R_source_panel": repo / "evidence/causal_emergent_source_scale_v0/d1r/CESS_D1R_PANEL_168.tsv",
        "D1R_reference_summary": repo / "evidence/causal_emergent_source_scale_v0/d1r/CESS_D1R_REFERENCE_SUMMARY.json",
        "G1A_input_audit": repo / "evidence/jtd_g1a_20260925/a0/JTD_G1A_A0_COMPATIBILITY.json",
    }
    code = {file.name: file for file in (repo / "research/neural_population_geometry_v0").iterdir()
            if file.is_file() and file.suffix in {".py", ".md"}}
    exclusions = {"NPG_G0_INPUT_SHA256.tsv", "NPG_G0_CODE_SHA256.tsv", "NPG_G0_OUTPUT_SHA256.tsv",
                  "NPG_G0_PROVENANCE.json", "NPG_G0_VERDICT_NOTE.md"}
    outputs = {file.name: file for file in folder.iterdir() if file.is_file() and file.name not in exclusions}
    inventory(folder / "NPG_G0_INPUT_SHA256.tsv", inputs)
    inventory(folder / "NPG_G0_CODE_SHA256.tsv", code)
    inventory(folder / "NPG_G0_OUTPUT_SHA256.tsv", outputs)
    print("NPG_G0_EVIDENCE_FINALIZED", result["decision"])


if __name__ == "__main__":
    main()
