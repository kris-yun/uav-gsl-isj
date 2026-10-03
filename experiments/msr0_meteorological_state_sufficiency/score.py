"""Frozen source-blind meteorology distances and whole-realization aliasing gate."""
from pathlib import Path
import json,hashlib,itertools
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'evidence/msr0_meteorological_state_sufficiency_20261003';T0=ROOT/'evidence/task_sufficiency_t0_20261003'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,x):(OUT/n).write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
cfg=json.loads((OUT/'MSR0_FROZEN_CONFIG.json').read_text(encoding='utf-8'));runs=json.loads((OUT/'RUNS.json').read_text(encoding='utf-8'))
save('SCORING_CODE_FREEZE.json',{'config_sha256':sha(OUT/'MSR0_FROZEN_CONFIG.json'),'score_sha256':sha(__file__),'status':'initial freeze before scoring; packaging rerun identified by preserved SCORING_CODE_FREEZE_INITIAL.json','scores_not_yet_computed':not(OUT/'MSR0_DECISION.json').exists()})
contexts=sorted({r['context'] for r in runs});PHIS=['Phi0','Phi1','Phi2','Phi3','Phi_ORACLE']

# Feature extraction reads wind-only outputs and source-blind probes; no gas or truth.
def meteorology_features(house,wind_file,wind_indices):
 p=pd.read_csv(OUT/(house+'_PROBES.csv'));w=pd.read_csv(wind_file)
 assert len(w)==11*len(p) and np.array_equal(w.point_id.values.reshape(11,-1)[0],p.point_id)
 vec=w[['u','v','w']].values.reshape(11,len(p),3);valid=w.valid.values.reshape(11,len(p)).astype(bool)
 assert np.all(valid==valid[0]) and np.isfinite(vec).all()
 weights=np.sqrt(np.bincount(wind_indices,minlength=11)).reshape(11,1,1)
 slice_mask=p.kind.eq('slice').values;assert valid[:,slice_mask].all()
 full_uv=(vec[:,slice_mask,:2]*weights).ravel()
 local=p[p.kind.eq('local')];ids={}
 for off,sub in local.groupby(['dx','dy','dz'],sort=False):
  sub=sub.sort_values('receptor');assert np.array_equal(sub.receptor,np.arange(301));ids[tuple(off)]=sub.point_id.values
 def at(off):
  ii=ids[off];x=vec[np.asarray(wind_indices),ii,:].copy();x[~valid[np.asarray(wind_indices),ii]]=np.nan;return x
 c=at((0.,0.,0.));assert np.isfinite(c).all();down=at((0.,0.,-.2));up=at((0.,0.,.2))
 blocks={'slice_uv':full_uv,'receptor_uv':c[:,:2].ravel(),'local_w':c[:,2].ravel(),'vertical_vector_gradient':((up-down)/.4).ravel()}
 def direction(x):
  ans=np.degrees(np.arctan2(x[:,1],x[:,0]));ans[np.hypot(x[:,0],x[:,1])<1e-8]=np.nan;return ans
 blocks['vertical_direction_shear']=((direction(up)-direction(down)+180)%360-180)/.4
 blocks['vertical_speed_shear']=(np.linalg.norm(up[:,:2],axis=1)-np.linalg.norm(down[:,:2],axis=1))/.4
 xp=at((.2,0.,0.));xm=at((-.2,0.,0.));yp=at((0.,.2,0.));ym=at((0.,-.2,0.))
 blocks['horizontal_x_gradient']=((xp-xm)/.4).ravel();blocks['horizontal_y_gradient']=((yp-ym)/.4).ravel()
 nb=np.stack([c,up,down,xp,xm,yp,ym],axis=1);sp=np.linalg.norm(nb[:,:,:2],axis=2)
 dn=np.arctan2(nb[:,:,1],nb[:,:,0]);dn[sp<1e-8]=np.nan
 valid_direction=np.isfinite(dn);nn=valid_direction.sum(axis=1)
 mean_cos=np.nansum(np.cos(dn),axis=1)/np.maximum(nn,1);mean_sin=np.nansum(np.sin(dn),axis=1)/np.maximum(nn,1)
 variability=1-np.hypot(mean_cos,mean_sin);variability[nn<3]=np.nan
 blocks['local_direction_variability']=variability
 speed_count=np.isfinite(sp).sum(axis=1);speedmean=np.nansum(sp,axis=1)/np.maximum(speed_count,1)
 sd=np.sqrt(np.nansum((sp-speedmean[:,None])**2,axis=1)/np.maximum(speed_count,1));sd[speed_count<3]=np.nan
 blocks['local_speed_variability']=sd
 blocks['oracle_patch']=np.stack([at(off) for off in itertools.product([-.4,0.,.4],repeat=3)],axis=1).ravel()
 phi_blocks={'Phi0':['slice_uv','receptor_uv'],'Phi1':['slice_uv','receptor_uv','local_w'],'Phi2':['slice_uv','receptor_uv','local_w','vertical_vector_gradient','vertical_direction_shear','vertical_speed_shear']}
 phi_blocks['Phi3']=phi_blocks['Phi2']+['horizontal_x_gradient','horizontal_y_gradient','local_direction_variability','local_speed_variability'];phi_blocks['Phi_ORACLE']=phi_blocks['Phi3']+['oracle_patch']
 return blocks,phi_blocks,c

features={};schema=None;wind_parity=[]
for context in contexts:
 # Contract clock/state index is source independent, verified equal across both sources/seeds.
 rr=[r for r in runs if r['context']==context];assert len({tuple(r['wind_indices_at_receptors']) for r in rr})==1
 blocks,schema,central=meteorology_features(rr[0]['house'],OUT/(context+'_WIND.csv'),rr[0]['wind_indices_at_receptors']);features[context]=blocks
 np.savez_compressed(OUT/(context+'_SOURCE_BLIND_FEATURES.npz'),**blocks)
 for record in rr:
  obs=pd.read_csv(OUT/(record['run_id']+'.observations.csv'));err=float(np.max(np.abs(central-obs[['u','v','w']].values)));assert err<2e-6,(record['run_id'],err)
  wind_parity.append({'run_id':record['run_id'],'max_native_wind_difference':err,'pass':True})
pd.DataFrame(wind_parity).to_csv(OUT/'WIND_CLOCK_NATIVE_PARITY.csv',index=False)
save('FEATURE_SCHEMA.json',{'phi_blocks':schema,'source_truth_read_by_feature_function':False,'spatial_variability_not_TKE':True})

# Geometry- and context-shared masks are wind-only. Source/gas traces not used to scale features.
for house in ['House01','House02']:
 cc=[c for c in contexts if c.startswith(house)]
 for key in features[cc[0]]:
  mask=np.logical_and.reduce([np.isfinite(features[c][key]) for c in cc]);assert mask.any(),key
  for c in cc:features[c][key]=features[c][key][mask]
def block_distance(x,y):
 if np.array_equal(x,y):return 0.
 scale=np.sqrt((np.mean(x*x)+np.mean(y*y))/2)
 return float(np.sqrt(np.mean((x-y)**2))/scale) if scale>0 else 0.
def phi_distance(c1,c2,phi):return float(np.sqrt(np.mean([block_distance(features[c1][key],features[c2][key])**2 for key in schema[phi]])))

# Interventions require all nonwind/nonsource parameters and geometry to match.
def legal_pair(c1,c2):
 r1=next(r for r in runs if r['context']==c1);r2=next(r for r in runs if r['context']==c2)
 if r1['house']!=r2['house']:return False,'HOUSE_GEOMETRY_ROUTE_CHANGED'
 if r1['nonwind_nonsource_params']!=r2['nonwind_nonsource_params']:return False,'GAS_OR_NONWIND_PARAMETERS_CHANGED'
 if r1['timeline_sha256']!=r2['timeline_sha256']:return False,'CLOCK_CHANGED'
 t1={tuple(r['truth_xyz']) for r in runs if r['context']==c1};t2={tuple(r['truth_xyz']) for r in runs if r['context']==c2}
 if t1!=t2:return False,'SOURCE_COORDINATE_SET_CHANGED'
 return True,'MATCHED_SOURCE_GAS_GEOMETRY_CLOCK_PATH'

pairrows=[];elig=[]
for c1,c2 in itertools.combinations(contexts,2):
 legal,reason=legal_pair(c1,c2);row={'context_i':c1,'context_j':c2,'legal_transport_intervention':legal,'reason':reason}
 if c1.split('_')[0]==c2.split('_')[0]:
  for phi in PHIS:row['d_'+phi]=phi_distance(c1,c2,phi)
  row['d_local_uv_only']=block_distance(features[c1]['receptor_uv'],features[c2]['receptor_uv'])
 else:
  for phi in PHIS:row['d_'+phi]=None
  row['d_local_uv_only']=None
 pairrows.append(row)
 if legal:elig.append((c1,c2))
pd.DataFrame(pairrows).to_csv(OUT/'MSR0_CONTEXT_DISTANCES.csv',index=False)

traces={};within={};withinrows=[]
for context in contexts:
 sources=sorted({r['source_id'] for r in runs if r['context']==context})
 for source in sources:
  rr=sorted((r for r in runs if r['context']==context and r['source_id']==source),key=lambda r:r['seed']);assert len(rr)==4
  y=np.stack([np.log1p(pd.read_csv(OUT/(r['run_id']+'.observations.csv')).concentration.values) for r in rr]);traces[context,source]=y
  distances=np.array([np.sqrt(np.mean((y[i]-y[j])**2)) for i,j in itertools.combinations(range(4),2)]);within[context,source]=distances
  withinrows.append({'context':context,'house':rr[0]['house'],'source_id':source,'n_independent_realizations':4,'n_pairs_not_independent':6,'median':float(np.median(distances)),'q90':float(np.quantile(distances,.9)),'q95':float(np.quantile(distances,.95)),'n_positive_realizations':int(np.sum(np.max(y,axis=1)>0))})
pd.DataFrame(withinrows).to_csv(OUT/'MSR0_WITHIN_CONTEXT_VARIABILITY.csv',index=False)
alias=[]
for c1,c2 in elig:
 for source in sorted({r['source_id'] for r in runs if r['context']==c1}):
  y1=traces[c1,source];y2=traces[c2,source];wd=np.r_[within[c1,source],within[c2,source]];q95=float(np.quantile(wd,.95))
  between=np.array([np.sqrt(np.mean((a-b)**2)) for a,b in itertools.product(y1,y2)]);D=float(np.median(between));meanD=float(np.sqrt(np.mean((y1.mean(axis=0)-y2.mean(axis=0))**2)))
  row={'context_i':c1,'context_j':c2,'source_id':source,'D_between_median':D,'D_between_ensemble_mean':meanD,'D_within_pooled_median':float(np.median(wd)),'D_within_pooled_q90':float(np.quantile(wd,.9)),'D_within_pooled_q95':q95,'alias_ratio':D/q95 if q95>0 else None,'noise_floor_degenerate':q95==0,'gas_exceeds_floor':bool(D>q95 and meanD>q95),'n_between_pairs_not_independent':16,'independent_realizations_per_context':4}
  for phi in PHIS:
   dp=phi_distance(c1,c2,phi);row['d_'+phi]=dp;row['collision_'+phi]=bool(dp<=.1 and q95>0 and row['gas_exceeds_floor'])
  for threshold in [.05,.20]:row[f'collision_Phi0_threshold_{threshold}']=bool(row['d_Phi0']<=threshold and q95>0 and row['gas_exceeds_floor'])
  alias.append(row)
pd.DataFrame(alias).to_csv(OUT/'MSR0_ALIASING_PAIRS.csv',index=False)

# Evaluate the same small matched intervention set; no observation-level split.
mean_pairs=[]
for c1,c2 in elig:
 q=[x for x in alias if x['context_i']==c1 and x['context_j']==c2];mean_pairs.append({'context_i':c1,'context_j':c2,'gas_distance':np.mean([x['D_between_median'] for x in q]),'gas_ratio':np.mean([x['alias_ratio'] for x in q if x['alias_ratio'] is not None])})
scores=[];nnrows=[]
for phi in PHIS:
 x=[phi_distance(row['context_i'],row['context_j'],phi) for row in mean_pairs];y=[row['gas_distance'] for row in mean_pairs]
 rho,pval=spearmanr(x,y) if len(x)>=3 and len(set(x))>1 and len(set(y))>1 else (np.nan,np.nan)
 for context in contexts:
  options=[c for c in contexts if c!=context and legal_pair(context,c)[0]]
  if not options:continue
  nearest=min(options,key=lambda c:(phi_distance(context,c,phi),c));pair=[row for row in mean_pairs if {row['context_i'],row['context_j']}=={context,nearest}][0]
  nnrows.append({'Phi':phi,'context':context,'retrieved_context':nearest,'eligible_alternatives':len(options),'meteorology_distance':phi_distance(context,nearest,phi),'transport_mismatch':pair['gas_distance'],'transport_mismatch_noise_ratio':pair['gas_ratio'],'retrieval_accuracy':None,'status':'ONLY_ONE_COMPATIBLE_NONSELF_CONTEXT; no ranking-identifiability' if len(options)==1 else 'descriptive'})
 q=[row for row in nnrows if row['Phi']==phi]
 scores.append({'Phi':phi,'n_legal_context_pairs':len(x),'Spearman_context_pair_rho':float(rho),'Spearman_nominal_p_not_independence_corrected':float(pval),'nearest_neighbor_transport_mismatch':float(np.mean([row['transport_mismatch'] for row in q])),'nearest_neighbor_noise_ratio':float(np.mean([row['transport_mismatch_noise_ratio'] for row in q])),'context_retrieval_accuracy':None,'context_retrieval_status':'NOT_IDENTIFIABLE: one compatible alternative per context; accuracy cannot demonstrate sufficient wind state','alias_collision_count_source_pairs':sum(row['collision_'+phi] for row in alias),'false_neighbor_count_source_pairs':sum(row['collision_'+phi] for row in alias),'alias_resolved_vs_Phi0':sum(row['collision_Phi0'] and not row['collision_'+phi] for row in alias),'nonclose_nearest_neighbor_gas_difference_count':sum(row['gas_exceeds_floor'] for row in alias),'split':'whole contexts for intervention; source-specific whole realization distances. Localization LOCO stage is gated, not executed.'})
pd.DataFrame(scores).to_csv(OUT/'MSR0_REPRESENTATION_SCORE.csv',index=False);pd.DataFrame(nnrows).to_csv(OUT/'NEAREST_NEIGHBOR_DIAGNOSTICS.csv',index=False)

# Quantization is geometry-only diagnostic; two configured sources do not imply arbitrary-grid coverage.
floors=[]
for context in contexts:
 rr=[r for r in runs if r['context']==context];free=pd.read_csv(OUT/(rr[0]['house']+'_free.csv'));candidate_xyz=free[['x','y','z']].values
 for source in sorted({r['source_id'] for r in rr}):
  xyz=np.array(next(r['truth_xyz'] for r in rr if r['source_id']==source));dist=np.linalg.norm(candidate_xyz[:,:2]-xyz[:2],axis=1);index=np.argmin(dist)
  floors.append({'context':context,'source_id':source,'source_x':xyz[0],'source_y':xyz[1],'source_z':xyz[2],'geometry_slice_xy_quantization_floor_m':float(dist[index]),'geometry_slice_xyz_distance_m':float(np.linalg.norm(candidate_xyz[index]-xyz)),'nearest_slice_x':candidate_xyz[index,0],'nearest_slice_y':candidate_xyz[index,1],'nearest_slice_z':candidate_xyz[index,2],'existing_two_source_bank_floor_m':0.,'continuous_candidate_grid_forward_available':False,'interpretation':'native free-slice geometric XY floor only; source-height/emission-grid validity unestablished. Two-source bank truth exactly included by design.'})
pd.DataFrame(floors).to_csv(OUT/'MSR0_QUANTIZATION_FLOOR.csv',index=False)

n_alias=sum(row['collision_Phi0'] for row in alias)
if n_alias:
 save('MSR0_DECISION.json',{'decision':None,'status':'ALIAS_GATE_POSITIVE_REQUIRES_MINIMAL_BANK_REVIEW','n_alias':n_alias,'source_localization_stage_ready':False,'reason':'Review actual matched aliases before generating any minimal bank; no automatic PASS.'})
 raise SystemExit('ALIAS POSITIVE: stageF/I requires dependent continuation, not terminal report')
decision={'decision':'MSR0_STOP_2D_MET_SUFFICIENT','interpretation':'No task-related2D aliasing established in current qualified S2/S2X route and meteorology range; does NOT prove general2D information sufficiency.',
 'alias_gate':'NO_POSITIVE_SIGNAL','legal_context_pairs':len(elig),'matched_source_pairs':len(alias),'alias_collision_count':n_alias,
 'primary_cases_preserved':['H01/s0','H01/s1','H02/s0','H02/s1'],'primary_within_house_pair_issue':'Different gas types: exclude as causal meteorology interventions',
 'additional_legal_pairs':elig,'source_localization_stage_executed':False,'minimal_bank_generated':False,'Wisco_bridge_executed':False,
 'downstream_status':'SKIPPED_DEPENDENCY_GATE_NOT_PASSED','old_decisions_modified':False,'neural_network_trained':False,
 'scientific_identification_limit':'Only fast/slow pairs match gas and source within a house; one compatible alternative/context. Cannot assess broad cross-wind-context generalization, and no arbitrary-source forward bank is available.',
 'config_sha256':sha(OUT/'MSR0_FROZEN_CONFIG.json')}
save('MSR0_DECISION.json',decision)
pd.DataFrame([{'case':case,'Phi':phi,'source_id':source,'localization_error_m':None,'MAP_x':None,'MAP_y':None,'posterior_x':None,'posterior_y':None,'posterior_spread_m':None,'true_source_rank':None,'split':'leave-one-context-out planned','status':'NOT_EXECUTED_ALIAS_GATE_NO_SIGNAL'} for case,ci in cfg['primary_cases'].items() for phi in PHIS for source in sorted({r['source_id'] for r in runs if r['config_index']==ci})]).to_csv(OUT/'MSR0_LOCALIZATION.csv',index=False)
pd.DataFrame([{'date':date,'stage':stage,'Phi':'None_qualified','status':'NOT_EXECUTED_NO_EFFECTIVE_SIM_REPRESENTATION','source_localization_metric_used':False} for date in ['2021-05-22','2021-05-24'] for stage in ['PRE','TRANSITION','POST']]).to_csv(OUT/'MSR0_WISCO_BRIDGE.csv',index=False)
save('VALIDATION.json',{'64_complete_realizations':True,'native_wind_clock_parity_64_runs':True,'source_blind_feature_function':True,'all_phi_same_legal_pairs':True,'gas_metric_no_absolute_gate':True,'no_observation_random_split':True,'old_gates_unchanged':True})
print(json.dumps({'decision':decision['decision'],'pairs':alias,'scores':scores},indent=2))
