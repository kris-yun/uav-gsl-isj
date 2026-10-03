"""Real fixed-path, source-blind Bayesian grid STE (published forward/log likelihood).

No source coordinate is read until after every posterior has been computed.
This is a conditional-wind baseline, not reproduction of the unpublished field PF.
"""
from pathlib import Path
import sys, json, hashlib, subprocess, platform, argparse
import numpy as np
import pandas as pd
from scipy.special import logsumexp
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(r'C:\work\SVALBARD_BOREHOLE_REAL_DATA_20261003')
sys.path.insert(0,str(ROOT/'dependencies'))
from pyproj import Transformer
REPO=Path(r'C:\work\LAKESHORE_OBSERVABILITY_EXEC_20261003')
OUT=REPO/'evidence/public_data_first_20261003/van_hove'
parser=argparse.ArgumentParser()
parser.add_argument('--background',type=float,default=2.09)
parser.add_argument('--sigma',type=float,default=.15)
parser.add_argument('--sensitivity-label',default='')
args=parser.parse_args()
if args.sensitivity_label: OUT=OUT/'sensitivity'/args.sensitivity_label
OUT.mkdir(parents=True,exist_ok=True)
raw=ROOT/'raw/active'
manifest=[]
tracked=subprocess.check_output(['git','-C',str(raw),'ls-files','-z']).decode().strip('\0').split('\0')
for rel in sorted(tracked):
    p=raw/rel
    content=p.read_bytes()
    manifest.append(dict(path=str(p.relative_to(ROOT)).replace('\\','/'),bytes=len(content),md5=hashlib.md5(content).hexdigest(),sha256=hashlib.sha256(content).hexdigest()))
pd.DataFrame(manifest).to_csv(OUT/'RAW_MANIFEST.csv',index=False)
commit=subprocess.check_output(['git','-C',str(raw),'rev-parse','HEAD'],text=True).strip()
cfg=dict(code_commit=commit,source_input=False,method='conditional-wind Bayesian grid STE; publisher Vergassola mirror forward model and log-concentration Gaussian likelihood',grid_spacing_m=2.5,domain='observed GPS rectangular envelope plus 30m on all four sides',Q_g_per_h=np.linspace(0,10000,81).tolist(),Q_prior='uniform discrete quadrature 0..10000 g/h',xy_prior='uniform rectangular cell prior',diffusivity_m2_s=1,background_ppm=2.09,log_sigma=.15,T_K=273.95,P_Pa=102000,tau_s=286977600,resample_seconds=10,altitude='OSD.vpsHeight [m] as publisher step 05',missing='complete-case per 1s then mean 10s bin; never impute gas',wind_variants=['flight_mean_vector','current_local_vector','height_mean_vector','publisher_angle_as_written'],limitations=['conditional wind (V,Phi not jointly inferred)','fixed log error from pinned prereview config','Q bound broader than stale 0..1000 g/h nature config; frozen before inference','no blind search: source-informed field route','phase is height/time block not independent atmospheric realization'],python=platform.python_version())
(OUT/'FROZEN_CONFIG.json').write_text(json.dumps(cfg,indent=2))
cfg['background_ppm']=args.background;cfg['log_sigma']=args.sigma
if args.sensitivity_label:
    cfg['wind_variants']=['flight_mean_vector','current_local_vector']
(OUT/'FROZEN_CONFIG.json').write_text(json.dumps(cfg,indent=2))
d=pd.read_csv(ROOT/'processed/07_df.csv',index_col='datetime',parse_dates=True)
d.index=pd.to_datetime(d.index,utc=True,format='ISO8601')
d=d[d.flight_phase>0].copy()
transform=Transformer.from_crs('EPSG:4326','EPSG:25833',always_xy=True)
E,N=transform.transform(d['OSD.longitude'].values,d['OSD.latitude'].values)
# Crucially, origin depends only on receptor GPS, never the borehole truth.
origin=np.array([np.median(E),np.median(N)])
d['east_m']=E-origin[0];d['north_m']=N-origin[1]
fields=['east_m','north_m','z','AERIS.CH4 [ppm]','U_corrected','V_corrected','windspeed_corrected','winddirection_corrected']
valid=d.dropna(subset=fields).copy();valid=valid[valid['AERIS.CH4 [ppm]']>0]
summary=[]; blocks=[]
for phase in (1,2,3):
    dd=valid[valid.flight_phase==phase]
    b=dd[fields].resample('10s').mean().dropna()
    ang=dd.winddirection_corrected.resample('10s').apply(lambda a:np.rad2deg(np.arctan2(np.sin(np.deg2rad(a)).mean(),np.cos(np.deg2rad(a)).mean()))%360)
    b['winddirection_corrected']=ang.loc[b.index];b['phase']=phase
    blocks.append(b)
    summary.append(dict(phase=phase,nominal_altitude_m=2*phase,rows_1s=len(d[d.flight_phase==phase]),gas_nonmissing=int(d[d.flight_phase==phase]['AERIS.CH4 [ppm]'].notna().sum()),complete_rows_1s=len(dd),rows_10s=len(b),start_utc=str(dd.index.min()),end_utc=str(dd.index.max()),mean_east_wind=float(dd.U_corrected.mean()),mean_north_wind=float(dd.V_corrected.mean()),mean_scalar_speed=float(dd.windspeed_corrected.mean()),vector_mean_speed=float(np.hypot(dd.U_corrected.mean(),dd.V_corrected.mean())),gas_max_ppm=float(dd['AERIS.CH4 [ppm]'].max()),gas_median_ppm=float(dd['AERIS.CH4 [ppm]'].median())))
obs=pd.concat(blocks).sort_index()
obs.to_csv(OUT/'REAL_FIELD_OBSERVATIONS_10S.csv')
pd.DataFrame(summary).to_csv(OUT/'FLIGHT_PHASE_SUMMARY.csv',index=False)
# Frame QA: the author's x=-north,y=east and advection (cos(phi),-sin(phi)).
ph=np.deg2rad(valid.winddirection_corrected.values)
code_e=-valid.windspeed_corrected.values*np.sin(ph)
code_n=-valid.windspeed_corrected.values*np.cos(ph)
frame=dict(expected_velocity='east=U_corrected,north=V_corrected',publisher_implied_velocity='east=-speed*sin(phi),north=-speed*cos(phi)',east_error_rms=float(np.sqrt(np.mean((code_e-valid.U_corrected.values)**2))),north_error_rms=float(np.sqrt(np.mean((code_n-valid.V_corrected.values)**2))),east_sign_flip_max_residual=float(np.max(np.abs(code_e+valid.U_corrected.values))),north_sign_preserved_max_residual=float(np.max(np.abs(code_n-valid.V_corrected.values))),claim='algebraic contract discrepancy, not an established atmosphere failure mechanism')
(OUT/'WIND_FRAME_QA.json').write_text(json.dumps(frame,indent=2))
xs=np.arange(np.floor(obs.east_m.min()/2.5)*2.5-30,np.ceil(obs.east_m.max()/2.5)*2.5+30.1,2.5)
ys=np.arange(np.floor(obs.north_m.min()/2.5)*2.5-30,np.ceil(obs.north_m.max()/2.5)*2.5+30.1,2.5)
gx,gy=np.meshgrid(xs,ys); candidates=np.column_stack([gx.ravel(),gy.ravel()]);Q=np.array(cfg['Q_g_per_h'])
conversion=8.314*273.95/(102000*16.04)*1e6/3600
results=[];pending=[]
for phase in (1,2,3,0):
    b=obs if phase==0 else obs[obs.phase==phase]
    for variant in cfg['wind_variants']:
        U=b.U_corrected.values.copy();V=b.V_corrected.values.copy()
        if variant=='flight_mean_vector': U[:]=U.mean();V[:]=V.mean()
        elif variant=='height_mean_vector':
            for p in b.phase.unique():
                take=b.phase.values==p;U[take]=U[take].mean();V[take]=V[take].mean()
        elif variant=='publisher_angle_as_written':
            # Keep the publisher scalar-direction convention literally.
            a=np.deg2rad(b.winddirection_corrected.values)
            U=-b.windspeed_corrected.values*np.sin(a);V=-b.windspeed_corrected.values*np.cos(a)
        speed=np.hypot(U,V)
        x=b.east_m.values;y=b.north_m.values;z=b.z.values;target=np.log(b['AERIS.CH4 [ppm]'].values)
        evidence=np.empty(len(candidates));bestQ=np.empty(len(candidates));minnll=np.empty(len(candidates))
        for start in range(0,len(candidates),192):
            s=candidates[start:start+192]
            dx=x[None,:]-s[:,0,None];dy=y[None,:]-s[:,1,None]
            distance=np.sqrt(dx*dx+dy*dy+z[None,:]**2)
            exponent=-distance*np.sqrt(1/cfg['tau_s']+speed[None,:]**2/4)+(dx*U+dy*V)/2
            unit=2*conversion/(4*np.pi*np.maximum(distance,.1))*np.exp(np.clip(exponent,-745,20))
            pred=cfg['background_ppm']+unit[:,:,None]*Q[None,None,:]
            nll=.5*np.sum(((target[None,:,None]-np.log(pred))/cfg['log_sigma'])**2,axis=1)
            evidence[start:start+len(s)]=logsumexp(-nll,axis=1)-np.log(len(Q))
            bestQ[start:start+len(s)]=Q[nll.argmin(axis=1)]
            minnll[start:start+len(s)]=nll.min(axis=1)
        p=np.exp(evidence-logsumexp(evidence));i=np.argmax(p)
        mean=p@candidates;area95=int(np.searchsorted(np.cumsum(np.sort(p)[::-1]),.95)+1)*6.25
        row=dict(phase=phase,wind=variant,n_observations=len(b),MAP_east_m=float(candidates[i,0]),MAP_north_m=float(candidates[i,1]),mean_east_m=float(mean[0]),mean_north_m=float(mean[1]),Q_MAP_g_per_h=float(bestQ[i]),area95_m2=area95,boundary_probability=float(p[(candidates[:,0]==xs.min())|(candidates[:,0]==xs.max())|(candidates[:,1]==ys.min())|(candidates[:,1]==ys.max())].sum()),minimum_nll=float(minnll.min()))
        results.append(row);pending.append((phase,variant,p))
        np.savez_compressed(OUT/f'posterior_phase{phase}_{variant}.npz',source_east_m=candidates[:,0],source_north_m=candidates[:,1],probability=p,Q_MAP_g_per_h=bestQ)
        print(json.dumps(row),flush=True)
# Freeze inversion output before retrieving evaluation truth from the publisher file.
(OUT/'INVERSION_BEFORE_TRUTH.json').write_text(json.dumps(dict(origin_utm=origin.tolist(),results=results),indent=2))
text=(raw/'nature_run/preprocess_drone_data/05_coordinate_system.py').read_text()
import re
truth_lat=float(re.search(r"'lat':\s*([\d.]+)",text).group(1));truth_lon=float(re.search(r"'lon':\s*([\d.]+)",text).group(1))
truth=np.array(transform.transform(truth_lon,truth_lat))-origin
for row in results:
    row['MAP_localization_error_m']=float(np.linalg.norm(np.array([row['MAP_east_m'],row['MAP_north_m']])-truth))
    row['posterior_mean_localization_error_m']=float(np.linalg.norm(np.array([row['mean_east_m'],row['mean_north_m']])-truth))
pd.DataFrame(results).to_csv(OUT/'SOURCE_INVERSION_RESULTS.csv',index=False)
fig,axes=plt.subplots(3,4,figsize=(16,11),sharex=True,sharey=True)
for phase,variant,p in pending:
    if phase==0:continue
    ax=axes[phase-1,cfg['wind_variants'].index(variant)]
    mesh=ax.pcolormesh(xs,ys,p.reshape(gx.shape)/p.max(),shading='auto',vmin=0,vmax=1);ax.plot(truth[0],truth[1],'r+',markersize=11)
    row=next(r for r in results if r['phase']==phase and r['wind']==variant)
    label=f'error={row["MAP_localization_error_m"]:.1f}m' if phase!=3 else 'Diffuse; unreliable location'
    ax.set_title(f'{phase*2}m {variant}\n{label}')
    ax.set_xlabel('East relative GPS median (m)');ax.set_ylabel('North (m)')
fig.tight_layout();fig.subplots_adjust(right=.92)
cb=fig.add_axes([.94,.15,.012,.65]);fig.colorbar(mesh,cax=cb,label='Posterior relative to panel maximum')
fig.savefig(OUT/'POSTERIOR_COMPARISON.png',dpi=130);plt.close(fig)
qual=dict(dataset='Svalbard borehole 2025 / van Hove 2026',decision='SVALBARD_GO_FIXED_PATH_POINT_SOURCE_WITH_LIMITATIONS',source_truth='explicit approximate point coordinate in official step 05, horizontal precision not separately quantified',source_lat=truth_lat,source_lon=truth_lon,source_type='geological CH4, legacy coal borehole leak; operators drilled five shallow ice holes (intervened natural-gas release)',scene='open Arctic Adventdalen valley, legacy borehole, ice/snow',flight_count_remote_control_files=4,usable_lawnmower_height_phases=3,independent_repeats='three sequential altitude phases, one site/date; not independent seeds or days',route='preplanned lawnmower surrounding already known borehole, source-informed; no blind-search validity',gas='AERIS MIRA Strato LDS 1 Hz; gas response/lag correction not explicitly in preprocessing',wind='Trisonica Sphere 20 Hz, publisher 1s averages; full attitude rotation and UAV velocity correction; preserve east/north frame issue QA',ground_wind='none in public active/drone_data',sync='remote Europe/Oslo→UTC; methane GPS Unix seconds UTC; sonic fixed -2h18m calibrated against pitch/roll; exact 1s merge, then10s averages',localization_metric='horizontal error valid against explicit publisher coordinate, uncertainty in ground-truth survey not supplied; conditional model exploratory',plume_metric='observed route plume concentration/path support available; no complete 3D plume truth',license='GPL-3.0 code repository; paper CC BY; no separate raw-data license text',public_code='8-step field preprocessing; source-fixed calibration scripts import absent bayesian_inference_github; core Bayesian RL code present',doi='10.1017/eds.2026.10029',download='https://github.com/AlouetteUiO/active',code_commit=commit,raw_total_bytes=sum(r['bytes'] for r in manifest),raw_file_count=len(manifest),truth_for_evaluation_only=True,source='https://www.cambridge.org/core/journals/environmental-data-science/article/actively-inferring-methane-sources-with-drones/B9636E970B3888E7503464A41633719E')
(OUT/'QUALIFICATION.json').write_text(json.dumps(qual,ensure_ascii=False,indent=2),encoding='utf8')
