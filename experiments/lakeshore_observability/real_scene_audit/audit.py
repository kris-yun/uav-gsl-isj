"""Exploratory all-file observation audit; no simulation and no retrospective gates."""
import pathlib,json,hashlib,itertools,os
import numpy as np,pandas as pd,xarray as xr,h5py
ROOT=pathlib.Path(__file__).resolve().parents[3];HERE=pathlib.Path(__file__).parent
OUT=ROOT/'evidence/wiscodisco_real_scene_feature_audit_20261003';OUT.mkdir(exist_ok=True)
BASE=pathlib.Path('C:/work/LAKESHORE_GSL_DATA_20261002');DATA=BASE/'data_external'
DATA=pathlib.Path(os.environ.get('WISCO_DATA_ROOT',str(DATA)))
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def js(name,value):(OUT/name).write_text(json.dumps(value,indent=2,allow_nan=False),encoding='utf-8')
def circ(v):
 v=np.asarray(v);v=v[np.isfinite(v)]
 return float(np.angle(np.exp(1j*np.deg2rad(v)).mean(),deg=True)%360) if len(v) else np.nan
def delta(a,b):return float(abs((a-b+180)%360-180))
def humid(T,RH,P):
 e=RH/100*6.112*np.exp(17.67*T/(T+243.5));return 1000*.622*e/(P-.378*e)
def longest(times,yes,maxgap):
 best=0.;start=None;previous=None
 for t,b in zip(times,yes):
  if not b:start=None;previous=None;continue
  if start is None or (t-previous).total_seconds()>maxgap:start=t
  best=max(best,(t-start).total_seconds());previous=t
 return best
cfg={'protocol_commit':'3cb1e989e901f6391fa4163571b8beb17b96f3ad','design':'exploratory all available files/dates; not a preregistered hypothesis PASS test','no_new_GADEN':True,'source_height_comparison':'published AGL for M210/lidar; RAAVEN derived launch-site AGL only under explicit ground reference QA; no assumed site elevation','RAAVEN_ground_reference':'30s intervals5..35s before first flight flag and after last flight flag; each>=150samples,IQR<=2m,ground median difference<=5m gives two-anchor primary; stable post-anchor alone is sensitivity; median of accepted anchors; half-difference plus2m reported as reference uncertainty indicator, not calibrated error','RAAVEN_wind':'Flight_Flag1,wind_flag0,finite u/v,wind speed>=.5m/s primary; sensitivity .1 and1m/s; source QC flags retain authority','time_height_contract':'RAAVEN nonoverlapping300s UTC windows; height bins10+/-5,30+/-5,50+/-10,60+/-10,100+/-10m; at least50 good10Hz samples per wind bin; bins overlap50/60 intentionally, never treated as independent profiles; means sequential/mobile,not simultaneous columns','lidar':'all6 profile files only,authors date+decimal UTC hour; no stare date/height correction; nearest actual gate within10m of target; no interpolation; primary directional comparison76vs93m,lowest42/59 flagged as unvalidated low-gate diagnostics irrespective of speed screening; no invented SNR threshold','M210':'all24 published90s tables; iMetFlag0 primary;1/2 sensitivity;finite physical T/RH/pressure;5<=h<=125m; strongest inversion in10..100m across pairs separated>=10m; report elapsed time and altitude SD,not lake-breeze-top; O3 separate POMFlag0','layer_height_rule':'lake_breeze_layer_top remains null unless independent air-mass boundary identification exists; max positive adjacent T jump midpoint is ONLY thermal-transition proxy; do not equate inversion proxy with lake-breeze or TIBL top','real_gate':'four necessary protocol conditions:task-scale/large-UAV-scale/independent replication/observable-state; plus lake-specificity and specific-source-failure evidence. Missing evidence gives NOT_ESTABLISHED; observed proxy does not automatically authorize a simulator run','preserve':'R1/R1A/R1B frozen;STOP current parametric-front line;no Word edit'}
js('ANALYSIS_CONTRACT.json',cfg)
files=sorted((DATA/'B_WiscoDISCO21_RAAVEN/raw').glob('*.nc'))+sorted((DATA/'B_WiscoDISCO21_M210/raw').glob('*.txt'))+sorted((DATA/'B_WiscoDISCO21_Lidar/raw').glob('*wind_profiles*.cdf'))
assert len(files)==42
inp=[dict(path=str(p),archive_path='inputs/'+p.parent.parent.name+'/raw/'+p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in files]
pd.DataFrame(inp).to_csv(OUT/'INPUT_MANIFEST.csv',index=False)
js('PRE_ANALYSIS_FREEZE.json',{'contract_sha256':sha(OUT/'ANALYSIS_CONTRACT.json'),'script_sha256':sha(pathlib.Path(__file__)),'raw_files':len(files),'raw_inputs':inp})

# M210: one ascent per file. Sequential observations cannot prove within-task persistence.
thermal=[];tempbins=[];ozone=[];rawpoints=[]
for p in sorted((DATA/'B_WiscoDISCO21_M210/raw').glob('*.txt')):
 d=pd.read_csv(p);stamp=pd.to_datetime(d.Date+' '+d.TimeUTC,utc=True);date=stamp.iloc[0].date().isoformat()
 required=['Temperature_Average_degC','RelativeHumidity_Average_percent','Pressure_Average_hPa','iMetFlag','POMFlag','Altitude_stdev','Temperature_stdev']
 missing=[c for c in required if c not in d]
 for c in missing:d[c]=np.nan # Structural absence stays missing, never imputed observations.
 d['utc']=stamp;h=d.Altitude_Average_magl;T=d.Temperature_Average_degC;RH=d.RelativeHumidity_Average_percent;P=d.Pressure_Average_hPa
 physical=np.isfinite(h)&np.isfinite(T)&np.isfinite(RH)&np.isfinite(P)&h.between(5,125)&T.between(-50,60)&RH.between(0,100)&P.between(800,1100)
 for policy in ['strict_flag0','flagged_sensitivity']:
  q=d[physical&((d.iMetFlag==0) if policy=='strict_flag0' else d.iMetFlag.isin([0,1,2]))].copy().sort_values('Altitude_Average_magl')
  q['theta_K']=(q.Temperature_Average_degC+273.15)*(1000/q.Pressure_Average_hPa)**.2854
  q['specific_humidity_g_kg']=humid(q.Temperature_Average_degC,q.RelativeHumidity_Average_percent,q.Pressure_Average_hPa)
  for height,width in [(10,5),(30,5),(60,10),(100,10)]:
   b=q[q.Altitude_Average_magl.between(height-width,height+width)]
   tempbins.append(dict(file=p.name,date=date,policy=policy,target_height=height,n=len(b),actual_height=b.Altitude_Average_magl.mean(),temperature_C=b.Temperature_Average_degC.mean(),RH_percent=b.RelativeHumidity_Average_percent.mean(),theta_K=b.theta_K.mean(),specific_humidity_g_kg=b.specific_humidity_g_kg.mean()))
  row=dict(file=p.name,date=date,policy=policy,n=len(q),missing_columns=';'.join(missing),utc_start=str(stamp.min()),utc_end=str(stamp.max()),flight_span_s=(stamp.max()-stamp.min()).total_seconds(),lake_breeze_layer_top_m=None)
  if len(q)>=2:
   z=q.Altitude_Average_magl.to_numpy();temp=q.Temperature_Average_degC.to_numpy();rh=q.RelativeHumidity_Average_percent.to_numpy();qt=q.specific_humidity_g_kg.to_numpy();theta=q.theta_K.to_numpy();tm=q.utc.to_numpy()
   choices=[(temp[j]-temp[i],i,j) for i in range(len(q)) for j in range(i+1,len(q)) if z[i]>=10 and z[j]<=100 and z[j]-z[i]>=10]
   best,i,j=max(choices) if choices else (np.nan,0,0)
   gradients=np.diff(temp)/np.diff(z);good=np.diff(z)>=5;index=int(np.argmax(np.where(good,gradients,-np.inf)))
   proxy=float((z[index]+z[index+1])/2) if good.any() and gradients[index]>0 else None
   elapsed=abs(pd.Timestamp(tm[j])-pd.Timestamp(tm[i])).total_seconds() if choices else None
   row.update(min_height=float(z.min()),max_height=float(z.max()),max_inversion10_100_C=float(max(0,best)) if choices else None,inversion_bottom_m=float(z[i]) if choices else None,inversion_top_m=float(z[j]) if choices else None,inversion_pair_elapsed_s=elapsed,thermal_transition_proxy_m=proxy,largest_adjacent_T_jump_C=float(np.diff(temp)[index]) if good.any() else None,upper_minus_lower_T_C=float(temp[-1]-temp[0]),upper_minus_lower_RH_pp=float(rh[-1]-rh[0]),upper_minus_lower_q_gkg=float(qt[-1]-qt[0]),upper_minus_lower_theta_K=float(theta[-1]-theta[0]),max_altitude_sd_m=float(q.Altitude_stdev.max()),height_order_has_reversals=bool((np.diff(d[physical].Altitude_Average_magl)<-5).any()))
   if not choices or best<=0:
    row['inversion_bottom_m']=None;row['inversion_top_m']=None;row['inversion_pair_elapsed_s']=None
  thermal.append(row)
  if policy=='strict_flag0':
   for r in q.itertuples():rawpoints.append(dict(file=p.name,date=date,utc=str(r.utc),height_m=r.Altitude_Average_magl,temperature_C=r.Temperature_Average_degC,RH_percent=r.RelativeHumidity_Average_percent,theta_K=r.theta_K,specific_humidity_g_kg=r.specific_humidity_g_kg,altitude_sd_m=r.Altitude_stdev,T_sd_C=r.Temperature_stdev))
 oq=d[(d.POMFlag==0)&d.Altitude_Average_magl.between(0,125)&d.Ozone_Average_ppb.between(0,300)]
 ozone.append(dict(file=p.name,date=date,n_good_ozone=len(oq),min_ppb=oq.Ozone_Average_ppb.min(),max_ppb=oq.Ozone_Average_ppb.max(),source_truth_available=False,spatial_convergence_available=False))
pd.DataFrame(thermal).to_csv(OUT/'M210_all_flight_thermal_features.csv',index=False);pd.DataFrame(tempbins).to_csv(OUT/'M210_target_height_thermodynamics.csv',index=False);pd.DataFrame(rawpoints).to_csv(OUT/'M210_QC_profile_points.csv',index=False);pd.DataFrame(ozone).to_csv(OUT/'M210_ozone_context.csv',index=False)

# Lidar no author QC flag: low gates remain diagnostic, even if speed exceeds screen.
lid=[];lowgates=[];cadence=[]
for p in sorted((DATA/'B_WiscoDISCO21_Lidar/raw').glob('*wind_profiles*.cdf')):
 with h5py.File(p) as f:z=f['height'][:]*1000;t=f['time'][:];speed=f['windSpeed'][:];direction=f['windDir'][:];snr=f['snr'][:];date=str(int(f['date'][()]))
 assert date in p.name
 valid=np.isfinite(speed)&np.isfinite(direction)&(speed>=0)&(speed<100)&(direction>=0)&(direction<=360)
 utc=pd.Timestamp(date,tz='UTC')+pd.to_timedelta(t,unit='h')
 dt=np.diff(t)*3600;cadence.append(dict(file=p.name,date=str(utc[0].date()),n_profiles=len(t),median_dt_s=float(np.median(dt)),min_dt_s=float(dt.min()),max_dt_s=float(dt.max()),fraction_dt_le300=float((dt<=300).mean()),min_native_height_m=float(z[(z>0)&(z<1e6)].min())))
 for k in range(6):
  q=speed[:,k][valid[:,k]];s=snr[:,k];s=s[np.isfinite(s)&(s>-999)&(s<1e10)]
  lowgates.append(dict(file=p.name,date=str(utc[0].date()),height_m=z[k],n_range_valid=len(q),median_speed=float(np.median(q)) if len(q) else np.nan,frac_speed_below0_5=float((q<.5).mean()) if len(q) else np.nan,median_snr=float(np.median(s)) if len(s) else np.nan,lowest_gate_unvalidated=bool(z[k]<75)))
 for screen in [.1,.5,1.]:
  for i,time in enumerate(utc):
   row=dict(platform='lidar',file=p.name,date=str(time.date()),utc=str(time),speed_screen=screen,quality='no_author_QC_flag;42/59m_diagnostic_only',lake_breeze_layer_top_m=None)
   for height in [10,30,60,100]:
    k=int(np.argmin(abs(z-height)));ok=abs(z[k]-height)<=10 and valid[i,k] and speed[i,k]>=screen
    row[f'direction_{height}m_deg']=float(direction[i,k]) if ok else np.nan;row[f'actual_height_{height}m']=float(z[k]) if abs(z[k]-height)<=10 else np.nan;row[f'speed_{height}m_s']=float(speed[i,k]) if ok else np.nan
   k76=int(np.argmin(abs(z-76)));k93=int(np.argmin(abs(z-93)))
   ok=valid[i,k76] and valid[i,k93] and min(speed[i,k76],speed[i,k93])>=screen
   row['direction_diff76_93_deg']=delta(direction[i,k76],direction[i,k93]) if ok else np.nan
   row['speed76_m_s']=float(speed[i,k76]) if valid[i,k76] else np.nan;row['speed93_m_s']=float(speed[i,k93]) if valid[i,k93] else np.nan
   row['diagnostic_diff59_93_deg']=delta(row['direction_60m_deg'],row['direction_100m_deg']) if np.isfinite(row['direction_60m_deg']) and np.isfinite(row['direction_100m_deg']) else np.nan
   lid.append(row)
lid=pd.DataFrame(lid);lid.to_csv(OUT/'LIDAR_all_date_event_wind_table.csv',index=False);pd.DataFrame(lowgates).to_csv(OUT/'LIDAR_gate_quality.csv',index=False);pd.DataFrame(cadence).to_csv(OUT/'LIDAR_native_cadence.csv',index=False)
daily=[]
for (date,screen),q in lid.groupby(['date','speed_screen']):
 a=q.direction_diff76_93_deg.dropna();time=pd.to_datetime(q.utc,format='mixed',utc=True);valid=a.notna()
 daily.append(dict(date=date,speed_screen=screen,n_profiles=len(q),n_valid_76_93=len(a),median_diff76_93=float(a.median()) if len(a) else np.nan,p90_diff76_93=float(a.quantile(.9)) if len(a) else np.nan,max_diff76_93=float(a.max()) if len(a) else np.nan,fraction_ge30=float((a>=30).mean()) if len(a) else np.nan,fraction_ge60=float((a>=60).mean()) if len(a) else np.nan,sampled_run_ge30_span_s=longest(time,(q.direction_diff76_93_deg>=30).to_numpy(),360),n_low_speed76=int((q.speed76_m_s<1).sum()),no_sub300_continuity_asserted=True))
pd.DataFrame(daily).to_csv(OUT/'LIDAR_daily_direction_statistics.csv',index=False)

# RAAVEN: derive a launch-ground reference with independent before/after checks.
ground=[];rw=[];flightstats=[];profiles=[]
for p in sorted((DATA/'B_WiscoDISCO21_RAAVEN/raw').glob('*.nc')):
 with xr.open_dataset(p,decode_times=False) as d:v={k:d[k].values.copy() for k in d.variables}
 time=pd.to_datetime(v['time'],unit='s',origin='2020-01-01',utc=True);sec=v['time'];a=v['alt'];flag=v['Flight_Flag'];ii=np.flatnonzero(flag==1);first=sec[ii[0]];last=sec[ii[-1]]
 presel=(flag==0)&(sec>=first-35)&(sec<first-5);postsel=(flag==0)&(sec>last+5)&(sec<=last+35)
 def anchor(mask):
  vals=a[mask];vals=vals[np.isfinite(vals)];return (float(np.median(vals)),float(np.percentile(vals,75)-np.percentile(vals,25)),len(vals)) if len(vals) else (np.nan,np.nan,0)
 pre=anchor(presel);post=anchor(postsel);both=pre[2]>=150 and post[2]>=150 and max(pre[1],post[1])<=2 and abs(pre[0]-post[0])<=5;postok=post[2]>=150 and post[1]<=2
 ground.append(dict(file=p.name,date=str(time[0].date()),pre_ground_msl=pre[0],post_ground_msl=post[0],pre_IQR=pre[1],post_IQR=post[1],pre_n=pre[2],post_n=post[2],reference_difference_m=post[0]-pre[0],reference_uncertainty_indicator_m=float(abs(pre[0]-post[0])/2+2) if both else np.nan,two_anchor_primary_accepted=bool(both),post_anchor_sensitivity_accepted=bool(postok),native_altitude_units='m MSL; no author AGL variable'))
 wf=(flag==1)&(v['wind_flag']==0)&np.isfinite(v['eastward_wind'])&np.isfinite(v['northward_wind'])
 flightstats.append(dict(file=p.name,date=str(time[0].date()),samples=len(sec),flight_samples=int((flag==1).sum()),good_wind_samples=int(wf.sum()),nominal_grid_dt_s=float(np.median(np.diff(sec))),two_anchor_primary=bool(both),post_anchor_sensitivity=bool(postok)))
 for policy,accepted,reference in [('two_anchor_primary',both,(pre[0]+post[0])/2),('post_anchor_sensitivity',postok,post[0])]:
  if not accepted:continue
  height=a-reference;window=time.floor('300s');u=v['eastward_wind'];n=v['northward_wind'];sp=np.hypot(u,n);temperature=v['air_temperature']-273.15;rh=v['relative_humidity'];pressure=v['air_pressure']
  for screen in [.1,.5,1.]:
   for start in pd.unique(window[(flag==1)&(height>=5)&(height<=125)]):
    sel=window==start;row=dict(platform='RAAVEN',file=p.name,date=str(start.date()),utc=str(start),height_policy=policy,ground_reference_msl=reference,speed_screen=screen,lake_breeze_layer_top_m=None)
    mean_times=[];dirs=[]
    for target,width in [(10,5),(30,5),(50,10),(60,10),(100,10)]:
     band=sel&(height>=target-width)&(height<=target+width)&wf&(sp>=screen);idx=np.flatnonzero(band);count=len(idx);good=count>=50
     winddir=(270-np.rad2deg(np.arctan2(n[idx],u[idx])))%360
     row[f'n_wind_{target}m']=count;row[f'direction_{target}m_deg']=circ(winddir) if good else np.nan;row[f'speed_{target}m_s']=float(np.hypot(u[idx].mean(),n[idx].mean())) if good else np.nan;row[f'actual_height_{target}m']=float(height[idx].mean()) if good else np.nan
     row[f'direction_resultant_R_{target}m']=float(abs(np.exp(1j*np.deg2rad(winddir)).mean())) if good else np.nan
     row[f'wind_sample_time_span_{target}m_s']=float(sec[idx[-1]]-sec[idx[0]]) if good else np.nan
     if target in [10,30,60,100] and good:dirs.append(row[f'direction_{target}m_deg']);mean_times.append(float(sec[idx].mean()))
     spatial=sel&(flag==1)&(height>=target-width)&(height<=target+width)
     tband=spatial&(v['air_temperature_flag']==0)&np.isfinite(temperature)
     rband=spatial&(v['relative_humidity_flag']==0)&np.isfinite(rh)&(rh>=0)&(rh<=100)
     thermalband=tband&rband&(v['air_pressure_flag']==0)&np.isfinite(pressure)&(pressure>800)&(pressure<1100)
     jj=np.flatnonzero(thermalband);ok=len(jj)>=50
     row[f'T_{target}m_C']=float(temperature[tband].mean()) if tband.sum()>=50 else np.nan;row[f'RH_{target}m_percent']=float(rh[rband].mean()) if rband.sum()>=50 else np.nan;row[f'q_{target}m_gkg']=float(humid(temperature[jj],rh[jj],pressure[jj]).mean()) if ok else np.nan
    row['max_requested_direction_diff_deg']=max(delta(x,y) for x,y in itertools.combinations(dirs,2)) if len(dirs)>=2 else np.nan
    row['n_requested_height_bins']=len(dirs);row['mean_height_sampling_time_gap_s']=max(mean_times)-min(mean_times) if len(mean_times)>=2 else np.nan
    row['direction_diff50_100_deg']=delta(row['direction_50m_deg'],row['direction_100m_deg']) if np.isfinite(row['direction_50m_deg']) and np.isfinite(row['direction_100m_deg']) else np.nan
    if any(row[f'n_wind_{h}m']>=50 for h in [10,30,50,60,100]):rw.append(row)
pd.DataFrame(ground).to_csv(OUT/'RAAVEN_ground_reference_QA.csv',index=False);pd.DataFrame(flightstats).to_csv(OUT/'RAAVEN_coverage_and_QC.csv',index=False);rw=pd.DataFrame(rw);rw.to_csv(OUT/'RAAVEN_300s_height_wind_thermo_table.csv',index=False)
rs=[]
for (date,policy,screen),q in rw.groupby(['date','height_policy','speed_screen']):
 arr=q.max_requested_direction_diff_deg.dropna();pair=q.direction_diff50_100_deg.dropna()
 rs.append(dict(date=date,height_policy=policy,speed_screen=screen,n_windows=len(q),n_with_two_requested_heights=len(arr),n_with_all4_heights=int((q.n_requested_height_bins==4).sum()),max_requested_diff=float(arr.max()) if len(arr) else np.nan,median_requested_diff=float(arr.median()) if len(arr) else np.nan,n_diff_ge30=int((arr>=30).sum()),n50_100=len(pair),median50_100=float(pair.median()) if len(pair) else np.nan,max50_100=float(pair.max()) if len(pair) else np.nan))
pd.DataFrame(rs).to_csv(OUT/'RAAVEN_daily_height_decoupling.csv',index=False)

# Requested event table: M210 thermal profile + nearest lidar column, not artificial10m winds.
event=[];strict=pd.DataFrame(thermal);strict=strict[strict.policy=='strict_flag0'];ls=lid[lid.speed_screen==.5].copy();ls['ts']=pd.to_datetime(ls.utc,format='mixed',utc=True)
for r in strict.itertuples():
 middle=pd.Timestamp(r.utc_start)+(pd.Timestamp(r.utc_end)-pd.Timestamp(r.utc_start))/2;dist=abs((ls.ts-middle).dt.total_seconds());j=dist.idxmin();near=ls.loc[j];match=dist.loc[j]<=180
 row=dict(event=r.file,date=r.date,thermal_start_UTC=r.utc_start,thermal_end_UTC=r.utc_end,thermal_n=r.n,lidar_profile_UTC=near.utc if match else None,lidar_match_gap_s=float(dist.loc[j]) if match else None,wind_10m_deg=None,wind_30m_deg=None,wind_60m_deg_unvalidated=near.direction_60m_deg if match else None,wind_100m_deg=near.direction_100m_deg if match else None,wind_100m_actual_gate=93,primary_max_diff76_93_deg=near.direction_diff76_93_deg if match else None,inversion10_100_C=getattr(r,'max_inversion10_100_C',None),inversion_bottom_m=getattr(r,'inversion_bottom_m',None),inversion_top_m=getattr(r,'inversion_top_m',None),inversion_pair_elapsed_s=getattr(r,'inversion_pair_elapsed_s',None),thermal_transition_proxy_m=getattr(r,'thermal_transition_proxy_m',None),inversion_layer_height_confirmed_m=None,lake_breeze_layer_height_m=None,platforms_spatially_separated=True)
 event.append(row)
pd.DataFrame(event).to_csv(OUT/'EVENT_UAV10_100_FEATURE_TABLE.csv',index=False)
effects= strict.groupby('date').agg(n_flights=('file','count'),n_usable=('max_inversion10_100_C','count'),median_inversion_C=('max_inversion10_100_C','median'),max_inversion_C=('max_inversion10_100_C','max'),median_vertical_Tcontrast_C=('upper_minus_lower_T_C','median'),median_vertical_RHcontrast_pp=('upper_minus_lower_RH_pp','median')).reset_index()
effects.to_csv(OUT/'M210_daily_thermal_statistics.csv',index=False)
checks={'raw_input_hashes_unchanged':all(sha(pathlib.Path(q['path']))==q['sha256'] for q in inp),'lidar_dates_match_files':True,'no_lidar10_30_wind_interpolation':bool(lid.direction_10m_deg.isna().all() and lid.direction_30m_deg.isna().all()),'no_lake_layer_height_invented':True,'raw_file_count':42,'M210_flights':24,'RAAVEN_flights':12,'lidar_dates':6,'no_new_simulation':True}
assert all(checks[k] for k in ['raw_input_hashes_unchanged','no_lidar10_30_wind_interpolation','no_lake_layer_height_invented'])
js('VALIDATION.json',checks)
print('All-file WiscoDISCO audit complete.');print(effects.to_string(index=False));print(pd.DataFrame(rs)[pd.DataFrame(rs).speed_screen==.5].to_string(index=False));print(pd.DataFrame(daily)[pd.DataFrame(daily).speed_screen==.5].to_string(index=False))
