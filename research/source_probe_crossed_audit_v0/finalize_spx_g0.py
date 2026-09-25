#!/usr/bin/env python3
"""Finalize SPX-G0 crossed-audit provenance and SHA256 inventories."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def manifest(path: Path, entries: dict[str, Path]) -> None:
    lines = ["role\tbytes\tsha256\tpath"]
    for role, file in sorted(entries.items()):
        lines.append(f"{role}\t{file.stat().st_size}\t{digest(file)}\t{file}")
    path.write_bytes(("\n".join(lines) + "\n").encode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--historical", type=Path, required=True)
    args = parser.parse_args()
    repo, historical = args.repo.resolve(), args.historical.resolve()
    folder = repo / "evidence/source_probe_crossed_audit_v0"
    result = json.loads((folder / "SPX_G0_RESULT.json").read_text(encoding="utf-8"))
    audit = json.loads((folder / "SPX_G0_INDEPENDENT_RECOMPUTATION.json").read_text(encoding="utf-8"))
    a0 = json.loads((folder / "SPX_G0_A0_COMPATIBILITY.json").read_text(encoding="utf-8"))
    asset = json.loads((folder / "SPX_G0_ASSET_AUDIT.json").read_text(encoding="utf-8"))
    rank = json.loads((folder / "SPX_G0_REFERENCE_PCA_RANK_AUDIT.json").read_text(encoding="utf-8"))
    lock = json.loads((folder / "SPX_G0_PRE_SCORE_LOCK.json").read_text(encoding="utf-8"))
    if (audit["independent_recomputation"] != "PASS" or audit["decision"] != result["decision"]
            or a0["decision"] != "SPX_G0_A0_COMPATIBLE" or asset["asset_usability"] != "ASSET_READY_FOR_CROSSED_EXTRACTION"):
        raise RuntimeError("SPX-G0 independent/asset gate incomplete")
    if lock["code_sha256"] != digest(repo / "research/source_probe_crossed_audit_v0/score_spx_g0.py"):
        raise RuntimeError("frozen scorer code drift")
    for key, record in a0["crossed_tensors"].items():
        if digest(folder / f"SPX_G0_{key}_10x30.npy") != record["sha256"]:
            raise RuntimeError(f"crossed tensor drift: {key}")
    note = f"""# SPX-G0 House02/W0 crossed diagnosis

Frozen label: `{result['decision']}`. This is a diagnostic label, not a main-innovation PASS. JTD-E2 and NPG-G0 remain STOP.

A0 found and numerically verified all 2,688 CENTRAL and 96 OFFSTRIP raw cubes, both 30-probe contracts, the House02 occupancy grid, and all 11 W0 wind arrays. CENTRAL×P_G1A and OFFSTRIP×P_E2 reproduce their historical 10×30 tensors with maximum absolute difference 0.0. The same raw cube was then extracted under both protocols. No new plume was generated.

The primary score is a uniform-prior two-source conditional likelihood on the 84 CENTRAL and three OFFSTRIP fixed 0.3 m pairs. It does not compare 168-way with 6-way posteriors. The H02 W2 distant-aliasing cases are outside this diagnosis.

For FULL versus BP, {result['comparators']['BP']['central_both_positive_count']}/84 CENTRAL pairs are positive under both probes, {result['comparators']['BP']['central_sign_reversal_count']}/84 reverse sign on probe switch, and {result['comparators']['BP']['offstrip_both_nonpositive_count']}/3 OFFSTRIP pairs are non-positive under both probes. The corresponding FULL versus MBD counts are {result['comparators']['MBD']['central_both_positive_count']}/84, {result['comparators']['MBD']['central_sign_reversal_count']}/84 and {result['comparators']['MBD']['offstrip_both_nonpositive_count']}/3.

Neither frozen SOURCE_REGIME_DOMINANT nor PROBE_PROTOCOL_DOMINANT inequalities hold for both comparators. Therefore the charter assigns SOURCE_PROBE_INTERACTION by exclusion. This label does not itself establish a physical relational mechanism; the source/probe effects may also include Gaussian model instability and severe NLL tails. Median CENTRAL paired probe effects are near zero, while target-level tails are large. The reference-only rank audit found {rank['insufficient_two_dimension_cases']}/{rank['pair_protocol_fold_block_total']} PCA2 blocks with fewer than two varying raw dimensions, affecting {rank['affected_pairs']} pairs. All pairs remain in the result.

An independent verifier refit all {audit['target_models_refit']} target/model scores, recomputed pair/probe effects, all 10,000 pair bootstrap draws and the frozen diagnosis. The maximum truth NLL difference was {audit['max_truth_nll_difference']:.3g}. No model, feature, pair, probe, threshold or interpretation rule was changed after the full score was observed.
"""
    (folder / "SPX_G0_VERDICT_NOTE.md").write_bytes(note.encode("utf-8"))
    provenance = {"branch": "research/source-probe-crossed-audit-20260925",
                  "a0_commit": "32937be94cd245522c8d55ffc5ffdca959b36eea",
                  "initial_pre_score_lock_commit": "e79cef5e370f20a9372b4881b82d7ab04946c11e",
                  "pre_score_rank_correction_commit": "234ba18685a80ce5358316d80478dc12eef49794",
                  "pre_score_lock_sha256": digest(folder / "SPX_G0_PRE_SCORE_LOCK.json"),
                  "asset_audit_sha256": digest(folder / "SPX_G0_ASSET_AUDIT.json"),
                  "a0_compatibility_sha256": digest(folder / "SPX_G0_A0_COMPATIBILITY.json"),
                  "decision": result["decision"], "new_plume_runs": 0,
                  "pair_count": 87, "sealed_data_read": False,
                  "scorer_or_gate_changed_after_full_result": False,
                  "independent_recomputation": audit["independent_recomputation"]}
    (folder / "SPX_G0_PROVENANCE.json").write_bytes((json.dumps(provenance, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    inputs = {
        "central_panel": repo / "evidence/causal_emergent_source_scale_v0/d1r/CESS_D1R_PANEL_168.tsv",
        "NPG_disjoint_pairs": repo / "evidence/neural_population_geometry_v0/g0/NPG_G0_PAIR_DEFINITION.csv",
        "OFFSTRIP_source_pairs": repo / "evidence/environment_level_benchmark_v0/e1/E1_HOUSE_SOURCE_PANELS.tsv",
        "P_E2_probe_contract": repo / "evidence/environment_level_benchmark_v0/e1/E1_HOUSE_PROBE_CONTRACTS.tsv",
        "P_G1A_probe_contract": historical / "repo/gate1a_contract.json",
        "historical_CENTRAL_tensor": historical / "data/reference_168x16x10x30.npy",
        "historical_E2_reference_tensor": repo / "evidence/jtd_e2_20260925/JTD_E2_REFERENCE_12x10x30.npy",
        "historical_E2_target_tensor": repo / "evidence/jtd_e2_20260925/JTD_E2_FRESH_TARGET_10x30.npy",
    }
    code = {file.name: file for file in (repo / "research/source_probe_crossed_audit_v0").iterdir()
            if file.is_file() and file.suffix in {".py", ".md"}}
    exclusions = {"SPX_G0_INPUT_SHA256.tsv", "SPX_G0_CODE_SHA256.tsv", "SPX_G0_OUTPUT_SHA256.tsv",
                  "SPX_G0_PROVENANCE.json", "SPX_G0_VERDICT_NOTE.md"}
    outputs = {file.name: file for file in folder.iterdir() if file.is_file() and file.name not in exclusions}
    manifest(folder / "SPX_G0_INPUT_SHA256.tsv", inputs)
    manifest(folder / "SPX_G0_CODE_SHA256.tsv", code)
    manifest(folder / "SPX_G0_OUTPUT_SHA256.tsv", outputs)
    print("SPX_G0_EVIDENCE_FINALIZED", result["decision"])


if __name__ == "__main__":
    main()
