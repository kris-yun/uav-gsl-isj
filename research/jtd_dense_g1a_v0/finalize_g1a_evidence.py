#!/usr/bin/env python3
"""Write G1A provenance and code/input/output hash inventories."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()


def inventory(path: Path, files: dict[str, Path]) -> None:
    lines = ["role\tbytes\tsha256\tpath"]
    for role, file in sorted(files.items()):
        lines.append(f"{role}\t{file.stat().st_size}\t{sha(file)}\t{file}")
    path.write_bytes(("\n".join(lines)+"\n").encode("utf-8"))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--input", type=Path, required=True)
    a = p.parse_args()
    repo, inp = a.repo.resolve(), a.input.resolve()
    out = repo / "evidence/jtd_g1a_20260925"
    result = json.loads((out / "science/JTD_G1A_RESULT.json").read_text(encoding="utf-8"))
    verify = json.loads((out / "science/JTD_G1A_INDEPENDENT_RECOMPUTATION.json").read_text(encoding="utf-8"))
    refit = json.loads((out / "science/JTD_G1A_INDEPENDENT_MODEL_REFITS.json").read_text(encoding="utf-8"))
    assert verify["decision"] == result["decision"] and refit["independent_model_refits"] == "PASS"
    inputs = {
        "D1R_reference_tensor": inp / "CESS_D1R_REFERENCE_REVIEW_20260925/data/reference_168x16x10x30.npy",
        "D1R_source_panel": repo / "evidence/causal_emergent_source_scale_v0/d1r/CESS_D1R_PANEL_168.tsv",
        "D1R_raw_cube_and_pooled_inventory": repo / "evidence/causal_emergent_source_scale_v0/d1r/CESS_D1R_ARTIFACT_SHA256.tsv",
        "Gate1A_observation_contract": inp / "CESS_D1R_REFERENCE_REVIEW_20260925/repo/gate1a_contract.json",
        "Gate1A_source_bank": inp / "CESS_D1R_REFERENCE_REVIEW_20260925/repo/source_bank.tsv",
        "G0_R0_input_audit": inp / "evidence/jtd_g0_20260925/audit/R0_INPUT_AUDIT.json",
        "G0_frozen_config": inp / "evidence/jtd_g0_20260925/config/frozen_config.yaml",
        "R0_source_panel": repo / "research/stochastic_benchmark_refoundation/R0_SOURCE_PANEL_18.tsv",
        "A0_compatibility_report": out / "a0/JTD_G1A_A0_COMPATIBILITY.json",
        "pre_score_null_key_lock": out / "null_lock/JTD_G1A_NULL_LOCK.json",
        "pre_score_null_derangements": out / "null_lock/JTD_G1A_NULL_DERANGEMENTS.npy",
        "pre_score_null_seeds": out / "null_lock/JTD_G1A_NULL_SEEDS.npy",
    }
    code = {f.name: f for f in (repo / "research/jtd_dense_g1a_v0").glob("*.py")}
    code.update({f.name: f for f in (repo / "research/jtd_dense_g1a_v0").glob("*.md")})
    science = {f.name: f for f in (out / "science").iterdir() if f.is_file()}
    inventory(out / "JTD_G1A_INPUT_SHA256.tsv", inputs)
    inventory(out / "JTD_G1A_CODE_SHA256.tsv", code)
    inventory(out / "JTD_G1A_OUTPUT_SHA256.tsv", science)
    note = f"""# JTD-G1A frozen dense assessment result

Decision: `{result['decision']}`. All frozen G1–G6 gates are `{result['gates']}`.

- A0: 168 sources × 16 realizations, all 2,688 raw cube hashes, re-pooling and tensor entries exact; R0-18 intersection = 1 source.
- Reference/target split: four folds with 12 references and 4 held-out realizations per source; 0 new plume.
- Mean truth NLL: FULL {result['models']['FULL']['mean_truth_nll']:.6f}, BLOCK-PRODUCT {result['models']['BLOCK_PRODUCT']['mean_truth_nll']:.6f}, MBD {result['models']['MATCHED_BLOCK_DIAG']['mean_truth_nll']:.6f}.
- Source-panel Delta BP {result['delta_bp']['source_panel_mean']:.6f}, 95% source-panel sensitivity interval {result['delta_bp']['source_sensitivity_ci_95']}; positive sources {result['delta_bp']['positive_source_count']}/168.
- Source-panel Delta MBD {result['delta_mbd']['source_panel_mean']:.6f}, interval {result['delta_mbd']['source_sensitivity_ci_95']}; positive sources {result['delta_mbd']['positive_source_count']}/168.
- BP comparison remains positive after 20% trimming ({result['delta_bp']['trimmed_20_mean']:.6f}) and removing the largest positive 5% of targets ({result['delta_bp']['remove_top_positive_5pct_mean']:.6f}). The largest positive target effect is {result['delta_bp']['largest_positive_target_delta']:.3f}; report tail-sensitive mean with the robust metrics.
- FULL vs BP mean Brier: {result['models']['FULL']['mean_brier']:.6f} vs {result['models']['BLOCK_PRODUCT']['mean_brier']:.6f}; 1.0 m posterior mass: {result['models']['FULL']['mean_mass_1p0m']:.6f} vs {result['models']['BLOCK_PRODUCT']['mean_mass_1p0m']:.6f}; expected distance: {result['models']['FULL']['mean_expected_distance_m']:.6f} vs {result['models']['BLOCK_PRODUCT']['mean_expected_distance_m']:.6f}.
- Independent recomputation of posterior-derived scores/gates passed. Separate all-fold model refits using Cholesky passed; maximum absolute log-posterior difference {refit['max_abs_logposterior_difference']:.9g}; MBD block marginals checked {refit['matched_block_marginal_exact_checks']} times.

This is a historical same-House dense assessment, not a fresh blinded or cross-environment confirmation. E1 cross-environment HOLD remains unchanged. No dense source was removed, and H01 DEV/House03 were not accessed.
"""
    (out / "JTD_G1A_VERDICT_NOTE.md").write_bytes(note.encode("utf-8"))
    provenance = {"branch": "research/jtd-dense-g1a-v0", "pre_score_commit": "e0f042c03cd98fc0f8e5ef9c727910885d8fb3e1",
                  "a0_decision": "JTD_G1A_A0_COMPATIBLE", "null_keys_frozen_before_scoring": True,
                  "scientific_decision": result["decision"], "new_plume_runs": 0,
                  "vm_scoring_checkout": "/home/zyc/jtd_g1a_repo_20260925",
                  "vm_scoring_commit": "e0f042c03cd98fc0f8e5ef9c727910885d8fb3e1",
                  "vm_raw_bank": "/home/zyc/cess_d1r_168x16_reference_20260925",
                  "independent_array_recomputation": verify["independent_recomputation"],
                  "independent_model_refits": refit["independent_model_refits"],
                  "review_boundary": "Same House02/3,5-1_slow frozen bank; no fresh blinded target or cross-environment confirmation."}
    (out / "JTD_G1A_PROVENANCE.json").write_bytes((json.dumps(provenance, indent=2, sort_keys=True)+"\n").encode("utf-8"))
    print("JTD_G1A_EVIDENCE_MANIFESTS_COMPLETE")


if __name__ == "__main__":
    main()
