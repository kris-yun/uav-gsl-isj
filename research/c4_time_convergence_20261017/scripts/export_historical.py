"""Retain the original captured adaptive result in addition to 3-state repeats."""
from pathlib import Path
import csv,hashlib,json,shutil
import numpy as np
R=Path(__file__).resolve().parents[1];P=R.parent/'NATIVE_PMFS_WIND_RECOVERY_20261014/PORTABLE_DATA'
plan=json.loads((R/'FROZEN_PLAN.json').read_text(encoding='utf-8'))
oldmanifest=json.loads((R.parent/'C4A17/INPUT_MANIFEST_SHA256.json').read_text(encoding='utf-8'))
def rows(p):
    with p.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
checks=[];source_rows=[];receiver_rows=[];pairs=[]
def cp(p,q):
    q.parent.mkdir(parents=True,exist_ok=True);h=hashlib.sha256(p.read_bytes()).hexdigest()
    rel=str(p.relative_to(P))
    assert h==oldmanifest[rel]['sha256'],rel
    shutil.copy2(p,q);assert h==hashlib.sha256(q.read_bytes()).hexdigest()
    checks.append(dict(original_relative_path=rel,sha256=h))
for case in plan['cases']:
    key=case['key'];c=key.split('_')[0];ep=case['context']['epoch'];ctx=case['context']
    native=P/f'cases/{c}/native_execution/runtime/updates/update_{ep}'
    out=R/'inputs/historical_native'/key;out.mkdir(parents=True,exist_ok=False)
    cp(native/'gaussian_cache.f32',out/'gaussian_cache.f32');cp(native/'gaussian_initial.csv',out/'gaussian_initial.csv')
    candidates={a['candidate_id']:a for a in rows(native/'candidates.csv')}
    selected=[('native_true_region',ctx['truth_parent'])]
    if ctx['prelocked_competitor_parent'] is not None:selected.append(('prelocked_competitor',ctx['prelocked_competitor_parent']))
    mr=case['metadata'];data=rows(R/'inputs'/key/'input.csv');free=np.array([a['occupancy']=='1' for a in data]);conf=np.array([float(a['confidence']) for a in data]);prob=1-1/(1+np.exp(np.array([float(a['logOdds']) for a in data])))
    source_scores={}
    for role,ident in selected:
        a=candidates[ident];maps={}
        for suffix in ['_unblurred.f32','.f32']:
            src=native/'maps'/(ident+suffix);cp(src,out/(role+suffix));maps[suffix]=np.fromfile(src,'<f4')
        point=native/a['points_file'];assert point.resolve().is_relative_to(native.resolve())
        cp(point,out/(role+'_source_points.f32'))
        raw,blur=maps['_unblurred.f32'],maps['.f32']
        ls=float(np.log(1-case['settings']['sourceDiscriminationPower']*conf[free]*np.abs(prob[free]-blur[free])).sum())
        assert abs(ls-float(a['logscore']))<1e-12;source_scores[role]=float(a['logscore'])
        warm=int(a['point_count'])//5-200
        source_rows.append(dict(key=key,reference='ORIGINAL_CAPTURED_ADAPTIVE_RESULT_NOT_A_NEW_RANDOM_STATE',source_role=role,source_id=ident,warmup_steps=warm,warmup_seconds=warm*.2,record_seconds=20,source_logscore=float(a['logscore']),rng_before=a['rng_before'],rng_after=a['rng_after'],source_releases=a['point_count']))
        for rx in rows(R/'inputs'/key/'receivers.csv'):
            k=int(rx['cell_index']);receiver_rows.append(dict(key=key,source_role=role,stop=rx['stop'],consumed_by_this_update=bool(int(rx['consumed_by_this_update'])),raw_frequency=float(raw[k]),blurred_frequency=float(blur[k]),source_logscore=float(a['logscore']),observed_window_hit_fraction=rx['hit_fraction']))
    (out/'candidates_selected.json').write_text(json.dumps({role:candidates[ident] for role,ident in selected},indent=2),encoding='utf-8')
    pairs.append(dict(key=key,truth_logscore=source_scores['native_true_region'],competitor_logscore=source_scores.get('prelocked_competitor'),
                      truth_minus_competitor_logscore=source_scores['native_true_region']-source_scores['prelocked_competitor'] if 'prelocked_competitor' in source_scores else None,
                      scope='ORIGINAL_CAPTURED_ADAPTIVE_HISTORY_NO_NEW_POSTERIOR'))
for name,data in [('HISTORICAL_NATIVE_SOURCE_REFERENCE.csv',source_rows),('HISTORICAL_NATIVE_RECEIVER_REFERENCE.csv',receiver_rows),('HISTORICAL_NATIVE_PAIR_REFERENCE.csv',pairs)]:
    with (R/'analysis'/name).open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
(R/'lineage/HISTORICAL_REFERENCE_VERIFY.json').write_text(json.dumps(dict(status='PASS_ORIGINAL_CAPTURED_REFERENCE_SHA_AND_NATIVE_LOGSCORE',files=checks,forward_calls=0),indent=2),encoding='utf-8')
print(json.dumps(pairs,indent=2))
