#!/usr/bin/env python3
"""Pre-fit causal data-contract qualifier for the V3 proximal bridge.

Fail before training if primary R contains source-downstream gas/sensor features
or if candidate panels violate R/Y candidate-invariance.

This is a contract/audit tool, not a proof of proximal identification.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np

R_DOWNSTREAM_TOKENS=(
    'gas','concentration','hit','encounter','odor','plume','sensor_state',
    'sensor_transient','inter_hit','inter_encounter','threshold_cross'
)
R_ORACLE_TOKENS=('truth','source_id','source_truth','wind_id','route_id','plume_seed','oracle','future')
ANY_FORBIDDEN_TOKENS=('source_truth','truth_x','truth_y','wind_id','route_id','plume_seed','simulator_phase','oracle','future')


def names(d,key,dim):
    if key not in d: raise ValueError(f'MISSING_{key.upper()}')
    a=np.asarray(d[key]).astype(str).reshape(-1)
    if len(a)!=dim: raise ValueError(f'{key} length {len(a)} != dim {dim}')
    return [x.strip().lower() for x in a]


def check_matrix(d,key):
    if key not in d: raise ValueError(f'MISSING_{key.upper()}')
    a=np.asarray(d[key],dtype=float)
    if a.ndim==1:a=a[:,None]
    if a.ndim!=2 or not np.all(np.isfinite(a)): raise ValueError(f'{key} must be finite 2-D')
    return a


def token_hits(nn,tokens):
    return sorted({name for name in nn if any(tok in name for tok in tokens)})


def audit_dataset(path,panel=False):
    d=np.load(path,allow_pickle=False)
    y=check_matrix(d,'y'); r=check_matrix(d,'r'); s=check_matrix(d,'s'); z=check_matrix(d,'z')
    n=len(y)
    if not (len(r)==len(s)==len(z)==n): raise ValueError('row count mismatch')
    yn=names(d,'y_feature_name',y.shape[1]); rn=names(d,'r_feature_name',r.shape[1]); zn=names(d,'z_feature_name',z.shape[1])
    sn=names(d,'s_feature_name',s.shape[1]) if 's_feature_name' in d else [f's{i}' for i in range(s.shape[1])]
    downstream=token_hits(rn,R_DOWNSTREAM_TOKENS)
    oracle_r=token_hits(rn,R_ORACLE_TOKENS)
    any_forbidden=token_hits(yn+rn+zn+sn,ANY_FORBIDDEN_TOKENS)
    errors=[]
    if downstream: errors.append('R_SOURCE_DOWNSTREAM:'+','.join(downstream))
    if oracle_r: errors.append('R_ORACLE:'+','.join(oracle_r))
    if any_forbidden: errors.append('FORBIDDEN_FEATURE_NAME:'+','.join(any_forbidden))
    panel_events=0
    if panel:
        for key in ('event_id','candidate_id'):
            if key not in d: errors.append('MISSING_'+key.upper())
        if not errors or ('event_id' in d and 'candidate_id' in d):
            event=np.asarray(d['event_id']).reshape(-1)
            if len(event)!=n: errors.append('EVENT_ID_LENGTH')
            else:
                for e in np.unique(event):
                    idx=np.flatnonzero(event==e); panel_events+=1
                    if len(idx)<2: errors.append(f'EVENT_SINGLE_CANDIDATE:{e}'); continue
                    if np.max(np.abs(r[idx]-r[idx[0]]))>1e-10: errors.append(f'R_NOT_CANDIDATE_INDEPENDENT:{e}')
                    if np.max(np.abs(y[idx]-y[idx[0]]))>1e-10: errors.append(f'Y_NOT_CANDIDATE_INDEPENDENT:{e}')
    return {'path':str(path.resolve()),'rows':n,'dims':{'y':y.shape[1],'r':r.shape[1],'s':s.shape[1],'z':z.shape[1]},
            'r_features':rn,'y_features':yn,'z_features':zn,'s_features':sn,
            'r_source_downstream_hits':downstream,'forbidden_feature_hits':any_forbidden,
            'panel_events':panel_events,'pass':not errors,'errors':errors}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--train',type=Path,required=True); ap.add_argument('--dev',type=Path,required=True)
    ap.add_argument('--dev-panel',type=Path,required=True); ap.add_argument('--test-panel',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    reports=[]
    for path,panel in [(a.train,False),(a.dev,False),(a.dev_panel,True),(a.test_panel,True)]:
        try: reports.append(audit_dataset(path,panel))
        except Exception as e: reports.append({'path':str(path),'pass':False,'errors':[f'EXCEPTION:{type(e).__name__}:{e}']})
    # Feature schemas must be frozen across all products.
    schemas=[]
    for r in reports:
        if all(k in r for k in ('r_features','y_features','z_features','s_features')):
            schemas.append((r['r_features'],r['y_features'],r['z_features'],r['s_features']))
    schema_same=bool(schemas) and all(x==schemas[0] for x in schemas)
    go=all(r.get('pass') is True for r in reports) and schema_same
    out={'contract':'CG_PC_CTT_V3_CAUSAL_PROXY_DATA_CONTRACT_V1',
         'scientific_boundary':'Operational exclusion/dataflow audit; not a theorem proving proximal identification.',
         'required_R_semantics':'source-independent pre/current context; no gas/sensor outcome descendants',
         'schema_identical_across_splits':schema_same,'reports':reports,
         'verdict':'CAUSAL_PROXY_CONTRACT_PASS' if go else 'INVALID_CAUSAL_PROXY_CONTRACT'}
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(out,indent=2),encoding='utf-8'); print(json.dumps(out,indent=2))
    raise SystemExit(0 if go else 2)

if __name__=='__main__': main()
