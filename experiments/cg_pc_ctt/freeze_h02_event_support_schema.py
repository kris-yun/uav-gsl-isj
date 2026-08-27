#!/usr/bin/env python3
"""Freeze a historical event-log schema using only paths and headers.
No row values are read. No truth, margin, score, or localization outcome is used.
"""
from __future__ import annotations
import argparse,collections,json
from pathlib import Path

def schema_key(item):
    return (Path(item['path']).name, tuple(c.strip().lower() for c in item['columns']))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('discovery_json',type=Path);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    d=json.loads(a.discovery_json.read_text(encoding='utf-8')); cases=d['results']
    groups=collections.defaultdict(lambda:collections.defaultdict(list))
    for case in cases:
        cid=case['case_id']
        for item in case.get('candidate_event_files',[]):
            if item.get('has_outcome'): groups[schema_key(item)][cid].append(item['path'])
    if not groups:raise SystemExit('NO_EVENT_SCHEMA_CANDIDATES')
    ranked=[]
    for key,bycase in groups.items():
        unique_cases=sum(len(v)==1 for v in bycase.values()); ambiguous=sum(len(v)>1 for v in bycase.values())
        ranked.append((unique_cases,-ambiguous,key,bycase))
    ranked.sort(key=lambda x:(x[0],x[1],x[2]),reverse=True)
    best=ranked[0];ties=[x for x in ranked if x[0]==best[0] and x[1]==best[1]]
    if len(ties)!=1:raise SystemExit(f'AMBIGUOUS_EVENT_SCHEMA tie_count={len(ties)} coverage={best[0]}')
    unique_cases,neg_amb,key,bycase=best; ambiguous=-neg_amb
    if ambiguous:raise SystemExit(f'AMBIGUOUS_EVENT_SCHEMA cases_with_multiple_matches={ambiguous}')
    mapping=[];missing=[]
    for case in cases:
        cid=case['case_id'];paths=bycase.get(cid,[])
        if len(paths)==1:mapping.append({'case_id':cid,'cluster_id':case['cluster_id'],'event_file':paths[0]})
        else:missing.append(cid)
    payload={'contract':'H02_RECONSTRUCTED_EVENT_SCHEMA_FREEZE_V1','header_only':True,'truth_read':False,
      'selected_basename':key[0],'selected_columns':list(key[1]),'matched_cases':len(mapping),'total_cases':len(cases),
      'missing_cases':missing,'mapping':mapping,
      'binding_note':'Selection used only basename/header coverage. Event row values remain unread at schema freeze.'}
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(payload,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in payload.items() if k!='mapping'},indent=2))
if __name__=='__main__':main()
