"""Independent RK0 cache/count/kernel/prediction/score audit; no LOS or experiment.

Only saved contribution NPZs and immutable raw snapshots are read. Neither the
producer nor M2 scoring functions are imported. Integer counts are exact;
float64 derived arithmetic uses rtol2e-12/atol3e-13; serial native float32 sums
are checked separately. Version labels never decide scientific equivalence.
"""
import sys
sys.dont_write_bytecode=True
import argparse,collections,csv,hashlib,importlib.util,json,math,time
from pathlib import Path
import numpy as np
RTOL=2e-12;ATOL=3e-13;F=np.float32
REF=('C7_0','C7_1','K2_0','K2_1')
TASKBANK={'H101':'C7_2','H102':'K2_2','H103':'C7_3','H104':'K2_3'}
def js(p):return json.loads(p.read_text(encoding='utf-8'))
def rows(p):
    with p.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def near(a,b,label=''):
    assert math.isclose(float(a),float(b),rel_tol=RTOL,abs_tol=ATOL),(label,a,b)
def tree(a,b,path=''):
    if isinstance(a,dict):
        assert isinstance(b,dict) and a.keys()==b.keys(),(path,'keys')
        for k in a:tree(a[k],b[k],path+'/'+str(k))
    elif isinstance(a,list):
        assert len(a)==len(b),(path,'length')
        for i,(x,y) in enumerate(zip(a,b)):tree(x,y,path+'/'+str(i))
    elif isinstance(a,bool):assert a==b,(path,a,b)
    elif isinstance(a,(int,float,np.number)):near(a,b,path)
    else:assert a==b,(path,a,b)
def savecsv(p,rr):
    if not rr:return
    with p.open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rr[0]));w.writeheader();w.writerows(rr)
def classes(fil,origin,model,cuts):
    xy=np.floor((fil[:,:2]-origin)/F(.25)).astype(np.int64)
    if model=='U':cl=np.zeros(len(fil),dtype=np.int64)
    elif model=='S':cl=(fil[:,2].astype(np.float64)>=cuts['z_split_m']).astype(np.int64)*2+(fil[:,3].astype(np.float64)>=cuts['sigma_split_cm']).astype(np.int64)
    else:
        salt=b'PMFS_RK0_NONPHYSICAL_F32_STATE_HASH_v1'
        cl=np.array([int.from_bytes(hashlib.sha256(salt+np.asarray(f,dtype='<f4').tobytes()).digest()[:8],'little')%4 for f in fil],dtype=np.int64)
    keys=np.column_stack((xy,cl));unique,inverse=np.unique(keys,axis=0,return_inverse=True)
    return unique,inverse,np.bincount(inverse,minlength=len(unique))
def own_score(ref,obs):
    probs={c:[(ref[c][0][i]+ref[c][1][i]+.5)/3 for i in range(50)] for c in ref};tasks={}
    for task,y in obs.items():
        tt={}
        for c,p in probs.items():
            logs=[math.log(v) if bit else math.log1p(-v) for bit,v in zip(y,p)];br=[(bit-v)**2 for bit,v in zip(y,p)]
            tt[c]=dict(log_sum=math.fsum(logs),log_mean=math.fsum(logs)/50,brier_sum=math.fsum(br),brier_mean=math.fsum(br)/50,per_block_log=logs,per_block_brier=br,per_stop_log_mean=[math.fsum(logs[k:k+5])/5 for k in range(0,50,5)],per_stop_brier_mean=[math.fsum(br[k:k+5])/5 for k in range(0,50,5)])
        tasks[task]=tt
    return dict(definition='marginal/composite Bernoulli log score and Brier; not joint likelihood or calibrated posterior',smoothing=dict(alpha=.5,beta=.5,reference_realizations_per_candidate=2),candidate_reference_probabilities=probs,tasks=tasks)
def verify(root,m2):
    start=time.perf_counter();root=Path(root);m2=Path(m2);contract=js(root/'frozen_contract.json')
    assert sha(root/'frozen_contract.json')==(root/'PRE_RUN_CONTRACT_SHA256.txt').read_text().split()[0]
    assert all(sha(m2/n)==h for n,h in contract['inputs_sha256'].items())
    for n,h in js(root/'BLIND_SCORES_PRE_ANALYSIS_SHA256.json').items():assert sha(root/n)==h
    sp=importlib.util.spec_from_file_location('independent_rk0_saved_snapshot_decoder',m2/'independent_raw_query_verify/verify_raw_receiver_queries.py');raw=importlib.util.module_from_spec(sp);sp.loader.exec_module(raw)
    # The decoder is used solely for saved state deserialization, never los,
    # concentration, motion or native executable calls.
    cache_dir=root/'reference_contribution_cache';cache=js(cache_dir/'CONTRIBUTION_CACHE_RESULT.json')
    assert tuple(cache['reference_ids'])==REF and len(cache['frames'])==196
    origin=np.array([contract['origin_x'],contract['origin_y']],dtype=F)
    alias={r['query_id']:r for r in rows(cache_dir/'RECEPTOR_ALIAS_51_TO_10.csv')};assert len(alias)==51
    poses=np.load(cache_dir/'RECEPTOR_POSES_STOP_ORDER.f32.npy',allow_pickle=False);assert poses.shape==(10,3) and poses.dtype==np.dtype('<f4')
    original_alias=rows(m2/'observation_lineage/FROZEN_RECEPTOR_SCHEDULE_ALL_MEMBERSHIP_BRANCHES.csv');assert len(original_alias)==51
    for r in original_alias:
        qid='receiver_b'+r['block_id']+'_v'+r['membership_branch'];pose=int(r['stop_id']);assert pose==int(alias[qid]['pose_index'])
        assert np.array_equal(poses[pose],np.array([F(float(r['sensor_'+k])) for k in ['x','y','z']],dtype=F))
    data=[];weighted=[];total_pairs=positive=zero=serial_total_disagreements=0;frame_weights={}
    for b in REF:
        native=[r for r in rows(m2/'native_reference_evidence/realizations'/b/'QUERY_OUTPUT.csv') if r['query_id'].startswith('receiver_')]
        frame_weights[b]=collections.Counter(int(r['frame']) for r in native if int(alias[r['query_id']]['membership_branch'])==0)
        assert sum(frame_weights[b].values())==50 and len(frame_weights[b])==49
        for r in native:assert np.array_equal(poses[int(alias[r['query_id']]['pose_index'])],np.array([F(float(r[k])) for k in ['x','y','z']],dtype=F))
    for e in cache['frames']:
        relative=Path(e['cache_relative_path']);p=root/relative if relative.parts[0]=='reference_contribution_cache' else cache_dir/relative
        assert sha(p)==e['cache_SHA256']
        with np.load(p,allow_pickle=False) as z:
            fil=z['filaments'].copy();phi=z['contributions'].copy();tot=z['native_totals'].copy();w=int(z['planned_time_exposure_weight']);desc=raw.snapshot(m2/'native_reference_evidence/realizations'/e['bank']/'bank'/('iteration_'+str(e['frame'])))
            assert np.array_equal(fil,desc['filaments']) and fil.dtype==np.dtype('<f4') and phi.dtype==np.dtype('<f4')
            assert phi.shape==(len(fil),10) and (phi>=0).all() and np.isfinite(phi).all()
            assert w==int(e['exposure_weight'])==frame_weights[e['bank']][e['frame']] and len(fil)==e['filament_records']
            nonzero=np.count_nonzero(phi,axis=0);assert np.array_equal(nonzero,z['positive_contributors'])
            assert np.all(nonzero<=z['cutoff_eligible']-z['LOS_blocked'])
            recomputed=np.cumsum(phi,axis=0,dtype=F)[-1]
            assert np.array_equal(recomputed,tot),'serial float32 cache total mismatch'
            serial_total_disagreements+=int((recomputed!=tot).sum());total_pairs+=phi.size;positive+=int(nonzero.sum());zero+=phi.size-int(nonzero.sum())
            data.append(dict(entry=e,fil=fil,phi=phi,native_totals=tot,w=w,desc=desc))
            weighted.append(np.repeat(fil[:,[2,3]].astype(np.float64),w,axis=0))
    allfit=np.concatenate(weighted);cuts=dict(z_split_m=float(np.median(allfit[:,0])),sigma_split_cm=float(np.median(allfit[:,1])))
    oldcuts=js(root/'REFERENCE_ONLY_STATE_BOUNDARIES.json');near(cuts['z_split_m'],oldcuts['z_split_m']);near(cuts['sigma_split_cm'],oldcuts['sigma_split_cm'])
    assert len(allfit)==oldcuts['total_reference_particle_exposures']==cache['fit_exposure_weighted_records'];del allfit,weighted
    assert total_pairs==cache['cross_pose_pairs'] and positive==cache['positive_pairs'] and zero==cache['zero_pairs']
    datalookup={(d['entry']['bank'],d['entry']['frame']):d for d in data};cpp_anchor_count=0;cpp_anchor_max=0.
    for b in REF:
        for q in rows(m2/'native_reference_evidence/realizations'/b/'QUERY_OUTPUT.csv'):
            if not q['query_id'].startswith('receiver_'):continue
            value=datalookup[b,int(q['frame'])]['native_totals'][int(alias[q['query_id']]['pose_index'])];target=F(float(q['ppm_float32']));difference=abs(float(value)-float(target))
            assert difference<=3e-7+5e-6*abs(float(target));cpp_anchor_count+=1;cpp_anchor_max=max(cpp_anchor_max,difference)
    assert cpp_anchor_count==204
    models=['U','S']+(['R'] if (root/'KERNEL_R.csv').exists() else [])
    kernels={};kernel_checks=[];conservation=[];bankbias=[]
    for model in models:
        counts={};sums={};bkpred={};bkactual={};totalweight=collections.Counter()
        for d in data:
            keys,inv,nn=classes(d['fil'],origin,model,cuts);w=d['w']
            vv=np.column_stack([np.bincount(inv,weights=d['phi'][:,r].astype(np.float64)*w,minlength=len(keys)) for r in range(10)])
            for k,n,v in zip(keys,nn,vv):
                key=tuple(map(int,k));counts[key]=counts.get(key,0)+int(n)*w
                if key not in sums:sums[key]=np.zeros(10,dtype=np.float64)
                sums[key]+=v
        h={k:sums[k]/counts[k] for k in counts};kernels[model]=h
        kk=rows(root/('KERNEL_'+model+'.csv'));assert len(kk)==len(h)*10
        maxsum=maxh=0.;zero_sum_rows=0
        for r in kk:
            key=(int(r['cell_i']),int(r['cell_j']),int(r['class_id']));pose=int(r['pose_id']);assert r['model']==model and counts[key]==int(r['complete_particle_exposure_denominator'])
            near(sums[key][pose],r['native_contribution_sum_ppm'],(model,key,pose,'sum'));near(h[key][pose],r['shared_h_ppm_per_particle'],(model,key,pose,'h'))
            maxsum=max(maxsum,abs(sums[key][pose]-float(r['native_contribution_sum_ppm'])));maxh=max(maxh,abs(h[key][pose]-float(r['shared_h_ppm_per_particle'])))
            zero_sum_rows+=sums[key][pose]==0
        kernel_checks.append(dict(model=model,active_cell_classes=len(h),particle_exposure_denominator=sum(counts.values()),zero_numerator_rows_with_positive_denominator=int(zero_sum_rows),maximum_contribution_sum_difference=maxsum,maximum_h_difference=maxh))
        mm=next(m for m in js(root/'MODEL_COMPLEXITY_AND_ZERO_DENOMINATORS.json') if m['model']==model)
        assert mm['active_cell_classes']==len(h) and mm['cell_count']==len({k[:2] for k in h}) and mm['reference_particle_exposures']==sum(counts.values())
        perbank=collections.Counter()
        for d in data:perbank[d['entry']['bank']]+=len(d['fil'])*d['w']
        assert dict(perbank)==mm['per_reference_particle_exposures']
        for d in data:
            b=d['entry']['bank'];keys,inv,nn=classes(d['fil'],origin,model,cuts);w=d['w'];pred=np.zeros(10)
            for k,n in zip(keys,nn):pred+=int(n)*h[tuple(map(int,k))]
            actual=d['phi'].sum(axis=0,dtype=np.float64)
            if b not in bkpred:bkpred[b]=np.zeros(10);bkactual[b]=np.zeros(10)
            bkpred[b]+=pred*w;bkactual[b]+=actual*w;totalweight[b]+=w
        for pose in range(10):
            total_pred=math.fsum(float(bkpred[b][pose]) for b in REF);total_actual=math.fsum(float(bkactual[b][pose]) for b in REF);near(total_pred,total_actual,'pool conservation')
            conservation.append(dict(model=model,pose_id=pose,population_N_times_h_sum_ppm=total_pred,weighted_native_particle_contribution_sum_float64_ppm=total_actual,absolute_difference=abs(total_pred-total_actual)))
            for b in REF:
                assert totalweight[b]==50
                bankbias.append(dict(model=model,reference_bank=b,pose_id=pose,planned_snapshot_exposures=50,mean_reconstructed_concentration_ppm=float(bkpred[b][pose])/50,mean_native_particle_sum_float64_ppm=float(bkactual[b][pose])/50,mean_reconstructed_minus_native_ppm=(float(bkpred[b][pose])-float(bkactual[b][pose]))/50))
    qbank={};desc_cache={};pred=[];miss=[];coverage=[];branchcheck=[]
    for bank in sorted((m2/'native_reference_evidence/realizations').iterdir()):
        if not bank.is_dir():continue
        qq=[r for r in rows(bank/'QUERY_OUTPUT.csv') if r['query_id'].startswith('receiver_')];assert len(qq)==51;qbank[bank.name]=qq
        for q in qq:
            frame=int(q['frame']);k=(bank.name,frame)
            if k not in desc_cache:desc_cache[k]=raw.snapshot(bank/'bank'/('iteration_'+str(frame)))
    pi=F(math.pi*math.pi*math.pi);fixed=math.sqrt(float(F(F(8)*pi)));tau=float(F(.1))
    def peak(sigma,desc):
        mole=F(float(desc['total_moles'])/(fixed*float(sigma)**3));return float(F(1e6*float(mole)/float(desc['all_gas_moles'])))
    pred_by_model={}
    for model in models:
        hh=kernels[model];expected=rows(root/('PREDICTIONS_'+model+'.csv'));ee={(r['bank'],int(r['block_id']),int(r['membership_branch'])):r for r in expected};got=[]
        groupcache={}
        for b,qq in qbank.items():
            for q in qq:
                block,branch=int(q['query_id'].split('_')[1][1:]),int(q['query_id'].split('_')[2][1:]);pose=int(alias[q['query_id']]['pose_index']);frame=int(q['frame']);desc=desc_cache[b,frame];fil=desc['filaments']
                if (b,frame) not in groupcache:groupcache[b,frame]=classes(fil,origin,model,cuts)
                keys,inv,nn=groupcache[b,frame];known=[];unknown=outside=0;upper=[]
                for key,n in zip(keys,nn):
                    key=tuple(map(int,key));n=int(n);outside+=n*int(not(0<=key[0]<34 and 0<=key[1]<45))
                    if key in hh:known.append(n*float(hh[key][pose]))
                    else:
                        unknown+=n;lower=cuts['sigma_split_cm'] if model=='S' and key[2]%2 else 10.;bound=peak(lower,desc)*(1+5e-6)+3e-7;upper.append(n*bound)
                        miss.append(dict(model=model,bank=b,block_id=block,membership_branch=branch,pose_id=pose,frame=frame,cell_i=key[0],cell_j=key[1],class_id=key[2],uncovered_particle_count=n,native_sigma_minimum_cm=lower,per_particle_physical_peak_upper_ppm=bound))
                lo=math.fsum(known);hi=lo+math.fsum(upper);event=1 if lo>tau else 0 if hi<=tau else 'AMBIGUOUS';full=float(q['ppm_float32']);nv=int(F(full)>F(.1));value=lo if unknown==0 else 'UNSUPPORTED'
                r=dict(model=model,bank=b,role='reference' if b in REF else 'previously_seen_heldout',block_id=block,membership_branch=branch,pose_id=pose,frame=frame,native_F_ppm=full,native_F_event=nv,particle_count=len(fil),outside_original_2D_frame_particles=outside,count_supported_particles=len(fil)-unknown,uncovered_particles=unknown,point_prediction_ppm=value,prediction_lower_ppm=lo,prediction_upper_ppm=hi,prediction_event=event,event_certified_by_nonnegativity_or_peak_bound=unknown>0 and event!='AMBIGUOUS',point_squared_error=(lo-full)**2 if unknown==0 else 'UNSUPPORTED',compression_error_lower_squared=max(lo-full,full-hi,0)**2,compression_error_upper_squared=max((lo-full)**2,(hi-full)**2),missing_interval_scope='Unknown kernel entries only; not physical-truth confidence interval or correction for covered-class compression error')
                ref=ee[b,block,branch]
                for field,v in r.items():
                    if isinstance(v,bool):assert str(v)==ref[field],(model,b,block,field)
                    elif isinstance(v,(float,int,np.number)):near(v,ref[field],(model,b,block,field))
                    else:assert v==ref[field],(model,b,block,field)
                got.append(r)
        assert len(got)==408;pred_by_model[model]=got;pred+=got
        missing_actual=rows(root/('UNCOVERED_STATES_'+model+'.csv'));mm={(r['bank'],int(r['block_id']),int(r['membership_branch']),int(r['cell_i']),int(r['cell_j']),int(r['class_id'])):r for r in missing_actual}
        mine=[r for r in miss if r['model']==model];assert len(mine)==len(mm)
        for r in mine:
            ref=mm[r['bank'],r['block_id'],r['membership_branch'],r['cell_i'],r['cell_j'],r['class_id']]
            assert r['uncovered_particle_count']==int(ref['uncovered_particle_count']);near(r['per_particle_physical_peak_upper_ppm'],ref['per_particle_physical_peak_upper_ppm'])
        for b in qbank:
            a=next(r for r in got if r['bank']==b and r['block_id']==40 and r['membership_branch']==0);c=next(r for r in got if r['bank']==b and r['block_id']==40 and r['membership_branch']==1)
            for field in a:
                if field!='membership_branch':tree(a[field],c[field],field)
            branchcheck.append(dict(model=model,bank=b,block40_same_frame_pose_prediction_and_support=True))
            z=[r for r in got if r['bank']==b and r['membership_branch']==0];complete=[r for r in z if r['uncovered_particles']==0];cert=[r for r in z if r['prediction_event']!='AMBIGUOUS'];errors=sum(r['prediction_event']!=r['native_F_event'] for r in cert)
            coverage.append(dict(model=model,bank=b,role=z[0]['role'],blocks=50,fully_covered_blocks=len(complete),certified_events=len(cert),ambiguous_events=50-len(cert),uncovered_particle_exposures=sum(r['uncovered_particles'] for r in z),total_particle_exposures=sum(r['particle_count'] for r in z),MSE_complete_support_only=math.fsum(r['point_squared_error'] for r in complete)/len(complete) if complete else 'UNSUPPORTED',all_block_MSE_outer_lower=math.fsum(r['compression_error_lower_squared'] for r in z)/50,all_block_MSE_outer_upper=math.fsum(r['compression_error_upper_squared'] for r in z)/50,certified_event_errors=errors,total_event_error_lower=errors,total_event_error_upper=errors+50-len(cert)))
        for a,ref in zip([r for r in coverage if r['model']==model],rows(root/('RECEIVER_METRICS_'+model+'.csv'))):
            for field,v in a.items():
                if isinstance(v,(float,int)):near(v,ref[field],field)
                else:assert v==ref[field]
    native_refs={b:[None]*50 for b in REF}
    for b in REF:
        for q in qbank[b]:
            if int(alias[q['query_id']]['membership_branch'])==0:native_refs[b][int(alias[q['query_id']]['block_id'])]=int(F(float(q['ppm_float32']))>F(.1))
    refs={'F':{c:[native_refs[c+'_0'],native_refs[c+'_1']] for c in ['C7','K2']}}
    for model in models:
        per={b:[None]*50 for b in REF}
        for r in pred_by_model[model]:
            if r['bank'] in REF and r['membership_branch']==0:
                assert r['prediction_event'] in [0,1];per[r['bank']][r['block_id']]=r['prediction_event']
        refs[model]={c:[per[c+'_0'],per[c+'_1']] for c in ['C7','K2']}
    obs=js(m2/'source_blind_inputs/branch_0.json')['observation_events'];scores={};taskrows=[];mapping=js(m2/'HELDOUT_GENERATOR_MAPPING_ANALYSIS_ONLY.json')
    for model,rr in refs.items():
        assert js(root/('SOURCE_BLIND_INPUT_'+model+'.json'))==dict(reference_events=rr,observation_events=obs)
        sc=own_score(rr,obs);tree(sc,js(root/('SOURCE_BLIND_SCORES_'+model+'.json')),model);scores[model]=sc
        for task,t in sc['tasks'].items():
            truth='C7' if task=='O0' else mapping[task];other='K2' if truth=='C7' else 'C7'
            taskrows.append(dict(model=model,task=task,truth_analysis_only=truth,log_choice=max(t,key=lambda c:t[c]['log_sum']),Brier_choice=min(t,key=lambda c:t[c]['brier_mean']),truth_directed_log_margin=t[truth]['log_sum']-t[other]['log_sum'],truth_directed_Brier_contrast=t[other]['brier_mean']-t[truth]['brier_mean']))
    def paired(first,second):
        result=[]
        for task,b in TASKBANK.items():
            truth=mapping[task];other='K2' if truth=='C7' else 'C7';x=scores[first]['tasks'][task];y=scores[second]['tasks'][task]
            lu=(x[truth]['log_sum']-x[other]['log_sum'])/50;ls=(y[truth]['log_sum']-y[other]['log_sum'])/50;bu=x[other]['brier_mean']-x[truth]['brier_mean'];bs=y[other]['brier_mean']-y[truth]['brier_mean']
            xx={r['block_id']:r for r in pred_by_model[first] if r['bank']==b and r['membership_branch']==0};yy={r['block_id']:r for r in pred_by_model[second] if r['bank']==b and r['membership_branch']==0};common=[i for i in xx if xx[i]['uncovered_particles']==yy[i]['uncovered_particles']==0]
            mse1=math.fsum(xx[i]['point_squared_error'] for i in common)/len(common) if common else None;mse2=math.fsum(yy[i]['point_squared_error'] for i in common)/len(common) if common else None
            result.append(dict(task=task,bank=b,truth_for_analysis_only=truth,U_truth_directed_mean_log_margin=lu,S_truth_directed_mean_log_margin=ls,delta_mean_log_margin=ls-lu,U_truth_directed_Brier_contrast=bu,S_truth_directed_Brier_contrast=bs,delta_Brier_contrast=bs-bu,common_complete_support_blocks=len(common),U_MSE_common_support=mse1 if mse1 is not None else 'UNSUPPORTED',S_MSE_common_support=mse2 if mse2 is not None else 'UNSUPPORTED',source_both_scores_gain=ls-lu>1e-12 and bs-bu>1e-12,response_common_support_gain=mse1 is not None and mse2<mse1,full_response_coverage=len(common)==50))
        return result
    pairs=paired('U','S');r_pairs=paired('R','S') if 'R' in models else []
    for ours,name in [(pairs,'PAIRED_U_S_HELDOUT_RESULTS.csv'),(r_pairs,'PAIRED_R_S_HELDOUT_RESULTS.csv')]:
        if not ours:continue
        for a,ref in zip(ours,rows(root/name)):
            for field,v in a.items():
                if isinstance(v,bool):assert str(v)==ref[field]
                elif isinstance(v,(int,float)):near(v,ref[field],field)
                else:assert v==ref[field]
    all_choices_match_F=all(next(r for r in taskrows if r['model']==m and r['task']==task)['log_choice']==next(r for r in taskrows if r['model']=='F' and r['task']==task)['log_choice'] and next(r for r in taskrows if r['model']==m and r['task']==task)['Brier_choice']==next(r for r in taskrows if r['model']=='F' and r['task']==task)['Brier_choice'] for m in models for task in obs)
    result=dict(verdict='PASS_INDEPENDENT_RK0_CACHE_ZERO_DENOMINATOR_KERNEL_PREDICTION_AND_SCORING_AUDIT',new_experiments=0,new_LOS=0,
      contract_SHA256=sha(root/'frozen_contract.json'),immutable_M2_input_hashes_checked=len(contract['inputs_sha256']),cache_frames_SHA_checked=196,cache_raw_filament_arrays_exact=True,
      contribution_pairs=total_pairs,positive_pairs=positive,explicit_zero_pairs=zero,serial_float32_total_disagreements=serial_total_disagreements,
      native_CPP_reference_anchor_count=cpp_anchor_count,maximum_cached_native_CPP_anchor_absolute_difference=cpp_anchor_max,pose_aliases_match_original_frozen_sensor_coordinates=True,
      recomputed_reference_weighted_medians=cuts,weighted_reference_particle_exposures=oldcuts['total_reference_particle_exposures'],kernel_checks=kernel_checks,
      reference_event_positive_counts={m:{c:[sum(v) for v in reps] for c,reps in rr.items()} for m,rr in refs.items()},
      all_U_S_R_choices_match_F_including_O0=all_choices_match_F,R_U_reference_events_identical=refs.get('R')==refs['U'],
      source_and_response_pairs=pairs,R_control_pairs=r_pairs,coverage=coverage,branch40_checks=len(branchcheck),
      independent_scientific_reading=['U already preserves current five discrete source decisions, including O0; classification superiority of S is not established.','S improves both source-margin diagnostics on all four inspected holdouts; joint common-support response gain occurs only on C7_2 and C7_3.','Common U/S concentration support is 16+9+37+0=62/200 exposures, not complete heldout response preservation.','S response errors are heterogeneous; ambiguity/unsupported entries are real missing coverage, not zeros.','S is ordinary reference-median fixed4 physical binning with oracle class counts, not learned clones or CSCG dynamics.','Same-cap hashed R control tests this one grouping only; no independent new task, calibrated source posterior or main innovation is established.'],
      numerical_rules=dict(derived_float64_relative=RTOL,derived_float64_absolute=ATOL,integer_counts='exact',native_threshold_ppm=float(F(.1)),native_serial_sums='exact float32 original order',versions_are_metadata_only=True),wall_s=time.perf_counter()-start)
    return result,dict(INDEPENDENT_KERNEL_POOL_CONSERVATION=conservation,INDEPENDENT_REFERENCE_BANK_POSE_RESIDUALS=bankbias,INDEPENDENT_SOURCE_TASK_RESULTS=taskrows,INDEPENDENT_COVERAGE_AND_RESPONSE_ERRORS=coverage,INDEPENDENT_U_S_PAIRS=pairs,INDEPENDENT_R_S_PAIRS=r_pairs,INDEPENDENT_BRANCH40_CHECKS=branchcheck)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--package',type=Path,required=True);p.add_argument('--m2',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();r,tt=verify(a.package,a.m2)
    a.out.mkdir(parents=True,exist_ok=False)
    (a.out/'RK0_INDEPENDENT_RESULT.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for n,t in tt.items():savecsv(a.out/(n+'.csv'),t)
    print(json.dumps({k:v for k,v in r.items() if k not in ['coverage','source_and_response_pairs','R_control_pairs']},ensure_ascii=False,indent=2))
