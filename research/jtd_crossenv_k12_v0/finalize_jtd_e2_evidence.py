#!/usr/bin/env python3
"""Write final E2 STOP provenance and SHA256 inventories without changing science."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def manifest(path:Path,records:dict[str,Path])->None:
    lines=["role\tbytes\tsha256\tpath"]
    for role,file in sorted(records.items()):
        lines.append(f"{role}\t{file.stat().st_size}\t{sha(file)}\t{file}")
    path.write_bytes(("\n".join(lines)+"\n").encode("utf-8"))


def main()->None:
    p=argparse.ArgumentParser()
    p.add_argument("--repo",type=Path,required=True)
    a=p.parse_args()
    repo=a.repo.resolve(); evidence=repo/"evidence/jtd_e2_20260925"
    result=json.loads((evidence/"JTD_E2_RESULT.json").read_text(encoding="utf-8"))
    independent=json.loads((evidence/"JTD_E2_INDEPENDENT_RECOMPUTATION.json").read_text(encoding="utf-8"))
    preverify=json.loads((evidence/"JTD_E2_PRE_TARGET_INDEPENDENT_VERIFICATION.json").read_text(encoding="utf-8"))
    rawverify=json.loads((evidence/"JTD_E2_RAW_ARCHIVE_VERIFICATION.json").read_text(encoding="utf-8"))
    assert result["decision"]==independent["decision"]
    assert preverify["independent_pre_target_model_refit"]=="PASS" and rawverify["raw_archive_validation"]=="PASS"
    inputs={
        "initial_pre_run_lock":evidence/"JTD_E2_INITIAL_LOCK.json",
        "all_180_seed_plan":evidence/"JTD_E2_SEED_PLAN_180.tsv",
        "historical_open_six_reference_tensor":evidence/"JTD_E2_EXISTING_6_REFERENCE_10x30.npy",
        "new_108_reference_tensor":evidence/"JTD_E2_NEW_REFERENCE_10x30.npy",
        "frozen_12_reference_tensor":evidence/"JTD_E2_REFERENCE_12x10x30.npy",
        "pre_target_model_lock":evidence/"JTD_E2_MODEL_LOCK.npz",
        "pre_target_null_model_lock":evidence/"JTD_E2_NULL_MODEL_LOCK.npz",
        "pre_target_lock":evidence/"JTD_E2_PRE_TARGET_LOCK.json",
        "fresh_72_target_tensor":evidence/"JTD_E2_FRESH_TARGET_10x30.npy",
        "new_raw_180_archive":evidence/"JTD_E2_RAW_180_20260925.tar.gz",
        "cross_house_source_contract":repo/"evidence/environment_level_benchmark_v0/e1/E1_HOUSE_SOURCE_PANELS.tsv",
        "cross_house_probe_contract":repo/"evidence/environment_level_benchmark_v0/e1/E1_HOUSE_PROBE_CONTRACTS.tsv",
        "E2_open_reference_index":repo/"evidence/environment_level_benchmark_v0/e2/E2_OPEN_DISCOVERY_INDEX.tsv",
        "E1_historical_target_manifest":repo/"evidence/jtd_e1_20260925/JTD_E1_TARGET_MANIFEST.tsv",
    }
    code={f.name:f for f in (repo/"research/jtd_crossenv_k12_v0").glob("*.py")}
    code.update({f.name:f for f in (repo/"research/jtd_crossenv_k12_v0").glob("*.sh")})
    code.update({f.name:f for f in (repo/"research/jtd_crossenv_k12_v0").glob("*.md")})
    outputs={f.name:f for f in evidence.iterdir() if f.is_file() and f.name not in (
        "JTD_E2_INPUT_SHA256.tsv","JTD_E2_CODE_SHA256.tsv","JTD_E2_OUTPUT_SHA256.tsv",
        "JTD_E2_PROVENANCE.json","JTD_E2_VERDICT_NOTE.md")}
    manifest(evidence/"JTD_E2_INPUT_SHA256.tsv",inputs)
    manifest(evidence/"JTD_E2_CODE_SHA256.tsv",code)
    manifest(evidence/"JTD_E2_OUTPUT_SHA256.tsv",outputs)
    note=f"""# JTD-E2 equal-depth fresh confirmation

Frozen decision: `{result['decision']}`. Gates: `{result['gates']}`.

All 108 added references and 72 genuinely fresh targets completed. The 12-reference model, nulls, source order, seed plan and G1–G6 rules were committed before the first E2 target.

| OPEN environment | FULL NLL | BP NLL | MBD NLL | FULL−BP advantage ΔBP | FULL−MBD advantage ΔMBD |
|---|---:|---:|---:|---:|---:|
"""
    for row in result["environment_summaries"]:
        note+=(f"| {row['house']} / {row['wind']} | {row['full_mean_nll']:.6f} | {row['bp_mean_nll']:.6f} | "
               f"{row['mbd_mean_nll']:.6f} | {row['mean_delta_bp']:+.6f} | {row['mean_delta_mbd']:+.6f} |\n")
    note+=f"""
Pooled ΔBP={result['delta_bp']['mean']:+.6f}, 95% environment-source panel interval {result['delta_bp']['ci_95_environment_source_panel']}; pooled ΔMBD={result['delta_mbd']['mean']:+.6f}, interval {result['delta_mbd']['ci_95_environment_source_panel']}.

Positive units: BP {result['delta_bp']['positive_units']}/18 ({result['delta_bp']['positive_units_per_environment']} by environment); MBD {result['delta_mbd']['positive_units']}/18 ({result['delta_mbd']['positive_units_per_environment']}).

The 20% trimmed BP effect is {result['delta_bp']['trimmed_20_mean']:+.9f}; the 20% trimmed MBD effect is {result['delta_mbd']['trimmed_20_mean']:+.9f}. E2-G1 through G6 fail under the preregistered inequalities. No threshold or model rescue was run.

Independent checks: all 72 fresh raw cubes re-extracted exactly; 180 new raw cubes archived and verified; 18 FULL/BP/MBD/DIAG model groups and all 3,600 null Gaussian models refit before target; 14,400 null SHA keys checked; posterior scores, spatial metrics, 10,000 bootstrap draws and decision recomputed after target.

Scope: only the three OPEN environments. H01 DEV and all House03 remained sealed. G1A remains a valid historical House02 dense finding, while this cross-environment STOP retires JTD as the main-innovation route under the frozen charter.
"""
    (evidence/"JTD_E2_VERDICT_NOTE.md").write_bytes(note.encode("utf-8"))
    provenance={"branch":"research/jtd-crossenv-k12-confirmation-v0",
                "initial_lock_commit":"ecb435ccb12834a481753c22714ff0001c71db51",
                "reference_infrastructure_patch_commit":"8b5318dbe0541b688c1e6f9bbc69b66edd433750",
                "pre_target_lock_commit":"6b1262a3865a11810e26a8bd44d0683c076501ae",
                "initial_lock_sha256":sha(evidence/"JTD_E2_INITIAL_LOCK.json"),
                "pre_target_lock_sha256":sha(evidence/"JTD_E2_PRE_TARGET_LOCK.json"),
                "new_reference_runs":108,"new_fresh_target_runs":72,
                "science_decision":result["decision"],"model_or_gate_changed_after_target":False,
                "vm_data_root":"/home/zyc/JTD_E2_K12_180_RUNS_20260925",
                "raw_archive_sha256":rawverify["archive_sha256"],
                "independent_pre_target_refit":preverify["independent_pre_target_model_refit"],
                "independent_post_target_recomputation":independent["independent_recomputation"],
                "sealed_environment_data_read":False}
    (evidence/"JTD_E2_PROVENANCE.json").write_bytes((json.dumps(provenance,indent=2,sort_keys=True)+"\n").encode("utf-8"))
    print("JTD_E2_EVIDENCE_FINALIZED",result["decision"])


if __name__=="__main__":
    main()
