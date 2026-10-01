#!/usr/bin/env python3
"""Exact PMFS final-source-update observation map from two archived snapshots.

This reconstructs the interval contribution in the additive Native PMFS
(logOdds, omega) state. It does not reconstruct arbitrary time windows.
"""
import argparse, csv, math
from pathlib import Path

def load(path):
    with open(path, newline="") as f:
        rows=list(csv.DictReader(f))
    return rows

def logit(p):
    return math.log(p/(1.0-p))

def logistic(x):
    if x >= 0:
        z=math.exp(-x); return 1.0/(1.0+z)
    z=math.exp(x); return z/(1.0+z)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--update4", required=True)
    ap.add_argument("--update5", required=True)
    ap.add_argument("--prior", required=True, type=float)
    ap.add_argument("--confidence-weight", required=True, type=float)
    ap.add_argument("--out", required=True)
    a=ap.parse_args()

    r4=load(a.update4); r5=load(a.update5)
    if len(r4)!=len(r5):
        raise SystemExit("row count mismatch")
    l0=logit(a.prior)
    max_l_recompose=max_w_recompose=max_c_recompute=0.0
    tiny_negative=0
    out=[]
    for x,y in zip(r4,r5):
        for k in ("cell_index","grid_i","grid_j","x","y","occupancy"):
            if x[k] != y[k]:
                raise SystemExit(f"metadata mismatch at {k}: {x[k]} != {y[k]}")
        L4=float(x["logOdds"]); L5=float(y["logOdds"])
        w4=float(x["omega"]); w5=float(y["omega"])
        wr=w5-w4
        if wr < -1e-12:
            raise SystemExit(f"omega decreased at cell {x['cell_index']}: {wr}")
        if wr < 0:
            wr=0.0; tiny_negative += 1
        Lr=l0+(L5-L4)
        cr=1.0-math.exp(-wr/(a.confidence_weight*a.confidence_weight))
        pr=logistic(Lr)

        max_l_recompose=max(max_l_recompose,abs((L4+(Lr-l0))-L5))
        max_w_recompose=max(max_w_recompose,abs((w4+wr)-w5))
        c5_re=1.0-math.exp(-w5/(a.confidence_weight*a.confidence_weight))
        max_c_recompute=max(max_c_recompute,abs(c5_re-float(y["confidence"])))

        row=dict(y)
        row["probability"]=format(pr,".17g")
        row["logOdds"]=format(Lr,".17g")
        row["confidence"]=format(cr,".17g")
        row["omega"]=format(wr,".17g")
        row["distanceFromRobot"]="nan"
        row["originalPropagationDirection_x"]="nan"
        row["originalPropagationDirection_y"]="nan"
        out.append(row)

    if max_l_recompose > 1e-12 or max_w_recompose > 1e-12 or max_c_recompute > 1e-12:
        raise SystemExit(
            f"integrity failure L={max_l_recompose} omega={max_w_recompose} conf={max_c_recompute}")

    fields=list(r5[0].keys())
    with open(a.out,"w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields)
        w.writeheader(); w.writerows(out)

    print({
        "rows":len(out),
        "tiny_negative_omega_clamped":tiny_negative,
        "max_logOdds_recompose_abs":max_l_recompose,
        "max_omega_recompose_abs":max_w_recompose,
        "max_confidence_recompute_abs":max_c_recompute,
    })

if __name__=="__main__":
    main()
