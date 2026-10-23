"""Fail-closed data qualification. A transport audit is not a performance claim."""
from pathlib import Path
import numpy as np
from ..io import read_json, sha256
from ..types import observation_from_dict

REQUIRED_METADATA=('scene','source_group','wind_group','realization_id','split','frame','units','readout','propagation_qualified','geometry_qualified','candidate_support_qualified')

def qualify_episode(record, for_training=False):
    errors=[]; warnings=[]; meta=record.get('metadata',{})
    for key in REQUIRED_METADATA:
        if key not in meta: errors.append('missing_metadata:'+key)
    if meta.get('split') not in ('train','development','calibration','frozen_test','legacy_evaluation'):
        errors.append('unknown_split')
    if for_training and meta.get('split')!='train': errors.append('training_split_forbidden')
    if for_training and 'source' not in record: errors.append('training_source_label_missing')
    if meta.get('future_wind_oracle',False): errors.append('future_wind_oracle_forbidden')
    if meta.get('readout')!='binary_hit': errors.append('V1_requires_explicit_binary_readout_adapter')
    for key in ('propagation_qualified','geometry_qualified','candidate_support_qualified'):
        if meta.get(key) is not True:
            (errors if for_training else warnings).append(key+':not_qualified')
    observations=[]
    try: observations=[observation_from_dict(v) for v in record.get('observations',[])]
    except (KeyError,TypeError,ValueError) as e: errors.append('schema:'+str(e))
    if not observations: errors.append('empty_history')
    ids=[o.uid for o in observations]
    if len(set(ids))!=len(ids): errors.append('duplicate_observation_id')
    times=[o.action.time for o in observations]
    if any(b<=a for a,b in zip(times,times[1:])): errors.append('non_increasing_time')
    for o in observations:
        vals=[o.action.x,o.action.y,o.action.z,o.action.time,o.action.dwell,o.gas,*o.wind]
        if len(o.wind)!=2 or not np.isfinite(vals).all(): errors.append('invalid_numeric_observation');break
        if o.gas not in (0.,1.): errors.append('binary_hit_required');break
        if o.action.dwell<=0: errors.append('invalid_dwell');break
    candidates=np.asarray(record.get('candidates',[]),float)
    if candidates.ndim!=2 or candidates.shape[1]!=2 or len(candidates)<2: errors.append('candidate_shape')
    elif not np.isfinite(candidates).all() or len(np.unique(candidates,axis=0))!=len(candidates): errors.append('invalid_candidates')
    return {'status':'PASS' if not errors else 'FAIL','errors':errors,'warnings':warnings,'observations':len(observations),'candidates':len(candidates),'training_eligible':not errors and for_training,'scientific_scope':meta.get('split','unknown')}

def load_episode(path,for_training=False):
    record=read_json(path); receipt=qualify_episode(record,for_training)
    if receipt['errors']: raise ValueError(str(receipt))
    return record,[observation_from_dict(v) for v in record['observations']]

def check_split_disjointness(records):
    errors=[]; groups={}
    for r in records:
        m=r['metadata'];role=m['split'];groups.setdefault(role,[]).append(m)
    # An independent realization is never split across any roles.
    seen={}
    for role,items in groups.items():
        for m in items:
            key=(m['scene'],str(m['source_group']),str(m['wind_group']),str(m['realization_id']))
            if key in seen and seen[key]!=role: errors.append('realization_leak:'+str(key))
            seen[key]=role
    train=groups.get('train',[])
    for role,items in groups.items():
        if role=='train':continue
        for m in items:
            if m.get('holdout_axis')=='source' and any(m['scene']==t['scene'] and m['source_group']==t['source_group'] for t in train): errors.append('unseen_source_leak')
            if m.get('holdout_axis')=='wind' and any(m['scene']==t['scene'] and m['wind_group']==t['wind_group'] for t in train): errors.append('unseen_wind_leak')
            if m.get('holdout_axis')=='scene' and any(m['scene']==t['scene'] for t in train): errors.append('unseen_scene_leak')
    return {'status':'PASS' if not errors else 'FAIL','errors':errors,'counts':{k:len(v) for k,v in groups.items()}}

def audit_manifest(path,for_training=False):
    p=Path(path);manifest=read_json(p);records=[];receipts=[]
    for entry in manifest.get('episodes',[]):
        q=p.parent/entry['path']
        if not q.is_file(): receipts.append({'path':str(q),'status':'FAIL','errors':['file_missing']});continue
        r=read_json(q);records.append(r);v=qualify_episode(r,for_training and r['metadata']['split']=='train')
        v.update(path=str(q),sha256=sha256(q))
        if entry.get('sha256') and entry['sha256']!=v['sha256']: v['status']='FAIL';v['errors'].append('sha256_mismatch')
        receipts.append(v)
    split=check_split_disjointness(records)
    return {'status':'PASS' if receipts and all(r['status']=='PASS' for r in receipts) and split['status']=='PASS' else 'FAIL','episodes':receipts,'splits':split,'manifest_sha256':sha256(p)}
