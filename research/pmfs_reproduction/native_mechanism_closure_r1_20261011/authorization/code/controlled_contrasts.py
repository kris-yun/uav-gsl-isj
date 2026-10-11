#!/usr/bin/env python3
"""Guarded 2x2 contrasts. Each input quartet must share its common contract.

Not a hypothesis test. Does not interpret candidates/pixels as independent runs.
CSV columns: task_id, realization_id, common_contract_sha256, scope, D, V, metric.
metric must have the same definition/units across all four conditions.
D/V are diagnostic treatment labels, NOT evidence that nature has those states.
"""
from __future__ import annotations
import argparse,csv,json,math
from collections import defaultdict
from pathlib import Path


def contrasts(rows: list[dict]) -> list[dict]:
    groups=defaultdict(list)
    for r in rows: groups[r['task_id'],r['realization_id']].append(r)
    out=[]
    for (task,real), group in sorted(groups.items()):
        if len({r['common_contract_sha256'] for r in group})!=1:
            raise ValueError(f'{task}/{real}: common physical/observation contract differs')
        if len({r['scope'] for r in group})!=1: raise ValueError('Mixed scientific scopes')
        vals={}
        for r in group:
            key=(int(r['D']),int(r['V']));val=float(r['metric'])
            if key not in {(0,0),(0,1),(1,0),(1,1)} or key in vals or not math.isfinite(val):
                raise ValueError('Bad/duplicate factor value or nonfinite metric')
            vals[key]=val
        if len(vals)!=4: raise ValueError(f'{task}/{real}: incomplete quartet; do not silently drop it')
        a,b,c,d=(vals[k] for k in [(0,0),(1,0),(0,1),(1,1)])
        out.append(dict(task_id=task,realization_id=real,scope=group[0]['scope'],
            D_effect_at_V0=b-a,D_effect_at_V1=d-c,V_effect_at_D0=c-a,V_effect_at_D1=d-b,
            interaction=d-b-c+a,claim='paired diagnostic contrasts only; no causal percentage or significance'))
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('input',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    if a.output.exists(): raise FileExistsError(a.output)
    with a.input.open(encoding='utf-8',newline='') as f:r=list(csv.DictReader(f))
    a.output.write_text(json.dumps(contrasts(r),ensure_ascii=False,indent=2),encoding='utf-8')
