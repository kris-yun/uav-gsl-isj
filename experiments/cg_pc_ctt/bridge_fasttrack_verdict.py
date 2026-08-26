#!/usr/bin/env python3
"""Fast-track decision from H02 hard-28 bridge evidence to full multi-seed closed loop.

This does not declare a paper claim. It answers only whether the frozen bridge
has enough falsification evidence to justify spending the next experiment on
the complete 3-House x 10-seed closed-loop matrix.

CSV required columns (28 rows expected):
  case_id,m1_margin,bridge_margin,z_shuffle_margin,source_shuffle_margin
Optional: time_reverse_margin

Frozen advance criteria:
  * exactly 28 hard cases;
  * mean and median (bridge_margin - m1_margin) > 0;
  * at least 19/28 cases improve (one-sided sign p<0.05);
  * each negative-control mean gain is <= 50% of the real bridge mean gain;
  * audit JSON says forbidden_feature_audit_pass, r_candidate_independent,
    test_not_used_for_tuning are all true.

If V2 global gate coverage on H02 is >=0.90, that gate is interpreted as a
model-side premise rather than a reliability selector; this alone does not
block the fast-track closed-loop test if the bridge criteria above pass.
"""
from __future__ import annotations
import argparse,csv,json
from math import comb
from pathlib import Path
import numpy as np

def sign_p(k,n): return sum(comb(n,i) for i in range(k,n+1))/float(2**n)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("csv",type=Path); ap.add_argument("--audit-json",type=Path,required=True); ap.add_argument("--gate-summary",type=Path,default=None); ap.add_argument("--out",type=Path,required=True); a=ap.parse_args()
    with a.csv.open(newline="") as f: rr=list(csv.DictReader(f))
    req=["m1_margin","bridge_margin","z_shuffle_margin","source_shuffle_margin"]
    if any(k not in rr[0] for k in req): raise ValueError(f"missing required columns {req}")
    n=len(rr); base=np.array([float(r["m1_margin"]) for r in rr]); br=np.array([float(r["bridge_margin"]) for r in rr]); d=br-base
    controls={"z_shuffle":np.array([float(r["z_shuffle_margin"]) for r in rr])-base,"source_shuffle":np.array([float(r["source_shuffle_margin"]) for r in rr])-base}
    if "time_reverse_margin" in rr[0]: controls["time_reverse"]=np.array([float(r["time_reverse_margin"]) for r in rr])-base
    mean=float(d.mean()); med=float(np.median(d)); improved=int(np.sum(d>0)); sp=sign_p(improved,n)
    control_means={k:float(v.mean()) for k,v in controls.items()}; erased=all(v<=0.5*max(mean,0.0) for v in control_means.values())
    audit=json.loads(a.audit_json.read_text()); audit_ok=all(audit.get(k) is True for k in ["forbidden_feature_audit_pass","r_candidate_independent","test_not_used_for_tuning"])
    gate_coverage=None; gate_role="UNKNOWN"
    if a.gate_summary:
        gs=json.loads(a.gate_summary.read_text()); gate_coverage=float(gs.get("coverage",float("nan"))); gate_role="MODEL_SIDE_PREMISE" if gate_coverage>=.90 else "RELIABILITY_SELECTOR_CANDIDATE"
    criteria={"exactly_28_cases":n==28,"mean_delta_margin_gt_0":mean>0,"median_delta_margin_gt_0":med>0,"improved_cases_ge_19":improved>=19,"sign_test_p_lt_0p05":sp<.05,"negative_controls_erase_at_least_half_gain":erased,"audit_pass":audit_ok}
    go=all(criteria.values())
    out={"contract":"CG_PC_CTT_BRIDGE_FASTTRACK_TO_CLOSED_LOOP_V1","n":n,"mean_delta_margin":mean,"median_delta_margin":med,"improved_cases":improved,"sign_test_one_sided_p":sp,"control_mean_delta":control_means,"gate_coverage":gate_coverage,"gate_role":gate_role,"criteria":criteria,"verdict":"BRIDGE_FASTTRACK_GO_TO_FULL_MULTI_SEED" if go else "BRIDGE_FASTTRACK_NO_GO"}
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(out,indent=2),encoding="utf-8"); print(json.dumps(out,indent=2))
if __name__=="__main__": main()
