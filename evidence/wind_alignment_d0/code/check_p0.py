#!/usr/bin/env python3
import argparse,csv,hashlib,json,math
from pathlib import Path
import numpy as np
ap=argparse.ArgumentParser();ap.add_argument('folder');ap.add_argument('output');a=ap.parse_args()
root=Path('/home/zyc/wind_alignment_d0_20260926');folder=Path(a.folder)
inputs=root/'inputs'
old=list(csv.DictReader((inputs/'C_candidate_scores.csv').open(newline='')))
new=list(csv.DictReader((folder/'candidate_scores.csv').open(newline='')))
events=list(csv.DictReader((inputs/'measurement_events.csv').open(newline='')))
snapshot=list(csv.DictReader((inputs/'measured_map_at_update.csv').open(newline='')))
width=int(snapshot[0]['grid_width']);n=len(snapshot)
prior=Path('/home/zyc/pmfs_evidence_pseudoreplication_20260926/result/candidate_scores.csv')
priorrows={r['candidate_id']:r for r in csv.DictReader(prior.open(newline=''))}
assert len(old)==len(new)==87
errors=[];score_errors=[];native_errors=[];maps_identical=[]
for historical,regenerated in zip(old,new):
    assert all(historical[k]==regenerated[k] for k in ('candidate_id','origin_i','origin_j','size_i','size_j','center_x','center_y'))
    cid=historical['candidate_id'];x=(inputs/'historical_maps'/(cid+'.f32')).read_bytes(); y=(folder/regenerated['map_file']).read_bytes()
    assert len(x)==len(y)==4*n
    b=np.frombuffer(y,dtype='<f4');errors.append(float(np.max(abs(np.frombuffer(x,dtype='<f4')-b))))
    maps_identical.append(x==y)
    native_errors.append(abs(float(historical['source_score'])-float(regenerated['source_score'])))
    elog=0.0;brier=0.0
    for e in events:
        p=float(b[int(e['robot_j'])*width+int(e['robot_i'])]);h=int(e['hit']);q=min(1-1e-6,max(1e-6,p))
        elog+=h*math.log(q)+(1-h)*math.log1p(-q);brier-=(h-p)**2
    score_errors.append(max(abs(elog-float(priorrows[cid]['event_logscore'])),abs(brier-float(priorrows[cid]['event_brier']))))
record={'candidate_count':87,'map_count':87,'map_max_abs_error':max(errors),
        'all_maps_byte_identical':all(maps_identical),'native_score_max_abs_error':max(native_errors),
        'historical_proper_score_max_abs_error':max(score_errors),
        'map_tolerance':0.0,'proper_score_tolerance':0.0,
        'pass':all(maps_identical) and max(native_errors)==0 and max(score_errors)==0}
Path(a.output).write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
print(json.dumps(record,indent=2))
if not record['pass']:raise SystemExit(31)
