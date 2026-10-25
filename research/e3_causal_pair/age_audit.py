"""Read-only mass-contribution age audit; no longer rollout or new worlds.

Original GADEN widths monotonically follow the saved native gamma/dt recurrence.
Infer age only on widths reproduced by that recurrence. Fixed-state truncation
is a contribution attribution, not a new stochastic simulation intervention.
"""
import struct,math
import numpy as np
from analyze import O,rows,load,table,put
def main():
 sig=[np.float32(10.)]
 for _ in range(10002):
  s=sig[-1];sig.append(np.float32(s+np.float32(np.float32(np.float32(15.)/np.float32(np.float32(2.)*s))*np.float32(.1))))
 sig=np.array(sig);maximum=[]
 for pred in load(O/'PREREGISTERED_CAUSAL_CONTRACT.json')['prediction_streams']:
  f=O/'event_control'/('true_'+pred['id']+'.particles.bin');smax=10.
  with f.open('rb') as h:
   while b:=h.read(8):
    step,n=struct.unpack('<2I',b);a=np.frombuffer(h.read(n*16),dtype='<f4').reshape(n,4);smax=max(smax,float(a[:,2].max()))
  maximum.append(dict(prediction=pred['id'],max_native_readout_sigma_cm=smax,continuous_growth_age_equivalent_s=(smax*smax-100)/15))
 cap=max(r['continuous_growth_age_equivalent_s'] for r in maximum)
 data=rows(O/'original_E3_decomposition/FILAMENT_CONTRIBUTIONS.csv');schedule={r['query_id']:r for r in rows(O/'schedule/QUERIES.csv') if r['group']=='historical'};qq={};errors=[];unknown=0
 for r in data:
  if float(r['contribution_ppm'])<=0:continue
  sigma=np.float32(r['sigma_cm']);i=int(np.searchsorted(sig,sigma));cand=[k for k in [i-1,i] if 0<=k<len(sig)];k=min(cand,key=lambda k:abs(float(sig[k])-float(sigma)));err=abs(float(sig[k])-float(sigma));errors.append(err)
  if err>1e-5:unknown+=1;continue
  age=k*.1;qid=r['query_id'];pp=float(r['contribution_ppm']);a=qq.setdefault(qid,dict(total=0.,age_weighted=0.,old=0.,young=0.))
  a['total']+=pp;a['age_weighted']+=pp*age;a['old' if age>cap else 'young']+=pp
 assert unknown==0,('unqualified age reconstruction',unknown,max(errors))
 summary=[];query=[]
 for qid,sc in schedule.items():
  a=qq.get(qid,dict(total=0.,age_weighted=0.,old=0.,young=0.));query.append(dict(query_id=qid,event=int(sc['window']),stop=int(sc['stop']),total_ppm=a['total'],concentration_weighted_age_s=a['age_weighted']/a['total'] if a['total'] else None,ppm_from_older_than_model_max_age=a['old'],ppm_from_within_model_age_support=a['young'],model_max_age_equivalent_s=cap))
 for stop in range(8,14):
  rr=[r for r in query if r['stop']==stop];total=sum(r['total_ppm'] for r in rr);old=sum(r['ppm_from_older_than_model_max_age'] for r in rr);event=[]
  for e in sorted({r['event'] for r in rr}):
   z=[r for r in rr if r['event']==e];event.append((np.mean([r['total_ppm'] for r in z]),np.mean([r['ppm_from_within_model_age_support'] for r in z])))
  summary.append(dict(stop=stop,mean_total_ppm=total/len(rr),mean_ppm_from_beyond_model_age_support=old/len(rr),fraction_concentration_from_beyond_model_age_support=old/total if total else None,concentration_weighted_age_s=sum(r['total_ppm']*r['concentration_weighted_age_s'] for r in rr if r['total_ppm'])/total if total else None,positive_actual_windows=sum(a>.1 for a,b in event),positive_windows_after_readonly_age_support_censor=sum(b>.1 for a,b in event),censor_scope='state-contribution ablation only, not regenerated world or tuned model'))
 table(O/'ORIGINAL_GAS_AGE_QUERY_CONTRIBUTIONS.csv',query);table(O/'ORIGINAL_GAS_AGE_SUPPORT_AUDIT.csv',summary);put(O/'AGE_INFERENCE_QA.json',dict(native_sigma_recurrence='float32 sigma += gamma/(2sigma)*dt; sigma0=10cm gamma=15cm2/s dt=0.1s',exact_or_tolerance_matched_contributions=len(errors),unmatched=unknown,max_width_error_cm=max(errors),native_prediction_age_equivalents=maximum,readout_age_support_upper_s=cap,no_new_forward_calls=True,not_unique_wind_or_warmup_cause=True))
 print(summary)
if __name__=='__main__':main()
