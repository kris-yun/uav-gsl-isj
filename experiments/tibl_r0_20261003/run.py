"""Restricted 2-D TIBL source-x falsification; no GADEN or field claims.

Conservative finite-volume steady operator, independently checked against
finite-duration implicit time stepping. Source strength/background profiled.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix, eye
from scipy.sparse.linalg import splu
from scipy.interpolate import RegularGridInterpolator
from scipy.special import xlogy
from scipy.optimize import minimize_scalar

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'evidence/tibl_r0_20261003'
CFG=dict(domain=[1000.,150.],u=2.,w=0.,Kx=.5,theta_ref_K=300.,g=9.81,kappa=.4,
         heat_fluxes=[.06,.04],closures=['USER_SIMPLIFIED_K','HOLTSLAG_SIEBESMA_FREE_CONVECTION_ED'],
         cases=['TIBL_X','Z_MEAN','K_MEAN'],grid=[5.,1.25],coarse_grid=[10.,2.5],fine_grid=[2.5,.625],
         sources_x=[73.4,161.7,287.3],source_z=3.,source_sigma_x=5.,source_sigma_z=.75,
         template_x=list(np.arange(20.,351.,10.)),profile_x=list(np.arange(20.,351.,1.)),
         Q_truth=1.,background=.002,noise_sigma=.0005,seeds=list(range(61001,61009)),
         paths={'P1':[400.,700.,900.],'P2':[500.,800.,950.]},heights=list(np.arange(2.,103.,2.)),
         duration_s=1500.,dt_checks=[20.,10.],boundary='zero inflow; zero diffusive ground/top/outlet flux; advective outlet',
         gates={'numerical_profile_relL2_max':.05,'mass_balance_max':1e-8,
                'geometry_JSD_min':.01,'effect_over_numerical_error_min':5.,
                'mismatch_median_abs_bias_min_m':20.,'aware_median_error_max_m':5.,
                'recovery_fraction_min':.5,'consistent_trial_fraction_min':.75,
                'matched_count_min':24,'matched_expected_SNR_ratio_max':1.25},
         limits=['Only source x is inverted; y is absent.',
                 'Prescribed local downgradient scalar closures; no thermal dynamics, entrainment or full EDMF.',
                 'Kz=0 outside the prescribed layer: no ambient turbulent mixing, no claim this is field truth.',
                 'Scalar diffusivity equals published heat-diffusivity form: unvalidated turbulent Schmidt assumption.',
                 'Engineering gates are frozen operational criteria, not literature-derived physical thresholds.',
                 'Steady forward limit is used only after fixed-duration numerical validation.',
                 'All physical source/profile choices frozen before scoring; synthetic source-aware curtains, not autonomous search.'])


def write(name,obj):
    (OUT/name).write_text(json.dumps(obj,indent=2,allow_nan=False),encoding='utf-8')


def grid(dx,dz,Lx=1000,Lz=150):
    return np.arange(dx/2,Lx,dx),np.arange(dz/2,Lz,dz)


def mixing(x,z,flux,closure,case):
    h=.1*x[:,None];r=z[None,:]/h
    ws=(CFG['g']/CFG['theta_ref_K']*flux*h)**(1/3)
    mult=1 if closure=='USER_SIMPLIFIED_K' else (39*CFG['kappa']*r)**(1/3)
    k=np.where(r<1,CFG['kappa']*ws*mult*z[None,:]*(1-r)**2,0.)
    if case=='Z_MEAN':k=np.broadcast_to(k.mean(axis=0,keepdims=True),k.shape).copy()
    elif case=='K_MEAN':k=np.full_like(k,k.mean())
    return k


def operator(x,z,kz,top='reflect',bottom='reflect'):
    nx,nz=len(x),len(z);dx=x[1]-x[0];dz=z[1]-z[0];N=nx*nz
    ix=np.arange(N).reshape(nx,nz);diag=np.full((nx,nz),CFG['u']/dx);rr=[];cc=[];vv=[]
    def off(a,b,v):rr.extend(a.ravel());cc.extend(b.ravel());vv.extend(v.ravel())
    off(ix[1:],ix[:-1],np.full((nx-1,nz),-CFG['u']/dx))
    # Diffusion face conductance; zero flux on exterior faces.
    q=CFG['Kx']/dx**2
    diag[:-1]+=q;diag[1:]+=q
    off(ix[:-1],ix[1:],np.full((nx-1,nz),-q));off(ix[1:],ix[:-1],np.full((nx-1,nz),-q))
    denom=kz[:,:-1]+kz[:,1:]
    f=np.divide(2*kz[:,:-1]*kz[:,1:],denom,out=np.zeros_like(denom),where=denom>0)/dz**2
    diag[:,:-1]+=f;diag[:,1:]+=f
    off(ix[:,:-1],ix[:,1:],-f);off(ix[:,1:],ix[:,:-1],-f)
    if top=='absorbing':diag[:,-1]+=2*kz[:,-1]/dz**2
    if bottom=='absorbing':diag[:,0]+=2*kz[:,0]/dz**2
    off(ix,ix,diag)
    return coo_matrix((vv,(rr,cc)),shape=(N,N)).tocsc()


def sources(x,z,sxs):
    dx=x[1]-x[0];dz=z[1]-z[0]
    gx=np.exp(-.5*((x[:,None]-np.array(sxs)[None,:])/CFG['source_sigma_x'])**2)
    gz=np.exp(-.5*((z-CFG['source_z'])/CFG['source_sigma_z'])**2)
    a=(gx[:,None,:]*gz[None,:,None]).reshape(len(x)*len(z),len(sxs))
    return a/(a.sum(axis=0)*dx*dz)


def solve(dx,dz,flux,closure,case,sxs,Lx=1000,Lz=150,top='reflect',bottom='reflect'):
    x,z=grid(dx,dz,Lx,Lz);k=mixing(x,z,flux,closure,case);A=operator(x,z,k,top,bottom)
    rhs=sources(x,z,sxs);c=splu(A).solve(rhs).reshape(len(x),len(z),len(sxs))
    assert c.min()>-1e-10
    return x,z,k,A,rhs,c


def samples(x,z,c,path):
    points=np.array([(xx,zz) for xx in CFG['paths'][path] for zz in CFG['heights']])
    return RegularGridInterpolator((x,z),c,bounds_error=True)(points)


def jsd(a,b):
    a=np.maximum(a,0);b=np.maximum(b,0)
    a=a/a.sum();b=b/b.sum();m=(a+b)/2
    ra=np.divide(a,m,out=np.ones_like(a),where=m>0)
    rb=np.divide(b,m,out=np.ones_like(b),where=m>0)
    return float(.5*np.sum(xlogy(a,ra))+.5*np.sum(xlogy(b,rb)))


def profile(template,y,sigma):
    # Closed-form intercept and nonnegative Q for every continuous-x template.
    t=template-template.mean(axis=0);yc=y-y.mean();den=(t*t).sum(axis=0)
    q=np.maximum(0,np.divide(t.T@yc,den,out=np.zeros(len(den)),where=den>1e-30))
    bg=y.mean()-q*template.mean(axis=0)
    chi=((y[:,None]-q[None,:]*template-bg[None,:])/sigma)**2
    chi=chi.sum(axis=0);best=int(chi.argmin());allowed=chi<=chi[best]+3.841458820694124
    xx=np.array(CFG['profile_x']);curvature=(chi[best+1]-2*chi[best]+chi[best-1]) if 0<best<len(xx)-1 else None
    def continuous(candidate):
        v=np.array([np.interp(candidate,xx,row) for row in template]);v0=v-v.mean()
        qq=max(0,float(v0@yc)/max(float(v0@v0),1e-30));bb=float(y.mean()-qq*v.mean())
        return float(np.sum(((y-qq*v-bb)/sigma)**2)),qq,bb
    optimum=minimize_scalar(lambda candidate:continuous(candidate)[0],bounds=(xx[max(0,best-1)],xx[min(len(xx)-1,best+1)]),method='bounded')
    refined=continuous(optimum.x)
    return dict(xhat=float(optimum.x),Qhat=refined[1],background_hat=refined[2],
                interval_low=float(xx[allowed].min()),interval_high=float(xx[allowed].max()),
                interval_width=float(xx[allowed].max()-xx[allowed].min()),curvature=curvature,
                boundary=best in [0,len(xx)-1],chi=chi,q=q,bg=bg)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    if (OUT/'R0_TIBL_CONFIG.json').exists():
        assert json.loads((OUT/'R0_TIBL_CONFIG.json').read_text())==CFG,'Frozen config changed'
    else:write('R0_TIBL_CONFIG.json',CFG)
    print('FREEZE_SAVED',flush=True)
    num=[];geom=[];budgets=[];local=[];matched=[];curves=[];mapping={};numerical_js=[]
    for closure in CFG['closures']:
        for flux in CFG['heat_fluxes']:
            print('SOLVING',closure,flux,flush=True)
            data={};err=[]
            for case in CFG['cases']:
                x,z,k,A,rhs,c=solve(*CFG['grid'],flux,closure,case,CFG['sources_x']+CFG['template_x'])
                data[case]=(x,z,c)
                budgets.append(dict(closure=closure,flux=flux,case=case,Kz_min=float(k.min()),Kz_max=float(k.max()),
                                    integral_Kz=float(k.sum()*np.prod(CFG['grid'])),h_at400=40,h_at700=70,h_at1000=100))
                # Independently refined truth fields; templates not used for numerical checks.
                for label,dims,Lx,Lz,top,bottom in [
                    ('coarse',CFG['coarse_grid'],1000,150,'reflect','reflect'),
                    ('fine',CFG['fine_grid'],1000,150,'reflect','reflect'),
                    ('top_extended',CFG['grid'],1000,250,'reflect','reflect'),
                    ('outlet_extended',CFG['grid'],1200,150,'reflect','reflect'),
                    ('top_absorbing',CFG['grid'],1000,150,'absorbing','reflect'),
                    ('bottom_absorbing',CFG['grid'],1000,150,'reflect','absorbing')]:
                    # Keep the same physical K field/control when extending the box.
                    # Z/K means must use the primary domain, not change with the new box.
                    if label in ['top_extended','outlet_extended'] and case!='TIBL_X':
                        xx,zz=grid(*dims,Lx,Lz);prim_x,prim_z=grid(*dims);base=mixing(prim_x,prim_z,flux,closure,case)
                        kk=np.tile(np.interp(zz,prim_z,base[0],left=base[0,0],right=base[0,-1]),(len(xx),1))
                        aa=operator(xx,zz,kk);rr=sources(xx,zz,CFG['sources_x']);cc=splu(aa).solve(rr).reshape(len(xx),len(zz),3)
                    else:xx,zz,_,_,_,cc=solve(*dims,flux,closure,case,CFG['sources_x'],Lx,Lz,top,bottom)
                    for path in CFG['paths']:
                        a=samples(x,z,c[:,:,:3],path);b=samples(xx,zz,cc,path)
                        e=float(np.linalg.norm(a-b)/max(np.linalg.norm(b),1e-20))
                        j=max(jsd(a[:,i],b[:,i]) for i in range(3))
                        num.append(dict(closure=closure,flux=flux,case=case,check=label,path=path,relative_L2=e,max_JSD=j))
                        if label in ['fine','top_extended','outlet_extended','top_absorbing']:
                            err.append(e);numerical_js.append(j)
                # Fixed-duration versus stationary-limit and time step validation.
                for dt in CFG['dt_checks']:
                    lu=splu(eye(A.shape[0],format='csc')+dt*A);v=np.zeros_like(rhs[:,:3])
                    for _ in range(round(CFG['duration_s']/dt)):v=lu.solve(v+dt*rhs[:,:3])
                    e=float(np.linalg.norm(v-c[:,:,:3].reshape(-1,3))/max(np.linalg.norm(v),1e-20))
                    num.append(dict(closure=closure,flux=flux,case=case,check='dt_'+str(dt),path='whole_domain',relative_L2=e,max_JSD=0.))
                    err.append(e)
                dx,dz=CFG['grid'];balance=CFG['u']*c[-1,:,:3].sum(axis=0)*dz
                e=float(abs(balance-1).max());assert e<CFG['gates']['mass_balance_max']
                num.append(dict(closure=closure,flux=flux,case=case,check='steady_mass_balance',path='all',relative_L2=e,max_JSD=0.))
                for i,sx in enumerate(CFG['sources_x']):
                    for diagnostic_x in [400,700,1000]:
                        ii=int(abs(x-diagnostic_x).argmin());p=c[ii,:,i];p=p/p.sum();mean=float(p@z)
                        geom.append(dict(closure=closure,flux=flux,case=case,source_x=sx,requested_x=diagnostic_x,
                                         actual_x=float(x[ii]),centroid_z=mean,vertical_variance=float(p@((z-mean)**2)),peak_z=float(z[p.argmax()])))
            # Before localization, compute the matched-control geometry residual.
            per_geometry=[]
            for case in ['Z_MEAN','K_MEAN']:
                for path in CFG['paths']:
                    a=samples(*data['TIBL_X'][:2],data['TIBL_X'][2][:,:,:3],path)
                    b=samples(*data[case][:2],data[case][2][:,:,:3],path)
                    per_geometry.extend(jsd(a[:,i],b[:,i]) for i in range(3))
            mapping[(closure,flux)]={'geometry_min_JSD':min(per_geometry),'numerical_max_relative_L2':max(err),
                                     'geometry_JSDs':per_geometry}
            # Predeclared numerical/geometry stage gate, before noise or inversion.
            assert np.isfinite(per_geometry).all() and np.isfinite(err).all()
            if max(err)>CFG['gates']['numerical_profile_relL2_max'] or min(per_geometry)<CFG['gates']['geometry_JSD_min']:
                print('PRELOCALIZATION_GATE_FAILED',closure,flux,max(err),min(per_geometry),flush=True)
                continue
            for path in CFG['paths']:
                obs={};templates={}
                for case in CFG['cases']:
                    xx,zz,cc=data[case];a=samples(xx,zz,cc,path);obs[case]=a[:,:3]
                    templates[case]=np.stack([np.interp(CFG['profile_x'],CFG['template_x'],row) for row in a[:,3:]])
                for i,sx in enumerate(CFG['sources_x']):
                    signals=np.stack([obs[case][:,i] for case in CFG['cases']])
                    lo=signals.min(axis=0);hi=signals.max(axis=0)
                    common=np.flatnonzero((lo>=3*CFG['noise_sigma'])&(hi<=CFG['gates']['matched_expected_SNR_ratio_max']*lo))
                    matched.append(dict(closure=closure,flux=flux,path=path,source_x=sx,common_hits=len(common),
                                        same_positions=True,same_count=True,expected_SNR_ratio_max=CFG['gates']['matched_expected_SNR_ratio_max'],
                                        selection='noiseless three-world common expected hits; synthetic truth-informed evaluation only'))
                    for seed in CFG['seeds']:
                        noise=np.random.default_rng(seed).normal(0,CFG['noise_sigma'],len(lo))
                        for mode in ['same_observations','matched_detection']:
                            indices=np.arange(len(lo)) if mode=='same_observations' else common
                            if mode=='matched_detection' and len(indices)<CFG['gates']['matched_count_min']:continue
                            # All inverse models receive EXACTLY the same truth observations.
                            y=obs['TIBL_X'][indices,i]+CFG['background']+noise[indices]
                            for inverse in CFG['cases']:
                                result=profile(templates[inverse][indices],y,CFG['noise_sigma'])
                                row={k:v for k,v in result.items() if k not in ['chi','q','bg']}
                                row.update(closure=closure,flux=flux,path=path,source_x=sx,seed=seed,mode=mode,
                                           inverse=inverse,bias=result['xhat']-sx,error=abs(result['xhat']-sx),
                                           coverage=result['interval_low']<=sx<=result['interval_high'],observations=len(indices))
                                local.append(row)
                                for j,candidate in enumerate(CFG['profile_x']):
                                    curves.append(dict(closure=closure,flux=flux,path=path,source_x=sx,seed=seed,mode=mode,
                                                       inverse=inverse,candidate_x=candidate,profile_chi2=result['chi'][j],
                                                       Q_hat=result['q'][j],background_hat=result['bg'][j]))
            pd.DataFrame(local).to_csv(OUT/'MODEL_MISMATCH_LOCALIZATION.csv',index=False)
            print('CONDITION_COMPLETE',closure,flux,flush=True)
    pd.DataFrame(num).to_csv(OUT/'NUMERICAL_CONVERGENCE.csv',index=False)
    pd.DataFrame(geom).to_csv(OUT/'PLUME_GEOMETRY.csv',index=False)
    pd.DataFrame(budgets).to_csv(OUT/'MATCHED_MIXING_CONTROLS.csv',index=False)
    pd.DataFrame(matched).to_csv(OUT/'MATCHED_DETECTION.csv',index=False)
    pd.DataFrame(curves).to_csv(OUT/'SOURCE_PROFILE_LIKELIHOOD.csv',index=False)
    pd.DataFrame(local).to_csv(OUT/'MODEL_MISMATCH_LOCALIZATION.csv',index=False)
    summaries=[]
    for key,value in mapping.items():summaries.append(dict(closure=key[0],flux=key[1],**value))
    # Result assembly is separate, so every intermediate gate is reviewable.
    write('STAGE_GATE_RESULTS.json',{'conditions':summaries,'numerical_max_JSD':max(numerical_js),'localization_rows':len(local)})
    print('R0_FORWARD_AND_SCORING_COMPLETE',len(local),flush=True)


if __name__=='__main__':main()
