#!/usr/bin/env python3
"""Header-only discovery of historical measurement/event logs for frozen H02 contexts.
Does not read row values, truth, margins, scores, or localization errors.
"""
from __future__ import annotations
import argparse,csv,json
from pathlib import Path

NAME_HINT=('event','block','measure','gas','sensor','concentration','aci')
X_HINT=('x','position_x','pose_x','robot_x')
Y_HINT=('y','position_y','pose_y','robot_y')
T_HINT=('time','sim_time','timestamp','t')
OUTCOME_HINT=('concentration','hit','gas','ppm','sensor')

def header(p:Path):
    try:
        with p.open(newline='',encoding='utf-8-sig') as f:return next(csv.reader(f),[])
    except Exception:return []

def read_manifest(p):
    with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))

def classify(cols):
    lo=[c.strip().lower() for c in cols]
    def has(hints):return any(any(h==c or h in c for h in hints) for c in lo)
    return {'has_x':has(X_HINT),'has_y':has(Y_HINT),'has_time':has(T_HINT),'has_outcome':has(OUTCOME_HINT)}

def candidate_roots(context:Path):
    roots=[context,context.parent]; p=context
    for _ in range(3): p=p.parent; roots.append(p)
    seen=[]
    for r in roots:
        if r.exists() and r not in seen:seen.append(r)
    return seen

def main():
    ap=argparse.ArgumentParser();ap.add_argument('analysis_manifest',type=Path);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    rows=read_manifest(a.analysis_manifest); results=[]
    for r in rows:
        context=Path(r['context_dir']); found=[]; seen=set()
        for root in candidate_roots(context):
            try: files=root.rglob('*.csv')
            except Exception: continue
            for p in files:
                s=str(p)
                if s in seen: continue
                seen.add(s)
                if not any(h in p.name.lower() for h in NAME_HINT):continue
                cols=header(p); c=classify(cols)
                if c['has_x'] and c['has_y'] and c['has_time']:
                    found.append({'path':s,'columns':cols,**c})
                if len(seen)>5000: break
        results.append({'case_id':r['case_id'],'cluster_id':r['cluster_id'],'context_dir':str(context),'candidate_event_files':found})
    viable=sum(any(x['has_outcome'] for x in r['candidate_event_files']) for r in results)
    payload={'contract':'H02_RECONSTRUCTED_EVENT_SUPPORT_DISCOVERY_V1','header_only':True,'truth_read':False,
      'cases':len(results),'cases_with_xy_time_outcome_candidate':viable,'results':results,
      'next_step':'If viable files exist, freeze exact event-file/schema selection before reading values. Otherwise use deterministic shadow replay to export rawProbabilities at actual events.'}
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(payload,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in payload.items() if k!='results'},indent=2))
if __name__=='__main__':main()
