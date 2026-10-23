"""Independent scalar QA of finite TRAIN diagnostics and one frozen DEV check."""
from pathlib import Path
import csv,json
import numpy as np
from common import PROJECT,OUT,PROTOCOL,sha,write,csvout,dataset
from analyze_train import METHODS,make_features
from gsl_discrimination.m1_opponent.operator import time_weights

def scalar_features(raw,t):
    log=np.log1p(raw);w=time_weights(t);di=np.arange(0,2*(len(t)//2),2)
    wd=time_weights(t[di]);order=sorted(range(len(t)),key=lambda i:(float(log[i,0]),float(log[i,1])))
    hit=(raw>=.1).astype(float)
    return [log[:,0],log[:,1],np.array([np.dot(log[:,0],w)]),np.array([np.dot(log[:,1],w)]),
       np.array([np.dot(hit[:,0],w)]),np.array([np.dot(hit[:,1],w)]),w@log,wd@log[di],w@hit,
       log.ravel(),log[order].ravel(),np.sort(log,axis=0).ravel(),log[di].ravel()]

def main():
    freeze=json.loads((OUT/'INPUT_FREEZE.json').read_text())
    assert sha(PROTOCOL)==freeze['protocol_sha256']
    for f,h in freeze['previous_frozen_files'].items():assert sha(PROJECT/f)==h
    selection=json.loads((OUT/'SELECTION_FREEZE.json').read_text())
    assert sha(Path(__file__).with_name('analyze_train.py'))==selection['analysis_code_sha256']
    assert sha(OUT/'TRAIN_PAIR_WORLD_OUTCOMES.npz')==selection['results_sha256']
    values,times,receipt=dataset()
    for r in receipt['worlds']:assert sha(OUT/r['file'])==r['sha256']
    assert len(receipt['worlds'])==4 and receipt['DEV_raw_frames_read']==0
    # Explicit explanation of a pre-analysis correction; not a post-score
    # change to a frozen comparison or selection gate.
    old_hash=freeze['code_sha256'].get('native/observability_20261023/analyze_train.py')
    write('PRE_ANALYSIS_SCOPE_CORRECTION.json',{'file':'analyze_train.py','input_stage_sha256':old_hash,
        'first_scoring_and_selection_sha256':selection['analysis_code_sha256'],
        'reason':'physical concentration gain cannot be applied as a linear gain to a thresholded hit fraction; these entries marked not applicable with prediction sentinel -2',
        'applied_before_first_TRAIN_scoring':True,'primary_known_amplitude_scores_and_selection_unchanged':True,
        'not_a_new_model_or_post_DEV_retune':True})
    checks=[];max_error=0.
    with np.load(OUT/'TRAIN_PAIR_WORLD_OUTCOMES.npz') as z:
        pairs=z['pairs'];prediction=z['prediction'];margins=z['signed_margin'];anchors=z['anchors'];truth=z['truth']
    for wi in (0,9,18):
        a=int(anchors[wi]);keep=np.flatnonzero((times>=a)&(times<=a+20));t=times[keep]
        for pi in (0,9,200,434):
            pair=pairs[pi]
            for source in range(2):
                for repeat in range(2):
                    obs=values[source,repeat][keep][:,pair]
                    fs=scalar_features(obs,t)
                    for mi,method in enumerate(METHODS):
                        ds=[]
                        for s in range(2):
                            template=values[s,1-repeat][keep][:,pair]
                            mu=scalar_features(template,t)[mi]
                            delta=fs[mi]-mu;ds.append(float(np.dot(delta,delta)/len(delta)))
                        tie=abs(ds[0]-ds[1])<=1e-12*max(1.,*ds)
                        pred=-1 if tie else int(ds[1]<ds[0])
                        expected=int(prediction[wi,0,mi,source*2+repeat,pi])
                        assert pred==expected
                        m=(ds[1-source]-ds[source])/max(sum(ds),1e-12)
                        error=abs(m-float(margins[wi,0,mi,source*2+repeat,pi]));max_error=max(max_error,error)
                        assert error<1e-10
                        checks.append({'anchor':a,'pair_index':pi,'source':source,'repeat':repeat,'method':method,'prediction':pred})
    # Gates are recomputed from saved classifications, independently of CSV.
    correct=np.sum(prediction[:,0]==truth[None,None,:,None],axis=2)
    single=correct[:,:6].max(axis=1);static=correct[:,[6,7,8]].max(axis=1)
    dynamic=(single<=3)&(static<=3)&(correct[:,10]<=3)&(correct[:,9]==4)&(correct[:,12]==4)
    spatial=(single<=3)&(correct[:,6]==4)&(correct[:,7]==4)
    result=json.loads((OUT/'TRAIN_ANALYSIS_RESULT.json').read_text())
    assert int(dynamic.sum())==result['dynamic_opportunity_pair_windows']
    assert int(spatial.sum())==result['spatial_opportunity_pair_windows']
    # Earlier 50-70 records must be an exact subset of this new full TRAIN
    # extraction. This catches probe, clock, pool and run-axis mistakes.
    first=np.flatnonzero((times>=50)&(times<=70))
    from gsl_discrimination.data import SynchronousBlock
    for s in range(2):
        for r in range(2):
            run=receipt['worlds'][2*s+r]['run_id']
            b=SynchronousBlock.load_npz(PROJECT/'results/native_20261023/blocks'/(run+'.npz'))
            assert np.array_equal(values[s,r,first][:,[11,16]],b.values)
    # Post-startup intermittency and actual local wind equality are descriptive
    # controls; no additional pair is selected from them.
    post=times>=50;rows=[]
    for s in range(2):
        for r in range(2):
            for p in range(30):
                x=values[s,r,post,p];hit=x>=.1;pos=x>0
                rows.append({'world_id':receipt['worlds'][2*s+r]['run_id'],'probe_rank':p+1,
                    'frames_post50':len(x),'exact_positive_fraction':float(pos.mean()),'hit_0p1_fraction':float(hit.mean()),
                    'exact_positive_switches':int(np.sum(pos[1:]!=pos[:-1])),
                    'hit_0p1_switches':int(np.sum(hit[1:]!=hit[:-1])),
                    'all_zero':bool(not pos.any()),'all_positive':bool(pos.all()),
                    'all_below_0p1':bool(not hit.any()),'all_above_0p1':bool(hit.all())})
    csvout('POST50_WORLD_PROBE_STATISTICS.csv',rows)
    winds=[]
    for r in receipt['worlds']:
        with np.load(OUT/r['file']) as z:winds.append(z['local_wind_mps'])
    assert all(np.array_equal(w,winds[0]) for w in winds)
    dev_check=json.loads((OUT/'DEV_CHECK_RESULT.json').read_text())
    dev_checks=0
    if dev_check['status']=='ONE_FROZEN_DEVELOPMENT_CHECK_COMPLETE':
        f=json.loads((OUT/'DEV_MODEL_FREEZE.json').read_text())
        assert sha(OUT/f['model_path'])==f['model_sha256']
        dev=[]
        for r in dev_check['worlds']:
            assert sha(OUT/r['file'])==r['sha256']
            with np.load(OUT/r['file']) as z:dev.append(z['values_ppm']);tt=z['times_s']
        dev=np.array(dev).reshape(2,2,len(tt),2)
        with (OUT/'SELECTED_DEV_PER_WORLD.csv').open(encoding='utf-8-sig',newline='') as handle:
            expected=list(csv.DictReader(handle))
        for known,prefix in ((True,'known'),(False,'unknown_gain')):
            feat=make_features(dev,tt,np.array([[0,1]]),known)
            for method,x in feat.items():
                if not known and 'hitfraction' in method:continue
                with np.load(OUT/f['model_path']) as model:mu=model[prefix+'__'+method]
                for s in range(2):
                    for r in range(2):
                        y=x[s,r,0];dist=[]
                        for m in mu:
                            if known:d=float(np.dot(y-m,y-m)/len(y))
                            else:
                                a=max(0.,float(np.dot(y,m)/np.dot(m,m))) if np.dot(m,m)>0 else 0.
                                d=float(np.dot(y-a*m,y-a*m)/np.dot(y,y)) if np.dot(y,y)>0 else 0.
                            dist.append(d)
                        ref=next(row for row in expected if row['amplitude_scope']==prefix and row['method']==method and row['world_id']==dev_check['worlds'][2*s+r]['run_id'])
                        assert abs(dist[0]-float(ref['score_A']))<1e-10
                        assert abs(dist[1]-float(ref['score_B']))<1e-10
                        dev_checks+=1
    write('INDEPENDENT_QA.json',{'status':'PASS_SCOPED_AUDIT','scalar_known_profile_checks':len(checks),
        'max_margin_difference':max_error,'TRAIN_gate_counts_recomputed':True,'earlier_TRAIN_blocks_match_exactly':True,
        'all_four_world_local_winds_equal':True,'old_V7_files_unchanged':True,'M1_0p04_unchanged':True,
        'post50_world_probe_rows':len(rows),'no_new_House_seed_or_physics':True,
        'selected_DEV_scalar_scores_recomputed':dev_checks,
        'unknown_gain_hitfraction_cells':'not applicable, stored as -2; do not interpret their placeholder counts as a classifier',
        'full_sampling_software_scope':'ideal simulator snapshots; no hardware Nyquist or PID calibration asserted'})
    print('AUDIT_QA_PASS',len(checks),max_error)

if __name__=='__main__':main()
