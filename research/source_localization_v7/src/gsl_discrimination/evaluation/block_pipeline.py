"""Qualified native-window calibration and fixed-trajectory replay.

This format deliberately cannot turn the bundled 50-second OCB snapshots into
continuous windows. Capability assertions require a pinned external review
receipt; the loader verifies bytes and structure, not fluid physics itself.
"""
from __future__ import annotations
from pathlib import Path
import hashlib,json,os,zipfile
from collections import defaultdict
import numpy as np
from ..data import SynchronousBlock,QualificationError
from ..m1_opponent import OpponentBank,SamplingContract,calibrate_source_contrast
from ..m1_opponent.raw_joint import calibrate_raw_joint,load_observation_model
from ..channel import JointPosterior
from ..ledger import RawObservationLedger
from ..m3_audit import AuditLedger
from .metrics import source_metrics
from .maps import export_source_map


def load_manifest(path,allowed_splits=('train','dev')):
    path=Path(path);d=json.loads(path.read_text());base=path.parent
    if d.get('schema')!='gsl-native-block-manifest-1':raise QualificationError('unsupported block manifest')
    for key in ('source_ids','source_xy','nuisance_ids','actions','records','capability_review'):
        if key not in d:raise QualificationError(f'manifest is missing {key}')
    proof=d['capability_review'];proof_path=base/proof['path']
    if hashlib.sha256(proof_path.read_bytes()).hexdigest()!=proof['sha256']:
        raise QualificationError('qualification review bytes changed')
    review=json.loads(proof_path.read_text())
    if review.get('status')!='QUALIFIED_FOR_DECLARED_USES':
        raise QualificationError('external physical qualification is not complete')
    if len(set(d['source_ids']))!=len(d['source_ids']):raise QualificationError('duplicate source ids')
    if len(set(d['nuisance_ids']))!=len(d['nuisance_ids']):raise QualificationError('duplicate nuisance ids')
    if not set(allowed_splits)<={'train','dev','final'}:raise QualificationError('invalid requested split')
    if 'final' in allowed_splits and d.get('final_freeze_authorized') is not True:
        raise QualificationError('final split is sealed; no observation bytes opened')
    records=[];world_split={};seen=set();loaded_bytes=0
    limit=float(os.environ.get('GSL_V7_MAX_CALIBRATION_MB','512'))*1024**2
    if not np.isfinite(limit) or limit<=0:raise ValueError('invalid GSL_V7_MAX_CALIBRATION_MB')
    for record in d['records']:
        if record.get('split') not in ('train','dev','final'):raise QualificationError('unknown split')
        # Select the authorized purpose BEFORE opening any observation bytes.
        if record['split'] not in allowed_splits:continue
        p=base/record['path']
        if p.suffix=='.npz':
            with zipfile.ZipFile(p) as archive:estimated=sum(x.file_size for x in archive.infolist())
        else:estimated=4*p.stat().st_size
        loaded_bytes+=estimated
        if loaded_bytes>limit:raise MemoryError('selected blocks exceed preflight calibration memory budget')
        if hashlib.sha256(p.read_bytes()).hexdigest()!=record['sha256']:
            raise QualificationError(f'block hash changed: {p.name}')
        if p.suffix=='.csv' and hashlib.sha256(p.with_suffix('.schema.json').read_bytes()).hexdigest()!=record.get('schema_sha256'):
            raise QualificationError('CSV schema sidecar must also be pinned')
        block=(SynchronousBlock.load_csv if p.suffix=='.csv' else SynchronousBlock.load_npz)(p)
        block.qualification.require('synchronous_spatial','physical_clock','native_samples_only',
                                    'source_occupancy_validated','sensor_response_calibrated')
        if d.get('temporal',False):block.require_dynamic(with_wind=False)
        if block.values.shape[1]!=2:raise QualificationError('paired model requires exactly two sensors')
        if block.metadata.get('truth_included',False):raise QualificationError('truth belongs to evaluator metadata only')
        if block.block_id in seen:raise QualificationError('duplicate block in dataset index')
        seen.add(block.block_id)
        if record['split'] not in ('train','dev','final'):raise QualificationError('unknown split')
        old=world_split.setdefault(block.realization_id,record['split'])
        if old!=record['split']:raise QualificationError('one realization cannot cross train/dev/final')
        if record['source_id'] not in d['source_ids'] or record['nuisance_id'] not in d['nuisance_ids']:
            raise QualificationError('unknown evaluator source/mechanism')
        if not 0<=int(record['action'])<len(d['actions']):raise QualificationError('unknown action')
        expected=np.asarray(d['actions'][int(record['action'])]['positions_m'],dtype=float)
        if expected.shape!=block.positions_m.shape or not np.allclose(expected,block.positions_m,atol=1e-6,rtol=0):
            raise QualificationError('actual paired geometry differs from calibrated action')
        records.append((record,block))
    return d,records


def calibrate_manifest(path,output,variant='secondary'):
    out=Path(output)
    if (out/'operator.json').exists():raise ValueError('frozen model already exists')
    d,records=load_manifest(path,allowed_splits=('train',));groups=defaultdict(list)
    sid={x:i for i,x in enumerate(d['source_ids'])};rid={x:i for i,x in enumerate(d['nuisance_ids'])}
    train=[(r,b) for r,b in records if r['split']=='train']
    if not train:raise QualificationError('no training blocks')
    times=train[0][1].times_s;relative=times-times[0]
    observation_contract={'units':train[0][1].units,'sensor_ids_order':list(train[0][1].sensor_ids)}
    for r,b in train:
        if {'units':b.units,'sensor_ids_order':list(b.sensor_ids)}!=observation_contract:
            raise QualificationError('all training blocks must share physical units and ordered sensor identities')
        if b.values.shape!=train[0][1].values.shape or not np.allclose(b.times_s-b.times_s[0],relative):
            raise QualificationError('calibration windows must have one declared physical clock; no interpolation')
        groups[(int(r['action']),sid[r['source_id']],rid[r['nuisance_id']])].append(b)
    a,s,m=len(d['actions']),len(sid),len(rid)
    counts=[len(groups[(i,j,k)]) for i in range(a) for j in range(s) for k in range(m)]
    if min(counts)<2 or min(counts)!=max(counts):
        raise QualificationError('balanced complete action/source/mechanism calibration, >=2 blocks per cell required')
    raw=np.stack([np.stack([np.stack([np.stack([b.values for b in groups[(i,j,k)]])
                   for k in range(m)]) for j in range(s)]) for i in range(a)])
    contract=SamplingContract(**d['sampling_contract']);contract.validate(times,d.get('temporal',False))
    names=[x['name'] for x in d['actions']];costs=[x['cost_s'] for x in d['actions']]
    if variant=='raw_joint':
        model=calibrate_raw_joint(raw,times,contract,d['source_xy'],names,d['source_ids'],costs,
                                 n_symbols=min(18,s*m*counts[0]))
    else:
        bank=OpponentBank.causal_default() if d.get('temporal',False) else OpponentBank()
        model=calibrate_source_contrast(raw,times,contract,d['source_xy'],names,d['source_ids'],costs,
              bank,variant=variant,max_filters=2,calibration_world_ids=sorted({b.realization_id for _,b in train}))
    model.channel.metadata.update({'calibration_manifest_sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),
          'training_realizations':sorted({b.realization_id for _,b in train}),
          'physical_review':d['capability_review'],'action_points_m':[x['positions_m'] for x in d['actions']],
          'capability_validation_scope':'byte/schema checks; physical claims rest on linked review',
          'native_estimated_channel_no_unconditional_risk_guarantee':True})
    model.channel.metadata['native_manifest_contract']={key:d[key] for key in
            ('source_ids','source_xy','nuisance_ids','actions','temporal','sampling_contract')}
    model.channel.metadata['observation_contract']=observation_contract
    model.save(out)
    receipt={'status':'CALIBRATED_QUALIFIED_BLOCKS','variant':variant,'shape':model.channel.shape,
             'training_blocks':len(train),'train_realizations':model.channel.metadata['training_realizations'],
             'world_split_checked':True,'unseen_source_generalization':False,
             'native_channel_risk_guarantee':'not established by estimated frequencies'}
    (out/'CALIBRATION_RECEIPT.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2))
    return receipt


def replay_manifest(path,model_directory,output,split='dev'):
    out=Path(output)
    if (out/'REPLAY_RESULT.json').exists():raise ValueError('replay receipt already exists')
    if split not in ('dev','final'):raise QualificationError('replay requires explicit dev or final split')
    d,records=load_manifest(path,allowed_splits=(split,));model=load_observation_model(model_directory)
    frozen=model.channel.metadata.get('native_manifest_contract')
    current={key:d[key] for key in ('source_ids','source_xy','nuisance_ids','actions','temporal','sampling_contract')}
    if frozen is None or current!=frozen:
        raise QualificationError('action/source/mechanism/sampling contract differs from frozen calibration')
    if d['source_ids']!=model.channel.source_ids:raise QualificationError('candidate support does not match calibration')
    if not np.allclose(d['source_xy'],model.channel.source_xy):raise QualificationError('source coordinates changed')
    train=set(model.channel.metadata.get('training_realizations',[]))
    episodes=defaultdict(list)
    for r,b in records:
        if r['split']=='train':continue
        if b.realization_id in train:raise QualificationError('calibration/evaluation realization leakage')
        if {'units':b.units,'sensor_ids_order':list(b.sensor_ids)}!=model.channel.metadata.get('observation_contract'):
            raise QualificationError('observation units or ordered sensor identity differs from training')
        if r['split']=='final' and d.get('final_freeze_authorized') is not True:
            raise QualificationError('final split is sealed until the experiment contract is frozen')
        episodes[r.get('episode_id',b.realization_id)].append((r,b))
    if not episodes:raise QualificationError('no held-out episodes')
    out.mkdir(parents=True,exist_ok=True);results=[]
    for episode,entries in sorted(episodes.items()):
        identities={r['source_id'] for r,b in entries}
        if len(identities)!=1:raise QualificationError('source changed within fixed-source episode')
        if len({r['nuisance_id'] for r,b in entries})!=1:
            raise QualificationError('shared nuisance changed within episode; split episodes or supply a different conditional model')
        if len({b.realization_id for r,b in entries})!=1:
            raise QualificationError('physical realization changed within episode')
        truth=d['source_ids'].index(next(iter(identities)))
        # Truth is only used after inference by the metric evaluator.
        post=JointPosterior(model.channel);audit=AuditLedger(model.channel)
        target=out/'episodes'/hashlib.sha256(episode.encode()).hexdigest()[:12]
        ledger=RawObservationLedger(target/'raw_ledger');rows=[]
        for r,b in sorted(entries,key=lambda x:float(x[1].times_s[0])):
            action=int(r['action']);audit.prepare(action,model_version='frozen-native-estimate')
            ledger.append(b,action);symbol=int(model.encode(action,b.values,b.times_s,SamplingContract(**d['sampling_contract'])))
            post.update(action,symbol,b.block_id);snap=audit.update(action,symbol,b.block_id)
            rows.append({'event_id':b.block_id,'time_s':float(b.times_s[-1]),'action':action,'symbol':symbol,
                'source_map':post.map_points(),'audit_list':list(snap.compatible_now),
                **source_metrics(post.source,truth,model.channel.source_xy)})
        (target/'replay.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
        export_source_map(model.channel.source_xy,post.source,target/'source_probability_map.npz')
        results.append({'episode_id':episode,'worlds':sorted({b.realization_id for _,b in entries}),
                        'n_blocks':len(rows),'final':rows[-1]})
    result={'status':'FIXED_TRAJECTORY_REPLAY_COMPLETE','n_episodes':len(results),
            'model_frozen':True,'active_flight':False,'results':results,
            'scientific_scope':'conditional on manifest physical review and proper sequential likelihood assumption'}
    (out/'REPLAY_RESULT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    return result
