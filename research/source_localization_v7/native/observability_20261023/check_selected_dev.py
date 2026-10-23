"""Freeze one TRAIN-selected ordinary comparison, then query DEV only once."""
from pathlib import Path
import csv,json,sys,time
import numpy as np
from common import PROJECT,OUT,PROTOCOL,OCC,run_path,sha,write,csvout,dataset,probes,points_for_probes,NativeQuery,decode_frame
from analyze_train import METHODS,make_features,score

MODEL=OUT/'SELECTED_ORDINARY_MODEL.npz'

def prepare():
    selection=json.loads((OUT/'SELECTION_FREEZE.json').read_text())
    if selection['selected'] is None:
        write('DEV_CHECK_RESULT.json',{'status':'NOT_EXECUTED_NO_TRAIN_CANDIDATE','new_DEV_queries':0});return
    if (OUT/'DEV_MODEL_FREEZE.json').exists():raise RuntimeError('selected model already frozen')
    c=selection['selected'];v,t,receipt=dataset();idx=c['window_indices']
    pairs=np.array([[c['probe_L']-1,c['probe_R']-1]])
    models={}
    for known,prefix in ((True,'known'),(False,'unknown_gain')):
        feat=make_features(v[:,:,idx,:],t[idx],pairs,known)
        for method,x in feat.items():
            if not known and 'hitfraction' in method:continue
            models[prefix+'__'+method]=x.mean(axis=1)[:,0,:]
    np.savez_compressed(MODEL,**models,times_s=t[idx])
    write('DEV_MODEL_FREEZE.json',{'status':'FROZEN_BEFORE_SELECTED_DEV_QUERY','candidate':c,
       'model_path':MODEL.name,'model_sha256':sha(MODEL),'selection_freeze_sha256':sha(OUT/'SELECTION_FREEZE.json'),
       'protocol_sha256':sha(PROTOCOL),'TRAIN_realizations':[r['run_id'] for r in receipt['worlds']],
       'fit':'arithmetic mean of the two TRAIN feature profiles for each source; fixed nearest-profile scores',
       'calibrated_probability_model':False,'source_height_confound':True,
       'methods':list(models),'DEV_access_at_this_stage':False,'code_sha256':sha(__file__),
       'test_status':'previously opened development worlds, not new blind test'})
    print('DEV_MODEL_FROZEN',c)

def evaluate():
    if (OUT/'DEV_CHECK_RESULT.json').exists():raise RuntimeError('first DEV result already exists, no alternate pair')
    freeze=json.loads((OUT/'DEV_MODEL_FREEZE.json').read_text())
    assert sha(MODEL)==freeze['model_sha256'] and sha(__file__)==freeze['code_sha256']
    config=json.loads(PROTOCOL.read_text());c=freeze['candidate'];pp=probes()
    chosen=[pp[c['probe_L']-1],pp[c['probe_R']-1]];points=points_for_probes(chosen)
    query=NativeQuery(OCC,PROJECT/'native/native_query.dll');all_values=[];receipts=[]
    started=time.perf_counter()
    for run in config['allowed_DEV_runs_after_selection_freeze']:
        root=run_path(run)
        with (root/'RECORD_TIMELINE.tsv').open(newline='') as f:timeline=list(csv.DictReader(f,delimiter='\t'))
        with (root/'OUTPUT_SHA256SUMS.tsv').open(newline='') as f:expected={r['name']:r for r in csv.DictReader(f,delimiter='\t')}
        indices=[i for i,r in enumerate(timeline) if c['anchor_s']<=float(r['internal_simulation_time_s'])<=c['anchor_s']+20]
        assert indices==c['window_indices']
        gas=[];wind=[];cache={}
        for i in indices:
            r=timeline[i];path=root/('iteration_'+r['record_index']);assert sha(path)==expected[path.name]['sha256']
            frame=decode_frame(path);assert frame['wind_index']==int(r['wind_index'])
            gas.append(query.query(frame,points).reshape(2,4).mean(1,dtype=np.float64))
            wi=frame['wind_index']
            if wi not in cache:cache[wi]=query.local_wind(root/'wind'/('wind_iteration_'+str(wi)),points).reshape(2,4,3).mean(1)
            wind.append(cache[wi])
        values=np.array(gas);times=np.array([float(timeline[i]['internal_simulation_time_s']) for i in indices])
        with np.load(MODEL) as z:assert np.array_equal(times,z['times_s'])
        p=OUT/'selected_DEV'/f'{run}.npz';p.parent.mkdir(exist_ok=True)
        np.savez_compressed(p,values_ppm=values,times_s=times,local_wind_mps=np.array(wind),
             positions_m=np.array([[float(p['center_x_m']),float(p['center_y_m']),float(p['z_m'])] for p in chosen]))
        receipts.append({'run_id':run,'file':str(p.relative_to(OUT)).replace('\\','/'),'sha256':sha(p),
              'source':'B' if '_s2x_' in run else 'A','repeat':int(run[-2:]),'frames_read':len(indices)})
        all_values.append(values)
    # Same ordering as four TRAIN worlds; only evaluator uses source labels.
    x=np.array(all_values).reshape(2,2,len(times),2);rows=[]
    for known,prefix in ((True,'known'),(False,'unknown_gain')):
        features=make_features(x,times,np.array([[0,1]]),known)
        for method,feature in features.items():
            if not known and 'hitfraction' in method:continue
            with np.load(MODEL) as z:mu=z[prefix+'__'+method]
            for s in range(2):
                for r in range(2):
                    y=feature[s,r,0]
                    d=np.array([score(y,mu[k],not known) for k in range(2)])
                    tie=bool(abs(d[0]-d[1])<=1e-12*max(1.,float(d.max())))
                    pred=-1 if tie else int(np.argmin(d))
                    rows.append({'world_id':receipts[2*s+r]['run_id'],'source':('A','B')[s],
                        'amplitude_scope':prefix,'method':method,'score_A':float(d[0]),'score_B':float(d[1]),
                        'prediction':pred,'strict_correct':pred==s,'tie':tie,
                        'MAP_error_m':None if tie else (0. if pred==s else float(np.linalg.norm(np.array([-.6,1.95])-np.array([-.4,-2.9]))))})
    csvout('SELECTED_DEV_PER_WORLD.csv',rows)
    summary=[]
    for prefix in ('known','unknown_gain'):
        for method in METHODS:
            rr=[r for r in rows if r['amplitude_scope']==prefix and r['method']==method]
            if not rr:continue
            summary.append({'amplitude_scope':prefix,'method':method,'worlds':len(rr),
                'strict_correct':sum(r['strict_correct'] for r in rr),'ties':sum(r['tie'] for r in rr),
                'wrong':sum(not r['strict_correct'] and not r['tie'] for r in rr),
                'mean_MAP_error_m_among_nonties':float(np.mean([r['MAP_error_m'] for r in rr if not r['tie']])) if any(not r['tie'] for r in rr) else None})
    csvout('SELECTED_DEV_SUMMARY.csv',summary)
    write('DEV_CHECK_RESULT.json',{'status':'ONE_FROZEN_DEVELOPMENT_CHECK_COMPLETE','candidate':c,
       'worlds':receipts,'model_freeze_sha256':sha(OUT/'DEV_MODEL_FREEZE.json'),'summaries':summary,
       'calibrated_source_probabilities_claimed':False,'new_blind_test':False,
       'new_M1_M2_M3_fit':False,'new_physics':0,'new_ROS':0,'wall_s':time.perf_counter()-started})
    print(json.dumps(summary,indent=2))

if __name__=='__main__':
    if sys.argv[1:]==['evaluate']:evaluate()
    else:prepare()
