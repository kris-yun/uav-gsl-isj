#!/usr/bin/env python3
"""Truth-blind run-level coverage for CG-PC-CTT V5 passive evidence ledger.

This does not use truth or localization performance. It asks a narrower
question: after accumulating spatially unique physical stops across archived OFF
source-update contexts, how many development runs would have at least one
scientifically valid V5 ACCEPT and hence be able to diverge from Classic PMFS?
"""
from __future__ import annotations
import argparse, csv, json
from collections import defaultdict
from pathlib import Path
import numpy as np

import v5_active_sequential_reference as v5


FORBIDDEN = {
    "truth", "true_source", "source_truth", "localization_error", "final_error",
    "off_on_improvement", "on_error", "off_error"
}


def scalar(d, key, default):
    if key not in d.files:
        return default
    x=d[key]
    if np.ndim(x)==0: return x.item()
    if np.size(x)==1: return np.ravel(x)[0].item()
    return default


def read_manifest(path: Path):
    by_context=defaultdict(list)
    with path.open(newline="",encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            by_context[row["context_id"]].append(row)
    for cid in by_context:
        by_context[cid].sort(key=lambda x:int(x["stop_index"]))
    return by_context


def load_context(path: Path):
    d=np.load(path,allow_pickle=False)
    leak=FORBIDDEN.intersection(d.files)
    if leak:
        raise ValueError(f"{path}: forbidden keys {sorted(leak)}")
    required={"stop_probability","stop_r","rectangles","geometry_prior"}
    missing=required.difference(d.files)
    if missing:
        raise ValueError(f"{path}: missing {sorted(missing)}")
    return {
        "path":path,
        "p":np.asarray(d["stop_probability"],float),
        "r":np.asarray(d["stop_r"],float),
        "rect":np.asarray(d["rectangles"],np.int64),
        "q0":np.asarray(d["geometry_prior"],float),
        "house":str(scalar(d,"house","UNKNOWN")),
        "seed":int(scalar(d,"seed",-1)),
        "update_id":int(scalar(d,"update_id",-1)),
        "context_id":str(scalar(d,"context_id",path.stem)),
        "timesteps":int(scalar(d,"timesteps",200)),
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("contexts",type=Path)
    ap.add_argument("--stop-manifest",type=Path,required=True)
    ap.add_argument("--out-csv",type=Path,required=True)
    ap.add_argument("--out-json",type=Path,required=True)
    a=ap.parse_args()
    manifest=read_manifest(a.stop_manifest)
    contexts=[load_context(p) for p in sorted(a.contexts.glob("*.npz"))]
    if not contexts:
        raise ValueError("no NPZ contexts")
    groups=defaultdict(list)
    for c in contexts:
        groups[(c["house"],c["seed"])].append(c)
    rows=[]; run_summary=[]
    for (house,seed),items in sorted(groups.items()):
        items.sort(key=lambda x:x["update_id"])
        q0=items[0]["q0"]
        rect=items[0]["rect"]
        T=items[0]["timesteps"]
        st=v5.initialize_state(q0)
        ever=False; first_accept=None
        for c in items:
            if c["context_id"] not in manifest:
                raise ValueError(f"missing stop manifest for {c['context_id']}")
            m=manifest[c["context_id"]]
            if len(m)!=c["p"].shape[2]:
                raise ValueError(f"stop manifest count mismatch for {c['context_id']}")
            keys=[x["stop_key"] for x in m]
            native=q0  # decision is independent of native_post; no performance read.
            _,st,d,active,alpha,beta,build,admitted=v5.apply_context(
                c["p"],c["r"],keys,c["context_id"],rect,q0,native,T,st
            )
            if d.accepted and not ever:
                first_accept=c["update_id"]
            ever |= bool(d.accepted)
            rows.append({
                "house":house,"seed":seed,"update_id":c["update_id"],
                "context_id":c["context_id"],"incoming_stops":len(keys),
                "new_unique_stops":int(np.sum(admitted)),
                "ledger_unique_stops":d.unique_stops,
                "effective_contexts":d.effective_contexts,
                "components":"" if build is None else int(len(np.unique(build.labels))),
                "accepted":bool(d.accepted),"reason":d.reason,
                "informative_contexts":d.informative_contexts,
                "min_absolute_gain":"" if d.heldout_absolute_gain is None else float(np.min(d.heldout_absolute_gain)),
                "min_rival_margin":"" if d.heldout_rival_margin is None else float(np.min(d.heldout_rival_margin)),
                "projection_active":bool(active),
                "alpha":"" if alpha is None else float(alpha),
                "beta":"" if beta is None else float(beta),
            })
        run_summary.append({
            "house":house,"seed":seed,"ever_accept":ever,
            "first_accept_update":first_accept,
            "final_unique_stops":len(st.stop_key),
            "contexts":len(items),
        })

    runs_with_accept=sum(int(r["ever_accept"]) for r in run_summary)
    by_house={}
    for h in sorted(set(r["house"] for r in run_summary)):
        hr=[r for r in run_summary if r["house"]==h]
        by_house[h]={
            "runs":len(hr),
            "runs_with_accept":sum(int(r["ever_accept"]) for r in hr),
            "accept_seeds":[r["seed"] for r in hr if r["ever_accept"]],
            "median_final_unique_stops":float(np.median([r["final_unique_stops"] for r in hr])),
        }
    if len(run_summary)!=30:
        verdict="INCOMPLETE_DEVELOPMENT_RUN_SET"
    elif runs_with_accept>=20:
        verdict="V5_PASSIVE_LEDGER_ACTIONABLE_FOR_CPP"
    else:
        verdict="V5_ACTIVE_PROBE_REQUIRED_BEFORE_PERFORMANCE_MATRIX"
    summary={
        "contract":"CG_PC_CTT_V5_PASSIVE_LEDGER_COVERAGE_V1",
        "truth_used":False,
        "localization_error_used":False,
        "runs":len(run_summary),
        "contexts":len(contexts),
        "runs_with_accept":runs_with_accept,
        "required_possible_improved_pairs":20,
        "houses":by_house,
        "verdict":verdict,
        "run_summary":run_summary,
        "note":"This is an actionability bound, not localization-performance evidence. No scientific threshold may be tuned from this report."
    }
    a.out_csv.parent.mkdir(parents=True,exist_ok=True)
    with a.out_csv.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    a.out_json.write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()
