#!/usr/bin/env python3
import argparse, csv, hashlib, json, math, os, pathlib, struct, sys

EXPECTED = {
    "measurement_events.csv":"f05114b558132a1c62d1ecf705d9bdd2f066905b9c48881b3457b9f0d9cd15e9",
    "measured_map_at_update.csv":"dee2f4e154860ae74bf9fd5375b4721864cdd96dc775badfbdc4ee56f2019eab",
    "C_candidate_scores.csv":"780366a446f4c27496b60939aec098d50d7ba6c516ac7f8b387b3b75f9469419",
}
DISC = 0.3
EPS = 1e-6

def sha256(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def rows(p):
    with open(p,newline='',encoding='utf-8') as f:
        return list(csv.DictReader(f))

def measured_prob(log_odds):
    x=float(log_odds)
    if x >= 0:
        e=math.exp(-x); return 1.0/(1.0+e)
    e=math.exp(x); return e/(1.0+e)

def load_f32(p,n):
    data=pathlib.Path(p).read_bytes()
    if len(data)!=4*n:
        raise RuntimeError(f"map byte count mismatch {p}: {len(data)} != {4*n}")
    return struct.unpack("<"+"f"*n,data)

def rank_values(vals, higher=True):
    order=sorted(range(len(vals)), key=lambda i: ((-vals[i]) if higher else vals[i], i))
    out=[0]*len(vals)
    for rank,i in enumerate(order,1): out[i]=rank
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--snapshot-dir",required=True)
    ap.add_argument("--c-scores",required=True)
    ap.add_argument("--maps-dir",required=True)
    ap.add_argument("--historical-manifest",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    sd=pathlib.Path(a.snapshot_dir); out=pathlib.Path(a.out)
    if out.exists(): raise SystemExit("output exists; refusing overwrite")
    out.mkdir(parents=True)

    inputs={
      "measurement_events.csv":sd/"measurement_events.csv",
      "measured_map_at_update.csv":sd/"measured_map_at_update.csv",
      "C_candidate_scores.csv":pathlib.Path(a.c_scores),
    }
    for name,p in inputs.items():
        got=sha256(p)
        if got!=EXPECTED[name]:
            raise RuntimeError(f"{name} sha mismatch: {got}")

    manifest=json.loads(pathlib.Path(a.historical_manifest).read_text())
    expected_maps=manifest["arms"]["C"]["candidate_map_sha256"]

    snap=rows(inputs["measured_map_at_update.csv"])
    events=rows(inputs["measurement_events.csv"])
    cand=rows(inputs["C_candidate_scores.csv"])
    if len(cand)!=87: raise RuntimeError(f"candidate count {len(cand)} != 87")
    n=len(snap)
    if n==0: raise RuntimeError("empty measured map")

    width=int(snap[0]["grid_width"]); height=int(snap[0]["grid_height"])
    if width*height!=n: raise RuntimeError("grid shape mismatch")
    free=[r["occupancy"]=="Free" for r in snap]
    mprob=[measured_prob(r["log_odds"]) for r in snap]
    conf=[float(r["confidence"]) for r in snap]

    event_data=[]
    unique_sites=[]
    seen=set()
    for e in events:
        i,j=int(e["robot_i"]),int(e["robot_j"])
        idx=j*width+i
        if not (0<=idx<n and free[idx]): raise RuntimeError("event outside free grid")
        hit=int(e["hit"])
        event_data.append((idx,hit,i,j))
        if idx not in seen:
            seen.add(idx); unique_sites.append(idx)

    out_rows=[]
    parity_diffs=[]
    clipped=0
    for c in cand:
        cid=c["candidate_id"]
        mp=pathlib.Path(a.maps_dir)/(pathlib.Path(c["map_file"]).name)
        if not mp.exists():
            # also allow map_file path relative to maps-dir parent
            q=pathlib.Path(a.maps_dir)/c["map_file"]
            if q.exists(): mp=q
            else: raise RuntimeError(f"missing map {cid}: {mp}")
        got=sha256(mp)
        exp=expected_maps.get(cid)
        if got!=exp: raise RuntimeError(f"map sha mismatch {cid}: {got} != {exp}")
        sim=load_f32(mp,n)

        logM=0.0
        for k in range(n):
            if not free[k]: continue
            f=1.0-conf[k]*DISC*abs(mprob[k]-sim[k])
            if not (f>0 and math.isfinite(f)): raise RuntimeError(f"invalid M factor {cid} cell {k}")
            logM += math.log(f)
        M=math.exp(logM)
        hist=float(c["source_score"])
        parity_diffs.append(abs(M-hist))

        logS=0.0
        for k in unique_sites:
            f=1.0-conf[k]*DISC*abs(mprob[k]-sim[k])
            if not (f>0 and math.isfinite(f)): raise RuntimeError(f"invalid S factor {cid} cell {k}")
            logS += math.log(f)

        elog=0.0; ebrier=0.0
        for k,h,_,_ in event_data:
            p=float(sim[k])
            q=min(1.0-EPS,max(EPS,p))
            if q!=p: clipped+=1
            elog += h*math.log(q)+(1-h)*math.log1p(-q)
            ebrier -= (h-p)*(h-p)

        out_rows.append({
            "candidate_id":cid,
            "origin_i":c["origin_i"],"origin_j":c["origin_j"],
            "size_i":c["size_i"],"size_j":c["size_j"],
            "center_x":c["center_x"],"center_y":c["center_y"],
            "native_historical_score":f"{hist:.21g}",
            "native_recomputed_score":f"{M:.21g}",
            "native_logscore":f"{logM:.21g}",
            "sensor_site_logscore":f"{logS:.21g}",
            "event_logscore":f"{elog:.21g}",
            "event_brier":f"{ebrier:.21g}",
        })

    maxdiff=max(parity_diffs)
    parity={"candidate_count":len(cand),"max_abs_native_score_diff":maxdiff,
            "tolerance":1e-10,"pass":maxdiff<=1e-10}
    (out/"native_parity.json").write_text(json.dumps(parity,indent=2,sort_keys=True))
    if not parity["pass"]: raise RuntimeError(f"native parity fail {maxdiff}")

    fields=list(out_rows[0].keys())
    with (out/"candidate_scores.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(out_rows)

    audit={
      "truth_read":False,
      "raw_event_count":len(event_data),
      "hit_count":sum(h for _,h,_,_ in event_data),
      "miss_count":len(event_data)-sum(h for _,h,_,_ in event_data),
      "unique_robot_site_count":len(unique_sites),
      "unique_robot_sites":[{"index":k,"i":k%width,"j":k//width} for k in unique_sites],
      "free_cell_count":sum(free),
      "confidence_gt_0":sum(x>0 for x in conf),
      "confidence_gt_0p01":sum(x>0.01 for x in conf),
      "confidence_gt_0p1":sum(x>0.1 for x in conf),
      "event_probability_clip_count":clipped,
      "event_probability_clip_epsilon":EPS,
      "source_discrimination_power":DISC,
    }
    (out/"event_support_audit.json").write_text(json.dumps(audit,indent=2,sort_keys=True))

    files=["candidate_scores.csv","event_support_audit.json","native_parity.json"]
    with (out/"SCORES_SHA256.txt").open("w") as f:
        for name in files:
            f.write(f"{sha256(out/name)}  {name}\n")
        f.write(f"{sha256(pathlib.Path(__file__))}  {pathlib.Path(__file__).name}\n")
    print(json.dumps({"status":"SOURCE_BLIND_SCORE_FREEZE_READY",**audit,**parity},indent=2))

if __name__=="__main__":
    main()
