"""Ordinary frozen inference; no truth, gas particle headers, fitting or hidden paths.
Input root contains source catalog, predictions, observedprefix maps/events only.
"""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import csv,json,time,hashlib
import numpy as np
from source_map_tools import native_log_score,event_composite_log_score,normalized_source_weights,rasterize_source_mass

def rows(p):return list(csv.DictReader(Path(p).open(encoding='utf-8',newline='')))
def calculate(root:Path,prefix:int):
 catalog=json.loads((root/'SOURCE_CATALOG.json').read_text());prior=np.array([r['prior'] for r in catalog['catalog']]);free=np.load(root/'SCORING_FREE_MASK.npy',allow_pickle=False);mapping=np.load(root/'SOURCE_CELL_TO_REGION.npy',allow_pickle=False);active=mapping>=0
 predictions=np.load(root/'ALL_CANDIDATE_PREDICTIONS.npz',allow_pickle=False);registry=json.loads((root/'OBSERVATION_REGISTRY.json').read_text());results=[];clock=[]
 for ob in registry:
  start=time.perf_counter();folder=root/ob['folder'];m=np.load(folder/'MEASURED_MAPS.npz',allow_pickle=False);p=m[f'p{prefix}'];c=m[f'c{prefix}'];events=rows(folder/f'EVENTS_{prefix}.csv');assert len(events)==prefix;y=np.array([int(r['event_hit']) for r in events]);plan=ob['plan']
  for group,refs in [('R0',[0]),('R1',[1]),('R01',[0,1])]:
   values={}
   for method in ['P3-O0','P3-O1','N_POINT_ALL']:
    name=f'{plan}_{method}_{prefix}' if method!='N_POINT_ALL' else 'N_POINT_ALL';a=predictions[name][:,refs,:].mean(axis=1).astype(np.float32);values[method]=native_log_score(p,c,a,free,D=.4)
   ref=predictions[plan+'_EVENTS'][:,refs,:prefix];values['E-event']=event_composite_log_score(ref,y,alpha=.5)
   a=predictions[f'{plan}_A1_{prefix}'][:,refs,:].mean(axis=1).astype(np.float32);values['A1-map']=-np.mean((a[:,free].astype(float)-p[free])**2,axis=1)
   for method,score in values.items():
    weights=normalized_source_weights(score,prior);raster=rasterize_source_mass(weights,mapping,active)
    results.append(dict(oid=ob['oid'],plan=plan,group=group,method=method,blocks=prefix,log_scores=score,source_weights=weights,posterior=raster))
  clock.append(dict(oid=ob['oid'],prefix=prefix,inference_only_wall_s=time.perf_counter()-start))
 return results,clock
def run(root,out):
 out.mkdir();records=[];arrays={};cost=[]
 for prefix in [20,35,50]:
  rs,cc=calculate(root,prefix);cost+=cc
  for r in rs:
   key=f'{r["oid"]}__{r["group"]}__{r["method"]}__{prefix}'
   arrays[key+'_scores']=r.pop('log_scores');arrays[key+'_weights']=r.pop('source_weights');arrays[key+'_posterior']=r.pop('posterior');records.append(dict(r,key=key))
 np.savez_compressed(out/'FULL_SOURCE_POSTERIORS.npz',**arrays);(out/'RESULT_INDEX.json').write_text(json.dumps(records,indent=2),encoding='utf-8');(out/'INFERENCE_COST.json').write_text(json.dumps(cost,indent=2),encoding='utf-8')
 return dict(status='PASS_REGISTERED_ORDINARY_INFERENCE',objects=len(records),truth_access=False,source_count=len(json.loads((root/'SOURCE_CATALOG.json').read_text())['catalog']))
if __name__=='__main__':print(json.dumps(run(Path(sys.argv[1]),Path(sys.argv[2]))))
