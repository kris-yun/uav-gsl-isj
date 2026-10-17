"""Analyze frozen fixed-history diagnostics. Never constructs a new posterior."""
from pathlib import Path
import csv,gzip,hashlib,json,math,os
import numpy as np
R=Path(__file__).resolve().parents[1]
assert (R/'CONTRASTS_COMPLETE.json').exists()
O=Path(os.environ.get('C4H17_ANALYSIS_OUTPUT',str(R/'analysis')));O.mkdir(exist_ok=False)
plan=json.loads((R/'FROZEN_PLAN.json').read_text(encoding='utf-8'))
def rows(p):
    with p.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def write(name,data):
    if not data:return
    with (O/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
def lse(x):
    a=np.asarray(x,dtype=float);m=a.max();return float(m+np.log(np.exp(a-m).sum()))
jobs=rows(R/'inputs/jobs.csv');jdict={(a['key'],int(a['seed']),a['job_id']):a for a in jobs}
responses=[];costs=[];blocks=[];correlations=[];checks=[];pairs=[];cumpairs=[];fullmapdiff=[];obsrows=[];rawpid=[]
loaded={};blockmaps={};cummaps={};raw_for_convergence={}
for context in plan['cases']:
    key=context['key'];meta=context['metadata'];n=meta['width']*meta['height'];case=key.split('_')[0]
    inp=rows(R/'inputs'/key/'input.csv');rxs=rows(R/'inputs'/key/'receivers.csv')
    free=np.array([r['occupancy']=='1' for r in inp]);conf=np.array([float(a['confidence']) for a in inp]);prob=1-1/(1+np.exp(np.array([float(a['logOdds']) for a in inp])))
    def score(mp):return float(np.log(1-context['settings']['sourceDiscriminationPower']*conf[free]*np.abs(prob[free]-mp[free])).sum())
    for rx in rxs:obsrows.append(dict(key=key,**rx))
    for a in rows(R/'inputs'/f'{case}_consumer_messages.csv'):
        if a['kind']!='gas':continue
        nearest=min(rxs,key=lambda b:math.hypot(float(a['map_x'])-float(b['receiver_x']),float(a['map_y'])-float(b['receiver_y'])))
        dist=math.hypot(float(a['map_x'])-float(nearest['receiver_x']),float(a['map_y'])-float(nearest['receiver_y']))
        rawpid.append(dict(key=key,receipt_ns=a['receipt_ns'],stamp_ns=a['stamp_ns'],ppm_unthresholded=a['value'],x=a['map_x'],y=a['map_y'],
                           matched_stop=nearest['stop'] if dist<1e-4 else '',position_error_m=dist,
                           received_no_later_than_update=int(a['receipt_ns'])<=meta['stamp_ns'],
                           exact_consumed_window_owner_known=False))
    for condition in plan['conditions']:
        cond=condition['id']
        for seed in plan['prediction_states']:
            root=R/'results'/key/cond/str(seed)
            actual=rows(root/'scores.csv');source_data={};cm={};bm={}
            for a in actual:
                ident=a['job_id'];job=jdict[(key,seed,ident)];q=root/ident
                raw=np.fromfile(q/'raw.f32','<f4');blur=np.fromfile(q/'blur.f32','<f4');assert len(raw)==len(blur)==n
                ls=float(a['source_logscore']);error=abs(score(blur)-ls);assert error<1e-12
                checks.append(error);source_data[ident]=(raw,blur,ls)
                cost=dict(key=key,condition=cond,seed=seed,job_id=ident,source_mode=job['mode'],
                          warmup_seconds=float(a['warmup_steps'])*.2,record_seconds=float(a['record_steps'])*.1,
                          **{k:float(a[k]) for k in ['cpu_s','wall_s']},
                          **{k:int(a[k]) for k in ['emitted','exited','warm_survivors','final_survivors','particle_moves','warmup_steps','record_steps']})
                costs.append(cost)
                trace=np.frombuffer(gzip.decompress((q/'trace.u32.gz').read_bytes()),dtype='<u4').reshape(-1,9+3*len(rxs))
                W,T=int(a['warmup_steps']),int(a['record_steps']);warm=trace[trace[:,0]==0];rec=trace[trace[:,0]==1]
                assert len(warm)==W and len(rec)==T
                assert np.all(trace[:,5].astype('i8')-trace[:,6].astype('i8')==trace[:,3].astype('i8'))
                assert int(trace[:,2].astype('u8').sum())==int(a['particle_moves'])
                assert (int(trace[-1,7])+(int(trace[-1,8])<<32))==int(a['particle_moves'])
                late=warm[-min(W,300):]
                warm_delta=int(late[-1,3])-int(late[0,2]-5)
                for ri,rx in enumerate(rxs):
                    cell=int(rx['cell_index']);hits=(rec[:,9+3*ri]>0).astype(float)
                    assert np.float32(hits.sum()/T)==raw[cell]
                    hitcount=rec[:,9+3*ri].astype('u8')
                    visit=trace[:,10+3*ri].astype('u8')
                    first=np.flatnonzero(trace[:,9+3*ri]>0)
                    firsttime=(float(trace[first[0],1]-1)*.2 if trace[first[0],0]==0 else W*.2+float(trace[first[0],1]-1)*.1) if len(first) else None
                    responses.append(dict(key=key,condition=cond,seed=seed,job_id=ident,source_mode=job['mode'],
                        stop=int(rx['stop']),receiver_cell=cell,receiver_x=rx['receiver_x'],receiver_y=rx['receiver_y'],
                        consumed_by_this_update=bool(int(rx['consumed_by_this_update'])),observed_window_hit_fraction=float(rx['hit_fraction']),
                        window_mean_ppm_min=float(rx['window_mean_ppm_min']),window_mean_ppm_max=float(rx['window_mean_ppm_max']),window_mean_ppm_mean=float(rx['window_mean_ppm_mean']),
                        raw_frequency=float(raw[cell]),blurred_frequency=float(blur[cell]),source_logscore=ls,
                        nominal_warmup_s=W*.2,record_s=T*.1,first_occupied_sample_time_s=firsttime,
                        unique_filaments_ever_observed=int(visit.sum()),record_occupied_frames=int(hits.sum()),
                        record_filament_occupancies=int(hitcount.sum()),record_cell_entries=int(rec[:,11+3*ri].astype('u8').sum()),
                        warm_survivors=int(a['warm_survivors']),final_survivors=int(a['final_survivors']),
                        late_warmup_60s_survivor_delta=warm_delta,
                        late_warmup_60s_exit_count=int(late[:,4].astype('u8').sum())))
                    if hits.var()>0:
                        centered=hits-hits.mean();v=float(centered@centered);ac=[]
                        for lag in range(1,min(T//4,200)+1):ac.append(float(centered[:-lag]@centered[lag:]/v))
                        pos=[]
                        for x in ac:
                            if x<=0:break
                            pos.append(x)
                        tau=max(1.,1+2*sum(pos))
                    else:tau=None
                    correlations.append(dict(key=key,condition=cond,seed=seed,job_id=ident,stop=int(rx['stop']),
                        record_frames=T,nonconstant_binary_trace=bool(hits.var()>0),descriptive_integrated_autocorrelation_frames=tau,
                        descriptive_effective_frames=T/tau if tau is not None else None,independent_world_repeats=1,confidence_interval_claim=False))
                    for phase,arr,dt,steps in [('warmup',warm,.2,50),('record',rec,.1,100)]:
                        for start in range(0,len(arr),steps):
                            part=arr[start:start+steps];x=(part[:,9+3*ri]>0)
                            blocks.append(dict(key=key,condition=cond,seed=seed,job_id=ident,stop=int(rx['stop']),phase=phase,
                                start_s=start*dt,end_s=(start+len(part))*dt,frames=len(part),raw_frequency=float(x.mean()),
                                unique_new_filaments=int(part[:,10+3*ri].astype('u8').sum()),entries=int(part[:,11+3*ri].astype('u8').sum()),
                                active_before=int(part[0,2]),active_after=int(part[-1,3]),
                                exits=int(part[:,4].astype('u8').sum())))
                bm[ident]={};cm[ident]={}
                for t in range(100,T+1,100):
                    rb=np.fromfile(q/f'block_{t}_raw.f32','<f4');bb=np.fromfile(q/f'block_{t}_blur.f32','<f4')
                    bm[ident][t]=(rb,bb,score(bb))
                for t in range(200,T+1,200):
                    rc=np.fromfile(q/f'cumulative_{t}_raw.f32','<f4');bc=np.fromfile(q/f'cumulative_{t}_blur.f32','<f4')
                    cm[ident][t]=(rc,bc,score(bc))
            loaded[(key,cond,seed)]=source_data;blockmaps[(key,cond,seed)]=bm;cummaps[(key,cond,seed)]=cm
            def pair_rows(data,seconds=None):
                fine=[v[2] for k,v in data.items() if k.startswith('fine_truth_')]
                truecell=f"fine_truth_{context['context']['truth_idx']}"
                specs=[('native_true_region',data['region_truth'][2],'region_competitor'),
                       ('all_subsources_area_likelihood',lse(fine)-math.log(len(fine)),'fine_competitor'),
                       ('true_0p25m_cell',data[truecell][2],'fine_competitor'),
                       ('exact_point_oracle',data['oracle_true'][2],'region_competitor')]
                result=[]
                for rep,truth,comp in specs:
                    comp_score=data[comp][2] if comp in data else None
                    result.append(dict(key=key,condition=cond,seed=seed,representation=rep,record_seconds=seconds if seconds is not None else condition['record_steps']*.1,
                        truth_logscore=truth,competitor_logscore=comp_score,truth_minus_competitor_logscore=truth-comp_score if comp_score is not None else None,
                        new_full_posterior=False,competitor_prelocked=comp_score is not None))
                return result
            pairs+=pair_rows(source_data)
            for t in range(200,condition['record_steps']+1,200):
                cumpairs+=pair_rows({ident:values[t] for ident,values in cm.items()},t*.1)
    # Common-prefix check: changing only the recording duration cannot alter its past.
    for seed in plan['prediction_states']:
        for longer in ['W180_R40','W180_R80']:
            for ident,data in cummaps[(key,longer,seed)].items():
                base=loaded[(key,'W180_R20',seed)][ident]
                assert data[200][0].tobytes()==base[0].tobytes()
                assert data[200][1].tobytes()==base[1].tobytes()
        for ident,data in cummaps[(key,'W180_R80',seed)].items():
            base=loaded[(key,'W180_R40',seed)][ident]
            assert data[400][0].tobytes()==base[0].tobytes() and data[400][1].tobytes()==base[1].tobytes()
        for left,right in [('W45_R20','W90_R20'),('W90_R20','W180_R20'),('W180_R20','W360_R20')]:
            for ident,a in loaded[(key,left,seed)].items():
                b=loaded[(key,right,seed)][ident]
                fullmapdiff.append(dict(key=key,seed=seed,job_id=ident,earlier=left,later=right,
                    raw_Linf=float(np.max(np.abs(a[0][free]-b[0][free]))),raw_L1_mean=float(np.mean(np.abs(a[0][free]-b[0][free]))),
                    blur_Linf=float(np.max(np.abs(a[1][free]-b[1][free]))),blur_L1_mean=float(np.mean(np.abs(a[1][free]-b[1][free]))),
                    source_logscore_change=b[2]-a[2]))

# State ranges and paired changes are descriptive; no independence or CI claim.
summary=[]
for context in plan['cases']:
 key=context['key']
 for cond in [a['id'] for a in plan['conditions']]:
  for rep in sorted({a['representation'] for a in pairs}):
   values=[a for a in pairs if a['key']==key and a['condition']==cond and a['representation']==rep]
   gaps=[a['truth_minus_competitor_logscore'] for a in values if a['truth_minus_competitor_logscore'] is not None]
   baseline={a['seed']:a for a in pairs if a['key']==key and a['condition']=='adaptive_R20' and a['representation']==rep}
   changes=[a['truth_minus_competitor_logscore']-baseline[a['seed']]['truth_minus_competitor_logscore'] for a in values if a['truth_minus_competitor_logscore'] is not None]
   summary.append(dict(key=key,condition=cond,representation=rep,prediction_states=len(values),
      truth_logscore_min=min(a['truth_logscore'] for a in values),truth_logscore_max=max(a['truth_logscore'] for a in values),
      pair_gap_min=min(gaps) if gaps else None,pair_gap_max=max(gaps) if gaps else None,
      paired_change_from_adaptive_min=min(changes) if changes else None,paired_change_from_adaptive_max=max(changes) if changes else None,
      states_truth_outranks_locked_competitor=sum(x>0 for x in gaps) if gaps else None))

write('SOURCE_RECEIVER_RESPONSES.csv',responses);write('SOURCE_PAIR_LOGSCORES.csv',pairs);write('PAIR_SUMMARY.csv',summary)
write('CUMULATIVE_PAIR_LOGSCORES.csv',cumpairs);write('TEMPORAL_RECEIVER_BLOCKS.csv',blocks);write('TEMPORAL_CORRELATION_DIAGNOSTICS.csv',correlations)
write('FULL_MAP_DURATION_DIFFERENCES.csv',fullmapdiff);write('COSTS.csv',costs);write('RECEIVER_OBSERVATIONS.csv',obsrows);write('RAW_PID_UNTHRESHOLDED.csv',rawpid)
audit=dict(status='PASS_FROZEN_DATA_ANALYSIS',forward_calls=len(costs),max_full_map_logscore_recompute_error=max(checks),
           receiver_response_rows=len(responses),temporal_blocks=len(blocks),raw_pid_rows=len(rawpid),
           native_movement_release_and_rng_adaptive_parity=True,record_window_common_prefix_byte_parity=True,
           trace_emission_exit_conservation=True,trace_move_totals_match=True,receiver_trace_equals_raw_map=True,
           new_full_posterior_generated=False,new_task_gain_claim=False,
           total_simulation_cpu_s=sum(a['cpu_s'] for a in costs),total_particle_moves=sum(a['particle_moves'] for a in costs),
           fixed_historic_2d_wind=True,raw_pid_owner_limit='Raw gas rows retain timestamps and positions. Proximity association does not certify exact ownership of each averaged consumption window.')
(O/'NUMERICAL_CHECKS.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
(O/'PAIR_SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(audit,ensure_ascii=False,indent=2))
