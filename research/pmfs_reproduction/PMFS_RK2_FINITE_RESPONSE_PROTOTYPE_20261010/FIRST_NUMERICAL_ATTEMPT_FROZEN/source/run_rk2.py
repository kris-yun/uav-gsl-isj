"""One bounded RK2-A comparison. Training/reference prediction precedes tests.
Inference imports a separate pure observation/forecast interface; compression
evaluation is explicitly simulator-state access, and never informs inference.
"""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import os,json,csv,hashlib,math,time,importlib.util,shutil,tempfile
import numpy as np
import rk2_models as models
import rk2_infer as inference
import test_rk2_infer as interface_tests

def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def csvout(p,rr):
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rr[0]));w.writeheader();w.writerows(rr)
def module(name,p):
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def main(parent,out):
    started=time.perf_counter();contract=load(out/'contract.json')
    assert sha(out/'contract.json')==(out/'PRE_RUN_CONTRACT_SHA256.txt').read_text().split()[0]
    for n,h in contract['source_SHA256'].items():assert sha(out/'source'/n)==h,n
    input_sha=load(out/'PARENT_INPUT_SHA256.json')
    for n,h in input_sha.items():assert sha(parent/n)==h,n
    for n,h in contract['prepared_input_SHA256'].items():assert sha(out/n)==h,n
    progress_file=out/'PROGRESS.json';progress_events=[]
    def progress(phase,**values):
        v=dict(phase=phase,wall_s=time.perf_counter()-started,sequence=len(progress_events)+1,**values)
        progress_events.append(v);dump(progress_file,v)
        with (out/'PROGRESS_EVENTS.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(v,ensure_ascii=False)+'\n')
        if v['wall_s']>contract['wall_limit_s']:raise TimeoutError('Internal frozen 600s wall budget')
    progress('INPUT_HASHES_PASS',inputs=len(input_sha))
    raw=module('rk2_frozen_native_raw_math',out/'source/verify_raw_receiver_queries.py')
    primitive=module('rk2_frozen_native_primitive',out/'source/cache_native.py').cutoff_and_contributions
    geometry=parent/'PARENT_M2M3_FROZEN/M2_FROZEN/frozen_B4_inputs/derived_B4/OccupancyGrid3D.csv'
    occ=raw.occupancy(geometry)
    layout=load(out/'INPUT_LAYOUT.json');references=layout['reference_banks'];test=layout['compression_evaluation']
    cache_root=parent/'RK0_NEW/reference_contribution_cache';ci=load(cache_root/'CONTRIBUTION_CACHE_RESULT.json')
    entries={(e['bank'],e['frame']):e for e in ci['frames']}
    frame_data={};filaments=[];phis=[];weights=[];slices={};offset=0
    refdesc={};m2=parent/'PARENT_M2M3_FROZEN/M2_FROZEN/native_reference_evidence/realizations'
    for ref in references:
        rid=ref['opaque_id'];bank=ref['parent_bank'];unique=sorted({q['frame'] for q in ref['queries']})
        total=sum(int(entries[bank,f]['exposure_weight'])*int(entries[bank,f]['filament_records']) for f in unique)
        for frame in unique:
            e=entries[bank,frame]
            with np.load(cache_root/e['cache_relative_path']) as z:
                ff=z['filaments'].copy();phi=z['contributions'].copy();native=z['native_totals'].copy()
            # Cache provenance/serial parity; no target/test states are loaded here.
            assert np.array_equal(np.cumsum(phi,axis=0,dtype=np.float32)[-1].view(np.uint32),native.view(np.uint32))
            frame_data[rid,frame]=dict(f=ff,phi=phi,native=native)
            slices[rid,frame]=(offset,offset+len(ff));offset+=len(ff)
            filaments.append(ff);phis.append(phi);weights.append(np.full(len(ff),e['exposure_weight']/total))
        refdesc[rid]=raw.snapshot(m2/bank/'bank'/('iteration_'+str(unique[0])))
    ff=np.concatenate(filaments);phi=np.concatenate(phis);ww=np.concatenate(weights)
    cells,features=models.physical_features(ff)
    queries=[dict(reference_id=r['opaque_id'],**q) for r in references for q in r['queries']]
    y=np.array([q['native_ppm'] for q in queries]);poses=np.array([q['pose_id'] for q in queries],dtype=np.int32)
    data=dict(f=ff,phi=phi,weights=ww,cells=cells,features=features,queries=queries,slices=slices,targets=y,poses=poses)
    # Run a real local native operator anchor before any new fit.
    first=references[0]['queries'][0];desc=refdesc[references[0]['opaque_id']]
    _,tot,e,b,p=primitive(desc['filaments'],np.array([first['receiver_xyz']],dtype=np.float32),desc,occ,raw)
    assert abs(float(tot[0])-first['native_ppm'])<=3e-7+5e-6*abs(first['native_ppm'])
    dump(out/'PRE_FIT_NATIVE_ANCHOR.json',dict(native_CPP_ppm=first['native_ppm'],local_native_ppm=float(tot[0]),absolute_difference=abs(float(tot[0])-first['native_ppm']),LOS_calls=int(e[0]),particle_tests=len(desc['filaments'])))
    progress('PRE_FIT_NATIVE_ANCHOR_PASS',reference_particles=len(ff),training_queries=len(queries))
    U=models.build_model(data,dict(kind='U'),contract);progress('U_QUERY_FITTED',train_MSE=U['train_MSE'],capacity=U['capacity'])
    S_spec=dict(kind='S',z_cut=models.weighted_quantile(features[:,2],ww,.5),sigma_cut=models.weighted_quantile(features[:,3],ww,.5))
    S=models.build_model(data,S_spec,contract);progress('S_QUERY_FITTED',train_MSE=S['train_MSE'],capacity=S['capacity'])
    L,proposals=models.learn_one_tree(data,contract,S,U,progress)
    fitted=dict(U_query=U,S_query=S,L=L)
    dump(out/'TRAIN_TREE_PROPOSAL_LOG.json',proposals)
    (out/'models').mkdir()
    for name,model in fitted.items():
        model['id']=name
        model['capacity'].update(decoder_nonzero_coefficients=int(np.count_nonzero(model['h'])),actual_key_array_nbytes=int(model['keys'].nbytes),actual_decoder_array_nbytes=int(model['h'].nbytes))
        np.savez_compressed(out/'models'/(name+'.npz'),keys=model['keys'],decoder=model['h'],prior=model['prior'],train_counts=model['X'],train_native_ppm=y,train_pose_ids=poses,routing_spec=np.array(json.dumps(model['spec'],sort_keys=True)))
    dump(out/'FINAL_MODEL_RULES_AND_TRAIN_FITS.json',{name:{k:model[k] for k in ['spec','capacity','fit_logs','train_MSE']} for name,model in fitted.items()})
    fit_hash={p.name:sha(p) for p in sorted((out/'models').iterdir())}
    dump(out/'PRE_REFERENCE_PREDICTION_MODEL_SHA256.json',fit_hash)
    runtime={name:dict(spec=json.loads(json.dumps(model['spec'])),keys=model['keys'].copy(),h=model['h'].copy()) for name,model in fitted.items()}
    (out/'runtime_models').mkdir()
    for name,model in runtime.items():
        np.savez(out/'runtime_models'/(name+'.npz'),keys=model['keys'],decoder=model['h'],routing_spec=np.array(json.dumps(model['spec'],sort_keys=True)))
        fitted[name]['capacity']['actual_runtime_NPZ_file_bytes']=(out/'runtime_models'/(name+'.npz')).stat().st_size
    progress('ONE_L_FIT_FROZEN',proposals=len(proposals),capacity=L['capacity'])

    # Candidate-only forecast generation; test observation or hidden state is unused.
    candidate_ids=list(dict.fromkeys(r['candidate_hypothesis_id'] for r in references))
    grouped={cid:[r for r in references if r['candidate_hypothesis_id']==cid] for cid in candidate_ids}
    assert len(candidate_ids)==2 and all(len(v)==2 for v in grouped.values())
    membership={r['opaque_id']:(c,ri) for c,cid in enumerate(candidate_ids) for ri,r in enumerate(grouped[cid])}
    source_xyz=[]
    for cid in candidate_ids:
        point=refdesc[grouped[cid][0]['opaque_id']]['source']
        assert all(np.array_equal(refdesc[r['opaque_id']]['source'],point) for r in grouped[cid])
        source_xyz.append(list(map(float,point)))
    reference_predictions=[];costs=[];responses={name:np.zeros((len(candidate_ids),2,50)) for name in ['F','U_query','S_query','L']}
    read_wall=0.
    for ref in references:
        c,r=membership[ref['opaque_id']];bank=ref['parent_bank'];rid=ref['opaque_id'];desc_cache={}
        for q in ref['queries']:
            t=time.perf_counter()
            if q['frame'] not in desc_cache:desc_cache[q['frame']]=raw.snapshot(m2/bank/'bank'/('iteration_'+str(q['frame'])))
            desc=desc_cache[q['frame']];read_time=time.perf_counter()-t;read_wall+=read_time
            t=time.perf_counter();_,total,eligible,blocked,positive=primitive(desc['filaments'],np.array([q['receiver_xyz']],dtype=np.float32),desc,occ,raw)
            Fwall=time.perf_counter()-t;fvalue=float(total[0]);assert abs(fvalue-q['native_ppm'])<=3e-7+5e-6*abs(q['native_ppm'])
            values={'F':fvalue};responses['F'][c,r,q['block_id']]=fvalue
            costs.append(dict(role='candidate_reference',input_id=rid,block_id=q['block_id'],method='F',particle_tests=len(desc['filaments']),LOS_calls=int(eligible[0]),fallback_particles=0,read_wall_s=read_time,route_wall_s=0.,decode_wall_s=0.,physical_wall_s=Fwall,total_readout_wall_s=Fwall))
            snap=models.CompressionSnapshot(desc,np.array(q['receiver_xyz'],dtype=np.float32),q['pose_id'])
            for name,model in runtime.items():
                value,detail=models.compress(snap,model,raw,primitive,occ);values[name]=value;responses[name][c,r,q['block_id']]=value
                costs.append(dict(role='candidate_reference',input_id=rid,block_id=q['block_id'],method=name,particle_tests=detail['phi_particle_tests'],LOS_calls=detail['LOS_calls'],fallback_particles=detail['fallback_particles'],read_wall_s=read_time,route_wall_s=detail['state_assignment_wall_s'],decode_wall_s=detail['decode_wall_s'],physical_wall_s=detail['fallback_wall_s'],total_readout_wall_s=detail['total_compression_wall_s']))
            reference_predictions.append(dict(reference_id=rid,candidate_id=ref['candidate_hypothesis_id'],block_id=q['block_id'],frame=q['frame'],pose_id=q['pose_id'],native_CPP_ppm=q['native_ppm'],**{k+'_ppm':v for k,v in values.items()}))
            if q['block_id']%10==0:progress('CANDIDATE_REFERENCE_READOUT',reference_id=rid,block_id=q['block_id'],models=len(fitted))
    (out/'candidate_forecasts').mkdir()
    for name,array in responses.items():
        np.savez_compressed(out/'candidate_forecasts'/(name+'.npz'),candidate_ids=np.array(candidate_ids),source_xyz=np.array(source_xyz),reference_response_ppm=array,receiver_plan_id=np.array('B4_FROZEN_50_V0'))
    csvout(out/'CANDIDATE_REFERENCE_READOUTS.csv',reference_predictions)
    forecast_hash={p.name:sha(p) for p in (out/'candidate_forecasts').iterdir()}
    dump(out/'CANDIDATE_FORECAST_SHA256_BEFORE_OBSERVATIONS.json',forecast_hash)
    progress('CANDIDATE_FORECASTS_FROZEN_ALL_SOURCES',reference_queries=200)
    # Pure inference path has no particles, source labels, Q, phi, or tails.
    blind=[];interface_checks=[]
    for name in responses:
        fp=out/'candidate_forecasts'/(name+'.npz')
        for obs_file in sorted((out/'observable_inputs').glob('O*.json')):
            answer=inference.infer_files(fp,obs_file,name);blind.append(dict(model_id=name,observation_id=obs_file.stem,result=answer))
            with tempfile.TemporaryDirectory(prefix='rk2_info_') as temp:
                tmp=Path(temp);hidden=tmp/'test_hidden_particles.bin';hidden.write_bytes(b'not_an_inference_input')
                truth=tmp/'test_generator_mapping.json';truth.write_text('{"false_source":"never_read"}',encoding='utf-8')
                qc=interface_tests.file_oracle_checks(fp,obs_file,name,hidden_files=(hidden,),truth_files=(truth,))
            interface_checks.append(dict(model_id=name,observation_id=obs_file.stem,checks=qc))
    dump(out/'SOURCE_TASK_PREDICTIONS_BLIND.json',blind)
    dump(out/'ACTUAL_INFER_INFORMATION_CHECKS.json',interface_checks)
    frozen={p.relative_to(out).as_posix():sha(p) for folder in ['models','candidate_forecasts','observable_inputs'] for p in (out/folder).iterdir()}
    frozen['SOURCE_TASK_PREDICTIONS_BLIND.json']=sha(out/'SOURCE_TASK_PREDICTIONS_BLIND.json')
    dump(out/'PRE_TRUTH_EVALUATION_SHA256.json',frozen)
    progress('INFERENCE_FROZEN_BEFORE_TRUTH_OR_COMPRESSION_TEST_STATES',tasks=len(blind))

    # Separate oracle compression interface: states used only after predictions freeze.
    compression=[]
    for ev in test:
        oid=ev['opaque_id'];bank=ev['parent_bank'];desc_cache={}
        for q in ev['queries']:
            t=time.perf_counter()
            if q['frame'] not in desc_cache:desc_cache[q['frame']]=raw.snapshot(m2/bank/'bank'/('iteration_'+str(q['frame'])))
            desc=desc_cache[q['frame']];read_time=time.perf_counter()-t
            t=time.perf_counter();_,total,eligible,blocked,positive=primitive(desc['filaments'],np.array([q['receiver_xyz']],dtype=np.float32),desc,occ,raw)
            Fwall=time.perf_counter()-t;fvalue=float(total[0]);assert abs(fvalue-q['native_ppm'])<=3e-7+5e-6*abs(q['native_ppm'])
            costs.append(dict(role='compression_oracle_evaluation',input_id=oid,block_id=q['block_id'],method='F',particle_tests=len(desc['filaments']),LOS_calls=int(eligible[0]),fallback_particles=0,read_wall_s=read_time,route_wall_s=0.,decode_wall_s=0.,physical_wall_s=Fwall,total_readout_wall_s=Fwall))
            snap=models.CompressionSnapshot(desc,np.array(q['receiver_xyz'],dtype=np.float32),q['pose_id'])
            for name,model in runtime.items():
                value,detail=models.compress(snap,model,raw,primitive,occ)
                compression.append(dict(observation_id=oid,block_id=q['block_id'],frame=q['frame'],pose_id=q['pose_id'],method=name,exact_F_ppm=fvalue,native_CPP_ppm=q['native_ppm'],predicted_ppm=value,error_ppm=value-fvalue,
                    event_error=int(np.float32(value)>np.float32(.1))!=int(np.float32(fvalue)>np.float32(.1)),**detail))
                costs.append(dict(role='compression_oracle_evaluation',input_id=oid,block_id=q['block_id'],method=name,particle_tests=detail['phi_particle_tests'],LOS_calls=detail['LOS_calls'],fallback_particles=detail['fallback_particles'],read_wall_s=read_time,route_wall_s=detail['state_assignment_wall_s'],decode_wall_s=detail['decode_wall_s'],physical_wall_s=detail['fallback_wall_s'],total_readout_wall_s=detail['total_compression_wall_s']))
            if q['block_id']%10==0:progress('COMPRESSION_EVALUATION_ONLY',observation_id=oid,block_id=q['block_id'])
    csvout(out/'COMPRESSION_EVALUATION_READOUTS.csv',compression);csvout(out/'ALL_READOUT_COSTS.csv',costs)
    # Ground-truth identity first read now, to evaluate immutable inference.
    truth=load(out/'evaluation_only/truth_mapping_AFTER_prediction_freeze.json')
    taskmetrics=[]
    for row in blind:
        oid=row['observation_id'];true=truth[oid];res=row['result'];byid={r['candidate_id']:r for r in res['candidates']};assert true in byid
        top=set(res['top1_candidate_ids']);prob=byid[true]['source_probability']
        taskmetrics.append(dict(observation_id=oid,method=row['model_id'],correct_source_for_evaluation_only=true,source_NLL_nat=-math.log(prob),Top1_error=int(len(top)!=1 or true not in top),Top1_tie_count=len(top),true_source_probability=prob,
            true_mean_Brier=byid[true]['mean_Brier'],true_mean_Bernoulli_log_score=byid[true]['mean_Bernoulli_log_score'],wrong_mean_Bernoulli_log_score=next(r['mean_Bernoulli_log_score'] for k,r in byid.items() if k!=true),score_is_composite_not_calibrated_posterior=True))
    csvout(out/'SOURCE_TASK_METRICS_AFTER_FREEZE.csv',taskmetrics)
    compmetrics=[]
    for oid in sorted(truth):
        for name in fitted:
            rr=[r for r in compression if r['observation_id']==oid and r['method']==name];assert len(rr)==50
            errors=[r['error_ppm'] for r in rr]
            compmetrics.append(dict(observation_id=oid,method=name,MSE_ppm2=math.fsum(e*e for e in errors)/50,mean_signed_error_ppm=math.fsum(errors)/50,MAE_ppm=math.fsum(abs(e) for e in errors)/50,event_errors=sum(r['event_error'] for r in rr),fallback_particle_fraction=sum(r['fallback_particles'] for r in rr)/sum(r['particles'] for r in rr),blocks_with_fallback=sum(r['fallback_particles']>0 for r in rr),all_50_queries_included=True,oracle_encoding_only=True))
    csvout(out/'COMPRESSION_METRICS.csv',compmetrics)
    summary={name:dict(equal_bank_source_NLL=math.fsum(r['source_NLL_nat'] for r in taskmetrics if r['method']==name)/4,Top1_errors=sum(r['Top1_error'] for r in taskmetrics if r['method']==name)) for name in responses}
    tol=contract['task_score_tolerance'];Lscores=summary['L']
    ordinary_gain=all(summary[n]['equal_bank_source_NLL']-Lscores['equal_bank_source_NLL']>tol and Lscores['Top1_errors']<=summary[n]['Top1_errors'] for n in ['U_query','S_query'])
    costs_summary=[]
    for role in sorted({r['role'] for r in costs}):
        for name in responses:
            rr=[r for r in costs if r['role']==role and r['method']==name]
            costs_summary.append(dict(role=role,method=name,queries=len(rr),total_readout_wall_s=math.fsum(r['total_readout_wall_s'] for r in rr),shared_parse_wall_s=math.fsum(r['read_wall_s'] for r in rr),phi_particle_tests=sum(r['particle_tests'] for r in rr),LOS_calls=sum(r['LOS_calls'] for r in rr),fallback_particles=sum(r['fallback_particles'] for r in rr)))
    csvout(out/'READOUT_COST_SUMMARY.csv',costs_summary)
    refcost={r['method']:r for r in costs_summary if r['role']=='candidate_reference'}
    latency_pass=refcost['L']['total_readout_wall_s']<=refcost['F']['total_readout_wall_s']
    storage_pass=(L['capacity']['canonical_total_bytes']<=S['capacity']['canonical_total_bytes'] and L['capacity']['actual_minimal_runtime_object_bytes']<=S['capacity']['actual_minimal_runtime_object_bytes'] and L['capacity']['actual_runtime_NPZ_file_bytes']<=S['capacity']['actual_runtime_NPZ_file_bytes'])
    status='A_DEVELOPMENT_GATE_PASS_REQUEST_B_ONLY' if ordinary_gain and latency_pass and storage_pass else 'A_CURRENT_CONSTRUCTION_NOT_QUALIFIED_NO_EXPANSION'
    result=dict(status=status,science_hypothesis_worth_studying='PASS_INHERITED_RK1_NOT_REVOKED',method_source_task_gain=ordinary_gain,latency_vs_local_python_F_pass=latency_pass,canonical_storage_budget_pass=storage_pass,
        source_summary=summary,equal_bank_compression_MSE={n:math.fsum(r['MSE_ppm2'] for r in compmetrics if r['method']==n)/4 for n in fitted},
        test_realizations=4,independent_new_realizations=0,proposals=len(proposals),new_L_constructions=1,
        new_GADEN_CFD_ROS_VM_navigation_or_network_training=0,source_probabilities_are_composite_softmax_not_calibrated_posterior=True,
        compression_states_not_used_in_inference=True,C_ORACLE_not_an_arm=True,shared_transport_cost_not_reduced=True,
        offline_model_fit_and_search_wall_s=next(v['wall_s'] for v in progress_events if v['phase']=='ONE_L_FIT_FROZEN'),
        producer_wall_s=time.perf_counter()-started,next_B_execution='NOT_AUTHORIZED_NOT_STARTED')
    dump(out/'RK2_RESULT.json',result)
    dump(out/'FINAL_CAPACITY_AND_STORAGE.json',{name:model['capacity'] for name,model in fitted.items()})
    for n,h in frozen.items():assert sha(out/n)==h,n
    progress('COMPLETED_NO_FUTURE_B_EXECUTION',result_status=status)
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':
    import argparse
    a=argparse.ArgumentParser();a.add_argument('--parent',type=Path,required=True);a.add_argument('--out',type=Path,required=True);args=a.parse_args()
    try:main(args.parent,args.out)
    except Exception as exc:
        dump(args.out/'RUN_FAILURE.json',dict(error_type=type(exc).__name__,error=str(exc),no_automatic_retry=True));raise
