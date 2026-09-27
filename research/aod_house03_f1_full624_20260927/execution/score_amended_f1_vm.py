#!/usr/bin/env python3
"""Execution adapter to unchanged archived B2 and signed full624 evaluator."""
import csv, hashlib, json, subprocess, sys, time
from pathlib import Path
import numpy as np
import pandas as pd
from resume_amended_f1_vm import R,O,sha,read,write,check_freeze
sys.path.insert(0,str(R/'amplitude_implementation'))
from amplitude_readout import AmplitudeTemplates,Arm,EPS

def main(out):
    check_freeze();f=json.loads((O/'TARGET_DATA_FREEZE.json').read_text());assert f['passed'] and f['targets']==96
    for n,h in f['all_artifact_sha256'].items():assert sha(O/'target_data'/n)==h
    out.mkdir(exist_ok=False)
    y=np.load(O/'target_data/TARGET_PATHS_12x8x2x10.npy',allow_pickle=False)
    assert y.shape==(12,8,2,10)
    sources=read(R/'protocol/frozen/HOUSE03_F1_TRUTH_PANEL_12.tsv')
    support=pd.read_csv(R/'templates/CANDIDATE_SUPPORT.csv')
    assert len(support)==624 and support.source_id.nunique()==624
    arrays=np.load(R/'templates/candidate_path_templates.npz',allow_pickle=False)
    records=[];diagnostics=[];zero_count=0;cost={}
    with (out/'FULL624_CANDIDATE_SCORES.csv').open('w',newline='') as handle:
        w=csv.writer(handle,lineterminator='\n')
        w.writerow(['condition','truth_source','realization','path','arm','candidate_source','SSE','gain','map_error_m'])
        for condition in ['nominal','state0_stress']:
            for si,source in enumerate(sources):
                truth=str(source['source_id']);truthidx=int(np.flatnonzero(support.source_id.to_numpy()==truth)[0])
                other=next(x for x in sources if x['pair_id']==source['pair_id'] and x['source_id']!=truth)
                pairidx=int(np.flatnonzero(support.source_id.to_numpy()==other['source_id'])[0])
                distance=np.hypot(support.x.to_numpy()-float(source['x_m']),support.y.to_numpy()-float(source['y_m']))
                for ri in range(8):
                    for pi,path in enumerate(['A','B']):
                        observed=y[si,ri,pi,:,None];zero=not np.any(observed);zero_count+=int(zero)
                        margins={}
                        for kind in ['u','rawu']:
                            start=time.perf_counter()
                            pred=np.maximum(arrays[f'{condition}_{kind}_path_{path}'][:,:,None],EPS)
                            bank=AmplitudeTemplates(Arm(kind+'_footprint'),pred[:,0,:],pred)
                            sse,gain=bank.score(observed)
                            cost.setdefault('prepare_and_score_seconds',[]).append(time.perf_counter()-start)
                            assert np.isfinite(sse).all() and np.isfinite(gain).all()
                            if zero:assert (sse==0).all(), 'Zero observations must tie'
                            for ci in range(624):w.writerow([condition,truth,ri,path,kind,str(support.source_id.iloc[ci]),repr(float(sse[ci])),repr(float(gain[ci])),repr(float(distance[ci]))])
                            den=float(np.square(observed).sum())
                            margins[kind]=None if den==0 else float((sse[pairidx]-sse[truthidx])/den)
                        diagnostics.append(dict(condition=condition,truth_source=truth,realization=ri,path=path,
                            paired_candidate=other['source_id'],zero_observation=zero,
                            D_u=margins['u'],D_rawu=margins['rawu'],
                            Delta_pair=None if zero else margins['rawu']-margins['u']))
    pd.DataFrame(diagnostics).to_csv(out/'PAIR_DIAGNOSTICS.csv',index=False)
    subprocess.run([sys.executable,str(R/'protocol/evaluate_f1_full624.py'),'--scores',str(out/'FULL624_CANDIDATE_SCORES.csv'),'--out',str(out)],check=True)
    summaries={}
    for condition,file in [('nominal','NOMINAL_FULL624_TARGET_METRICS.csv'),('state0_stress','STATE0_FULL624_TARGET_METRICS.csv')]:
        m=pd.read_csv(out/file);arms={}
        for arm in ['u','rawu']:
            a=m[m.arm==arm]
            arms[arm]=dict(mean_rank=float(a.true_rank.mean()),unique_top1=float(a.unique_top1.mean()),
                          top3=float((a.true_rank<=3).mean()),mean_map_error_m=float(a.map_error_m.mean()))
        pair=m.pivot(index=['truth_source','realization','path'],columns='arm',values='unique_top1')
        per=pair.reset_index();per['effect']=per.rawu-per.u
        arms['rescued_path_targets']=int(((pair.rawu==1)&(pair.u==0)).sum())
        arms['harmed_path_targets']=int(((pair.rawu==0)&(pair.u==1)).sum())
        effects=per.groupby('truth_source').effect.mean()
        arms['improved_sources']=int((effects>0).sum());arms['harmed_sources']=int((effects<0).sum())
        summaries[condition]=arms
    write(out/'DESCRIPTIVE_METRICS.json',dict(metrics=summaries,zero_path_observations=zero_count//2,
          independent_plumes=96,paths_not_independent=True,secondary_baselines='Not part of signed primary gate'))
    # Runtime is diagnostic and excluded from byte-identical scientific output.
    write(O/f'{out.name}_COMPUTATION_COST.json',dict(median_prepare_score_seconds=float(np.median(cost['prepare_and_score_seconds'])),
          calls=len(cost['prepare_and_score_seconds']),frozen_b2_module_sha256=sha(R/'amplitude_implementation/amplitude_readout.py')))
    write(out/'SCIENTIFIC_OUTPUT_HASHES.json',{p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file()})
if __name__=='__main__':main(Path(sys.argv[1]))
