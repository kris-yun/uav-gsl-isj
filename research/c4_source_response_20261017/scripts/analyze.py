"""Fixed-history source and receiver diagnostics; no simulator or ROS calls."""
from pathlib import Path
import json,csv,math,subprocess,sys,hashlib,shutil,os
import numpy as np
R=Path(__file__).resolve().parents[1];P=R.parent/'NATIVE_PMFS_WIND_RECOVERY_20261014/PORTABLE_DATA'
plan=json.loads((R/'FROZEN_PLAN.json').read_text())
assert (R/'results/CONTRASTS_COMPLETE.json').exists()
O=R/'results/analysis';O.mkdir(exist_ok=False)
def rows(p):return list(csv.DictReader(p.open()))
def writecsv(p,rs):
    if not rs:return
    with p.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
def lse(a):m=np.max(a);return float(m+np.log(np.exp(a-m).sum()))
def cell(m,x,y):
    i=int(np.float32(np.float32(x)-np.float32(m['origin_x']))/np.float32(m['cell_size']))
    j=int(np.float32(np.float32(y)-np.float32(m['origin_y']))/np.float32(m['cell_size']))
    return i,j,i+j*m['width']
metrics=[];receiver_rows=[];source_rows=[];costs=[];posterior_rows=[];readouts=[];rechecks=[];contexts=[]
for item in plan['cases']:
    case,ep=item['case'],item['epoch'];key=f'{case}_update_{ep}';m=item['metadata'];n=m['width']*m['height']
    native=P/f'cases/{case}/native_execution/runtime/updates/update_{ep}'
    inp=rows(native/'input.csv');free=np.array([r['occupancy']=='1' for r in inp]);ii=np.flatnonzero(free)
    prob=1-1/(1+np.exp(np.array([float(r['logOdds']) for r in inp])));confidence=np.array([float(r['confidence']) for r in inp]);D=plan['parameters_by_case'][case]['sourceDiscriminationPower']
    truth=np.array(item['truth'][:2]);ti,tj,truth_idx=cell(m,*truth);assert free[truth_idx]
    prior=np.array([float(r['prior_posterior']) for r in inp]);competitor=int(ii[np.argmax(prior[ii])]) if ep>0 else None
    tree=[r for r in rows(native/'final_tree.csv') if r['has_children']=='0' and r['value']=='1']
    owner=np.full(n,'',object);groups={}
    for r in tree:
        idx=np.array([x+y*m['width'] for y in range(int(r['origin_j']),int(r['origin_j'])+int(r['size_j'])) for x in range(int(r['origin_i']),int(r['origin_i'])+int(r['size_i']))])
        assert np.all(free[idx]) and np.all(owner[idx]=='');owner[idx]=r['node_id'];groups[r['node_id']]=idx
    assert np.all((owner!='')==free)
    truth_parent=owner[truth_idx];comp_parent=owner[competitor] if competitor is not None else None
    x=(np.float32(m['origin_x'])+(np.arange(n)%m['width']+.5).astype('f4')*np.float32(m['cell_size'])).astype(float)
    y=(np.float32(m['origin_y'])+(np.arange(n)//m['width']+.5).astype('f4')*np.float32(m['cell_size'])).astype(float)
    xy=np.c_[x,y];distance=np.linalg.norm(xy-truth,axis=1)
    ev=np.loadtxt(R/f'inputs/{case}_measurement_events.csv',delimiter=',',ndmin=2);ev=ev[ev[:,0]<=m['stamp_ns']]
    stops=[]
    for stop in np.unique(ev[:,6]).astype(int):
        a=ev[ev[:,6]==stop];rx,ry=a[-1,4:6];ri,rj,idx=cell(m,rx,ry);valid=0<=ri<m['width'] and 0<=rj<m['height'] and free[idx]
        row=dict(case=case,epoch=ep,stop=stop,windows=len(a),window_mean_ppm_min=float(a[:,1].min()),window_mean_ppm_max=float(a[:,1].max()),window_mean_ppm_mean=float(a[:,1].mean()),hit_fraction=float(np.mean(a[:,1]>.1)),first_consumed_stamp_ns=int(a[0,0]),last_consumed_stamp_ns=int(a[-1,0]),receiver_x=float(rx),receiver_y=float(ry),native_cell_index=idx,receiver_2d_free=bool(valid),stop_pose_span_m=float(np.max(np.linalg.norm(a[:,4:6]-a[-1,4:6],axis=1))))
        row.update(native_measured_hit_probability=float(prob[idx]) if valid else None,native_confidence=float(confidence[idx]) if valid else None,native_u=float(inp[idx]['u']) if valid else None,native_v=float(inp[idx]['v']) if valid else None)
        stops.append(row);receiver_rows.append(row)
    def scoremap(mp):return float(np.log(1-D*confidence[free]*np.abs(prob[free]-mp[free])).sum())
    def metric(arm,seed,log_by_cell,leaflog):
        q=np.zeros(n);q[free]=np.exp(log_by_cell[free]-lse(log_by_cell[free]))
        order=ii[np.argsort(-q[ii],kind='stable')];cred=order[:np.searchsorted(np.cumsum(q[order]),.9)+1]
        point=xy[int(np.argmax(q))]
        r=dict(case=case,epoch=ep,arm=arm,prediction_state=seed,truth_cell_index=truth_idx,truth_parent=truth_parent,competitor_cell_index=competitor,competitor_parent=comp_parent,
               truth_logscore=float(log_by_cell[truth_idx]),truth_minus_competitor_logscore=float(log_by_cell[truth_idx]-log_by_cell[competitor]) if competitor is not None else None,
               truth_parent_minus_competitor_parent_loglike=float(leaflog[truth_parent]-leaflog[comp_parent]) if comp_parent is not None else None,
               truth_strict_rank=int(1+np.sum(q[free]>q[truth_idx])),truth_cell_probability=float(q[truth_idx]),truth_parent_probability=float(q[groups[truth_parent]].sum()),
               true_source_in90pct=bool(truth_idx in cred),mass_within_0p5m=float(q[distance<=.5].sum()),mass_within_1p5m=float(q[distance<=1.5].sum()),
               map_x=float(point[0]),map_y=float(point[1]),map_error_m=float(np.linalg.norm(point-truth)))
        metrics.append(r);readouts.append((m,ii,q,truth,r))
        for k in ii:posterior_rows.append(dict(case=case,epoch=ep,arm=arm,prediction_state=seed,cell_index=int(k),parent=owner[k],probability=float(q[k]),log_density=float(log_by_cell[k])))
        return q
    def source_diagnostics(arm,seed,ident,parent,raw,blur,logscore,indices):
        for s in stops:
            if not s['receiver_2d_free']:continue
            k=s['native_cell_index']
            source_rows.append(dict(case=case,epoch=ep,arm=arm,prediction_state=seed,source_id=ident,parent=parent,source_cells=len(indices),contains_truth=bool(truth_idx in indices),contains_prelocked_competitor=bool(competitor is not None and competitor in indices),stop=s['stop'],receiver_cell=k,consumed_hit_fraction=s['hit_fraction'],mean_consumed_ppm=s['window_mean_ppm_mean'],predicted_raw_frequency=float(raw[k]),predicted_blurred_frequency=float(blur[k]),source_logscore=float(logscore)))
    def region_logs(ids,ls):
        a=np.full(n,np.nan);d={}
        for ident,l in zip(ids,ls):a[groups[ident]]=l;d[ident]=float(l)
        return a,d
    # Archived native responses and native posterior are independently reconstructed.
    candidates={r['candidate_id']:r for r in rows(native/'candidates.csv')}
    original_ids=[r['node_id'] for r in tree];old_logs=[]
    for ident in original_ids:
        old=candidates[ident];raw=np.fromfile(native/'maps'/(ident+'_unblurred.f32'),'<f4');blur=np.fromfile(native/'maps'/(ident+'.f32'),'<f4');l=float(old['logscore']);old_logs.append(l)
        source_diagnostics('archived_native',0,ident,ident,raw,blur,l,groups[ident])
    native_logs,leaflogs=region_logs(original_ids,old_logs);q=metric('archived_native',0,native_logs,leaflogs)
    native_q=np.fromfile(native/'posterior.f64','<f8');assert np.max(np.abs(q-native_q))<1e-10
    contexts.append(dict(case=case,epoch=ep,truth_idx=truth_idx,truth_parent=truth_parent,truth_parent_cells=groups[truth_parent].tolist(),prelocked_competitor=competitor,prelocked_competitor_parent=comp_parent,events_consumed=len(ev),updates_after_this_unchanged=True))
    for seed in plan['prediction_rng_states']:
        loaded={}
        for mode in ['region','coarse_equal','fine']:
            dest=R/'results/predictions'/f'{key}_{mode}_{seed}'
            if not (dest/'COMPLETE.json').exists():dest=dest.with_name(dest.name+'_dispatch_retry1')
            assert (dest/'COMPLETE.json').exists()
            rs=rows(dest/'scores.csv');raws=[];blurs=[];logs=[];parents=[];ids=[]
            for r in rs:
                ident=r['id'];parent=r['parent_id'];raw=np.fromfile(dest/'maps'/(ident+'_unblurred.f32'),'<f4');blur=np.fromfile(dest/'maps'/(ident+'.f32'),'<f4');l=float(r['logscore'])
                rechecks.append(abs(scoremap(blur)-l));assert rechecks[-1]<1e-10
                indices=groups[parent] if mode!='fine' else [int(ident.split('_')[1])]
                source_diagnostics(mode,seed,ident,parent,raw,blur,l,indices)
                raws.append(raw);blurs.append(blur);logs.append(l);parents.append(parent);ids.append(ident)
            loaded[mode]=(rs,np.array(raws),np.array(blurs),np.array(logs),np.array(parents,object),ids)
            costs.append(dict(case=case,epoch=ep,arm=mode,prediction_state=seed,simulations=len(rs),releases=sum(int(r['releases']) for r in rs),particle_moves=sum(int(r['particle_moves']) for r in rs),measured_cpu_s=sum(float(r['cpu_s']) for r in rs),measured_wall_s=sum(float(r['wall_s']) for r in rs),maximum_recorded_steps_per_call=200,maximum_warmup_steps_per_call=500))
        rs,raws,blurs,logs,parents,ids=loaded['region'];a,d=region_logs(ids,logs);metric('ordinary_region_rng_repeat',seed,a,d)
        assert len(loaded['coarse_equal'][0])==len(loaded['fine'][0])==len(ii)
        for mode in ['coarse_equal','fine']:
            rs,raws,blurs,logs,parents,ids=loaded[mode]
            meanlogs={};mixlogs={}
            for parent,idxs in groups.items():
                mask=parents==parent;assert mask.sum()==len(idxs)
                meanraw=raws[mask].mean(axis=0,dtype=np.float64).astype('f4');meanblur=blurs[mask].mean(axis=0,dtype=np.float64).astype('f4')
                ml=scoremap(meanblur);mix=lse(logs[mask])-math.log(mask.sum());meanlogs[parent]=ml;mixlogs[parent]=mix
                source_diagnostics(mode+'_mean_response',seed,parent,parent,meanraw,meanblur,ml,idxs)
            a,d=region_logs(list(meanlogs),list(meanlogs.values()));metric(mode+'_average_response_then_score',seed,a,d)
            a,d=region_logs(list(mixlogs),list(mixlogs.values()));integrated_q=metric(mode+'_area_likelihood_marginal_parent_uniform',seed,a,d)
            if mode=='fine':
                a=np.full(n,np.nan)
                for ident,l in zip(ids,logs):a[int(ident.split('_')[1])]=l
                flat_q=metric('fine_cell_hierarchical_posterior',seed,a,mixlogs)
                for parent,idxs in groups.items():assert abs(flat_q[idxs].sum()-integrated_q[idxs].sum())<1e-12

# Invoke the already qualified native C++ ExpectedValue/Variance, including the original tie handling.
inp=O/'native_readout_input.txt'
with inp.open('w') as f:
    f.write(str(len(readouts))+'\n')
    for m,ii,q,truth,r in readouts:
        f.write(f"{m['width']} {m['height']} {m['origin_x']:.17g} {m['origin_y']:.17g} {m['cell_size']:.17g} {len(ii)}\n")
        for k in ii:f.write(f'{k} {q[k]:.17g}\n')
exe=Path(os.environ.get('C4_READOUT_EXE','/tmp/c4a17_readout/readout'))
res=subprocess.run([str(exe),str(inp)],capture_output=True,text=True)
(O/'native_readout_stdout.csv').write_text(res.stdout);(O/'native_readout_stderr.log').write_text(res.stderr)
assert res.returncode==0
for a,(m,ii,q,truth,r) in zip(csv.DictReader(res.stdout.splitlines()),readouts):
    r.update(posterior_mean_x=float(a['mean_x']),posterior_mean_y=float(a['mean_y']),official_top5_x=float(a['top5_x']),official_top5_y=float(a['top5_y']),full_probability_variance_m2=float(a['variance_m2']))
    r['posterior_mean_error_m']=float(np.linalg.norm(np.array([r['posterior_mean_x'],r['posterior_mean_y']])-truth))
    r['official_top5_error_m']=float(np.linalg.norm(np.array([r['official_top5_x'],r['official_top5_y']])-truth))
    r['false_confident_variance_below_1p5_and_top5_error_above_1p5']=r['full_probability_variance_m2']<1.5 and r['official_top5_error_m']>1.5
writecsv(O/'SOURCE_POSTERIOR_METRICS.csv',metrics);writecsv(O/'SOURCE_RECEIVER_RESPONSES.csv',source_rows);writecsv(O/'RECEIVER_OBSERVATIONS.csv',receiver_rows);writecsv(O/'COSTS.csv',costs);writecsv(O/'CELL_POSTERIORS.csv',posterior_rows)
(O/'LOCKED_SOURCE_CONTEXTS.json').write_text(json.dumps(contexts,indent=2))
(O/'NUMERICAL_CHECKS.json').write_text(json.dumps(dict(max_prediction_logscore_independent_recompute_abs=max(rechecks),fine_cell_vs_area_marginal_parent_mass_max_tolerance=1e-12,native_readout_returncode=res.returncode,readout_executable_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),fixed_history=True,new_closed_loop_benefit=False),indent=2))
summary=[]
for item in plan['cases']:
    cs=[r for r in metrics if r['case']==item['case'] and r['epoch']==item['epoch']]
    for arm in sorted({r['arm'] for r in cs}):
        a=[r for r in cs if r['arm']==arm]
        summary.append(dict(case=item['case'],epoch=item['epoch'],arm=arm,states=len(a),truth_rank_min=min(r['truth_strict_rank'] for r in a),truth_rank_max=max(r['truth_strict_rank'] for r in a),truth_mass_min=min(r['truth_cell_probability'] for r in a),truth_mass_max=max(r['truth_cell_probability'] for r in a),truth_parent_mass_min=min(r['truth_parent_probability'] for r in a),truth_parent_mass_max=max(r['truth_parent_probability'] for r in a),true_source_in90_count=sum(r['true_source_in90pct'] for r in a),mean_error_min=min(r['posterior_mean_error_m'] for r in a),mean_error_max=max(r['posterior_mean_error_m'] for r in a),official_top5_error_min=min(r['official_top5_error_m'] for r in a),official_top5_error_max=max(r['official_top5_error_m'] for r in a),truth_minus_competitor_min=min((r['truth_minus_competitor_logscore'] for r in a if r['truth_minus_competitor_logscore'] is not None),default=None),truth_minus_competitor_max=max((r['truth_minus_competitor_logscore'] for r in a if r['truth_minus_competitor_logscore'] is not None),default=None)))
writecsv(O/'SUMMARY.csv',summary);(O/'SUMMARY.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(dict(status='PASS_OFFLINE_SOURCE_AND_RECEIVER_ANALYSIS',posterior_rows=len(metrics),receiver_source_rows=len(source_rows),forward_calls=sum(r['simulations'] for r in costs),particle_moves=sum(r['particle_moves'] for r in costs),cpu_s=sum(r['measured_cpu_s'] for r in costs)),indent=2))
