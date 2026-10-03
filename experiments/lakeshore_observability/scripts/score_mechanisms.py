"""Frozen M1/M2/M3 descriptive diagnostics and README secondary gate."""
import json,numpy as np,pandas as pd
from score_identifiability import load,ENVS,SOURCES,RATES,HEIGHTS,OUT,ROOT
def mechanisms(a,xy,threshold):
 hit=a>=threshold;p=hit.mean(axis=3);m1=[];m2=[];m3=[]
 for e,env in enumerate(ENVS):
  for r,rate in enumerate(RATES):
   for s,(sx,sy) in enumerate(SOURCES):
    # u_h is y-independent; obtain exact native query values (not analytic proxy).
    raw=pd.read_csv(OUT/'observations'/f'{env}_x{sx}_y{sy}_r{rate}_seed30001.csv')
    for h,height in enumerate(HEIGHTS):
     q=raw[raw.z==height];up=-q[['u','v']].to_numpy();bearing=np.array([sx,sy])-xy;den=np.linalg.norm(up,axis=1)*np.linalg.norm(bearing,axis=1);angle=np.degrees(np.arccos(np.clip(np.divide((up*bearing).sum(axis=1),den,out=np.zeros(300),where=den>0),-1,1)));mask=hit[e,r,s,:,h,:]&(den>0)[None,:];angles=np.broadcast_to(angle,(8,300))[mask]
     m1.append(dict(environment=env,release=rate,source_x=sx,source_y=sy,height=height,gas_hits=len(angles),median_error_deg=float(np.median(angles)) if len(angles) else None,q75_error_deg=float(np.quantile(angles,.75)) if len(angles) else None,cone_capture=float(np.mean(angles<=45)) if len(angles) else None))
    if env in ['F1','F2']:
     eligible=p[0,r,s,0]>=.5;restore=p[e,r,s,1:].max(axis=0);blind=eligible&(p[e,r,s,0]<=.2)&(restore>=.5)
     m2.append(dict(environment=env,release=rate,source_x=sx,source_y=sy,baseline_eligible_points=int(eligible.sum()),blind_points=int(blind.sum()),blind_spatial_fraction=float(blind.mean()),eligible_blind_fraction=float(blind.sum()/eligible.sum()) if eligible.any() else 0.,low_high_recovery=float((restore-p[e,r,s,0])[blind].mean()) if blind.any() else 0.))
    for k in range(8):
     field=a[e,r,s,k];maximum=field.max()
     if maximum<=0:continue
     h,t=np.unravel_index(np.argmax(field),field.shape);x,y=xy[t];ds=float(np.linalg.norm([x-sx,y-sy,HEIGHTS[h]-1]));df=abs(float(x)-120)
     m3.append(dict(environment=env,release=rate,source_x=sx,source_y=sy,seed=30001+k,peak_x=x,peak_y=y,peak_height=HEIGHTS[h],peak_concentration=maximum,d_peak_to_source=ds,d_peak_to_front=df,near_front=df<=15))
 secondary=[]
 df1=pd.DataFrame(m1);df2=pd.DataFrame(m2);df3=pd.DataFrame(m3)
 for env in ['F1','F2']:
  per=[]
  for rate in RATES:
   q=df1[(df1.environment==env)&(df1.release==rate)];n=df1[(df1.environment=='N0')&(df1.release==rate)]
   def capture(t):
    tt=t[t.gas_hits>0];return float((tt.cone_capture*tt.gas_hits).sum()/tt.gas_hits.sum()) if len(tt) else None
   fc=capture(q);nc=capture(n);drop=nc-fc if nc is not None and fc is not None else None
   b=df2[(df2.environment==env)&(df2.release==rate)];blind_sources=int((b.blind_points>0).sum())
   p3=df3[(df3.environment==env)&(df3.release==rate)];n3=df3[(df3.environment=='N0')&(df3.release==rate)];frontfrac=float(p3.near_front.mean()) if len(p3) else 0;baselinefrac=float(n3.near_front.mean()) if len(n3) else 0;groups=int(p3[p3.near_front].source_x.nunique())
   m3pass=bool(groups>=2 and frontfrac>baselinefrac and len(p3) and p3.d_peak_to_front.median()<p3.d_peak_to_source.median())
   per.append({'release':rate,'M1_capture_drop_pp':100*drop if drop is not None else None,'M1_pass':bool(drop is not None and drop>=.2),'M2_blind_source_count':blind_sources,'M2_pass':blind_sources>=2,'M3_front_peak_fraction':frontfrac,'M3_N0_front_peak_fraction':baselinefrac,'M3_x_groups':groups,'M3_pass':m3pass})
  secondary.append({'environment':env,'release_results':per,'secondary_pass':any(sum(q[f'{m}_pass'] for q in per)>=2 for m in ['M1','M2','M3'])})
 return df1,df2,df3,secondary
if __name__=='__main__':
 a,xy=load();results={}
 for factor in [.5,1,2]:
  m1,m2,m3,sec=mechanisms(a,xy,.001*factor)
  for name,d in [('M1',m1),('M2',m2),('M3',m3)]:d.to_csv(OUT/f'{name}_threshold_{factor:g}.csv',index=False)
  results[str(factor)]=sec
 (OUT/'secondary_gate.json').write_text(json.dumps(results,indent=2))
 primary=json.loads((OUT/'M4_gate.json').read_text())
 matched=[env for env in ['F1','F2'] if sum(q['primary_pass'] for q in primary['1']['primary_rows'] if q['environment']==env)>=2 and any(q['environment']==env and q['secondary_pass'] for q in results['1'])]
 anysecondary=any(q['secondary_pass'] for q in results['1']);decision='R1_PASS_LAKESHORE_OBSERVABILITY_DISTORTION' if matched else ('R1_HOLD_WEAK_OR_UNSTABLE' if anysecondary else 'R1_FAIL_STOP_SCENE_MECHANISM')
 final={'decision':decision,'R0':'R0_GO','R1':{'execution_status':'COMPLETED_FULL_864','primary':primary['1'],'secondary':results['1'],'M1':'M1_threshold_1.csv','M2':'M2_threshold_1.csv','M3':'M3_threshold_1.csv','M4':'M4_summary_threshold_1.csv','matched_primary_secondary_environments':matched},'R2':{'execution_status':'PENDING' if matched else 'NOT_EXECUTED_R1_GATE'},'threshold_sensitivity':{k:{'primary_pass':primary[k]['primary_pass'],'secondary':results[k]} for k in results}}
 (OUT/'FINAL_DECISION.json').write_text(json.dumps(final,indent=2));print(json.dumps(final,indent=2))
