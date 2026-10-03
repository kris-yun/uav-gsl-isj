"""Real meteorology only. Conditional uniform-field kinematics, not plume inversion."""
from pathlib import Path
import json, hashlib, subprocess, os
import numpy as np
import pandas as pd
import xarray as xr
import h5py
from scipy.integrate import trapezoid

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'evidence/front_lag_audit_20261003'; OUT.mkdir(parents=True,exist_ok=True)
BASE=Path(os.environ.get('WISCO_DATA_ROOT','C:/work/LAKESHORE_GSL_DATA_20261002/data_external'))
SRC=Path('C:/work/FRONT_LAG_AUDIT_20261003/sources')
DATES=['20210522','20210524']; RANGES=[50,100,200,300,500,750,1000]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def js(name,x):(OUT/name).write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
def csv(name,rows):pd.DataFrame(rows).to_csv(OUT/name,index=False)
def ang(u,v):return (270-np.degrees(np.arctan2(v,u)))%360
def delta(a,b):return abs((a-b+180)%360-180)
def quant(a,p):
 a=np.asarray(a);a=a[np.isfinite(a)];return float(np.percentile(a,p)) if len(a) else None

contract={
 'status':'FROZEN_BEFORE_NEW_NUMERICAL_SCORING; prior summaries already known, not blind preregistration',
 'base_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
 'dates':DATES,'selection_basis':'User fixed May22 and May24 before analysis; ESSD Table2 and RSC2023 section3.2 identify campaign lake-breeze conditions. No event replacement.',
 'evaluation_window_UTC':'13:00<=time<23:00 both dates; all eligible samples, no maximum-effect window selection',
 'context_window_UTC':'13:00<=time<17:00; observed background variability proxy, NOT stationary instrument noise',
 'source_distance_m':RANGES,
 'wind_speed_screen_m_s':{'primary':0.5,'sensitivity':[0.1,1.0]},
 'lidar_primary_heights_m':[76,93], 'lidar_secondary_heights_m':[110,127,144],
 'exclude_primary':[42,59], 'lidar_qc':'finite speed0..100 and direction0..360; no author SNR/QC threshold invented',
 'direction_convention':'Meteorological FROM; lidar u=-speed*sin(direction),v=-speed*cos(direction); RAAVEN author eastward/northward vectors used, not published direction',
 'direction_windows_s':[60,120,300,600],
 'window_matching':'Nearest previous observed sample to t-window within max(.15*window,.55*native_dt); require actual dt>=window/2 and actual interval/window in[.75,1.25]. Lidar 1/2min never resolved; nearest native 5min accepted with actual317..319s reported.',
 'tau_met':'reference_angle / (observed circular endpoint change / actual interval); angle30deg primary,60deg sensitivity; no min timescale selection. Speed timescale=current_speed/abs(speed rate). Endpoint definition misses intervening reversals.',
 'integration':'tau=L/current_speed; fixed tau for instantaneous and retarded. Exact piecewise-linear integral of observed ENU components; past-hold sensitivity. No future point beyond endpoint t.',
 'resolution':'history >=2 native/bin intervals and >=3 timestamps covering interval; no gap>1.5*cadence; no extrapolation. Sub-resolution estimates retained explicitly as interpolation-dependent, never evidence for gate.',
 'RAAVEN':'Flight_Flag1,wind_flag0; past-bin median vectors in10/30/60s bins with >=50% nominal samples, time=last accepted raw sample in bin (no future samples); primary backtrace30s,60s sensitivity. Full within-bin coordinate/height extrema retained for conservative mobile-history screen, height range<=10/20m and horizontal bbox diameter<=50/100m. None certify spatial homogeneity. Median bin winds are temporally smoothed, not instantaneous10Hz wind.',
 'RAAVEN_AGL':'Same earlier two-anchor checks; stable post-anchor is sensitivity only; no site-altitude imputation. Primary UAV-height applicability requires two-anchor accepted endpoint and history AGL10..100m.',
 'onset_proxy':'First east-sector90..180deg run lasting>=15min after17UTC with preceding west-sector>180deg sample in30min; same rule both dates. It is a wind marker, not independently validated thermal front onset.',
 'measurement_floor':'Observed pre17 native-step angular/vector variability separated from instrument uncertainty (not supplied by reviewed author files). Heading5/10/20deg and speed.1/.5m/s are ASSUMED sensitivity bounds, not measured precision. Sampling sensitivity PWL versus causal past-hold.',
 'stable_screen':'Exploratory screen only: at least3 consecutive resolved lidar samples with >=30m endpoint difference and above past-hold interpolation difference plus conservative assumed10deg/.5m/s endpoint bound. Not a calibrated uncertainty or lake-front specificity test.',
 'decision':'PASS needs two independent events plus calibrated uncertainty and resolvable temporal/spatial contract; missing required contract -> HOLD with explicit reason, not physical STOP. No new threshold changes to old experiments.',
 'approximation':'Spatially uniform conditional proxy; NOT a guaranteed lower bound and NOT recovered source coordinates.',
 'preserved':['R1','R1A','R1B','R3','TIBL-R0 .01 gate and skipped source stage'],
 'prohibited':['plume','CFD','GADEN','PMFS','training','new inverse model']}
js('FRONT_EVENT_CONTRACT.json',contract)
files=[]
for folder,pattern in [('B_WiscoDISCO21_Lidar','*wind_profiles*.cdf'),('B_WiscoDISCO21_RAAVEN','*.nc'),('B_WiscoDISCO21_M210','*.txt')]:
 files.extend(p for p in sorted((BASE/folder/'raw').glob(pattern)) if any(d in p.name for d in DATES))
inputs=[{'path':str(p),'archive_path':'inputs/'+p.parent.parent.name+'/raw/'+p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in files]
csv('INPUT_MANIFEST.csv',inputs)
js('PRE_ANALYSIS_FREEZE.json',{'contract_sha256':sha(OUT/'FRONT_EVENT_CONTRACT.json'),'script_sha256':sha(__file__),'inputs':inputs})

# Integral checked against analytically known constant and linear vectors.
def integrate(t,u,v,a,b,hold=False):
 knots=np.r_[a,t[(t>a)&(t<b)],b]
 if hold:
  idx=np.searchsorted(t,knots[:-1],side='right')-1
  return np.array([np.sum(u[idx]*np.diff(knots)),np.sum(v[idx]*np.diff(knots))])
 return np.array([trapezoid(np.interp(knots,t,w),knots) for w in [u,v]])
assert np.allclose(integrate(np.array([0.,1.,2.]),np.ones(3)*2,np.ones(3)*3,.25,1.75),[3,4.5])
assert np.allclose(integrate(np.array([0.,1.,2.]),np.array([0.,1.,2.]),np.zeros(3),.5,2),[1.875,0])
assert delta(359,1)==2

series=[];rawrows=[];coverage=[];coords=[];anchors=[];thermal=[]
for p in files:
 if 'wind_profiles' in p.name:
  with h5py.File(p) as f:
   date=str(int(f['date'][()]));tm=f['time'][:]*3600;z=f['height'][:]*1000;s=f['windSpeed'][:];d=f['windDir'][:]
   for k in ['latitude','longitude','lat','lon']:
    if k in f:coords.append({'platform':'lidar','file':p.name,'field':k,'value':str(f[k][:].tolist() if f[k].shape else f[k][()])})
  for h in [76,93,110,127,144]:
   k=np.argmin(abs(z-h));ok=np.isfinite(s[:,k])&np.isfinite(d[:,k])&(s[:,k]>=.5)&(s[:,k]<100)&(d[:,k]>=0)&(d[:,k]<=360)
   q=pd.DataFrame({'t':tm,'u':-s[:,k]*np.sin(np.radians(d[:,k])),'v':-s[:,k]*np.cos(np.radians(d[:,k]))})[ok].copy()
   q['z']=h;q['east']=0.;q['north']=0.;q['agl']=h
   series.append((date,'lidar',p.name,h,float(np.median(np.diff(tm))),q,True))
  coverage.append({'platform':'lidar','file':p.name,'date':date,'cadence_s':float(np.median(np.diff(tm))),'count':len(tm),'ground_wind':False})
 elif p.suffix=='.nc':
  with xr.open_dataset(p,decode_times=False) as ds:
   v={k:ds[k].values.copy() for k in ['time','Flight_Flag','wind_flag','eastward_wind','northward_wind','alt','lat','lon','Flight_State']}
  ts=pd.to_datetime(v['time'],unit='s',origin='2020-01-01',utc=True);date=ts[0].strftime('%Y%m%d');t=(ts-ts.normalize()).total_seconds().to_numpy();ff=v['Flight_Flag'];a=v['alt'];ii=np.flatnonzero(ff==1)
  def anchor(mask):
   x=a[mask];x=x[np.isfinite(x)];return (float(np.median(x)),float(np.percentile(x,75)-np.percentile(x,25)),len(x)) if len(x) else (np.nan,np.nan,0)
  pre=anchor((ff==0)&(t>=t[ii[0]]-35)&(t<t[ii[0]]-5));post=anchor((ff==0)&(t>t[ii[-1]]+5)&(t<=t[ii[-1]]+35))
  both=pre[2]>=150 and post[2]>=150 and max(pre[1],post[1])<=2 and abs(pre[0]-post[0])<=5
  postok=post[2]>=150 and post[1]<=2;ref=(pre[0]+post[0])/2 if both else post[0] if postok else np.nan
  anchors.append({'file':p.name,'date':date,'pre_msl':pre[0],'post_msl':post[0],'pre_IQR':pre[1],'post_IQR':post[1],'two_anchor':both,'post_sensitivity':postok,'reference_msl':ref})
  u=v['eastward_wind'];vv=v['northward_wind'];ok=(ff==1)&(v['wind_flag']==0)&np.isfinite(u)&np.isfinite(vv)&(np.hypot(u,vv)>=.5)&np.isfinite(a)&np.isfinite(v['lat'])&np.isfinite(v['lon'])
  lat=v['lat'];lon=v['lon'];lat0=np.median(lat[ok]);lon0=np.median(lon[ok])
  frame=pd.DataFrame({'t':t[ok],'u':u[ok],'v':vv[ok],'z':a[ok],'agl':a[ok]-ref,'east':(lon[ok]-lon0)*111195*np.cos(np.radians(lat0)),'north':(lat[ok]-lat0)*111195,'lat':lat[ok],'lon':lon[ok]})
  for dt in [10,30,60]:
   q=frame.assign(bin=np.floor(frame.t/dt)).groupby('bin').agg(t=('t','max'),u=('u','median'),v=('v','median'),z=('z','median'),agl=('agl','median'),east=('east','median'),north=('north','median'),count=('t','size'),z_min=('z','min'),z_max=('z','max'),agl_min=('agl','min'),agl_max=('agl','max'),east_min=('east','min'),east_max=('east','max'),north_min=('north','min'),north_max=('north','max'))
   q=q[q['count']>=dt*5].copy();q=q[np.hypot(q.u,q.v)>=.5]
   if dt in [30,60]:series.append((date,'RAAVEN_mobile',p.name,dt,dt,q,both))
   coverage.append({'platform':'RAAVEN_mobile','file':p.name,'date':date,'cadence_s':dt,'count':len(q),'two_anchor_AGL':both,'mobile_spatial_unverified':True})
   if dt==10:
    for r in q.itertuples():rawrows.append({'date':date,'file':p.name,'utc':str(pd.Timestamp(date,tz='UTC')+pd.to_timedelta(r.t,unit='s')),'u':r.u,'v':r.v,'alt_msl':r.z,'agl':r.agl,'lat_approx':lat0+r.north/111195,'lon_approx':lon0+r.east/(111195*np.cos(np.radians(lat0))),'two_anchor_AGL':both})
 elif p.suffix=='.txt':
  q=pd.read_csv(p);q=q[(q.iMetFlag==0)&q.Altitude_Average_magl.between(0,125)]
  for r in q.itertuples(index=False):
   thermal.append({'file':p.name,'utc':str(pd.to_datetime(r.Date+' '+r.TimeUTC,utc=True)),'height_agl':r.Altitude_Average_magl,'temperature_C':r.Temperature_Average_degC,'temperature_sd_C':r.Temperature_stdev,'height_sd_m':r.Altitude_stdev,'RH':r.RelativeHumidity_Average_percent,'lat':r.latitude,'lon':r.longitude,'support_s':90})
csv('RAAVEN_10s_vectors.csv',rawrows);csv('RAAVEN_ANCHOR_QA.csv',anchors);csv('M210_TEMPERATURE.csv',thermal);csv('PLATFORM_COORDINATES.csv',coords);csv('COVERAGE.csv',coverage)

front=[];adv=[];ret=[];floors=[];native=[];onsets=[]
for date,platform,file,height,dt,q,agl_valid in series:
 q=q.sort_values('t');t=q.t.to_numpy();u=q.u.to_numpy();v=q.v.to_numpy();speed=np.hypot(u,v);direction=ang(u,v)
 context=(t>=13*3600)&(t<17*3600);step=(np.diff(t)<=dt*1.5)&context[1:]&context[:-1]
 angularfloor=quant(delta(direction[1:],direction[:-1])[step],95);vectorfloor=quant(np.hypot(np.diff(u),np.diff(v))[step],95)
 floors.append({'date':date,'platform':platform,'file':file,'height_or_bin':height,'native_cadence_s':dt,'background_pairs':int(step.sum()),'background_step_angle_p95_deg':angularfloor,'background_step_vector_p95_m_s':vectorfloor,'instrument_heading_accuracy_deg':None,'instrument_speed_accuracy_m_s':None,'accuracy_status':'No calibrated per-observation bound recovered; empirical background is not instrument error','assumed_heading_sensitivity_deg':'5;10;20','assumed_speed_sensitivity_m_s':'.1;.5'})
 # A reproducible wind-sector onset marker. Not the paper's full temperature+wind event rule.
 for i in range(len(t)):
  if t[i]<17*3600 or t[i]>=23*3600:continue
  after=(t>=t[i])&(t<=t[i]+900);before=(t<t[i])&(t>=t[i]-1800)
  if after.sum()>=3 and t[after][-1]-t[i]>=900-dt and np.max(np.diff(t[after]))<=dt*1.5 and np.all((direction[after]>=90)&(direction[after]<180)) and np.any(direction[before]>180):
   onsets.append({'date':date,'platform':platform,'file':file,'height_or_bin':height,'onset_proxy_utc':str(pd.Timestamp(date,tz='UTC')+pd.to_timedelta(t[i],unit='s')),'previous_observation_utc':str(pd.Timestamp(date,tz='UTC')+pd.to_timedelta(t[i-1],unit='s')) if i else None,'bracket_s':float(t[i]-t[i-1]) if i else None,'persistent_until_utc':str(pd.Timestamp(date,tz='UTC')+pd.to_timedelta(t[after][-1],unit='s')),'definition':'wind sector only; thermal-front timing unverified'});break
 for i in np.flatnonzero((t>=13*3600)&(t<23*3600)):
  stamp=str(pd.Timestamp(date,tz='UTC')+pd.to_timedelta(t[i],unit='s'))
  base={'date':date,'platform':platform,'file':file,'height_or_bin':height,'utc':stamp,'cadence_s':dt,'speed_m_s':speed[i],'direction_from_deg':direction[i],'u_m_s':u[i],'v_m_s':v[i]}
  if platform=='lidar':native.append(base)
  scales={}
  for window in [60,120,300,600]:
   past=np.flatnonzero(t<t[i]);j=past[np.argmin(abs(t[past]-(t[i]-window)))] if len(past) else -1
   elapsed=t[i]-t[j] if j>=0 else np.nan
   resolved=bool(j>=0 and .75<=elapsed/window<=1.25 and abs(elapsed-window)<=max(.15*window,.55*dt) and np.max(np.diff(t[j:i+1]))<=1.5*dt and not(platform=='lidar' and window<300))
   dc=float(delta(direction[i],direction[j])) if resolved else np.nan;dr=dc/elapsed if resolved else np.nan
   scales[window]=30/dr if resolved and dr>0 else np.inf if resolved else np.nan
   front.append(dict(base,window_s=window,actual_interval_s=elapsed if resolved else None,resolved=resolved,circular_change_deg=dc,direction_rate_deg_min=dr*60,speed_rate_m_s_min=(speed[i]-speed[j])/elapsed*60 if resolved else None,tau_met_30deg_s=scales[window],tau_met_60deg_s=scales[window]*2,tau_speed_s=speed[i]*elapsed/abs(speed[i]-speed[j]) if resolved and speed[i]!=speed[j] else None))
  for L in RANGES:
   tau=L/speed[i];start=t[i]-tau
   adv.append(dict(base,distance_m=L,tau_adv_s=tau,Lambda_5min_definition=tau/scales[300],Lambda_10min_definition=tau/scales[600],Lambda_60deg_5min=tau/(2*scales[300])))
   j=int(np.searchsorted(t,start,side='right')-1)
   support=bool(j>=0 and i>j and np.max(np.diff(t[j:i+1]))<=dt*1.5)
   resolved=bool(support and tau>=2*dt and np.sum((t>=start)&(t<=t[i]))>=3)
   row=dict(base,distance_m=L,tau_adv_s=tau,history_supported=support,temporally_resolved=resolved,spatial_history_verified=platform=='lidar',spatial_field_verified=False,primary_UAV_height=platform=='lidar' and height in [76,93],AGL_two_anchor=agl_valid,approximation='conditional uniform temporal proxy; not lower bound',angular_mismatch_deg=None,endpoint_mismatch_m=None,normalized_endpoint_mismatch=None,interpolation_sensitivity_m=None)
   if support:
    inst=-np.array([u[i],v[i]])*tau;rt=-integrate(t,u,v,start,t[i]);rh=-integrate(t,u,v,start,t[i],True)
    mis=float(np.linalg.norm(inst-rt));inter=float(np.linalg.norm(rt-rh));aerr=float(delta(ang(*inst),ang(*rt))) if np.linalg.norm(rt)>1e-9 else np.nan
    span=q.iloc[j:i+1];zr=quant(span.z,95)-quant(span.z,5);diam=float(np.hypot(span.east.max()-span.east.min(),span.north.max()-span.north.min()))
    in_band=span.agl.between(10,100).all()
    if platform=='RAAVEN_mobile':
     zr=float(span.z_max.max()-span.z_min.min());diam=float(np.hypot(span.east_max.max()-span.east_min.min(),span.north_max.max()-span.north_min.min()));in_band=span.agl_min.ge(10).all() and span.agl_max.le(100).all()
    bound=2*L*np.sin(np.radians(10))+2*tau*.5 # triangle bound for independently allowed errors in both wind histories, not calibrated accuracy
    mobile_primary=bool(agl_valid and in_band and zr<=10 and diam<=50)
    row.update(angular_mismatch_deg=aerr,endpoint_mismatch_m=mis,normalized_endpoint_mismatch=mis/L,interpolation_sensitivity_m=inter,inst_east_m=inst[0],inst_north_m=inst[1],ret_east_m=rt[0],ret_north_m=rt[1],past_hold_endpoint_mismatch_m=float(np.linalg.norm(inst-rh)),ret_endpoint_norm_m=float(np.linalg.norm(rt)),ret_endpoint_range_ratio=float(np.linalg.norm(rt)/L),assumed_10deg_0_5ms_triangle_bound_m=bound,above_assumed_bound_and_interp=bool(mis>bound+inter),above_background_vector_proxy=bool(vectorfloor is not None and mis>tau*vectorfloor),height_spread_m=zr,path_bbox_diameter_m=diam,mobile_height10m_pos50m_screen=mobile_primary,mobile_height20m_pos100m_screen=bool(agl_valid and in_band and zr<=20 and diam<=100))
    for deg in [5,10,20]:
     for du in [.1,.5]:row[f'assumed_bound_{deg}deg_{str(du).replace(".","p")}ms_m']=float(2*L*np.sin(np.radians(deg))+2*tau*du)
   ret.append(row)
csv('LIDAR_NATIVE_VECTORS.csv',native);csv('FRONT_TIMESCALES.csv',front);csv('ADVECTIVE_TIMESCALES.csv',adv);csv('RETARDED_BACKTRACE.csv',ret);csv('MEASUREMENT_FLOOR.csv',floors);csv('ONSET_PROXIES.csv',onsets)

summary=[];rr=pd.DataFrame(ret);aa=pd.DataFrame(adv);ft=pd.DataFrame(front)
for date in DATES:
 for L in RANGES:
  r=rr[(rr.date==date)&(rr.platform=='lidar')&rr.height_or_bin.isin([76,93])&(rr.distance_m==L)]
  s=r[r.history_supported];resolved=s[s.temporally_resolved]
  a=aa[(aa.date==date)&(aa.platform=='lidar')&aa.height_or_bin.isin([76,93])&(aa.distance_m==L)]
  summary.append({'date':date,'distance_m':L,'n_total':len(r),'n_supported':len(s),'n_temporally_resolved':len(resolved),'conditional_all_mismatch_median_m':quant(s.endpoint_mismatch_m,50),'conditional_all_mismatch_p95_m':quant(s.endpoint_mismatch_m,95),'resolved_mismatch_median_m':quant(resolved.endpoint_mismatch_m,50),'resolved_mismatch_p95_m':quant(resolved.endpoint_mismatch_m,95),'resolved_mismatch_max_m':quant(resolved.endpoint_mismatch_m,100),'n_above_assumed_bound_and_interpolation':int(resolved.above_assumed_bound_and_interp.fillna(False).sum()),'tau_adv_median_s':quant(a.tau_adv_s,50),'Lambda_5min_median':quant(a.Lambda_5min_definition,50),'Lambda_5min_p95':quant(a.Lambda_5min_definition,95)})
csv('DISTANCE_SUMMARY.csv',summary)
ts=[]
for (date,plat,h,w),q in ft[ft.resolved].groupby(['date','platform','height_or_bin','window_s']):
 ts.append({'date':date,'platform':plat,'height_or_bin':h,'window_s':w,'n':len(q),'circular_change_p50_deg':quant(q.circular_change_deg,50),'circular_change_p95_deg':quant(q.circular_change_deg,95),'circular_change_max_deg':quant(q.circular_change_deg,100),'tau_met30_p25_s':quant(q.tau_met_30deg_s,25),'tau_met30_median_s':quant(q.tau_met_30deg_s,50),'tau_met30_p75_s':quant(q.tau_met_30deg_s,75)})
csv('TIMESCALE_SUMMARY.csv',ts)
stable=[]
for keys,q in rr[(rr.platform=='lidar')&rr.height_or_bin.isin([76,93])].groupby(['date','height_or_bin','distance_m']):
 q=q.sort_values('utc');run=best=0;last=None
 for r in q.itertuples():
  tnow=pd.Timestamp(r.utc);ok=r.temporally_resolved and r.endpoint_mismatch_m is not None and r.endpoint_mismatch_m>=30 and bool(r.above_assumed_bound_and_interp)
  run=(run+1 if last is not None and (tnow-last).total_seconds()<=r.cadence_s*1.5 else 1) if ok else 0;best=max(best,run);last=tnow
 stable.append({'date':keys[0],'height_m':keys[1],'distance_m':keys[2],'max_consecutive_exploratory_screen':best,'engineering_stable_screen':best>=3,'formal_uncertainty_validated':False})
csv('STABILITY_SCREEN.csv',stable)
decision={'decision':'R0_FRONT_LAG_HOLD_EVENT_SPECIFIC','reason':'Required measurement uncertainty / high-frequency fixed-site history contracts incomplete; code name retained from allowed vocabulary, NOT a claim that only one date has a signal.',
 'independent_dates_analyzed':DATES,'n_real_front_events_with_calibrated_resolved_mismatch':None,
 'ground_station_raw_wind':'Not in three author public archives; paper confirms4.5m observations but raw time-resolved series not recovered.',
 'spatial_front_speed_m_s':None,'shore_inland_onset_lag_s':None,'layer_top_series_m':None,
 'event_context':'Both dates have independently published lake-breeze context; exact comparable passage intervals not recovered from metadata. Paper layer-height/onset descriptions remain literature context, not newly measured time series.',
 'why_not_STOP':'Sub-cadence lidar and mobile RAAVEN cannot establish absence of mismatch. Large conditional endpoint differences likewise do not prove source error.',
 'next_stage_authorized':False,'source_localization_improved':False,'no_plume_or_inverse_executed':True,'old_gates_unchanged':True,
 'contract_sha256':sha(OUT/'FRONT_EVENT_CONTRACT.json'),'input_manifest_sha256':sha(OUT/'INPUT_MANIFEST.csv')}
js('R0_FRONT_LAG_DECISION.json',decision)
print(json.dumps({'decision':decision['decision'],'inputs':len(inputs),'backtrace_rows':len(ret),'distance_summary':summary},indent=2))
