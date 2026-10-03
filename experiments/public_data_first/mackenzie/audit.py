"""Portable author-GPI reproduction and explicitly conditional, truth-blind inversion.

This is a diagnostic Gaussian model, not a reconstruction of upstream wind.
No source coordinate enters the inverse domain, observations, priors or fits.
"""
import ast, hashlib, json, sys, shutil, argparse
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import least_squares
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(r'C:\work\MACKENZIE_CHANNEL_SEEP2_REAL_DATA_20261003')
REPO=Path(__file__).resolve().parents[3]
OUT=REPO/'evidence/public_data_first_20261003/mackenzie'
sys.path.insert(0,str(ROOT/'tools/python_deps'))
from pyproj import Transformer
TRANSFORM=Transformer.from_crs(4326,32608,always_xy=True)
CONFIG=dict(domain='GPS envelope in mean-wind axes; source 10..400 m upwind of minimum observation x; y within observed envelope',
            nx=31,ny=31,tau_y=[.04,.10,.25],tau_z=[.025,.075,.20],source_height_m=0,
            arms=['flight_mean','uav_current_local','height_dependent'],
            primary_background_ppm={'CP':2.031797,'OP':2.064857},
            paper_background_sensitivity_ppm={'CP':2.0318,'OP':2.0291},
            CP_north_offset_deg=19,spatial_thinning='CP every 2 rows (2 Hz); OP means by published integer TimeStamp; not cross-platform synchronization',
            objective='Gaussian concentration least squares; nonnegative Q profiled; same Q and dispersion for paired curtains',
            uncertainty='profile RSS <= 1.05 * minimum RSS support extent; diagnostic, NOT posterior credible interval',
            ground_arm='UNAVAILABLE_NO_PUBLISHED_GROUND_TIME_SERIES',
            no_truth_in_fitting=True)

def wind(speed,direction):
    a=np.deg2rad(direction);return -speed*np.sin(a),-speed*np.cos(a)

def kernel(dx,dy,z,u,v,ty,tz):
    s=np.maximum(np.hypot(u,v),.2)
    x=(dx*u+dy*v)/s;y=(-dx*v+dy*u)/s
    xx=np.maximum(x,1.)
    sy=ty*xx;sz=tz*xx
    k=np.exp(-y*y/(2*sy*sy)-z*z/(2*sz*sz))/(np.pi*sy*sz*s)
    return np.where(x>1,k,0)

def author_model(X,ty,tz,Q,y0,h):
    x,y,z=X.T;sy=ty*x;sz=tz*x
    return Q/(2*np.pi*sy*sz)*np.exp(-(y-y0)**2/(2*sy*sy))*(np.exp(-(z-h)**2/(2*sz*sz))+np.exp(-(z+h)**2/(2*sz*sz)))

def prepare():
    frames={};inventory=[]
    for file in sorted((ROOT/'author_code_and_data/Data').glob('*.csv')):
        raw=pd.read_csv(file);name=file.stem;cp=name.startswith('CP')
        lon=raw.Long if cp else raw.longitude;lat=raw.Lat if cp else raw.latitude
        e,n=TRANSFORM.transform(lon.to_numpy(),lat.to_numpy())
        s=raw.WS_corr if cp else raw.w_speed;di=(raw.WD_corr+19)%360 if cp else raw.w_dir
        u,v=wind(s,di)
        d=pd.DataFrame(dict(e=e,n=n,z=raw.Alt_smooth if cp else raw.altitude,
                            ch4=raw.CH4/1000 if cp else raw.CH4,u=u,v=v))
        d['row_group']=np.arange(len(d))//2 if cp else raw.TimeStamp
        d=d.groupby('row_group',sort=False).mean().reset_index(drop=True)
        d.to_csv(OUT/f'{name}_processed.csv',index=False)
        frames[name]=d
        inventory.append(dict(flight=name,original_rows=len(raw),processed_rows=len(d),
                              platform='UAV-MPI CP' if cp else 'UAV-NRCan OP',
                              corrected_wind_speed_mean_m_s=float(s.mean()),
                              corrected_wind_direction_mean_deg=float(di.mean()),
                              height_min_m=float(d.z.min()),height_max_m=float(d.z.max()),
                              CH4_max_ppm=float((raw.CH4/1000 if cp else raw.CH4).max()),
                              published_rate_hz=2 if cp else 10,
                              sensor_nominal_rate_hz=2 if cp else 100,
                              clock_contract='CP1 unzoned full datetime; CP2 mm:ss truncated' if cp else 'integer POSIX plus Excel serial day TIME_UTC; do not assume UTC labeling proves alignment',
                              wind_dimensions='2D corrected horizontal; CP VertWind ancillary, not a verified 3D wind contract',
                              ground_time_series_available=False))
    pd.DataFrame(inventory).to_csv(OUT/'FLIGHT_INVENTORY.csv',index=False)
    return frames

def reproduce(frames):
    # Known source is used ONLY here, to reproduce the author's fixed-source flux fit.
    se,sn=TRANSFORM.transform(-135.477520,69.319583);angle=188.54163351823857
    a=np.deg2rad(angle);rows=[]
    code=ROOT/'author_code_and_data/GPI/GPI_NF.py'
    tree=ast.parse(code.read_text(encoding='utf8'))
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='gaussian_inversion_NF_3d')
    ns={'np':np};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(code),'exec'),ns)
    sample=np.array([[100.,2.,3.],[150.,4.,6.]])
    err=np.max(abs(author_model(sample,.1,.12,4000,1,0)-ns[fn.name](sample,.1,.12,4000,1,0)))
    assert err<1e-12
    for name,d in frames.items():
        # Direct UTM rotation is exactly the composition in Prep_Curtains.py.
        e=d.e.to_numpy()-se;n=d.n.to_numpy()-sn
        x=-np.sin(a)*e-np.cos(a)*n;y=np.cos(a)*e-np.sin(a)*n
        X=np.column_stack([x,y,d.z]);rho=(101987-12.26*d.z)*.01604/(292.4627*8.31446261815324)
        wd=np.rad2deg(np.arctan2(-d.u,-d.v))%360
        qme=(d.ch4-CONFIG['primary_background_ppm'][name[:2]])*np.hypot(d.u,d.v)*np.cos(np.deg2rad(wd-angle))*rho
        res=least_squares(lambda p:author_model(X,*p,0)-qme,[.1,.1,4000,0],
                          bounds=([.001,.001,0,float(y.min())],[1,1,1e6,float(y.max())]),max_nfev=2000,x_scale='jac')
        qmo=author_model(X,*res.x,0);delta=res.x[2]*np.sqrt(np.sum((qme-qmo)**2)/np.sum(qme**2))
        rows.append(dict(flight=name,tau_y=res.x[0],tau_z=res.x[1],Q_mg_s=res.x[2],y0_m=res.x[3],
                         residual_flux_fraction=float(delta/max(res.x[2],1e-20)),Q_delta_mg_s=delta,
                         median_distance_m=float(np.median(x)),author_kernel_max_difference=float(err),
                         reproduction='same forward/coordinates/background/density; scipy solver, 1s reduction; NOT unknown-source localization'))
    pd.DataFrame(rows).to_csv(OUT/'AUTHOR_FIXED_SOURCE_GPI_REPRODUCTION.csv',index=False)

def inverse_inputs(frames,names):
    d=pd.concat([frames[n].assign(flight=n) for n in names],ignore_index=True)
    origin=np.array([d.e.mean(),d.n.mean()])
    # Frame and source domain derive solely from observed GPS and vectors.
    ue,un=d.u.mean(),d.v.mean();direction=np.array([ue,un]);direction/=np.linalg.norm(direction)
    cross=np.array([-direction[1],direction[0]])
    xy=d[['e','n']].to_numpy()-origin
    x=xy@direction;y=xy@cross
    gx=np.linspace(x.min()-400,x.min()-10,CONFIG['nx']);gy=np.linspace(y.min(),y.max(),CONFIG['ny'])
    xx,yy=np.meshgrid(gx,gy,indexing='ij')
    sources=origin+xx.ravel()[:,None]*direction+yy.ravel()[:,None]*cross
    return d,sources,xx,yy

def fit_case(frames,names,arm,bglabel):
    d,sources,xx,yy=inverse_inputs(frames,names)
    u=d.u.to_numpy().copy();v=d.v.to_numpy().copy()
    for name in names:
        m=(d.flight==name).to_numpy()
        if arm=='flight_mean':u[m]=u[m].mean();v[m]=v[m].mean()
        elif arm=='height_dependent':
            z=d.z.to_numpy()[m];A=np.column_stack([np.ones(m.sum()),z-z.mean()])
            u[m]=A@np.linalg.lstsq(A,u[m],rcond=None)[0];v[m]=A@np.linalg.lstsq(A,v[m],rcond=None)[0]
    bg=CONFIG['primary_background_ppm'] if bglabel=='author_code' else CONFIG['paper_background_sensitivity_ppm']
    rho=(101987-12.26*d.z.to_numpy())*.01604/(292.4627*8.31446261815324)
    measured=(d.ch4.to_numpy()-np.array([bg[n[:2]] for n in d.flight]))*rho
    # Equal total weights for each curtain, preserving negative background residuals.
    weights=np.array([1/sum(d.flight==n) for n in d.flight]);weighted=measured*weights
    dx=d.e.to_numpy()[None,:]-sources[:,0,None];dy=d.n.to_numpy()[None,:]-sources[:,1,None]
    best=np.full(len(sources),np.inf);qs=np.zeros(len(sources));tys=qs.copy();tzs=qs.copy()
    for ty in CONFIG['tau_y']:
        for tz in CONFIG['tau_z']:
            k=kernel(dx,dy,d.z.to_numpy()[None,:],u[None,:],v[None,:],ty,tz)
            denom=(k*k)@weights;num=k@weighted;q=np.maximum(0,num/np.maximum(denom,1e-30))
            rss=np.sum(weights*measured**2)-2*q*num+q*q*denom
            better=rss<best;best[better]=rss[better];qs[better]=q[better];tys[better]=ty;tzs[better]=tz
    idx=int(best.argmin());support=best<=best[idx]*1.05
    span=np.ptp(sources[support],axis=0) if support.sum()>1 else np.zeros(2)
    edge=(idx//CONFIG['ny'] in [0,CONFIG['nx']-1] or idx%CONFIG['ny'] in [0,CONFIG['ny']-1])
    row=dict(case='+'.join(names),wind_arm=arm,background=bglabel,source_easting_MAP_m=sources[idx,0],source_northing_MAP_m=sources[idx,1],
             Q_mg_s=qs[idx],tau_y=tys[idx],tau_z=tzs[idx],weighted_RMSE_mg_m3=float(np.sqrt(best[idx]/len(names))),
             source_on_grid_boundary=bool(edge),rss_5pct_support_points=int(support.sum()),
             rss_5pct_easting_span_m=float(span[0]),rss_5pct_northing_span_m=float(span[1]),
             identifiable_distance='NOT_ESTABLISHED_FROM_SINGLE_CURTAIN' if len(names)==1 else 'CONDITIONAL_SHARED_Q_AND_DISPERSION_MODEL',
             uncertainty='RSS support, not calibrated posterior',source_height_m=0)
    stem='_'.join(names)+'_'+arm+'_'+bglabel
    pd.DataFrame(dict(source_easting_m=sources[:,0],source_northing_m=sources[:,1],profile_rss=best,Q_mg_s=qs,tau_y=tys,tau_z=tzs)).to_csv(OUT/(stem+'_profile.csv'),index=False)
    if len(names)==2 and bglabel=='author_code':
        fig,ax=plt.subplots(figsize=(6,5));ax.tricontourf(sources[:,0],sources[:,1],np.log10(best/max(best.min(),1e-20)),levels=16)
        ax.scatter(d.e,d.n,s=2,c='white');ax.plot(sources[idx,0],sources[idx,1],'rx');ax.set_aspect('equal');ax.set_title(stem+'\nlog10(RSS / min RSS); white = observations');ax.set_xlabel('UTM easting / m');ax.set_ylabel('UTM northing / m');fig.tight_layout();fig.savefig(OUT/(stem+'.png'),dpi=140);plt.close(fig)
    return row

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--dispersion-sensitivity',action='store_true');args=parser.parse_args()
    global OUT
    if args.dispersion_sensitivity:
        OUT=OUT/'sensitivity_broader_dispersion'
        CONFIG['tau_y']=[.03,.05,.08,.12,.18,.25,.35]
        CONFIG['tau_z']=[.015,.025,.04,.065,.10,.16,.25]
        CONFIG['sensitivity']='broader dispersion support; primary outputs preserved; no result used to choose best wind arm'
    OUT.mkdir(parents=True,exist_ok=True)
    # Freeze before any unknown-source fit or truth-based error is inspected.
    (OUT/'FROZEN_CONFIG.json').write_text(json.dumps(CONFIG,indent=2),encoding='utf8')
    frames=prepare();reproduce(frames)
    results=[]
    cases=[['CP1'],['CP2'],['OP1'],['OP2'],['CP1','CP2'],['OP1','OP2']]
    if args.dispersion_sensitivity:cases=cases[-2:]
    for case in cases:
        for arm in CONFIG['arms']:
            print('fit',case,arm,flush=True);results.append(fit_case(frames,case,arm,'author_code'))
    if not args.dispersion_sensitivity:
        for case in cases[-2:]:
            for arm in CONFIG['arms']:results.append(fit_case(frames,case,arm,'paper_background'))
    # Truth is read into inverse evaluation only AFTER all fits have finished.
    truth=np.array(TRANSFORM.transform(-135.477520,69.319583))
    result=pd.DataFrame(results)
    result['conditional_localization_error_m']=np.hypot(result.source_easting_MAP_m-truth[0],result.source_northing_MAP_m-truth[1])
    result.to_csv(OUT/'WIND_REPRESENTATION_INVERSION.csv',index=False)
    center=[]
    for name,d in frames.items():
        if name not in result['case'].values:continue
        enh=np.maximum(d.ch4-CONFIG['primary_background_ppm'][name[:2]],0)
        for arm in CONFIG['arms']:
            r=result[(result['case']==name)&(result.wind_arm==arm)&(result.background=='author_code')].iloc[0]
            center.append(dict(flight=name,wind_arm=arm,observed_enhancement_weighted_easting_m=float(np.average(d.e,weights=enh)),observed_enhancement_weighted_northing_m=float(np.average(d.n,weights=enh)),inferred_source_easting_m=r.source_easting_MAP_m,inferred_source_northing_m=r.source_northing_MAP_m))
    pd.DataFrame(center).to_csv(OUT/'PLUME_CENTERLINE_DIAGNOSTICS.csv',index=False)
    shutil.copy2(ROOT/'metadata/DOWNLOAD_RECEIPT.json',OUT/'DOWNLOAD_RECEIPT.json')
    shutil.copy2(ROOT/'metadata/EXTRACTED_MANIFEST.json',OUT/'EXTRACTED_MANIFEST.json')
    (OUT/'ANALYSIS_COMPLETED.json').write_text(json.dumps(dict(decision='REAL_MACKENZIE_CONDITIONAL_FIXED_PATH_INVERSION',ground_arm='NOT_RUN_DATA_UNAVAILABLE',author_reproduction='fixed-source flux fit',posterior='NOT_CLAIMED_RSS_SUPPORT_ONLY',temporal_transport='NOT_RUN_CLOCK_CONTRACT_INCOMPLETE',independent_real_dataset_count=1),indent=2),encoding='utf8')
    print(result[['case','wind_arm','background','conditional_localization_error_m','source_on_grid_boundary']].to_string(index=False),flush=True)

if __name__=='__main__':main()
