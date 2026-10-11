"""All preregistered diagnostics. Scalar inference freezes before truth evaluation."""
from common_b import *
import csv,math,collections,itertools,shutil,numpy as np
from rk2b_infer import infer,future

def rows(p):
    with Path(p).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def write(p,a):
    if not a:return
    keys=list(dict.fromkeys(k for r in a for k in r))
    with Path(p).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys,lineterminator='\n');w.writeheader();w.writerows(a)
def pack(m):return {k:v.tolist() if isinstance(v,np.ndarray) else v for k,v in m.items()}
def crps(x,y):
    x=np.log1p(np.asarray(x,dtype=np.float32).astype(float));y=np.log1p(np.asarray(y,dtype=np.float32).astype(float))
    return np.mean(np.abs(x-y[None,:]),axis=0)-.5*np.mean(np.abs(x[:,None,:]-x[None,:,:]),axis=(0,1))

def main():
    start=time.perf_counter();reg=load(CORE/'experiment_registry.json');physical=Path(reg['host_data_path']);led=load(physical/'GENERATION_LEDGER.json')
    assert led['status'].startswith('PASS') and len(led['records'])==reg['mode']
    Ms=[2,4] if reg['mode']==24 else [2];refs={};scales={};allpose={};methods={}
    # Verify frozen forecasts before any diagnostic or formal observable is opened.
    freezes={}
    for M in Ms:
        d=CORE/f'M{M}';status=load(d/'MODEL_STATUS.json');assert 'F' in status['methods']
        freeze=load(d/'PRE_TEST_PREDICTION_FREEZE.json')
        assert all(sha(d/n)==h for n,h in freeze.items())
        freezes[f'M{M}']=sha(d/'PRE_TEST_PREDICTION_FREEZE.json');methods[M]=status['methods'];scales[M]=load(d/'HEAD_SCALE_FROZEN.json')['H1_scale']
        for name in methods[M]:
            with np.load(d/'forecasts'/f'{name}.npz',allow_pickle=False) as z:refs[M,name]=z['reference_response_ppm'].copy()
        with np.load(d/'F_REFERENCE_ALL_POSES.npz',allow_pickle=False) as z:allpose[M]=z['response_ppm'].copy()
    dump(CORE/'ALL_MODELS_FROZEN_BEFORE_OBSERVATIONS.json',dict(time_ns=time.time_ns(),model_freezes=freezes,formal_observations_opened=False))
    observed_dir=CORE/'scalar_observations';observed_dir.mkdir(exist_ok=False)
    evaluation=CORE/'evaluation_only';evaluation.mkdir(exist_ok=False)
    observations={};identities={};tasks={};obslog=[]
    for task,role in [('diagnostic','diagnostic'),('formal','heldout')]:
        jobs=[j for j in reg['jobs'] if j['role']==role]
        for number,job in enumerate(jobs):
            oid=('D' if task=='diagnostic' else 'O')+f'{number:02d}';r=physical/'realizations'/job['job_id'];v={a['query_id']:float(a['ppm_float32']) for a in rows(r/'QUERY_OUTPUT.csv')}
            matrix=np.array([[v[f'b{b}_p{p}'] for p in range(len(reg['all_receiver_xyz']))] for b in range(50)],dtype=np.float32)
            y=matrix[np.arange(50),np.arange(50)//5]
            np.savez_compressed(observed_dir/f'{oid}.npz',observed_ppm=y,receiver_plan_id=np.array(reg['receiver_plan_id']))
            np.savez_compressed(evaluation/f'{oid}_F_allposes.npz',response_ppm=matrix)
            observations[oid]=y;tasks[oid]=task
            identities[oid]=dict(candidate_id=job['candidate_id'],job_id=job['job_id'],source_xyz=job['source_xyz'],role=role)
            obslog.append(dict(oid=oid,task=task,scalar_SHA256=sha(observed_dir/f'{oid}.npz'),test_particles_opened=False))
    dump(CORE/'OBSERVABLE_OPEN_LEDGER.json',dict(time_ns=time.time_ns(),records=obslog,forecast_freeze_verified=True))
    candidate_ids=[s['future_candidate_id'] for s in reg['sources']];xyz=np.array([s['xyz_m'] for s in reg['sources']]);blind={};full=[];terms=[];margins=[];event_changes=[];prefix=[];futures=[];sensitivity=[];infercost=[];collisions=[];aux=[]
    for M in Ms:
        f=refs[M,'F'][:,:M]
        for head in ['H0','H1']:
            fingerprint=((f.astype(np.float32)>.1).sum(axis=1) if head=='H0' else np.sort(np.log1p(f.astype(np.float32).astype(float)),axis=1))
            groups=[]
            for a,b in itertools.combinations(range(3),2):
                if np.array_equal(fingerprint[a],fingerprint[b]):groups.append([candidate_ids[a],candidate_ids[b]])
            collisions.append(dict(M=M,head=head,exact_collision_pairs=groups,scope='registered finite reference responses only; not universal identifiability'))
            for oid,y in observations.items():
                fr=infer(f,y,head,scales[M]);base=dict(M=M,head=head,oid=oid,task=tasks[oid])
                for name in methods[M]:
                    x=refs[M,name][:,:M];t=time.perf_counter();r=infer(x,y,head,scales[M]);infercost.append(base|dict(method=name,stage='scalar_source_infer_once',wall_s=time.perf_counter()-t,F_readout_charged_here=0))
                    key=f'{M}|{head}|{oid}|{name}';blind[key]=pack(r)
                    for c,cid in enumerate(candidate_ids):
                        full.append(base|dict(method=name,candidate_id=cid,score=float(r['scores'][c]),log_probability=float(r['log_prob'][c]),probability=float(r['prob'][c])))
                        for b in range(50):terms.append(base|dict(method=name,candidate_id=cid,block=b,term=float(r['block_terms'][c,b]),event_probability=float(r['event_probability'][c,b]),CRPS_log1p=float(r['CRPS'][c,b])))
                    delta=r['scores']-fr['scores'];R=float(np.ptp(delta));kl=float(np.dot(fr['prob'],fr['log_prob']-r['log_prob']));assert kl<=R*R/8+1e-12
                    for c,d in itertools.combinations(range(3),2):margins.append(base|dict(method=name,candidate_a=candidate_ids[c],candidate_b=candidate_ids[d],score_margin=float(r['scores'][c]-r['scores'][d]),F_score_margin=float(fr['scores'][c]-fr['scores'][d]),score_delta_range_R=R,KL_F_to_method=kl,KL_bound_R2_over8=R*R/8))
                    for n in [10,20,30,40,50]:
                        pr=infer(x,y,head,scales[M],np.arange(n));blind[f'{key}|prefix{n}']=pack(pr)
                        for c,cid in enumerate(candidate_ids):prefix.append(base|dict(method=name,blocks=n,candidate_id=cid,score=float(pr['scores'][c]),probability=float(pr['prob'][c]),log_probability=float(pr['log_prob'][c])))
                    pr=infer(x,y,head,scales[M],np.arange(25));fp=future(x,y,pr['prob']);blind[f'{key}|future25']=dict(prefix25=pack(pr),future=fp)
                    futures.append(base|dict(method=name,prefix_blocks=25,future_blocks=25,mean_Brier=fp['mean_Brier'],mean_CRPS_log1p=fp['mean_CRPS'],source_probabilities=json.dumps(pr['prob'].tolist()),future_not_used_to_infer=True))
                if M==2 and reg['mode']==24:
                    for pair,select in [('original2',[0,1]),('extra2',[2,3]),('all4',[0,1,2,3])]:
                        xx=refs[M,'F'][:,select];zz=np.log1p(xx.astype(np.float32).astype(float));a=float(np.quantile(zz,.75)-np.quantile(zz,.25));a=a if a>1e-12 else 1.
                        r=infer(xx,y,head,a);blind[f'F_PAIR|{head}|{oid}|{pair}']=pack(r)
                        for c,cid in enumerate(candidate_ids):sensitivity.append(dict(head=head,oid=oid,task=tasks[oid],reference_pair=pair,M=len(select),H1_scale=a,candidate_id=cid,score=float(r['scores'][c]),probability=float(r['prob'][c]),log_probability=float(r['log_prob'][c])))
        for name in methods[M]:
            x=refs[M,name]
            for c,cid in enumerate(candidate_ids):
                for ri in range(x.shape[1]):
                    for b in range(50):
                        v=float(np.float32(x[c,ri,b]));fv=float(np.float32(refs[M,'F'][c,ri,b]));eh=v>float(np.float32(.1));ef=fv>float(np.float32(.1))
                        event_changes.append(dict(M=M,method=name,candidate_id=cid,reference=ri,block=b,pose=b//5,predicted_ppm=v,F_ppm=fv,event=eh,F_event=ef,flip=eh!=ef,flip_direction='negative_to_positive' if eh and not ef else ('positive_to_negative' if ef and not eh else 'unchanged'),F_threshold_margin_ppm=fv-float(np.float32(.1)),method_threshold_margin_ppm=v-float(np.float32(.1))))
        # Auxiliary poses have no fitted decoder: candidate-side F fallback for every method.
        for oid,y in observations.items():
            with np.load(evaluation/f'{oid}_F_allposes.npz',allow_pickle=False) as z:obs=z['response_ppm']
            for c,cid in enumerate(candidate_ids):
                for p in range(14):
                    forecast=allpose[M][c,:M,:,p];by=obs[:,p];pe=(np.sum(forecast.astype(np.float32)>np.float32(.1),axis=0)+.5)/(M+1)
                    aux.append(dict(M=M,oid=oid,task=tasks[oid],candidate_id=cid,pose=p,role='auxiliary_F_fallback' if p>=10 else 'original_offroute_diagnostic',mean_ppm_MSE=float(np.mean((forecast.mean(axis=0)-by)**2)),mean_ppm_MAE=float(np.mean(np.abs(forecast.mean(axis=0)-by))),mean_CRPS_log1p=float(np.mean(crps(forecast,by))),mean_Brier=float(np.mean((pe-(by>np.float32(.1)))**2)),methods_share_F=True,no_zero_shot_claim=True))
    dump(CORE/'BLIND_PREDICTIONS.json',blind)
    dump(CORE/'BLIND_PREDICTION_FREEZE.json',dict(time_ns=time.time_ns(),SHA256=sha(CORE/'BLIND_PREDICTIONS.json'),truth_mapping_opened=False,allowed_infer_inputs=['candidate own reference scalar forecasts','observed scalar concentration','frozen scale/head/prefix']))
    # Truth is written and evaluated only after all source predictions have been frozen.
    dump(evaluation/'TRUTH_MAPPING.json',identities)
    metrics=[];predictive=[];failures=[];prefixmetrics=[];pairmetrics=[]
    for M in Ms:
        for head in ['H0','H1']:
            for oid,y in observations.items():
                true=candidate_ids.index(identities[oid]['candidate_id']);base=dict(M=M,head=head,oid=oid,task=tasks[oid])
                for name in methods[M]:
                    r=blind[f'{M}|{head}|{oid}|{name}'];top=r['top1'];mean=np.array(r['prob'])@xyz
                    error=len(top)!=1 or top[0]!=true;pointdist=float(np.linalg.norm(xyz[top[0],:2]-xyz[true,:2])) if len(top)==1 else 'NA_ABSTAIN';meandist=float(np.linalg.norm(mean[:2]-xyz[true,:2]));x=refs[M,name][true,:M];xx=refs[M,'F'][true,:M]
                    rr=base|dict(method=name,true_candidate=candidate_ids[true],NLL=-r['log_prob'][true],top1_error=int(error),top1_candidates=json.dumps([candidate_ids[c] for c in top]),top1_distance_m=pointdist,posterior_mean_distance_m=meandist,p_true=r['prob'][true],observation_positive_blocks=int(np.sum(y>np.float32(.1))),independent_realization=oid,correlated_blocks=50,virtual_stops=10)
                    metrics.append(rr)
                    if error:failures.append(rr)
                    pe=(np.sum(x.astype(np.float32)>np.float32(.1),axis=0)+.5)/(M+1)
                    predictive.append(base|dict(method=name,true_candidate=candidate_ids[true],mean_ppm_MSE=float(np.mean((x.mean(axis=0)-y)**2)),mean_ppm_MAE=float(np.mean(np.abs(x.mean(axis=0)-y))),mean_CRPS_log1p=float(np.mean(crps(x,y))),mean_Brier=float(np.mean((pe-(y>np.float32(.1)))**2)),same_reference_compression_ppm_MSE_vs_F=float(np.mean((x-xx)**2)),same_reference_compression_ppm_MAE_vs_F=float(np.mean(np.abs(x-xx)))))
                    for n in [10,20,30,40,50]:
                        pr=blind[f'{M}|{head}|{oid}|{name}|prefix{n}'];prefixmetrics.append(base|dict(method=name,blocks=n,NLL=-pr['log_prob'][true],p_true=pr['prob'][true],top1_error=int(len(pr['top1'])!=1 or pr['top1'][0]!=true)))
                if M==2 and reg['mode']==24:
                    for pair in ['original2','extra2','all4']:
                        r=blind[f'F_PAIR|{head}|{oid}|{pair}'];pairmetrics.append(dict(head=head,oid=oid,task=tasks[oid],reference_pair=pair,NLL=-r['log_prob'][true],p_true=r['prob'][true],top1_error=int(len(r['top1'])!=1 or r['top1'][0]!=true),top1=json.dumps(r['top1'])))
    tables={'source_scores_all.csv':full,'block_scores.csv':terms,'candidate_pairwise_margins.csv':margins,'reference_event_changes.csv':event_changes,'prefix_scores.csv':prefix,'prefix_evaluation.csv':prefixmetrics,'future_prediction_scores.csv':futures,'sampling_sensitivity.csv':sensitivity,'sampling_sensitivity_evaluation.csv':pairmetrics,'predictive_metrics.csv':predictive,'per_realization_metrics.csv':metrics,'failure_cases.csv':failures,'runtime_infer_costs.csv':infercost,'auxiliary_receiver_diagnostics.csv':aux}
    for n,a in tables.items():write(CORE/n,a)
    dump(CORE/'FINITE_REFERENCE_COLLISIONS.json',collisions)
    summaries=[]
    for M in Ms:
        for head in ['H0','H1']:
            for task in ['diagnostic','formal']:
                for name in methods[M]:
                    r=[a for a in metrics if a['M']==M and a['head']==head and a['task']==task and a['method']==name]
                    summaries.append(dict(M=M,head=head,task=task,method=name,independent_realizations=len(r),mean_NLL=float(np.mean([a['NLL'] for a in r])),Top1_errors=sum(a['top1_error'] for a in r),mean_p_true=float(np.mean([a['p_true'] for a in r])),mean_posterior_mean_distance_m=float(np.mean([a['posterior_mean_distance_m'] for a in r])),maximum_posterior_mean_distance_m=max(a['posterior_mean_distance_m'] for a in r)))
    write(CORE/'SUMMARY_METRICS.csv',summaries)
    gate=dict(scope='Original B formal6 M2 H0 only',arms_present=all(a in methods[2] for a in ['U_query','S_query','L']),gain_each_baseline={},Top1_no_worse={},maximum_individual_harm_nat={},capacity_pass=False,information_audit='PENDING',scientific_endpoint=None)
    if gate['arms_present']:
        selection={n:sorted([r for r in metrics if r['M']==2 and r['head']=='H0' and r['task']=='formal' and r['method']==n],key=lambda r:r['oid']) for n in ['U_query','S_query','L']}
        for n in ['U_query','S_query']:
            b=np.mean([r['NLL'] for r in selection[n]]);l=np.mean([r['NLL'] for r in selection['L']]);gate['gain_each_baseline'][n]=float((b-l)/b);gate['Top1_no_worse'][n]=sum(r['top1_error'] for r in selection['L'])<=sum(r['top1_error'] for r in selection[n]);gate['maximum_individual_harm_nat'][n]=max(lr['NLL']-br['NLL'] for lr,br in zip(selection['L'],selection[n]))
        meta=load(CORE/'M2/MODEL_METADATA.json');L=meta['L']['capacity'];S=meta['S_query']['capacity'];gate['capacity_pass']=all(L[k]<=S[k] for k in ['active_states','canonical_total_bytes','actual_minimal_runtime_object_bytes','runtime_NPZ_bytes'])
        gate['scientific_endpoint']='PASS_NUMERICAL_ENDPOINT_PENDING_INTEGRITY' if all(v>=.1 for v in gate['gain_each_baseline'].values()) and all(gate['Top1_no_worse'].values()) and all(v<=.2 for v in gate['maximum_individual_harm_nat'].values()) and gate['capacity_pass'] else 'FAIL_ORIGINAL_B_ENDPOINT'
    else:gate['scientific_endpoint']='NOT_QUALIFIED_L_ARM_MISSING'
    dump(CORE/'ORIGINAL_B_GATE.json',gate)
    dump(CORE/'ANALYSIS_STAGE_STATUS.json',dict(status='PASS_ALL_REGISTERED_SCALAR_DIAGNOSTICS_COMPUTED',wall_s=time.perf_counter()-start,scientific_fail_did_not_control_branches=True,formal_realizations=6,diagnostic_realizations=6,models=methods,truth_evaluation_after_blind_freeze=True))
    print(json.dumps(dict(gate=gate,summaries=summaries),indent=2))
if __name__=='__main__':main()
