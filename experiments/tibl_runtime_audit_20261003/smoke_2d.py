"""Conservative 2D scalar solver smoke check, NOT a TIBL mechanism test.

K fields below are numerical fixtures, not WiscoDISCO estimates. No scientific
PASS/FAIL, source inference, stochastic realization, or GADEN change is made.
"""
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'evidence/tibl_runtime_audit_20261003'
CFG={'label':'NUMERICAL_SMOKE_ONLY_UNCALIBRATED_CLOSURES',
     'domain_m':[300,120], 'dx_dz_m':[2,2], 'dt_s':0.1,'duration_s':180,
     'u_m_s':2,'w_m_s':0,'Kx_m2_s':0.5,'Q_arbitrary_mass_per_s':1,
     'nominal_source_x_z_m':[20,1],
     'boundary':'zero inflow; advective outflow; zero diffusive flux on all boundaries',
     'fixtures':['homogeneous_Kz_0.5','imposed_h_10_plus_0.1x_Kz_0.05_to_2.0'],
     'limits':['x-z plane cannot recover source y or crosswind variance',
               'imposed h and Kz do not solve thermal dynamics',
               'no literature-calibrated parameter bounds; no scientific gate']}


def evolve(kz):
    dx,dz=CFG['dx_dz_m'];dt=CFG['dt_s'];u=CFG['u_m_s'];kx=CFG['Kx_m2_s']
    c=np.zeros_like(kz);nx,nz=c.shape
    ix=int(CFG['nominal_source_x_z_m'][0]//dx)
    iz=int(CFG['nominal_source_x_z_m'][1]//dz)
    adv=np.zeros((nx+1,nz));fx=np.zeros_like(adv);fz=np.zeros((nx,nz+1))
    face=2*kz[:,:-1]*kz[:,1:]/(kz[:,:-1]+kz[:,1:])
    lost=0.
    for _ in range(round(CFG['duration_s']/dt)):
        adv[1:]=u*c
        fx[1:-1]=-kx*np.diff(c,axis=0)/dx
        fz[:,1:-1]=-face*np.diff(c,axis=1)/dz
        lost+=float(adv[-1].sum())*dz*dt
        c-=dt*(np.diff(adv+fx,axis=0)/dx+np.diff(fz,axis=1)/dz)
        c[ix,iz]+=dt*CFG['Q_arbitrary_mass_per_s']/(dx*dz)
    mass=float(c.sum()*dx*dz);expected=CFG['duration_s']*CFG['Q_arbitrary_mass_per_s']
    error=abs(mass+lost-expected)/expected
    assert c.min()>=-1e-12 and error<1e-10
    return c,{'remaining_mass':mass,'advective_outflow_mass':lost,
              'relative_mass_balance_error':error,'minimum_concentration':float(c.min()),
              'actual_cell_center_source_x_z_m':[(ix+.5)*dx,(iz+.5)*dz]}


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    # Save configuration before generating any field.
    text=json.dumps(CFG,indent=2)
    (OUT/'NUMERICAL_SMOKE_CONFIG.json').write_text(text,encoding='utf-8')
    x=np.arange(1,300,2);z=np.arange(1,120,2)
    h=10+0.1*x
    fields={'homogeneous':np.full((len(x),len(z)),.5),
            'imposed_mixing_profile':.05+1.95*(1-np.tanh((z[None,:]-h[:,None])/2))/2}
    rows={};arrays={}
    for name,kz in fields.items():
        c,q=evolve(kz);rows[name]=q;arrays[name+'_C']=c;arrays[name+'_Kz']=kz
    np.savez_compressed(OUT/'NUMERICAL_SMOKE_FIELDS.npz',x=x,z=z,**arrays)
    result={'decision':'NUMERICAL_SMOKE_PASS_SCIENTIFIC_GATE_NOT_EXECUTED',
            'config_sha256':hashlib.sha256(text.encode()).hexdigest(),'checks':rows,
            'physical_mechanism_validated':False,'localization_validated':False}
    (OUT/'NUMERICAL_SMOKE_RESULT.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result))


if __name__=='__main__':main()
