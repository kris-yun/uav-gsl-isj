"""Frozen-response compression gate, using old snapshots only. No native simulation.

U/S kernels pool all four references, with complete zero denominators. F is the
existing native PID observation. Physical classes are oracle information.
"""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import argparse,csv,json,math,hashlib,importlib.util,time
import numpy as np
HERE=Path(__file__).resolve().parent
def js(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):
    with p.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def table(p,r):
    if not r:return
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(r[0]));w.writeheader();w.writerows(r)
def module(p,n):
    s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def keyset(fil,origin,model,cuts):
    xy=np.floor((fil[:,:2]-origin)/np.float32(.25)).astype(np.int64)
    if model=='U':cl=np.zeros(len(fil),dtype=np.int64)
    elif model=='S':cl=(fil[:,2].astype(float)>=cuts['z_split_m']).astype(np.int64)*2+(fil[:,3].astype(float)>=cuts['sigma_split_cm']).astype(np.int64)
    else:
        salt=b'PMFS_RK0_NONPHYSICAL_F32_STATE_HASH_v1'
        cl=np.array([int.from_bytes(hashlib.sha256(salt+np.asarray(f,dtype='<f4').tobytes()).digest()[:8],'little')%4 for f in fil],dtype=np.int64)
    return [(int(i),int(j),int(k)) for (i,j),k in zip(xy,cl)]
def frame_exposures(bank):
    schedule=[r for r in rows(bank/'QUERY_PHYSICAL_LINEAGE.csv') if r['membership_branch']=='0']
    n={}
    for r in schedule:n[int(r['selected_frame'])]=n.get(int(r['selected_frame']),0)+1
    assert sum(n.values())==50
    return n
def learn(model,cache_entries,root,origin,cuts):
    sums={};counts={};perbank={}
    for e in cache_entries:
        z=np.load(root/e['cache_relative_path']);fil=z['filaments'];phi=z['contributions']
        w=int(e['exposure_weight']);keys=keyset(fil,origin,model,cuts)
        for idx,key in enumerate(keys):
            if key not in counts:counts[key]=0;sums[key]=np.zeros(10,dtype=np.float64)
            counts[key]+=w;sums[key]+=phi[idx].astype(float)*w
        perbank[e['bank']]=perbank.get(e['bank'],0)+len(fil)*w
    kernels={k:sums[k]/counts[k] for k in counts}
    rr=[]
    for key in sorted(counts):
        for pose in range(10):rr.append(dict(model=model,cell_i=key[0],cell_j=key[1],class_id=key[2],pose_id=pose,complete_particle_exposure_denominator=counts[key],native_contribution_sum_ppm=float(sums[key][pose]),shared_h_ppm_per_particle=float(kernels[key][pose])))
    return kernels,rr,dict(model=model,active_cell_classes=len(counts),cell_count=len({k[:2] for k in counts}),reference_particle_exposures=sum(counts.values()),per_reference_particle_exposures=perbank,
      denominator='All particles including zero contributions; exposure multiplicity from frozen 50 block schedule',max_classes_per_XY=1 if model=='U' else 4)
def peak(sigma,desc,raw):
    den=math.sqrt(float(np.float32(np.float32(8)*raw.PI_CUBED)))*float(sigma)**3
    mol=np.float32(float(desc['total_moles'])/den)
    return float(np.float32(1e6*float(mol)/float(desc['all_gas_moles'])))
def predict(model,kernels,m2,origin,cuts,raw):
    out=[];missing=[]
    global_schedule={('receiver_b'+r['block_id']+'_v'+r['membership_branch']):r for r in rows(m2/'observation_lineage/FROZEN_RECEPTOR_SCHEDULE_ALL_MEMBERSHIP_BRANCHES.csv')}
    for bank in sorted((m2/'native_reference_evidence/realizations').iterdir()):
        if not bank.is_dir():continue
        query=[r for r in rows(bank/'QUERY_OUTPUT.csv') if r['query_id'].startswith('receiver_')]
        schedule={('receiver_b'+r['block_id']+'_v'+r['membership_branch']):r for r in rows(bank/'QUERY_PHYSICAL_LINEAGE.csv')}
        cache={}
        for q in query:
            frame=int(q['frame'])
            if frame not in cache:cache[frame]=raw.snapshot(bank/'bank'/('iteration_'+str(frame)))
            desc=cache[frame];fil=desc['filaments'];block=int(q['query_id'].split('_')[1][1:]);branch=int(q['query_id'].split('_')[2][1:]);r=schedule[q['query_id']];pose=int(global_schedule[q['query_id']]['stop_id'])
            assert pose in range(10)
            keys=keyset(fil,origin,model,cuts);counts={}
            for k in keys:counts[k]=counts.get(k,0)+1
            known=[];unknown=0;upper_extra=0.;outside=0;nonnav=0
            for k,n in counts.items():
                if k in kernels:known.append(n*float(kernels[k][pose]))
                else:
                    unknown+=n
                    sigma_lower=10. if model!='S' or k[2]%2==0 else cuts['sigma_split_cm']
                    pmax=peak(sigma_lower,desc,raw)
                    # Conservative native arithmetic allowance, fixed before execution.
                    bound=pmax*(1+raw.RTOL)+raw.ATOL;upper_extra+=n*bound
                    missing.append(dict(model=model,bank=bank.name,block_id=block,membership_branch=branch,pose_id=pose,frame=frame,cell_i=k[0],cell_j=k[1],class_id=k[2],uncovered_particle_count=n,
                                        native_sigma_minimum_cm=sigma_lower,per_particle_physical_peak_upper_ppm=bound))
                outside+=n*int(not(0<=k[0]<34 and 0<=k[1]<45))
            lo=math.fsum(known);hi=lo+upper_extra
            tau=float(np.float32(.1))
            event=1 if lo>tau else 0 if hi<=tau else None
            value=lo if unknown==0 else None
            full=float(q['ppm_float32']);truth=int(np.float32(full)>np.float32(.1))
            out.append(dict(model=model,bank=bank.name,role='reference' if bank.name in ['C7_0','C7_1','K2_0','K2_1'] else 'previously_seen_heldout',block_id=block,membership_branch=branch,pose_id=pose,frame=frame,
              native_F_ppm=full,native_F_event=truth,particle_count=len(fil),outside_original_2D_frame_particles=outside,
              count_supported_particles=len(fil)-unknown,uncovered_particles=unknown,point_prediction_ppm=value if value is not None else 'UNSUPPORTED',
              prediction_lower_ppm=lo,prediction_upper_ppm=hi,prediction_event=event if event is not None else 'AMBIGUOUS',
              event_certified_by_nonnegativity_or_peak_bound=unknown>0 and event is not None,
              point_squared_error=(value-full)**2 if value is not None else 'UNSUPPORTED',
              compression_error_lower_squared=max(lo-full,full-hi,0)**2,
              compression_error_upper_squared=max((lo-full)**2,(hi-full)**2),
              missing_interval_scope='Unknown kernel entries only; not physical-truth confidence interval or correction for covered-class compression error'))
    # Every reference key is learned; predicted reference events can always be scored.
    assert all(r['uncovered_particles']==0 for r in out if r['role']=='reference')
    return out,missing
def events(predictions):
    out={b:[None]*50 for b in ['C7_0','C7_1','K2_0','K2_1']}
    for r in predictions:
        if r['bank'] in out and r['membership_branch']==0:
            assert isinstance(r['prediction_event'],int);out[r['bank']][r['block_id']]=r['prediction_event']
    assert all(all(v is not None for v in z) for z in out.values())
    return {c:[out[c+'_0'],out[c+'_1']] for c in ['C7','K2']}
def native_events(m2):
    refs={b:[None]*50 for b in ['C7_0','C7_1','K2_0','K2_1']}
    for b in refs:
        for r in rows(m2/'native_reference_evidence/realizations'/b/'QUERY_OUTPUT.csv'):
            if r['query_id'].startswith('receiver_') and '_v0' in r['query_id']:
                i=int(r['query_id'].split('_')[1][1:]);refs[b][i]=int(np.float32(float(r['ppm_float32']))>np.float32(.1))
    return {c:[refs[c+'_0'],refs[c+'_1']] for c in ['C7','K2']}
def evaluate(model,pred,m2,out):
    obs=js(m2/'source_blind_inputs/branch_0.json')['observation_events'];sc=module(m2/'score_source_blind.py','rk0_sourceblind_scorer')
    ref=native_events(m2) if model=='F' else events(pred)
    inp=dict(reference_events=ref,observation_events=obs);dump(out/('SOURCE_BLIND_INPUT_'+model+'.json'),inp)
    scores=sc.source_blind_scores(ref,obs);dump(out/('SOURCE_BLIND_SCORES_'+model+'.json'),scores)
    return scores
def metrics(pred):
    rr=[]
    for bank in sorted({r['bank'] for r in pred}):
        z=[r for r in pred if r['bank']==bank and r['membership_branch']==0];assert len(z)==50
        v=[r for r in z if r['uncovered_particles']==0];cert=[r for r in z if isinstance(r['prediction_event'],int)]
        rr.append(dict(model=z[0]['model'],bank=bank,role=z[0]['role'],blocks=50,fully_covered_blocks=len(v),certified_events=len(cert),ambiguous_events=50-len(cert),
          uncovered_particle_exposures=sum(r['uncovered_particles'] for r in z),total_particle_exposures=sum(r['particle_count'] for r in z),
          MSE_complete_support_only=math.fsum(r['point_squared_error'] for r in v)/len(v) if v else 'UNSUPPORTED',
          all_block_MSE_outer_lower=math.fsum(r['compression_error_lower_squared'] for r in z)/50,
          all_block_MSE_outer_upper=math.fsum(r['compression_error_upper_squared'] for r in z)/50,
          certified_event_errors=sum(r['prediction_event']!=r['native_F_event'] for r in cert),
          total_event_error_lower=sum(r['prediction_event']!=r['native_F_event'] for r in cert),
          total_event_error_upper=sum(r['prediction_event']!=r['native_F_event'] for r in cert)+50-len(cert)))
    return rr
def comparisons(scoresU,scoresS,predU,predS,m2):
    mapping=js(m2/'HELDOUT_GENERATOR_MAPPING_ANALYSIS_ONLY.json');task_to_bank={'H101':'C7_2','H102':'K2_2','H103':'C7_3','H104':'K2_3'};task=[];receiver=[]
    for name,bank in task_to_bank.items():
        truth=mapping[name];wrong='K2' if truth=='C7' else 'C7'
        a=scoresU['tasks'][name];b=scoresS['tasks'][name]
        lu=(a[truth]['log_sum']-a[wrong]['log_sum'])/50;ls=(b[truth]['log_sum']-b[wrong]['log_sum'])/50
        bu=a[wrong]['brier_mean']-a[truth]['brier_mean'];bs=b[wrong]['brier_mean']-b[truth]['brier_mean']
        uu={r['block_id']:r for r in predU if r['bank']==bank and r['membership_branch']==0};ss={r['block_id']:r for r in predS if r['bank']==bank and r['membership_branch']==0}
        common=[i for i in uu if uu[i]['uncovered_particles']==ss[i]['uncovered_particles']==0]
        mseU=math.fsum(uu[i]['point_squared_error'] for i in common)/len(common) if common else None
        mseS=math.fsum(ss[i]['point_squared_error'] for i in common)/len(common) if common else None
        gain=ls-lu>1e-12 and bs-bu>1e-12
        task.append(dict(task=name,bank=bank,truth_for_analysis_only=truth,U_truth_directed_mean_log_margin=lu,S_truth_directed_mean_log_margin=ls,delta_mean_log_margin=ls-lu,
          U_truth_directed_Brier_contrast=bu,S_truth_directed_Brier_contrast=bs,delta_Brier_contrast=bs-bu,
          common_complete_support_blocks=len(common),U_MSE_common_support=mseU if mseU is not None else 'UNSUPPORTED',S_MSE_common_support=mseS if mseS is not None else 'UNSUPPORTED',
          source_both_scores_gain=gain,response_common_support_gain=mseU is not None and mseS<mseU,
          full_response_coverage=len(common)==50))
    return task
def main(m2,out,contract):
    start=time.perf_counter();assert sha(out/'frozen_contract.json')==(out/'PRE_RUN_CONTRACT_SHA256.txt').read_text().split()[0]
    for name,h in contract['inputs_sha256'].items():assert sha(m2/name)==h,name
    raw=module(out/'source/verify_raw_receiver_queries.py','rk0_native_math')
    producer=module(out/'source/cache_native.py','rk0_native_cache')
    cache=producer.build_cache(m2,out/'reference_contribution_cache',contract)
    assert cache['reference_ids']==contract['reference_realizations']
    for e in cache['frames']:e['cache_relative_path']='reference_contribution_cache/'+e['cache_relative_path']
    origin=np.array([contract['origin_x'],contract['origin_y']],dtype=np.float32)
    allfit=[]
    for e in cache['frames']:
        fil=np.load(out/e['cache_relative_path'])['filaments']
        for _ in range(int(e['exposure_weight'])):allfit.append(fil[:,[2,3]].astype(np.float64))
    full=np.concatenate(allfit,axis=0);cuts=dict(z_split_m=float(np.median(full[:,0])),sigma_split_cm=float(np.median(full[:,1])),
      definition='Global reference-only population-occurrence median; weighted by 50 planned-time exposures, repeated frames are correlated observations.',
      total_reference_particle_exposures=len(full),reference_source_identity_not_used_for_class_split=True)
    dump(out/'REFERENCE_ONLY_STATE_BOUNDARIES.json',cuts);del full,allfit
    scores={};predictions={};modelmeta=[]
    for model in ['U','S']:
        print('FIT '+model,flush=True)
        kernels,kt,meta=learn(model,cache['frames'],out,origin,cuts);table(out/('KERNEL_'+model+'.csv'),kt);modelmeta.append(meta)
        pred,missing=predict(model,kernels,m2,origin,cuts,raw);predictions[model]=pred
        table(out/('PREDICTIONS_'+model+'.csv'),pred);table(out/('UNCOVERED_STATES_'+model+'.csv'),missing)
        table(out/('RECEIVER_METRICS_'+model+'.csv'),metrics(pred));scores[model]=evaluate(model,pred,m2,out)
    scores['F']=evaluate('F',None,m2,out)
    # Freeze predictions/source-blind scores before generator identities enter analysis.
    blind_files=[p for p in out.glob('SOURCE_BLIND_*.json')]
    dump(out/'BLIND_SCORES_PRE_ANALYSIS_SHA256.json',{p.name:sha(p) for p in blind_files})
    comp=comparisons(scores['U'],scores['S'],predictions['U'],predictions['S'],m2);table(out/'PAIRED_U_S_HELDOUT_RESULTS.csv',comp)
    sg=sum(r['source_both_scores_gain'] for r in comp);rg=sum(r['source_both_scores_gain'] and r['response_common_support_gain'] for r in comp)
    nonadverse=math.fsum(r['delta_mean_log_margin'] for r in comp)>=-1e-12 and math.fsum(r['delta_Brier_contrast'] for r in comp)>=-1e-12
    control_trigger=rg>=2 and nonadverse
    control=[]
    if control_trigger:
        print('PREDECLARED R CONTROL',flush=True)
        kernels,kt,meta=learn('R',cache['frames'],out,origin,cuts);table(out/'KERNEL_R.csv',kt);modelmeta.append(meta)
        pred,missing=predict('R',kernels,m2,origin,cuts,raw);predictions['R']=pred;table(out/'PREDICTIONS_R.csv',pred);table(out/'UNCOVERED_STATES_R.csv',missing)
        table(out/'RECEIVER_METRICS_R.csv',metrics(pred));scores['R']=evaluate('R',pred,m2,out)
        control=comparisons(scores['R'],scores['S'],pred,predictions['S'],m2);table(out/'PAIRED_R_S_HELDOUT_RESULTS.csv',control)
    taskrows=[];mapping=js(m2/'HELDOUT_GENERATOR_MAPPING_ANALYSIS_ONLY.json')
    for model,sc in scores.items():
        for name,t in sc['tasks'].items():
            truth='C7' if name=='O0' else mapping[name];wrong='K2' if truth=='C7' else 'C7'
            taskrows.append(dict(model=model,task=name,truth_analysis_only=truth,log_choice='C7' if t['C7']['log_sum']>t['K2']['log_sum'] else 'K2' if t['K2']['log_sum']>t['C7']['log_sum'] else 'TIE',
              Brier_choice='C7' if t['C7']['brier_mean']<t['K2']['brier_mean'] else 'K2' if t['K2']['brier_mean']<t['C7']['brier_mean'] else 'TIE',
              truth_directed_log_margin=t[truth]['log_sum']-t[wrong]['log_sum'],truth_directed_Brier_contrast=t[wrong]['brier_mean']-t[truth]['brier_mean'],
              log_correct=t[truth]['log_sum']>t[wrong]['log_sum'],Brier_correct=t[truth]['brier_mean']<t[wrong]['brier_mean']))
    table(out/'ALL_SOURCE_TASK_RESULTS.csv',taskrows);dump(out/'MODEL_COMPLEXITY_AND_ZERO_DENOMINATORS.json',modelmeta)
    counts={m:{kind:sum(r[kind+'_correct'] for r in taskrows if r['model']==m and r['task']!='O0') for kind in ['log','Brier']} for m in scores}
    supported_full=all(r['full_response_coverage'] for r in comp)
    if control_trigger:
        beatsR=sum(r['source_both_scores_gain'] and r['response_common_support_gain'] for r in control)>=2
        verdict='S_ADDITIONAL_DIAGNOSTIC_VALUE' if beatsR else 'RESPONSE_OR_PARAMETER_GAIN_NOT_SPECIFIC_STATE_EVIDENCE'
        if not supported_full:verdict+='_WITH_KERNEL_COVERAGE_LIMIT'
    elif counts['U']==counts['F'] and rg<2:verdict='U_SUFFICIENT_FOR_CURRENT_SOURCE_DECISIONS_S_NO_ADDITIONAL_TASK_GATE'
    elif any(r['response_common_support_gain'] for r in comp):verdict='RESPONSE_IMPROVEMENT_WITHOUT_TASK_GATE'
    else:verdict='U_S_NOT_F_PRESERVING_OR_NULL'
    result=dict(execution_status='PASS_WITH_UNSUPPORTED_PREDICTIONS_REPORTED' if not supported_full else 'PASS',research_decision=verdict,
      source_task_correct_counts=counts,S_source_both_score_gains=sg,S_joint_common_support_response_and_task_gains=rg,S_direction_nonadverse=nonadverse,
      same_cap_R_control_triggered=control_trigger,full_heldout_U_S_receiver_coverage=supported_full,
      total_wall_s=time.perf_counter()-start,new_gas=0,new_CFD=0,new_navigation=0,new_training=0,
      interpretation=['Response/state compression only, not new transport or deployed source localization.','S is fixed physical binning, not CSCG or learned clones.','Four previously inspected heldouts are exploratory; two proper scores are not independent experiments.',
      'Unseen h entries are missing, never zero-filled; intervals bound their contribution only, not covered-class model error.','Candidate event probability averages per-realization threshold events; does not threshold average concentration across realizations.',
      'Conditional mean class kernels still omit within-class response fluctuations. Population count randomness is preserved only across these finite oracle realizations.'])
    dump(out/'RK0_RESULT.json',result);print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--m2',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    main(a.m2,a.output,js(a.output/'frozen_contract.json'))
