"""Independent raw checks, stable tails, scalar likelihoods and gate arithmetic."""
from pathlib import Path
import csv,hashlib,json,math
import numpy as np
from scipy.special import erfc
R=Path(__file__).resolve().parent;F=R.parent/'m0_clean_support_r0_20261007';D=R/'evidence'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def rows(p,delimiter=','):
    with Path(p).open(encoding='utf-8') as f:return list(csv.DictReader(f,delimiter=delimiter))
for q in rows(F/'M0_R0_FILES_SHA256.csv'):assert sha(F/q['path'])==q['sha256']
raw_hashes=rows(D/'NATIVE_FILES_SHA256.csv')
for q in raw_hashes:assert sha(D/q['path'])==q['sha256'] and (D/q['path']).stat().st_size==int(q['bytes']),q['path']
for name,h in read(R/'E3_EXECUTION_SEAL.json')['scripts_sha256'].items():assert sha(R/name)==sha(D/name)==h
INDEX=read(D/'ALL40_INDEX.json');AUTH=read(R/'E3_AUTHORIZATION.json');assert len(INDEX)==40 and {q['frozen_row']['run_id'] for q in INDEX}=={q['run_id'] for q in AUTH['all_frozen_rows']};assert read(D/'E3_PROGRESS.json')['qualified_completed']==28
source=read(F/'M0_SOURCE_CONTRACT.json');domain=read(F/'M0_DOMAIN_ROI_GUARD_CONTRACT.json');P=read(F/'M0_PERTURBATION_CONTRACT.json');G=read(F/'M0_GATE_CONTRACT.json');I=read(F/'M0_INFERENCE_CONTRACT.json');E0=read(R/'PARENT_E0_QUALIFICATION.json');lo=np.array(domain['effective_outlet_inner_planes_m']['min']);hi=np.array(domain['effective_outlet_inner_planes_m']['max']);outcomes=read(R/'ALL40_QUALIFICATION.json');stable=[];obs={};columns={};parity_total=0;margin_diff=0.;times_req=list(range(20,121,2))
for entry in INDEX:
    row=entry['frozen_row'];rid=row['run_id'];arm=row['wind_arm'];s=row['source_id'];seed=int(row['realization']);audit=D/'bank'/rid/'audit';ref=D/'bank'/('m0r0_U0_'+s+'_r'+str(seed).zfill(2))/'audit';frames=rows(audit/'native_frames.csv');bframes=rows(ref/'native_frames.csv');state=np.fromfile(audit/'filament_states.f32',dtype='<f4').reshape(-1,4);bstate=np.fromfile(ref/'filament_states.f32',dtype='<f4').reshape(-1,4);q=next(a for a in outcomes if a['run_id']==rid)
    assert q['qualified'] and q['zero_deletion_certified']==0 and q['records']==246 and not q['native_exceptions'];assert len(frames)==len(bframes)==246
    manifest=entry['manifest'];assert manifest['generator_sha256']==source['runtime']['intended_generator_sha256'] and manifest['libgaden_sha256']==source['runtime']['intended_libgaden_sha256'];assert manifest['master_seed']==2026100700+seed and manifest['runtime_env']['GADEN_RNG_SEED']==str(2026100700+seed) and manifest['runtime_env']['OMP_NUM_THREADS']=='1'
    assert q['noise_table_sequence_sha256']==E0['native_noise_table_bounds'][str(2026100700+seed)]['table_sequence_sha256'];assert sha(D/'noise'/str(2026100700+seed))==q['noise_table_sequence_sha256']
    minimum=math.inf;bounds=[];clock=[];sigsha=hashlib.sha256()
    for f,b in zip(frames,bframes):
        assert all(f[k]==b[k] for k in ['record_index','time_s','wind_index','n_filaments','offset_filaments']);off=int(f['offset_filaments']);n=int(f['n_filaments']);a=state[off:off+n];baseline=bstate[off:off+n];assert np.array_equal(a[:,3],baseline[:,3]);sigsha.update(a[:,3].tobytes());xyz=a[:,:3].astype(float);sd=a[:,3,None].astype(float)/100
        minimum=min(minimum,float((np.minimum(xyz-lo,hi-xyz)-3*sd).min()));clock.append(float(f['time_s']));outer=.5*erfc((xyz-lo)/(sd*math.sqrt(2)))+.5*erfc((hi-xyz)/(sd*math.sqrt(2)));inner=.5*erfc((xyz-lo-1)/(sd*math.sqrt(2)))+.5*erfc((hi-1-xyz)/(sd*math.sqrt(2)));bounds.append(float(inner.sum(axis=1).mean()/(1-outer.sum(axis=1).mean())))
    chosen=[max(j for j,t in enumerate(clock) if t<=requested) for requested in times_req];selected=np.array(bounds)[chosen];assert minimum>=1 and selected.mean()<=.05 and np.quantile(selected,.95,method='linear')<=.1;assert sigsha.hexdigest()==q['sigma_sequence_sha256'];margin_diff=max(margin_diff,abs(minimum-q['minimum_3sigma_margin_m']))
    assert minimum>q['max_gap_motion_bound_m'];stable.append({'run_id':rid,'stable_all6_band_mean_upper_bound':float(selected.mean()),'stable_all6_band_q95_upper_bound':float(np.quantile(selected,.95,method='linear')),'minimum_3sigma_margin_m':minimum})
    route=rows(audit/'route.csv');refroute=rows(ref/'route.csv');assert len(route)==51 and all(all(a[k]==b[k] for k in ['time_s','record_index','x','y','z']) for a,b in zip(route,refroute));obs[(s,seed,arm)]=[float(a['ppm']) for a in route];columns[(s,seed,arm)]=np.array([np.fromfile(audit/('roi_column_t'+str(t)+'.f32'),dtype='<f4') for t in times_req],dtype=float)
    parity=rows(audit/'sampling_parity.csv');assert len(parity)>=1275 and all(float(a['absolute_difference'])<=1e-5*(1+abs(float(a['native']))) for a in parity);parity_total+=len(parity)
assert margin_diff==0 and len(obs)==40
# Recompute matched RMSE from actual raw native arrays, not from reported values.
shape=(96,160,240,3);u0=np.fromfile(D/'projects/U0/wind/wind_iteration_0',dtype='<f4',offset=8).reshape(shape);wind_errors={}
for arm in ['U0','A_on','A_off','B_shear','B_speed']:
    p=D/'projects'/arm/'wind/wind_iteration_0';assert sha(p)==sha(D/'native_readback'/arm/'native_readback.wind')==P['expected_modern_wind_sha256'][arm];a=np.fromfile(p,dtype='<f4',offset=8).reshape(shape).astype(float);delta=a-u0.astype(float);squared=np.sum(delta*delta,axis=3);assert np.isfinite(a).all() and a[...,0].min()>=.02 and np.sqrt((a*a).sum(axis=3)).max()<=.2 and np.sqrt(squared).max()<=.0500001
    divergence=((a[1:-1,1:-1,2:,0]-a[1:-1,1:-1,:-2,0])+(a[1:-1,2:,1:-1,1]-a[1:-1,:-2,1:-1,1])+(a[2:,1:-1,1:-1,2]-a[:-2,1:-1,1:-1,2]))/.5;assert abs(divergence).max()<=1e-6 and np.sqrt((divergence*divergence).mean())<=1e-7
    wind_errors[arm]={'Free_RMSE':float(np.sqrt(squared[1:-1,1:-1,1:-1].mean())),'ROI_RMSE':float(np.sqrt(squared[36:68,48:112,56:136].mean()))};del a,delta,squared,divergence
for a,b in [('A_on','A_off'),('B_shear','B_speed')]:
    for k in ['Free_RMSE','ROI_RMSE']:
        x,y=wind_errors[a][k],wind_errors[b][k];assert x>0 and y>0 and abs(x-y)<=1e-7 and abs(x-y)/max(x,y)<=1e-4
pred=rows(R/'ALL40_SOURCE_POSTERIORS.csv');fw=rows(R/'ALL40_FORWARD_DAMAGE.csv');pm={};brier={};p_diff=0.;lik_diff=0.;f_diff=0.;manual_forward={};models=I['WRONG_MODEL_BMA']['models'];bmw=rows(R/'WRONG_MODEL_BMA_WEIGHTS.csv');model_weight_diff=0.
def scalar_score(train,query,family):
    score=0.
    for i in range(51):
        if family=='HIT_FORWARD':p=(sum(a[i]>=.1 for a in train)+.5)/4;score+=math.log(p if query[i]>=.1 else 1-p)
        else:
            z=[math.log1p(a[i]) for a in train];mean=sum(z)/3;variance=max(sum((v-mean)**2 for v in z)/2,.0625);score-=.5*(math.log(2*math.pi*variance)+(math.log1p(query[i])-mean)**2/variance)
    return score
for s in ['S0','S1']:
    for r in [1,2,3,4]:
        query=obs[(s,r,'U0')];train=[i for i in [1,2,3,4] if i!=r];truth=0 if s=='S0' else 1
        for family in ['HIT_FORWARD','LOG_GAUSSIAN']:
            evidence={}
            for arm in ['U0','A_on','A_off','B_shear','B_speed']:
                ll=[scalar_score([obs[(cand,k,arm)] for k in train],query,family) for cand in ['S0','S1']];evidence[arm]=ll;maximum=max(ll);unnorm=[math.exp(x-maximum) for x in ll];den=sum(unnorm);p=[v/den for v in unnorm];pm[(s,r,family,arm)]=p;brier[(s,r,family,arm)]=(1-p[truth])**2
                actual=next(q for q in pred if q['source_id']==s and int(q['realization'])==r and q['family']==family and q['model']==arm);p_diff=max(p_diff,abs(p[0]-float(actual['p_S0'])),abs(p[1]-float(actual['p_S1'])));lik_diff=max(lik_diff,abs(ll[0]-float(actual['loglik_S0'])),abs(ll[1]-float(actual['loglik_S1'])));assert actual['train_realizations']==';'.join(map(str,train)) and actual['query_wind_always_U0']=='True'
                tie=abs(p[0]-p[1])<=1e-12;correct=not tie and (0 if p[0]>p[1] else 1)==truth;rank=1.5 if tie else (1 if correct else 2);assert rank==float(actual['rank']) and correct==(actual['top1']=='True');assert abs(2*(1-p[truth])-float(actual['posterior_mean_error_m']))<1e-12
            maxjoint=max(v for arm in models for v in evidence[arm]);joint=[[math.exp(evidence[arm][c]-maxjoint) for arm in models] for c in [0,1]];den=sum(sum(v) for v in joint);p=[sum(v)/den for v in joint];pm[(s,r,family,'WRONG_MODEL_BMA')]=p
            actual=next(q for q in pred if q['source_id']==s and int(q['realization'])==r and q['family']==family and q['model']=='WRONG_MODEL_BMA');p_diff=max(p_diff,abs(p[0]-float(actual['p_S0'])),abs(p[1]-float(actual['p_S1'])))
            for k,arm in enumerate(models):
                weight=(joint[0][k]+joint[1][k])/den;actual=next(q for q in bmw if q['source_id_evaluator_only']==s and int(q['realization'])==r and q['family']==family and q['wrong_model']==arm);model_weight_diff=max(model_weight_diff,abs(weight-float(actual['model_posterior'])))
        f0=columns[(s,r,'U0')]
        for arm in ['U0','A_on','A_off','B_shear','B_speed']:
            fm=columns[(s,r,arm)];norm=lambda x:math.sqrt(float(np.dot(x.ravel(),x.ravel())));df=norm(fm-f0)/(.5*(norm(fm)+norm(f0)));dy=math.sqrt(sum((math.log1p(a)-math.log1p(b))**2 for a,b in zip(obs[(s,r,arm)],query))/51);manual_forward[(s,r,arm)]=(df,dy);actual=next(q for q in fw if q['source_id']==s and int(q['realization'])==r and q['wind_arm']==arm);f_diff=max(f_diff,abs(df-float(actual['D_F'])),abs(dy-float(actual['D_Y'])))
assert p_diff<1e-12 and model_weight_diff<1e-12 and f_diff<1e-12 and lik_diff<1e-10
# Independent complete/partial/stop logic, no import of primary gate or scorer.
complete=[];partial=[];replication={};margin=G['material_margins']
for pair,(a,b) in G['pairs'].items():
    replication[pair]={}
    for direction in G['replication']['allowed_pair_directions']:
        both={}
        for s in G['sources']:
            intersection=[];single={f:[] for f in G['families']}
            for r in G['realizations']:
                df1,dy1=manual_forward[(s,r,a)];df2,dy2=manual_forward[(s,r,b)];forward=direction*(df1-df2)>=margin['absolute_D_F_pair_difference_min'] and direction*(dy1-dy2)>=margin['absolute_D_Y_pair_difference_min'];posterior_ok=[]
                for f in G['families']:
                    ba,bb,bo=brier[(s,r,f,a)],brier[(s,r,f,b)],brier[(s,r,f,'U0')];material=direction*(ba-bb)>=margin['absolute_Brier_pair_difference_min_each_family'];harm=(ba if direction==1 else bb)-bo>=margin['worse_arm_Brier_damage_vs_oracle_min_each_family'];posterior_ok.append(material and harm)
                    if material:single[f].append(r)
                if forward and all(posterior_ok):intersection.append(r)
            both[s]=intersection
            for f,ids in single.items():
                if len(ids)>=3:partial.append({'pair':pair,'sign':direction,'source':s,'family':f,'seed_ids':ids})
        replication[pair][str(direction)]=both
        if all(len(ids)>=3 for ids in both.values()):complete.append({'pair':pair,'sign':direction})
verdict='M0_PASS' if complete else ('M0_PARTIAL_HOLD' if partial else 'M0_STOP');primary=read(R/'FINAL_DECISION.json');assert primary['verdict']==verdict
for pair,directions in replication.items():
    for sign,count in directions.items():assert count==primary['pair_reports'][pair][sign]['intersection_seed_ids']
result={'status':'INDEPENDENT_FINAL_VERIFICATION_PASS','independent_verdict':verdict,'primary_verdict':primary['verdict'],'native_files_verified':len(raw_hashes),'R0_frozen_files_verified':39,'qualified_runs':40,'additional_runs_after_E3':0,'native_parity_queries':parity_total,'max_margin_difference_m':margin_diff,'max_likelihood_difference':lik_diff,'max_posterior_difference':p_diff,'max_forward_metric_difference':f_diff,'max_BMA_weight_difference':model_weight_diff,'wind_errors_independently_recomputed':wind_errors,'independent_full_pair_survivors':complete,'independent_partial_effects':partial,'same_seed_intersections':replication,'stable_Gaussian_tail_bounds':stable,'claim_scope':'Frozen controlled mechanism only; no PRIMARY_GO or calibration claim.','STOP':True}
(R/'INDEPENDENT_FINAL_VERIFICATION.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps({k:v for k,v in result.items() if k!='stable_Gaussian_tail_bounds'},indent=2))
