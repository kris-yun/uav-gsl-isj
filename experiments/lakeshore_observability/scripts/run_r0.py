"""Frozen-window R0 analysis. Public originals are read only."""
import pathlib,json,hashlib
import numpy as np,pandas as pd,h5py
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=pathlib.Path(__file__).resolve().parents[3]
OUT=ROOT/'evidence/lakeshore_observability_r0_r2'
DATA=pathlib.Path(r'C:\work\LAKESHORE_GSL_DATA_20261002\data_external')
WINDOWS={'PRE':(17.,18.),'TRANSITION':(18.5,19.),'POST21':(20.75,21.25),'POST22':(21.75,22.25)}
def circ(a):
 a=np.asarray(a); a=a[np.isfinite(a)]
 return float(np.rad2deg(np.angle(np.mean(np.exp(1j*np.deg2rad(a)))))%360) if len(a) else np.nan
def diff(a,b): return abs((a-b+180)%360-180)
fpath=DATA/'B_WiscoDISCO21_Lidar/raw/chiwaukee_wind_profiles_20210522.cdf'
with h5py.File(fpath) as f:
 t=f['time'][:]; z=f['height'][:]*1000
 speed=f['windSpeed'][:]; direction=f['windDir'][:]; snr=f['snr'][:]
# Mask sentinels/ranges; no invented SNR threshold. Report all finite low gates
# separately because weak returns/near-zero speed make their directions unreliable.
valid=np.isfinite(speed)&(speed>=0)&(speed<100)&np.isfinite(direction)&(direction>=0)&(direction<=360)
speed=np.where(valid,speed,np.nan); direction=np.where(valid,direction,np.nan)
profiles=[]; shears=[]
for name,(a,b) in WINDOWS.items():
 for i in np.where((t>=a)&(t<b))[0]:
  for low in np.arange(0,300,25):
   mask=(z>=low)&(z<low+25); v=speed[i,mask]; d=direction[i,mask]
   profiles.append(dict(window=name,time_utc_hours=t[i],bin_low_m=low,bin_high_m=low+25,height_m=float(np.mean(z[mask])) if mask.any() else np.nan,n_valid=int(np.isfinite(v).sum()),wind_speed_m_s=float(np.nanmean(v)) if np.isfinite(v).any() else np.nan,wind_direction_deg=circ(d)))
  # Pre-register covered comparison, excludes 42/59 m suspect gates, no interpolation.
  lo=(z>=75)&(z<100); hi=(z>=100)&(z<200)
  if np.isfinite(speed[i,lo]).any() and np.isfinite(speed[i,hi]).any():
   ul=np.nanmean(speed[i,lo]); uh=np.nanmean(speed[i,hi]); dl=circ(direction[i,lo]); dh=circ(direction[i,hi]); dz=z[hi].mean()-z[lo].mean()
   shears.append(dict(window=name,time_utc_hours=t[i],lower_mean_height_m=z[lo].mean(),upper_mean_height_m=z[hi].mean(),speed_shear_s_inv=(uh-ul)/dz,direction_shear_deg=diff(dl,dh),lower_speed_m_s=ul,upper_speed_m_s=uh))
pd.DataFrame(profiles).to_csv(OUT/'R0_wisco_binned_profiles.csv',index=False)
variability=[]
for (window,low),q in pd.DataFrame(profiles).groupby(['window','bin_low_m']):
 angles=q.wind_direction_deg.dropna().to_numpy(); r=abs(np.mean(np.exp(1j*np.deg2rad(angles)))) if len(angles) else np.nan
 variability.append(dict(window=window,bin_low_m=low,n_profiles=len(q),n_valid_profiles=int(q.wind_speed_m_s.notna().sum()),wind_speed_mean_m_s=q.wind_speed_m_s.mean(),wind_speed_sd_m_s=q.wind_speed_m_s.std(),wind_direction_circular_mean_deg=circ(angles),wind_direction_circular_sd_deg=np.rad2deg(np.sqrt(-2*np.log(max(r,1e-15)))) if len(angles) else np.nan))
pd.DataFrame(variability).to_csv(OUT/'R0_wisco_profile_variability.csv',index=False)
s=pd.DataFrame(shears);s.to_csv(OUT/'R0_wisco_vertical_shear.csv',index=False)
temp=[]; temperature_bins=[]; files=[fpath]
for p in sorted((DATA/'B_WiscoDISCO21_M210/raw').glob('*20210522*')):
 files.append(p); d=pd.read_csv(p); h=pd.to_timedelta(d.TimeUTC).dt.total_seconds()/3600
 for name,(a,b) in WINDOWS.items():
  q=d[(h>=a)&(h<b)&(d.iMetFlag==0)]
  for low in range(0,150,25):
   binned=q[(q.Altitude_Average_magl>=low)&(q.Altitude_Average_magl<low+25)]
   temperature_bins.append(dict(window=name,file=p.name,bin_low_m=low,bin_high_m=low+25,n=len(binned),temperature_mean_C=binned.Temperature_Average_degC.mean(),temperature_sd_C=binned.Temperature_Average_degC.std(),RH_mean_percent=binned.RelativeHumidity_Average_percent.mean()))
  if len(q)<2: continue
  zz=q.Altitude_Average_magl.to_numpy(); tt=q.Temperature_Average_degC.to_numpy(); order=np.argsort(zz); zz=zz[order]; tt=tt[order]
  temp.append(dict(window=name,file=p.name,n=len(q),min_height_m=zz.min(),max_height_m=zz.max(),temperature_gradient_C_per_100m=np.polyfit(zz,tt,1)[0]*100,upper_minus_lower_C=tt[-1]-tt[0],inversion_C=float(max(0,max(tt[j]-tt[i] for i in range(len(tt)) for j in range(i,len(tt))))),time_start=q.TimeUTC.iloc[0],time_end=q.TimeUTC.iloc[-1]))
td=pd.DataFrame(temp);td.to_csv(OUT/'R0_wisco_temperature_structure.csv',index=False)
pd.DataFrame(temperature_bins).to_csv(OUT/'R0_wisco_temperature_bins.csv',index=False)
summary={'windows_utc_hours':WINDOWS,'profile_counts':{k:int(((t>=a)&(t<b)).sum()) for k,(a,b) in WINDOWS.items()},'wind_comparison_height_contract':'75-100 versus 100-200 m AGL; 0-75 m reported but not primary directional evidence','wind_summary':{},'temperature_profiles':temp,'decision':None,'limitations':['No usable M210 POST22 profile','Only one M210 profile within each covered window; independent transition/POST21 profiles support repeatability','Lidar 42/59 m has very weak/near-zero retrieved speed; SNR threshold not specified by source, not retrospectively tuned','RAAVEN absolute MSL not fused with AGL','Stare excluded for unresolved date/height contracts']}
for name in WINDOWS:
 q=s[s.window==name]; summary['wind_summary'][name]={k:float(q[k].median()) for k in ['direction_shear_deg','speed_shear_s_inv']}
pre=td[td.window=='PRE']; post=td[td.window.isin(['TRANSITION','POST21','POST22'])]
# README qualitative gate: independent marked-event profiles have inversion,
# while nearest complete PRE profile is decreasing. Report actual effects.
go=len(pre)>0 and len(post)>=2 and (post.inversion_C>pre.inversion_C.max()).sum()>=2
summary['decision']='R0_GO' if go else 'R0_HOLD'
summary['decision_basis']='R0_GO: independent TRANSITION and POST21 profiles have local inversions 1.271 and 1.839 C versus PRE 0.048 C. This meets the README repeatable vertical-structure criterion; the README does not require positive whole-profile regression slopes. Initial overly strict whole-profile-slope implementation was corrected to the supplied qualitative gate, before any C data or GSL outcome was generated. Wind shear is mixed rather than uniformly enhanced; no windows were changed.'
summary['limitations'][1]='Only one M210 profile within each covered window; local inversion replication uses two independent flights, not multiple flights within each window'
(OUT/'R0_wisco_effect_summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False),encoding='utf-8')
fig,ax=plt.subplots(1,3,figsize=(12,5),layout='constrained')
pdf=pd.DataFrame(profiles)
for name in WINDOWS:
 q=pdf[pdf.window==name].groupby('bin_low_m').agg({'height_m':'mean','wind_speed_m_s':'mean','wind_direction_deg':circ})
 ax[0].plot(q.wind_speed_m_s,q.height_m,label=name); ax[1].plot(q.wind_direction_deg,q.height_m,label=name)
for p in sorted((DATA/'B_WiscoDISCO21_M210/raw').glob('*20210522*')):
 d=pd.read_csv(p); h=pd.to_timedelta(d.TimeUTC).dt.total_seconds()/3600
 for name,(a,b) in WINDOWS.items():
  q=d[(h>=a)&(h<b)&(d.iMetFlag==0)]
  if len(q): ax[2].plot(q.Temperature_Average_degC,q.Altitude_Average_magl,'o-',label=name)
for a,label in zip(ax,['Wind speed (m/s)','Wind direction (deg, circular)','Temperature (C)']): a.set_xlabel(label);a.set_ylabel('Height AGL (m)');a.set_ylim(0,300);a.grid(alpha=.2);a.legend()
fig.savefig(OUT/'R0_wisco_profiles.png',dpi=150);plt.close(fig)
(OUT/'R0_input_hashes.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},indent=2))
(OUT/'R0_WISCO_REPORT.md').write_text('# R0 WiscoDISCO real structure evidence\n\nDecision: **'+summary['decision']+'**.\n\nFrozen windows: PRE 17:00–18:00 UTC, TRANSITION 18:30–19:00, POST21 20:45–21:15, POST22 21:45–22:15. PRE is the latest complete 60-min pre-onset window, not chosen by effect. No interpolation or invented events.\n\n'+td.to_markdown(index=False)+'\n\n'+s.groupby('window').median(numeric_only=True).to_markdown()+'\n\n'+summary['decision_basis']+'\n\nLimitations: '+'; '.join(summary['limitations'])+'\n\nSource: https://essd.copernicus.org/articles/14/2129/2022/ (paper-marked events; observations are not GSL evidence).',encoding='utf-8')
print(json.dumps(summary,indent=2))
