#!/usr/bin/env python3
"""Preregistered verdict for H02_RECONSTRUCTED_CHALLENGE_V1.

This replaces the lost legacy hard-28 as the current H02 falsification gate.
It does NOT recreate or relabel the historical 28-case product.

Required CSV columns:
  case_id,cluster_id,base_margin,method_margin,
  source_shuffle_margin,observation_shuffle_margin,
  member_identity_destruction_margin,false_confident_collapse

If audit JSON declares `temporal_marker_claimed=true`, CSV must also contain:
  time_reverse_margin

Required audit JSON booleans:
  provenance_pass
  selection_outcome_blind
  forbidden_feature_audit_pass
  test_not_used_for_tuning
  negative_controls_frozen_before_outcomes
Optional for a proximal/host-aware bridge:
  r_candidate_independent

Frozen advancement criteria from
`docs/H02_LEGACY_HARD28_PROVENANCE_LOSS_AND_REPLACEMENT_20260827.md`:
  * >=18 eligible context atoms;
  * >=3 independent run/seed clusters;
  * real mean and median margin change >0;
  * >=70% of clusters have positive mean margin change;
  * every destruction-control mean gain <=50% of the real mean gain;
  * zero false-confident-collapse flags;
  * all provenance/data-contract audits pass.
"""
from __future__ import annotations
import argparse,csv,json
from pathlib import Path
import numpy as np

MIN_ATOMS=18
MIN_CLUSTERS=3
MIN_POSITIVE_CLUSTER_FRACTION=0.70
MAX_CONTROL_GAIN_FRACTION=0.50


def as_bool(x):
    return str(x).strip().lower() in {"1","true","yes","y"}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("csv",type=Path)
    ap.add_argument("--audit-json",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()

    audit=json.loads(a.audit_json.read_text(encoding="utf-8"))
    with a.csv.open(newline="",encoding="utf-8-sig") as f:
        rows=list(csv.DictReader(f))
    required=["case_id","cluster_id","base_margin","method_margin",
              "source_shuffle_margin","observation_shuffle_margin",
              "member_identity_destruction_margin","false_confident_collapse"]
    if audit.get("temporal_marker_claimed") is True:
        required.append("time_reverse_margin")
    if not rows or any(k not in rows[0] for k in required):
        raise ValueError(f"CSV requires columns {tuple(required)}")

    def col(name):
        x=np.asarray([float(r[name]) for r in rows],dtype=float)
        if not np.all(np.isfinite(x)): raise ValueError(f"nonfinite {name}")
        return x

    base=col("base_margin")
    method=col("method_margin")
    real=method-base
    controls={
        "source_shuffle":col("source_shuffle_margin")-base,
        "observation_shuffle":col("observation_shuffle_margin")-base,
        "member_identity_destruction":col("member_identity_destruction_margin")-base,
    }
    if audit.get("temporal_marker_claimed") is True:
        controls["time_reverse"]=col("time_reverse_margin")-base

    clusters={}
    for i,r in enumerate(rows): clusters.setdefault(str(r["cluster_id"]),[]).append(i)
    cluster_delta={k:float(np.mean(real[np.asarray(v,dtype=int)])) for k,v in clusters.items()}
    positive_clusters=sum(v>0 for v in cluster_delta.values())
    positive_cluster_fraction=positive_clusters/max(len(cluster_delta),1)

    real_mean=float(np.mean(real)); real_median=float(np.median(real))
    control_means={k:float(np.mean(v)) for k,v in controls.items()}
    control_ok=all(v <= MAX_CONTROL_GAIN_FRACTION*max(real_mean,0.0) for v in control_means.values())
    collapse_count=sum(as_bool(r["false_confident_collapse"]) for r in rows)

    mandatory=("provenance_pass","selection_outcome_blind","forbidden_feature_audit_pass",
               "test_not_used_for_tuning","negative_controls_frozen_before_outcomes")
    audit_ok=all(audit.get(k) is True for k in mandatory)
    if "r_candidate_independent" in audit:
        audit_ok = audit_ok and audit.get("r_candidate_independent") is True

    criteria={
        "eligible_atoms_ge_18":len(rows)>=MIN_ATOMS,
        "independent_clusters_ge_3":len(cluster_delta)>=MIN_CLUSTERS,
        "mean_margin_delta_gt_0":real_mean>0,
        "median_margin_delta_gt_0":real_median>0,
        "positive_cluster_fraction_ge_0p70":positive_cluster_fraction>=MIN_POSITIVE_CLUSTER_FRACTION,
        "destruction_controls_retain_at_most_half_gain":control_ok,
        "temporal_control_present_if_claimed":not audit.get("temporal_marker_claimed",False) or "time_reverse" in controls,
        "zero_false_confident_collapse":collapse_count==0,
        "audit_pass":audit_ok,
    }
    go=all(criteria.values())
    out={
        "contract":"H02_RECONSTRUCTED_CHALLENGE_V1_VERDICT",
        "legacy_hard28_recreated":False,
        "temporal_marker_claimed":bool(audit.get("temporal_marker_claimed",False)),
        "atoms":len(rows),
        "clusters":len(cluster_delta),
        "real_mean_margin_delta":real_mean,
        "real_median_margin_delta":real_median,
        "positive_clusters":positive_clusters,
        "positive_cluster_fraction":positive_cluster_fraction,
        "cluster_mean_margin_delta":cluster_delta,
        "control_mean_margin_delta":control_means,
        "false_confident_collapse_count":collapse_count,
        "criteria":criteria,
        "verdict":"H02_RECONSTRUCTED_CHALLENGE_GO_TO_FULL_MULTI_SEED" if go else "H02_RECONSTRUCTED_CHALLENGE_NOT_GO",
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,indent=2),encoding="utf-8")
    print(json.dumps(out,indent=2))

if __name__=="__main__": main()
