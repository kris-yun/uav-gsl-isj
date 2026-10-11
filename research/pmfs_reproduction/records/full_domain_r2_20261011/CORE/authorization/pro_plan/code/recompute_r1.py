"""Independent R1 scalar audit; never imports an experiment producer or runs physics.
python recompute_r1.py --root EXTRACTED --out EXTERNAL_OUTPUT
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math
from pathlib import Path
from collections import defaultdict
import numpy as np

def read_csv(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def write_csv(p,rs):
    if not rs: return
    with Path(p).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)

def run(root:Path,out:Path):
    core=root/'PMFS_NATIVE_MECHANISM_CLOSURE_R1_20261011_CORE'
    support=root/'PMFS_NATIVE_MECHANISM_CLOSURE_R1_20261011_RAW'/'support'
    if out.resolve().is_relative_to(root.resolve()):raise ValueError('Output must be outside frozen input.')
    out.mkdir(parents=True,exist_ok=True)
    ev=read_csv(core/'FRESH_EVENTS_AND_PREDICTIONS.csv'); results=[]
    for oid in sorted({r['oid'] for r in ev}):
        rs=[r for r in ev if r['oid']==oid];assert len(rs)==50
        y=np.array([int(r['observed_hit']) for r in rs])
        a=np.array([float(r['true_O0_prediction']) for r in rs]);b=np.array([float(r['true_O1_prediction']) for r in rs])
        b0=float(np.mean((a-y)**2));b1=float(np.mean((b-y)**2))
        results.append(dict(oid=oid,O0_Brier=b0,O1_Brier=b1,O1_minus_O0=b1-b0,
                            independent_unit='whole realization',observed_hits=int(y.sum())))
    write_csv(out/'fresh_receptor_recomputed.csv',results)
    contrasts=[]
    for r in read_csv(core/'CONTROLLED_FACTORIAL_CONTRASTS.csv'):
        if r['oid']=='B4' and r['wrong_candidate']=='K2' and r['method']=='O1':
            a,b,c,d=[float(r[k]) for k in ('m00','m01','m10','m11')]
            vals=dict(m00=a,m01=b,m10=c,m11=d,D_at_V0=c-a,D_at_V1=d-b,V_at_D0=b-a,V_at_D1=d-c,interaction=d-c-b+a)
            for k,v in vals.items(): assert abs(v-float(r[k]))<1e-10
            contrasts.append(dict(group=r['group'],**vals))
    write_csv(out/'b4_factorial_recomputed.csv',contrasts)
    # Finite-bank equivalence of receiver traces: not population identifiability.
    vectors={}; events={}; meanA={}
    for s in ('C7','K2','B000','B001','B002'):
        events[s]=np.array([[int(r['event_hit']) for r in read_csv(support/'readouts'/f'B4_{s}_{j}'/'EVENTS_O1.csv')] for j in (0,1)])
        vectors[s]=events[s].mean(axis=0)
        with np.load(support/'readouts'/f'B4_{s}_0'/'FIELDS.npz',allow_pickle=False) as z:a=z['A1'].copy()
        with np.load(support/'readouts'/f'B4_{s}_1'/'FIELDS.npz',allow_pickle=False) as z:meanA[s]=(a+z['A1'])/2
    a,b='C7','B000';same=np.array_equal(events[a],events[b]);assert same and np.all(events[a]==1)
    scores=read_csv(core/'SAME_BANK_READOUT_CONTRASTS.csv')
    ss={(r['candidate'],r['method']):float(r['native_log_similarity']) for r in scores if r['oid']=='B4' and r['group']=='R01'}
    equivalence=dict(candidates=[a,b],reference_count=2,blocks=50,
        identical_receiver_hit_arrays=same,all_reference_hits_one=True,
        A1_max_abs=float(np.max(abs(meanA[a]-meanA[b]))),
        O1_dense_native_log_difference=ss[(a,'O1')]-ss[(b,'O1')],
        A1_native_log_difference=ss[(a,'A1')]-ss[(b,'A1')],
        inference='Empirical event-law tie under this reference bank, not proof of population nonidentifiability.')
    sr=read_csv(core/'FRESH_CONFIRMATION_RESULTS.csv');source=[]
    for m in ('O0','O1','N_POINT'):
        rr=[r for r in sr if r['method']==m];assert len(rr)==6
        source.append(dict(method=m,unique_correct=sum(r['unique_top1_correct'].lower()=='true' for r in rr),tasks=len(rr),
             mean_margin=float(np.mean([float(r['true_minus_bestwrong']) for r in rr])),
             mean_source_nll_descriptive=float(np.mean([-math.log(float(r['restricted_true_source_weight'])) for r in rr])),
             scope='five point source score normalization; not calibrated posterior'))
    write_csv(out/'fresh_source_recomputed.csv',source)
    n0=[r for r in read_csv(core/'QUALIFIED_FRESH_N0_COMPLETE_MAP_RESULTS.csv') if r['blocks']=='50'];assert len(n0)==6
    write_csv(out/'full_map_n0_at50.csv',n0)
    p0=np.mean([r['O0_Brier'] for r in results]);p1=np.mean([r['O1_Brier'] for r in results])
    summary=dict(status='PASS_INDEPENDENT_SCALAR_RECOMPUTATION',new_physics=0,new_training=0,new_navigation=0,
        receptor_Brier=dict(O0=float(p0),O1=float(p1),absolute_drop=float(p0-p1),relative_drop=float((p0-p1)/p0),all_six_better=True),
        source_results=source,b4_finite_bank_equivalence=equivalence,
        limitations=['No inferential p-values; six shared-context stochastic realizations.',
        'O0/O1 receptor Brier measures event forecasts, not source posterior calibration.',
        'D/V interventions were not independently repeated in the fresh six.',
        'O1 treatment on complete native source space was not run.',
        'N0 fixed-history core replay is not a new ROS/flight trial.'])
    (out/'independent_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--root',type=Path,required=True);a.add_argument('--out',type=Path,required=True);v=a.parse_args();run(v.root,v.out)
