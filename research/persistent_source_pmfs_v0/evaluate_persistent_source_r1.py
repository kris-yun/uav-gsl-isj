#!/usr/bin/env python3
import csv, json, math, hashlib, pathlib, sys, statistics

if len(sys.argv) != 4:
    raise SystemExit("usage: evaluate_persistent_source_r1.py OUT_DIR FROZEN_TRUTH_JSON RESULT_JSON")
out = pathlib.Path(sys.argv[1])
truth_path = pathlib.Path(sys.argv[2])
result_path = pathlib.Path(sys.argv[3])
freeze = out / "SCORES_SHA256.txt"
if not freeze.exists():
    raise SystemExit("scores are not frozen; missing SCORES_SHA256.txt")

with truth_path.open() as f:
    prior = json.load(f)
truth_id = prior["arms"]["C"]["truth_candidate_id"]
tx, ty = float(prior["source_x"]), float(prior["source_y"])

with (out/"candidate_summary.csv").open(newline="") as f:
    rows = list(csv.DictReader(f))

def rank_for(col):
    ordered = sorted(rows, key=lambda r:(-float(r[col]), r["candidate_id"]))
    rank = next(i+1 for i,r in enumerate(ordered) if r["candidate_id"]==truth_id)
    top = ordered[0]
    err = math.hypot(float(top["center_x"])-tx, float(top["center_y"])-ty)
    return rank, top["candidate_id"], err, ordered

def avg_rank(vals):
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    ranks=[0.0]*len(vals); k=0
    while k<len(order):
        j=k+1
        while j<len(order) and vals[order[j]]==vals[order[k]]: j+=1
        r=(k+j-1)/2+1
        for z in order[k:j]: ranks[z]=r
        k=j
    return ranks

def pearson(a,b):
    ma=sum(a)/len(a); mb=sum(b)/len(b)
    num=sum((x-ma)*(y-mb) for x,y in zip(a,b))
    da=sum((x-ma)**2 for x in a); db=sum((y-mb)**2 for y in b)
    return num/math.sqrt(da*db) if da and db else float("nan")

R=rank_for("resampled_mean")
C=rank_for("fixed_center_mean")
P=rank_for("persistent_marginal_mean")

rvals=[float(r["resampled_mean"]) for r in rows]
pvals=[float(r["persistent_marginal_mean"]) for r in rows]
rho=pearson(avg_rank(rvals),avg_rank(pvals))

rankR={r["candidate_id"]:i+1 for i,r in enumerate(R[3])}
rankP={r["candidate_id"]:i+1 for i,r in enumerate(P[3])}
displacements=[abs(rankR[k]-rankP[k]) for k in rankR]

truth_row=next(r for r in rows if r["candidate_id"]==truth_id)
area_groups={}
for r in rows:
    area=int(r["size_i"])*int(r["size_j"])
    area_groups.setdefault(area,[]).append({
        "id":r["candidate_id"],
        "delta_score":float(r["persistent_marginal_mean"])-float(r["resampled_mean"]),
        "delta_rank":rankR[r["candidate_id"]]-rankP[r["candidate_id"]],
    })

decision="MECHANISM_NULL_OR_ADVERSE"
if P[0] < R[0] and P[2] <= R[2] + 1e-12:
    decision="MECHANISM_SIGNAL_POSITIVE"
    if R[0]-P[0] >= 10:
        decision="MECHANISM_SIGNAL_STRONG"

result={
    "contract":"PERSISTENT_SOURCE_PMFS_R1_V0",
    "development_only":True,
    "truth_candidate_id":truth_id,
    "truth_xy":[tx,ty],
    "ranks":{"resampled":R[0],"fixed_center":C[0],"persistent_marginal":P[0]},
    "truth_scores":{
        "resampled":float(truth_row["resampled_mean"]),
        "fixed_center":float(truth_row["fixed_center_mean"]),
        "persistent_marginal":float(truth_row["persistent_marginal_mean"]),
    },
    "top1":{
        "resampled":{"candidate":R[1],"center_error_m":R[2]},
        "fixed_center":{"candidate":C[1],"center_error_m":C[2]},
        "persistent_marginal":{"candidate":P[1],"center_error_m":P[2]},
    },
    "persistent_minus_resampled_truth_rank_improvement":R[0]-P[0],
    "spearman_resampled_vs_persistent":rho,
    "candidate_rank_abs_displacement_median":statistics.median(displacements),
    "candidate_rank_abs_displacement_max":max(displacements),
    "area_groups":area_groups,
    "one_by_one":[g for g in area_groups.get(1,[])],
    "decision":decision,
}
result_path.write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
print(json.dumps(result,indent=2,sort_keys=True))
