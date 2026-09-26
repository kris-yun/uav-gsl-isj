#!/usr/bin/env python3
import argparse,csv,json,math,pathlib,statistics

def avg_rank(values):
    order=sorted(range(len(values)),key=lambda i:values[i])
    ranks=[0.0]*len(values);k=0
    while k<len(order):
        j=k+1
        while j<len(order) and values[order[j]]==values[order[k]]: j+=1
        rr=(k+j-1)/2+1
        for q in order[k:j]: ranks[q]=rr
        k=j
    return ranks
def pearson(a,b):
    ma=sum(a)/len(a); mb=sum(b)/len(b)
    num=sum((x-ma)*(y-mb) for x,y in zip(a,b))
    da=sum((x-ma)**2 for x in a); db=sum((y-mb)**2 for y in b)
    return num/math.sqrt(da*db) if da and db else float("nan")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--score-dir",required=True)
    ap.add_argument("--truth-json",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    sd=pathlib.Path(a.score_dir)
    if not (sd/"SCORES_SHA256.txt").exists(): raise SystemExit("scores not frozen")
    with open(sd/"candidate_scores.csv",newline="") as f: rows=list(csv.DictReader(f))
    truth=json.loads(pathlib.Path(a.truth_json).read_text())
    tid=truth["arms"]["C"]["truth_candidate_id"]
    tx,ty=float(truth["source_x"]),float(truth["source_y"])
    cols={
      "M":"native_recomputed_score",
      "S":"sensor_site_logscore",
      "Elog":"event_logscore",
      "Ebrier":"event_brier",
    }
    res={}
    orders={}
    for name,col in cols.items():
        order=sorted(rows,key=lambda r:(-float(r[col]),r["candidate_id"]))
        orders[name]=order
        rank=next(i+1 for i,r in enumerate(order) if r["candidate_id"]==tid)
        tr=next(r for r in rows if r["candidate_id"]==tid)
        top=order[0]
        err=math.hypot(float(top["center_x"])-tx,float(top["center_y"])-ty)
        res[name]={
          "truth_rank":rank,"truth_score":float(tr[col]),
          "top1_candidate":top["candidate_id"],"top1_center_error_m":err,
          "top10":[r["candidate_id"] for r in order[:10]]
        }
    mvals=[float(r[cols["M"]]) for r in rows]
    mr=avg_rank(mvals)
    for name in ["S","Elog","Ebrier"]:
        vals=[float(r[cols[name]]) for r in rows]
        res[name]["spearman_vs_M"]=pearson(mr,avg_rank(vals))
        rm={r["candidate_id"]:i+1 for i,r in enumerate(orders["M"])}
        rn={r["candidate_id"]:i+1 for i,r in enumerate(orders[name])}
        disp=[abs(rm[k]-rn[k]) for k in rm]
        res[name]["rank_abs_displacement_median"]=statistics.median(disp)
        res[name]["rank_abs_displacement_max"]=max(disp)

    imp={name:res["M"]["truth_rank"]-res[name]["truth_rank"] for name in ["S","Elog","Ebrier"]}
    spatial_ok=sum(res[name]["top1_center_error_m"]<=res["M"]["top1_center_error_m"]+1e-12
                   for name in ["S","Elog","Ebrier"])
    decision="EVIDENCE_PSEUDOREPLICATION_NULL_OR_ADVERSE"
    if all(imp[n]>0 for n in ["S","Elog","Ebrier"]) and imp["Elog"]>=10 and imp["Ebrier"]>=10 and spatial_ok>=2:
        decision="EVIDENCE_PSEUDOREPLICATION_SIGNAL_STRONG"
    elif ((imp["Elog"]>0 and imp["Ebrier"]>0 and
           res["Elog"]["top1_center_error_m"]<=res["M"]["top1_center_error_m"]+1e-12 and
           res["Ebrier"]["top1_center_error_m"]<=res["M"]["top1_center_error_m"]+1e-12)
          or (imp["S"]>=10 and imp["Elog"]>=0 and imp["Ebrier"]>=0)):
        decision="EVIDENCE_PSEUDOREPLICATION_SIGNAL_POSITIVE"

    out={
      "contract":"PMFS_EVIDENCE_PSEUDOREPLICATION_V0",
      "truth_candidate_id":tid,"truth_xy":[tx,ty],
      "arms":res,
      "truth_rank_improvement_vs_M":imp,
      "event_scores_direction_agree":(imp["Elog"]>0)==(imp["Ebrier"]>0),
      "decision":decision,
    }
    pathlib.Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True))
    print(json.dumps(out,indent=2,sort_keys=True))
if __name__=="__main__": main()
