#!/usr/bin/env python3
"""Post-hoc oracle mechanism audit for one-sided transport falsification.

This is NOT the deployable SITER model. It uses completed R1 Oracle-2D and
Oracle-3D scores to test whether a one-sided transport penalty can preserve the
useful false-source suppression while preventing 3-D-only positive promotions.

score_safe = min(score_2d, score_3d)
           = score_2d - max(0, score_2d-score_3d)

Inputs are already-unblinded development evidence, so results are mechanism
evidence only.
"""
import csv, json, argparse
from pathlib import Path

def rank(scores, truth, tol=1e-12):
    ahead=sum(v > truth+tol for v in scores)
    ties=sum(abs(v-truth) <= tol for v in scores)
    return 1.0 + ahead + 0.5*ties, 1 + ahead + ties

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--r1-result", required=True)
    ap.add_argument("--out", required=True)
    a=ap.parse_args()

    with open(a.candidates, newline="") as f:
        rows=list(csv.DictReader(f, delimiter="\t"))
    with open(a.r1_result) as f:
        r1=json.load(f)

    result={"method":"oracle one-sided contradiction screen",
            "formula":"min(oracle2d,oracle3d)",
            "confirmatory":False,
            "cases":[]}

    for case in r1["cases"]:
        name=case["case"]
        rr=[r for r in rows if r["case"]==name]
        t2=float(case["arms"]["oracle2d"]["truth_log_score"])
        t3=float(case["arms"]["oracle3d"]["truth_log_score"])
        ts=min(t2,t3)
        safe=[min(float(r["score2d"]),float(r["score3d"])) for r in rr]
        mid,pess=rank(safe,ts)
        margin=ts-max(safe)
        base=float(case["arms"]["oracle2d"]["truth_leaf_midrank"])
        margin2=float(case["arms"]["oracle2d"]["source_margin"])
        harmful=sum(
            float(r["score2d"]) <= t2+1e-12 and
            min(float(r["score2d"]),float(r["score3d"])) > ts+1e-12
            for r in rr)
        repaired=sum(
            float(r["score2d"]) > t2+1e-12 and
            min(float(r["score2d"]),float(r["score3d"])) <= ts+1e-12
            for r in rr)
        result["cases"].append({
            "case":name,
            "oracle2d_rank":base,
            "safe_rank":mid,
            "safe_pessimistic_rank":pess,
            "rank_improvement":base-mid,
            "oracle2d_margin":margin2,
            "safe_margin":margin,
            "margin_improvement":margin-margin2,
            "repaired_crossings":repaired,
            "harmful_crossings":harmful
        })

    Path(a.out).write_text(json.dumps(result,indent=2)+"\n")

if __name__=="__main__":
    main()
