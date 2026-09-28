#!/usr/bin/env python3
"""Read-only selector x decoder cross-attribution for HD-PLF D0.5.

Consumes only frozen D05_RESULT.json and GOAL_COUNTERFACTUALS.csv.
No simulation, fitting, action reselection, or metric changes.
"""
from __future__ import annotations
import argparse, csv, json
from collections import defaultdict
from pathlib import Path

ARMS=("LF-u","LF-rawu")

def mean(xs): return sum(xs)/len(xs)

def load_csv(path: Path):
    with path.open(newline="",encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--result",type=Path,required=True)
    ap.add_argument("--goals",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args(); a.out.mkdir(parents=True,exist_ok=True)

    d=json.loads(a.result.read_text(encoding="utf-8"))
    rows=load_csv(a.goals)
    table=defaultdict(lambda:{arm:{} for arm in ARMS})
    for r in rows:
        k=(int(r["environment"]),int(r["source_index"]),int(r["target_index"]))
        arm=r["arm"]; goal=int(r["goal_cell"])
        if arm not in ARMS: raise ValueError(arm)
        if goal in table[k][arm]: raise ValueError(("duplicate",k,arm,goal))
        table[k][arm][goal]={
            "rank":float(r["rank_after_tie_aware"]),
            "gain":float(r["rank_gain"]),
        }

    out=[]
    for ep in d["episodes"]:
        k=(int(ep["environment"]),int(ep["source_index"]),int(ep["target_index"]))
        t=table[k]
        if set(t)!=set(ARMS): raise ValueError(("missing decoder",k))
        goals=set(t["LF-u"])
        if goals!=set(t["LF-rawu"]) or len(goals)!=int(ep["feasible_goals"]):
            raise ValueError(("feasible-set mismatch",k))
        selected={arm:int(ep[arm]["selected_cell"]) for arm in ARMS}
        if not set(selected.values())<=goals: raise ValueError(("selected missing",k))
        for dec in ARMS:
            vals=list(t[dec].values())
            uniform_rank=mean([v["rank"] for v in vals])
            uniform_gain=mean([v["gain"] for v in vals])
            oracle_rank=min(v["rank"] for v in vals)
            oracle_gain=max(v["gain"] for v in vals)
            for sel in ARMS:
                v=t[dec][selected[sel]]
                out.append({
                    "environment":k[0],"source_index":k[1],"target_index":k[2],
                    "decoder":dec,"selector":sel,"selected_goal":selected[sel],
                    "expected_final_rank":v["rank"],"rank_gain":v["gain"],
                    "uniform_feasible_mean_rank":uniform_rank,
                    "uniform_feasible_mean_gain":uniform_gain,
                    "truth_oracle_rank_diagnostic_only":oracle_rank,
                    "truth_oracle_gain_diagnostic_only":oracle_gain,
                    "regret_to_oracle_rank":v["rank"]-oracle_rank,
                    "selected_minus_uniform_rank":v["rank"]-uniform_rank,
                    "action_count":len(goals),
                })

    expected={(int(e["environment"]),int(e["source_index"]),int(e["target_index"])) for e in d["episodes"]}
    if set(table)!=expected: raise ValueError("unexpected/missing episodes")

    with (a.out/"D05_SELECTOR_DECODER_CROSS_EPISODES.csv").open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)

    groups=defaultdict(list)
    for r in out: groups[(r["environment"],r["decoder"],r["selector"])].append(r)
    summary=[]
    for (env,dec,sel),rs in sorted(groups.items()):
        bysrc=defaultdict(list)
        for r in rs: bysrc[r["source_index"]].append(r)
        def sb(field): return mean([mean([r[field] for r in vv]) for vv in bysrc.values()])
        summary.append({
            "environment":env,"decoder":dec,"selector":sel,
            "sources":len(bysrc),"episodes":len(rs),
            "source_balanced_expected_final_rank":sb("expected_final_rank"),
            "source_balanced_rank_gain":sb("rank_gain"),
            "source_balanced_uniform_rank":sb("uniform_feasible_mean_rank"),
            "source_balanced_oracle_rank":sb("truth_oracle_rank_diagnostic_only"),
            "source_balanced_regret_to_oracle":sb("regret_to_oracle_rank"),
        })
    with (a.out/"D05_SELECTOR_DECODER_CROSS_SUMMARY.csv").open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)

if __name__=="__main__":
    main()
