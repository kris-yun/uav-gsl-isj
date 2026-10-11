from common_r2 import *
import csv,numpy as np,sys,math
sys.path.insert(0,str(WORK/'pro_plan/code'));from source_map_tools import score_perturbation
def rows(p):return list(csv.DictReader(Path(p).open(encoding='utf-8',newline='')))
def wc(p,rs):
 with Path(p).open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rs[0]),lineterminator='\n');w.writeheader();w.writerows(rs)
root=CORE/'inference_inputs';pred=np.load(root/'ALL_CANDIDATE_PREDICTIONS.npz');registry=load(root/'OBSERVATION_REGISTRY.json');truth=load(CORE/'evaluation_only/DEVELOPMENT_TRUTH.json');cat=load(root/'SOURCE_CATALOG.json')['catalog'];free=np.load(root/'SCORING_FREE_MASK.npy');post=np.load(CORE/'development_inference/FULL_SOURCE_POSTERIORS.npz');receptors=[];sensitivity=[];contributions={};bounds=[];prior_diag=[]
raw0={plan:[] for plan in ['B4','PUBLIC_B']}
for c in cat:
 rr={plan:[] for plan in raw0}
 for m in [0,1]:
  a=np.load(HOST/'references'/f'{c["source_id"]}_REF{m}'/'PREDICTIONS.npz')
  for plan in raw0:
   ev=rows(HOST/'references'/f'{c["source_id"]}_REF{m}'/(plan+'_RECEIVER_EVENTS.csv'));ci=np.array([int(np.float32((np.float32(float(r['x']))-np.float32(-7.55))/.25))+34*int(np.float32((np.float32(float(r['y']))-np.float32(-7.88))/.25)) for r in ev]);rr[plan].append(a[plan+'_O0'][np.arange(50),ci])
 for plan in raw0:raw0[plan].append(np.stack(rr[plan]))
raw0={k:np.stack(v) for k,v in raw0.items()};np.savez_compressed(CORE/'RECEPTOR_PREDICTIONS.npz',**{plan+'_O0_events':a for plan,a in raw0.items()})
for ob in registry:
 oid=ob['oid'];plan=ob['plan'];tr=truth[oid];ti=tr['true_region'];d=root/ob['folder'];maps=np.load(d/'MEASURED_MAPS.npz');ee=rows(d/'EVENTS_50.csv');y=np.array([int(r['event_hit']) for r in ee]);con=np.array([float(r['concentration_ppm']) for r in ee]);pm=pred[plan+'_PPM'][ti];
 for group,refs in [('R0',[0]),('R1',[1]),('R01',[0,1])]:
  for n in [20,35,50]:
   for method,hit in [('O0-centre',raw0[plan][ti]),('O1-PID',pred[plan+'_EVENTS'][ti])]:
    q=hit[refs,:n].mean(0);receptors.append(dict(oid=oid,source_group=tr['source_group'],true_region=ti,reference_group=group,blocks=n,method=method,Brier=float(np.mean((q-y[:n])**2)),observed_hits=int(y[:n].sum()),observed_stops=n/5,continuous_ppm_RMSE=float(np.sqrt(np.mean((pm[refs,:n].mean(0)-con[:n])**2))) if tr['continuous_ppm_available'] and method=='O1-PID' else '',scope='coarse representative prediction vs continuous observed source; includes common discretization',blocks_are_correlated=True))
 for n in [20,35,50]:
  p=maps[f'p{n}'][free];conf=maps[f'c{n}'][free];qs={m:pred[f'{plan}_{m}_{n}'].mean(1).astype(np.float32)[:,free].astype(float) for m in ['P3-O0','P3-O1']};log={m:np.log(1-.4*conf[None,:]*abs(q-p[None,:])) for m,q in qs.items()};contributions[f'{oid}__{n}__O0']=log['P3-O0'];contributions[f'{oid}__{n}__O1']=log['P3-O1'];key=f'{oid}__R01__P3-O1__{n}';sc=post[key+'_scores'];delta=log['P3-O1']-log['P3-O0'];assert np.max(abs(delta.sum(1)-(sc-post[f'{oid}__R01__P3-O0__{n}'+'_scores'])))<1e-10
  bounds.append(dict(oid=oid,blocks=n,comparison='P3-O0_to_O1_readout',**score_perturbation(post[f'{oid}__R01__P3-O0__{n}'+'_scores'],sc)))
  for method in ['P3-O0','P3-O1','N_POINT_ALL','E-event','A1-map']:
   a=post[f'{oid}__R0__{method}__{n}'+'_scores'];b=post[f'{oid}__R1__{method}__{n}'+'_scores'];wa=post[f'{oid}__R0__{method}__{n}'+'_weights'];wb=post[f'{oid}__R1__{method}__{n}'+'_weights'];sensitivity.append(dict(oid=oid,blocks=n,method=method,R0_NLL=-math.log(wa[ti]),R1_NLL=-math.log(wb[ti]),reference_NLL_absolute_difference=abs(math.log(wa[ti])-math.log(wb[ti])),R0_top_region=int(wa.argmax()),R1_top_region=int(wb.argmax()),same_top_region=wa.argmax()==wb.argmax(),weight_L1=float(abs(wa-wb).sum()),**score_perturbation(a,b)))
   s=post[f'{oid}__R01__{method}__{n}'+'_scores'];w=np.exp(s-s.max());w/=w.sum();prior_diag.append(dict(oid=oid,blocks=n,method=method,uniform_region_prior_true_mass=float(w[ti]),registered_area_prior_true_mass=float(post[f'{oid}__R01__{method}__{n}'+'_weights'][ti]),registered_highest_region=int(post[f'{oid}__R01__{method}__{n}'+'_weights'].argmax()),uniform_highest_region=int(w.argmax()),scope='posthoc prior sensitivity only, not deployment model or rescued performance'))
wc(CORE/'RECEPTOR_METRICS.csv',receptors);wc(CORE/'REFERENCE_SENSITIVITY.csv',sensitivity);wc(CORE/'AREA_PRIOR_DIAGNOSTIC.csv',prior_diag);dump(CORE/'SCORE_PERTURBATION_BOUNDS.json',bounds);np.savez_compressed(CORE/'PER_SOURCE_PER_CELL_SCORE_CONTRIBUTIONS.npz',active_cells=np.flatnonzero(free),**contributions)
eq=[];pairs=[]
for plan in ['B4','PUBLIC_B']:
 for n in [20,35,50]:
  event=pred[plan+'_EVENTS'][:,:,:n];marg=event.mean(1);a1=pred[f'{plan}_A1_{n}'].mean(1).astype(np.float32);ppm=pred[plan+'_PPM'][:,:,:n].mean(1);aux=pred[plan+'_AUX'][:,:,:n].mean(1)
  def classes(arr):
   groups={}
   for i,row in enumerate(arr):groups.setdefault(hashlib.sha256(row.tobytes()).hexdigest(),[]).append(i)
   return list(groups.values())
  marginal_classes=classes(marg);sequence=np.stack([np.array(sorted(x.tolist()),np.uint8) for x in event]);jointclasses=classes(sequence);mapclasses=classes(a1)
  eq.append(dict(plan=plan,blocks=n,event_marginal_classes=marginal_classes,two_reference_full_sequence_classes=jointclasses,A1_mean_map_classes=mapclasses,source_count=32,exact_finite_reference_equality_not_population_identifiability=True))
  for i in range(32):
   for j in range(i+1,32):
    me=bool(np.array_equal(marg[i],marg[j]));je=bool(np.array_equal(sequence[i],sequence[j]));ae=bool(np.array_equal(a1[i],a1[j]));
    if me or je or ae:pairs.append(dict(plan=plan,blocks=n,source_i=i,source_j=j,event_marginal_equal=me,two_reference_sequences_equal=je,A1_mean_map_equal=ae,ppm_RMSE_between_candidates=float(np.sqrt(np.mean((ppm[i]-ppm[j])**2))),auxiliary_ppm_RMSE=float(np.sqrt(np.mean((aux[i,:, :,0]-aux[j,:,:,0])**2))) if plan=='PUBLIC_B' else '',auxiliary_physical_free_min=float(min(aux[i,:,:,1].min(),aux[j,:,:,1].min())) if plan=='PUBLIC_B' else '',scope='Four auxiliary points only input diagnostic, no route modification'))
dump(CORE/'EVENT_EQUIVALENCE.json',eq);wc(CORE/'EVENT_EQUIVALENCE_PAIR_DIFFERENCES.csv',pairs)
dump(CORE/'ORDINARY_HEAD_AND_IDENTIFIABILITY_BOUNDARIES.json',dict(status='FIXED_DIAGNOSTICS_COMPLETED',events='two finite reference realizations, no population nonidentifiability proof',E_event='Jeffreys0.5 marginal Bernoulli mean composite score, temp1, not joint independent likelihood',A1='mean reference native-map probability negative mean-square distance at447 cells; cannot distinguish distributions with same mean',continuous_B4='placeholder zeros excluded; no amplitude error claimed',MAP='raster density maximum can differ from maximum region mass because regions have unequal areas; all ties retained',N0='unchanged native adaptive histories projected onto coarse regions for bookkeeping; no same-head effect subtraction',coarse_source='continuous true source differs from geometry representative, paired models share this error',auxiliary='kept all finite values including physical support; not additional independent flight samples',no_future_references_or_outcomes_used_by_inference=True))
print(json.dumps({'status':'PASS_FIXED_ALL_BRANCH_DIAGNOSTICS','equivalent_pairs':len(pairs),'receptor_rows':len(receptors),'sensitivity_rows':len(sensitivity)}))
