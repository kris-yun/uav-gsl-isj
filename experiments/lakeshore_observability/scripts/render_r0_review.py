"""Presentation annotation only; does not change R0 data, windows or gate."""
import pathlib,pandas as pd,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=pathlib.Path(__file__).resolve().parents[3];OUT=ROOT/'evidence/lakeshore_observability_r0_r2'
v=pd.read_csv(OUT/'R0_wisco_profile_variability.csv');b=pd.read_csv(OUT/'R0_wisco_binned_profiles.csv');data=pathlib.Path(r'C:\work\LAKESHORE_GSL_DATA_20261002\data_external\B_WiscoDISCO21_M210\raw')
fig,axs=plt.subplots(1,3,figsize=(12,5),layout='constrained')
windows={'PRE':(17,18),'TRANSITION':(18.5,19),'POST21':(20.75,21.25),'POST22':(21.75,22.25)}
for window in windows:
 q=v[v.window==window].merge(b[b.window==window].groupby('bin_low_m').height_m.mean(),on='bin_low_m');good=q.height_m>=75
 for a,column in zip(axs[:2],['wind_speed_mean_m_s','wind_direction_circular_mean_deg']):
  line=a.plot(q.loc[good,column],q.loc[good,'height_m'],label=window)[0]
  a.plot(q[column],q.height_m,':',color=line.get_color(),alpha=.5)
for p in sorted(data.glob('*20210522*')):
 d=pd.read_csv(p);h=pd.to_timedelta(d.TimeUTC).dt.total_seconds()/3600
 for window,(a,b) in windows.items():
  q=d[(h>=a)&(h<b)&(d.iMetFlag==0)]
  if len(q):axs[2].plot(q.Temperature_Average_degC,q.Altitude_Average_magl,'o-',label=window)
for a in axs[:2]:
 a.axhspan(0,75,color='grey',alpha=.12);a.text(.02,.02,'Weak low gates: not primary evidence',transform=a.transAxes,fontsize=8);a.set_ylim(0,300)
axs[2].set_ylim(0,150)
for a,label in zip(axs,['Wind speed (m/s)','Wind direction (deg, circular)','Temperature (C)']):a.set_xlabel(label);a.set_ylabel('Height AGL (m)');a.grid(alpha=.2);a.legend(fontsize=8)
fig.savefig(OUT/'R0_wisco_profiles.png',dpi=150);plt.close(fig)
