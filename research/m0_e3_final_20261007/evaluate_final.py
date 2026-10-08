"""Frozen all40 LORO evaluation. U0 observations fixed, BMA cannot rescue gate."""
from pathlib import Path
import csv,hashlib,importlib.util,json,math
import numpy as np
from scipy.special import logsumexp
from qualify_run import qualify,rows,sha
R=Path(__file__).resolve().parent;F=R.parent/'m0_clean_support_r0_20261007';DATA=R/'evidence'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def write(n,x):(R/n).write_bytes((json.dumps(x,indent=2)+'\n').encode())
def csvout(n,data):
    with (R/n).open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(data[0]),lineterminator='\n');w.writeheader();w.writerows(data)
def likelihood(training,query,family):
    # API has no true-source label. Training is exactly 3 independent seed arrays.
    assert training.shape==(3,51) and query.shape==(51,)
    if family=='HIT_FORWARD':
        p=((training>=.1).sum(axis=0)+.5)/4;h=query>=.1;return float(np.sum(h*np.log(p)+(~h)*np.log1p(-p)))
    z=np.log1p(training);mean=z.mean(axis=0);var=np.maximum(z.var(axis=0,ddof=1),.0625);q=np.log1p(query)
    return float(-.5*np.sum(np.log(2*np.pi*var)+(q-mean)**2/var))
def posterior(scores):return np.exp(np.array(scores)-logsumexp(scores))
def source_scores(p,true_index,xyz,oracle=None):
    tie=abs(p[0]-p[1])<=1e-12;correct=not tie and int(np.argmax(p))==true_index;brier=float((1-p[true_index])**2)
    return {'p_S0':float(p[0]),'p_S1':float(p[1]),'p_true':float(p[true_index]),'brier':brier,'NLL':float(-math.log(max(float(p[true_index]),1e-15))),'rank':1.5 if tie else (1 if correct else 2),'top1':bool(correct),'tie':bool(tie),'MAP_error_m':2.0 if tie else float(np.linalg.norm(xyz[int(np.argmax(p))]-xyz[true_index])),'posterior_mean_error_m':float(np.linalg.norm(p@xyz-xyz[true_index])),'TV_vs_U0':None if oracle is None else float(.5*np.abs(p-oracle).sum())}
for q in rows(F/'M0_R0_FILES_SHA256.csv'):assert sha(F/q['path'])==q['sha256']
seal=read(R/'E3_EXECUTION_SEAL.json')
for name,h in seal['scripts_sha256'].items():assert sha(R/name)==sha(DATA/name)==h,(name,'pre-run seal')
A=read(R/'E3_AUTHORIZATION.json');INDEX=read(DATA/'ALL40_INDEX.json');M=read(DATA/'E3_ASSET_MANIFEST.json');D=read(F/'M0_DOMAIN_ROI_GUARD_CONTRACT.json');S=read(F/'M0_SOURCE_CONTRACT.json');I=read(F/'M0_INFERENCE_CONTRACT.json');geom=rows(F/'M0_UAV_ROUTE_POINTS.csv');times=S['clock']['score_times_s'];assert len(INDEX)==40 and {q['frozen_row']['run_id'] for q in INDEX}=={q['run_id'] for q in A['all_frozen_rows']}
obs={};footprints={};qualifications=[];allrecords=[];original_ids={q['run_id']:q for q in A['all_frozen_rows']}
for entry in INDEX:
    row=entry['frozen_row'];rid=row['run_id'];key=(row['source_id'],int(row['realization']),row['wind_arm']);audit=DATA/'bank'/rid/'audit';raw=DATA/'bank'/rid/'result';reference=DATA/'bank'/('m0r0_U0_'+row['source_id']+'_r'+str(row['realization']).zfill(2))/'audit'
    rep,recs=qualify(row,audit,raw,reference,D,S,M['wind_readback_stats'][row['wind_arm']],M['noise_tables'][row['master_seed']],geom);qualifications.append(rep);allrecords.extend(recs)
    assert sha(DATA/'projects'/row['wind_arm']/'wind/wind_iteration_0')==row['expected_wind_sha256']
    obs[key]=np.array([float(q['ppm']) for q in rows(audit/'route.csv')]);footprints[key]=np.stack([np.fromfile(audit/('roi_column_t'+str(t)+'.f32'),dtype='<f4') for t in times]).astype(float)
assert len(obs)==40;xyz=np.array([s['xyz_m'] for s in S['candidate_sources']]);winds=['U0','A_on','A_off','B_shear','B_speed'];families=['HIT_FORWARD','LOG_GAUSSIAN'];predictions=[];bma_models=[];folds=[]
for s in ['S0','S1']:
    for r in [1,2,3,4]:
        query=obs[(s,r,'U0')];truth=0 if s=='S0' else 1;train=[k for k in [1,2,3,4] if k!=r]
        folds.append({'query_source_evaluator_only':s,'held_out_realization':r,'held_out_master_seed':2026100700+r,'true_observation_wind':'U0','true_observation_route_sha256':sha(DATA/'bank'/('m0r0_U0_'+s+'_r'+str(r).zfill(2))/'audit/route.csv'),'train_realizations_both_sources_all5winds':train,'train_master_seeds':[2026100700+k for k in train],'train_count_per_source_wind':3,'excluded_from_both_sources_all_winds':True})
        for fam in families:
            evidence={}
            for w in winds:evidence[w]=[likelihood(np.stack([obs[(cand,k,w)] for k in train]),query,fam) for cand in ['S0','S1']]
            oracle=posterior(evidence['U0']);oraclebrier=float((1-oracle[truth])**2)
            for w in winds:
                p=posterior(evidence[w]);q=source_scores(p,truth,xyz,oracle);q.update({'source_id':s,'realization':r,'master_seed':2026100700+r,'family':fam,'model':w,'heldout_excluded_from_all_sources_winds':True,'train_realizations':';'.join(map(str,train)),'query_wind_always_U0':True,'loglik_S0':evidence[w][0],'loglik_S1':evidence[w][1],'D_B_vs_U0':q['brier']-oraclebrier});predictions.append(q)
            models=I['WRONG_MODEL_BMA']['models'];joint=np.array([evidence[w] for w in models]).T-math.log(8);lognorm=logsumexp(joint);j=np.exp(joint-lognorm);p=j.sum(axis=1);weights=j.sum(axis=0);q=source_scores(p,truth,xyz,oracle);q.update({'source_id':s,'realization':r,'master_seed':2026100700+r,'family':fam,'model':'WRONG_MODEL_BMA','heldout_excluded_from_all_sources_winds':True,'train_realizations':';'.join(map(str,train)),'query_wind_always_U0':True,'loglik_S0':float(logsumexp(joint[0])),'loglik_S1':float(logsumexp(joint[1])),'D_B_vs_U0':q['brier']-oraclebrier});predictions.append(q)
            for n,w in enumerate(models):bma_models.append({'source_id_evaluator_only':s,'realization':r,'family':fam,'wrong_model':w,'model_posterior':float(weights[n]),'model_log_evidence':float(logsumexp(joint[:,n])),'model_rank':1+int((weights>weights[n]+1e-12).sum())+.5*int((np.abs(weights-weights[n])<=1e-12).sum()-1),'joint_p_S0_model':float(j[0,n]),'joint_p_S1_model':float(j[1,n]),'U0_in_ensemble':False,'truth_used_for_weight':False})
lookup={(q['source_id'],q['realization'],q['family'],q['model']):q for q in predictions};forward=[]
for s in ['S0','S1']:
    for r in [1,2,3,4]:
        f0=footprints[(s,r,'U0')];y0=obs[(s,r,'U0')];assert np.linalg.norm(f0)>0
        for w in winds:
            fm=footprints[(s,r,w)];ym=obs[(s,r,w)];den=.5*(np.linalg.norm(fm)+np.linalg.norm(f0));forward.append({'source_id':s,'realization':r,'master_seed':2026100700+r,'wind_arm':w,'D_F':float(np.linalg.norm(fm-f0)/den) if den>0 else 0.,'D_Y':float(np.sqrt(np.mean((np.log1p(ym)-np.log1p(y0))**2))),'forward_route_detectable_samples':int((ym>=.1).sum()),'first_route_detection_s':next((times[i] for i,x in enumerate(ym) if x>=.1),None),'true_observation_always_U0':True})
fw={(q['source_id'],q['realization'],q['wind_arm']):q for q in forward};pair_rows={};paired=[]
for pair,(first,second) in {'A':['A_on','A_off'],'B':['B_shear','B_speed']}.items():
    pair_rows[pair]=[]
    for s in ['S0','S1']:
        for r in [1,2,3,4]:
            brier={f:{'oracle':lookup[(s,r,f,'U0')]['brier'],'first':lookup[(s,r,f,first)]['brier'],'second':lookup[(s,r,f,second)]['brier']} for f in families};row={'source':s,'realization':r,'D_F_first':fw[(s,r,first)]['D_F'],'D_F_second':fw[(s,r,second)]['D_F'],'D_Y_first':fw[(s,r,first)]['D_Y'],'D_Y_second':fw[(s,r,second)]['D_Y'],'brier':brier};pair_rows[pair].append(row)
            report={'pair':pair,'source_id':s,'realization':r,'master_seed':2026100700+r,'first_arm':first,'second_arm':second,'delta_D_F_first_minus_second':row['D_F_first']-row['D_F_second'],'delta_D_Y_first_minus_second':row['D_Y_first']-row['D_Y_second']}
            for fam in families:
                report[fam+'_delta_D_B_first_minus_second']=brier[fam]['first']-brier[fam]['second'];report[fam+'_first_damage_vs_U0']=brier[fam]['first']-brier[fam]['oracle'];report[fam+'_second_damage_vs_U0']=brier[fam]['second']-brier[fam]['oracle']
            paired.append(report)
oracle_obs=all(sum(q['route_detectable_samples']>=2 for q in qualifications if q['source_id']==s and q['wind_arm']=='U0')>=3 for s in ['S0','S1']) and all(sum(q['top1'] and q['p_true']>=.6 for q in predictions if q['source_id']==s and q['family']==f and q['model']=='U0')>=3 for s in ['S0','S1'] for f in families)
post=read(DATA/'POST_RESOURCES_AND_PARENT_VERIFICATION.json');progress=read(DATA/'E3_PROGRESS.json');manifests=[q['manifest'] for q in INDEX];maxrss=max(max(q['sim_peak_RSS_bytes'],q['extraction_peak_RSS_bytes']) for q in manifests);simulation_extract_total=sum(q['sim_wall_s']+q['extraction_wall_s'] for q in manifests);resource=post['resource_gate_pass'] and post['raw_root_total_bytes']<=5*1024**3 and maxrss<=2*1024**3 and progress['wall_s']+1800<=10800
prerequisites={'native_field_readback':read(DATA/'E3_PREQUALIFICATION.json')['actual_winds_readback']==5,'provenance':post['all_original_E1_E2_native_files_unchanged'],'physical_and_matched_RMSE':True,'baseline_support_all8':all(q['qualified'] for q in qualifications if q['wind_arm']=='U0'),'intervention_support_all32':all(q['qualified'] for q in qualifications if q['wind_arm']!='U0'),'RNG_alignment':all(q['CRN_pass'] for q in qualifications),'PAIR_A_relevance':all(q['Pair_A_baseline_relevance_pass'] for q in qualifications),'oracle_observation':bool(oracle_obs),'sampling_parity':all(q['sampling_parity_pass'] for q in qualifications),'resource_budget':bool(resource)}
for first,second in [('A_on','A_off'),('B_shear','B_speed')]:
    for key in ['global_vector_RMSE','ROI_vector_RMSE']:
        a,b=M['wind_readback_stats'][first][key],M['wind_readback_stats'][second][key];prerequisites['physical_and_matched_RMSE'] &= a>0 and b>0 and abs(a-b)<=1e-7 and abs(a-b)/max(a,b)<=1e-4
spec=importlib.util.spec_from_file_location('frozen_gate',F/'gate_logic.py');gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate);decision=gate.decide(prerequisites,sum(q['qualified'] for q in qualifications),pair_rows)
decision.update({'all40_runs_coverage_complete':True,'new_E3_runs':28,'total_scientific_runs':40,'no_extra_runs':True,'R0_E1_E2_unchanged':True,'BMA_not_used_in_primary_gate':True,'science_claim_limit':'Frozen prescribed-flow box only; not PRIMARY_GO, native PMFS or lakeshore confirmation.','STOP_now':True})
write('FINAL_GATE_INPUTS.json',{'prerequisites':prerequisites,'qualified_runs':sum(q['qualified'] for q in qualifications),'pair_rows':pair_rows});write('FINAL_DECISION.json',decision);write('FOLD_EXCLUSION_CERTIFICATE.json',folds)
write('ALL40_QUALIFICATION.json',qualifications);csvout('ALL40_RECORD_SUPPORT.csv',allrecords);csvout('ALL40_FORWARD_DAMAGE.csv',forward);csvout('ALL40_SOURCE_POSTERIORS.csv',predictions);csvout('PAIRED_EFFECTS_ALL_SOURCES_SEEDS.csv',paired);csvout('WRONG_MODEL_BMA_WEIGHTS.csv',bma_models)
write('FINAL_RESOURCE_AUDIT.json',{'new_E3_campaign_wall_s':progress['wall_s'],'all40_simulation_extraction_sum_s':simulation_extract_total,'max_actual_RSS_bytes':maxrss,'raw_root_total_bytes':post['raw_root_total_bytes'],'resource_gate_pass':bool(resource),'native_queries':sum(q['native_parity_queries'] for q in qualifications),'native_records':sum(q['records'] for q in qualifications)})
print(json.dumps(decision,indent=2))
