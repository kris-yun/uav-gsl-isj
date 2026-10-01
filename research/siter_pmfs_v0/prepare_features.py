"""Source-blind archived Native reconstruction and fixed SITER descriptors.

Does not read evaluator truth, Oracle scores, concentration or protected data.
"""
import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path

import numpy as np
from scipy.stats import rankdata

EPS = 1e-12
NAMES = ["native_badness", "abs_residual_mean", "abs_residual_q50",
         "abs_residual_q90", "unsupported_hit", "miss_prediction",
         "support_disagreement", "leaf_area", "upwind_violation",
         "crossflow_dispersion", "alongflow_asymmetry", "wind_incoherence",
         "downwind_miss_prediction"]


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False)+"\n")


def safe_ratio(numerator, denominator):
    return float(numerator / denominator) if denominator > 0 else 0.0


def weighted_quantile(values, weights, fraction):
    total = weights.sum()
    if total <= 0:
        return 0.0
    order = np.argsort(values, kind="stable")
    pos = np.searchsorted(np.cumsum(weights[order]), fraction*total, side="left")
    return float(values[order[min(pos, len(order)-1)]])


def features(scores, p, c, h, wind, xy, source_xy, owner, prior):
    """No label argument. Candidate axis is the complete active-leaf partition."""
    n = len(scores)
    gas = c * np.maximum(p-prior, 0)
    miss = c * (1-p)
    direction = wind / (np.linalg.norm(wind, axis=1)[:, None]+EPS)
    badness = 1-(rankdata(scores, method="average")-0.5)/n
    result = np.zeros((n, len(NAMES)))
    for k in range(n):
        residual = p-h[k]
        ar = np.abs(residual)
        delta = xy-source_xy[k]
        along = np.sum(delta*direction, axis=1)
        across = np.linalg.norm(delta-along[:, None]*direction, axis=1)
        wr = c*ar
        center = safe_ratio(np.dot(wr, across), wr.sum())
        dispersion = math.sqrt(max(0, safe_ratio(np.dot(wr, (across-center)**2), wr.sum())))
        overlap_denom = np.dot(c, np.maximum(p,h[k]))
        result[k] = [badness[k], safe_ratio(np.dot(c,ar), c.sum()),
                     weighted_quantile(ar,c,0.5), weighted_quantile(ar,c,0.9),
                     safe_ratio(np.dot(gas,h[k]==0),gas.sum()),
                     safe_ratio(np.dot(miss,h[k]),miss.sum()),
                     1-safe_ratio(np.dot(c,np.minimum(p,h[k])),overlap_denom) if overlap_denom>0 else 0,
                     float(np.mean(owner==k)),
                     safe_ratio(np.dot(gas,along<0),gas.sum()), dispersion,
                     safe_ratio(abs(np.dot(c*residual,along)),np.dot(c,np.abs(residual*along))),
                     max(0,1-safe_ratio(np.linalg.norm(np.sum(gas[:,None]*direction,axis=0)),gas.sum())) if gas.sum()>0 else 0,
                     safe_ratio(np.dot(miss*h[k],along>0),miss.sum())]
    assert np.isfinite(result).all() and (result >= -1e-14).all()
    return result


def prepare(root, out):
    out.mkdir(parents=True, exist_ok=True)
    declared=json.loads((root/"SHA256SUMS.json").read_text())
    verified=[]
    def verify(path):
        relative=path.relative_to(root).as_posix()
        digest=sha(path)
        assert relative in declared and digest==declared[relative], relative
        verified.append({"path":relative,"sha256":digest,"bytes":path.stat().st_size})
    datasets=[]
    arrays={}
    for house in ("House01","House02","House03"):
        for seed in (0,1):
            case=f"{house}_seed{seed}"
            run=root/"native"/f"{case}_off_off"
            bank=run/"context_bank"
            timing_path=bank/"source_update_timing.csv"
            verify(timing_path)
            params={}
            for file in sorted((run/"resolved_runtime").glob("launch_params_*")):
                verify(file)
                for line in file.read_text().splitlines():
                    m=re.match(r"\s+(hitPriorProbability|sourceDiscriminationPower):\s*(.*?)\s*$",line)
                    if m:
                        value=float(m[2])
                        assert m[1] not in params or params[m[1]]==value
                        params[m[1]]=value
            assert set(params)=={"hitPriorProbability","sourceDiscriminationPower"}
            timings=read_csv(timing_path)
            assert [int(t["source_update_id"]) for t in timings]==[1,2,3,4,5]
            for timing in timings:
                update=int(timing["source_update_id"])
                assert float(timing["sim_time"])<=300
                key=f"{case}_u{update}"
                folder=bank/f"source_update_{update:04d}"
                for name in ("measured_hit_probability.csv","candidate_manifest.csv","candidate_support_alignment.csv","estimated_wind.csv","source_posterior.csv"):
                    verify(folder/name)
                cells=sorted((r for r in read_csv(folder/"measured_hit_probability.csv") if r["occupancy"]=="Free"),key=lambda r:int(r["cell_index"]))
                idx=np.array([int(r["cell_index"]) for r in cells])
                index={int(v):k for k,v in enumerate(idx)}
                ij=np.array([[int(r["grid_i"]),int(r["grid_j"])] for r in cells])
                xy=np.array([[float(r["x"]),float(r["y"])] for r in cells])
                p=np.array([float(r["probability"]) for r in cells])
                c=np.array([float(r["confidence"]) for r in cells])
                manifests=read_csv(folder/"candidate_manifest.csv")
                byid={r["candidate_id"]:r for r in manifests}
                assert len(byid)==len(manifests)
                owner_id=[]
                for i,j in ij:
                    covers=[r for r in manifests if int(r["origin_i"])<=i<int(r["origin_i"])+int(r["size_i"]) and int(r["origin_j"])<=j<int(r["origin_j"])+int(r["size_j"])]
                    assert covers
                    owner_id.append(min(covers,key=lambda r:(int(r["size_i"])*int(r["size_j"]),r["candidate_id"]))["candidate_id"])
                active=sorted(set(owner_id))
                candidate_index={cid:k for k,cid in enumerate(active)}
                owner=np.array([candidate_index[cid] for cid in owner_id])
                hit=np.zeros((len(active),len(cells)))
                all_logs={cid:[] for cid in byid}
                seen={cid:set() for cid in byid}
                for r in read_csv(folder/"candidate_support_alignment.csv"):
                    cid=r["candidate_id"]; v=int(r["cell_index"])
                    assert cid in byid
                    if v not in index:
                        continue
                    pos=index[v]
                    assert v not in seen[cid]; seen[cid].add(v)
                    assert float(r["measured_probability"])==p[pos]
                    assert float(r["measured_confidence"])==c[pos]
                    value=float(r["simulated_hit_probability"])
                    factor=1-c[pos]*abs(p[pos]-value)*params["sourceDiscriminationPower"]
                    assert factor>0 and math.isfinite(factor)
                    all_logs[cid].append(math.log(factor))
                    if cid in candidate_index:
                        hit[candidate_index[cid],pos]=value
                for cid in active:
                    assert set(idx[c>0]).issubset(seen[cid]), (key,cid,"missing positive-confidence cell")
                scores=np.array([sum(all_logs[cid]) for cid in active])
                raw=np.exp(scores[owner]-scores.max()); posterior=raw/raw.sum()
                exported={int(r["cell_index"]):float(r["source_probability"]) for r in read_csv(folder/"source_posterior.csv")}
                assert set(exported)==set(idx)
                original=np.array([exported[int(v)] for v in idx]); original/=original.sum()
                deviation=float(np.max(abs(posterior-original)))
                assert deviation<=1e-10, (key,deviation)
                winds={int(r["cell_index"]):[float(r["wind_x"]),float(r["wind_y"])] for r in read_csv(folder/"estimated_wind.csv")}
                assert set(idx).issubset(winds)
                wind=np.array([winds[int(v)] for v in idx])
                source=[]
                rectangles=[]
                fallback=[]
                for cid in active:
                    r=byid[cid]
                    try:
                        point=[float(r["native_source_x"]),float(r["native_source_y"])]
                    except (ValueError,KeyError):
                        point=[float("nan")]*2
                    if not np.isfinite(point).all():
                        point=[float(r["center_x"]),float(r["center_y"])];fallback.append(cid)
                    source.append(point)
                    rectangles.append([int(r[k]) for k in ("origin_i","origin_j","size_i","size_j")])
                source=np.array(source)
                x=features(scores,p,c,hit,wind,xy,source,owner,params["hitPriorProbability"])
                for name,value in {"X":x,"scores":scores,"p":p,"c":c,"hit":hit,"wind":wind,"xy":xy,"source":source,"owner":owner,"ij":ij,"idx":idx,"native_posterior":original,"rectangles":np.array(rectangles)}.items():
                    arrays[f"{key}__{name}"]=value
                datasets.append({"key":key,"case":case,"house":house,"seed":seed,"update":update,"timing":timing,"candidate_ids":active,"parameters":params,"candidate_point_fallback":fallback,"native_parity_max_abs":deviation})
                print(key,len(active),deviation,flush=True)
    np.savez_compressed(out/"SOURCE_BLIND_FEATURE_DATA.npz",**arrays)
    write_json(out/"SOURCE_BLIND_UPDATES.json",datasets)
    write_json(out/"FEATURE_PROVENANCE.json",{"archive_root":str(root),"archive_sha256":"81c72910b2fc912e5e0a9340d3f6b1ba20024da510ef58eb95da2ff1d8055708","features":NAMES,"truth_read_by_preparation":False,"oracle_features_used":False,"verified_inputs":verified,"all_30_native_parity_pass":True,"max_native_parity_error":max(d["native_parity_max_abs"] for d in datasets),"feature_data_sha256":sha(out/"SOURCE_BLIND_FEATURE_DATA.npz")})


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    prepare(args.root,args.out)
