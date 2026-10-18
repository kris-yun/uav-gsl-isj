#!/usr/bin/env python3
"""Synthetic fault-injection tests only; NOT E2 physical concentration results."""
import csv, tempfile, copy, hashlib
from pathlib import Path
import numpy as np
from e2_open_response_adapter import parse_manifest,check_discovery,whitelisted_bank,mse_rankings,ContractFail,TIMES

def writecsv(p,fields,rows):
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def make(root):
    rng=np.random.default_rng(20261018)
    times=[55.0997314453125,85.09927368164062,115.09881591796875,142.2994842529297,167.30101013183594,192.3025360107422,217.30406188964844,242.3055877685547,267.3070983886719,292.3086242675781]
    wind=[2,9,6,2,7,2,7,2,7,2]
    tb=[dict(save_record_id=t,clock_before_s=v,active_wind_index=wi,state_stage='POST_MOVE_PRE_WIND_PRE_CLOCK') for t,v,wi in zip(TIMES,times,wind)]
    writecsv(root/'timebase.csv',['save_record_id','clock_before_s','active_wind_index','state_stage'],tb)
    pts=[(float(x),float(y)) for y in np.linspace(-1,1,5) for x in np.linspace(-1.5,1.5,6)]
    probes=[{'house':'House01','probe_id':f'p{i:02d}','x_m':x,'y_m':y,'z_m':0.2} for i,(x,y) in enumerate(pts)]
    writecsv(root/'probes.csv',['house','probe_id','x_m','y_m','z_m'],probes)
    manifest=[]
    fields=['run_id','house','wind','source_id','replicate_id','role','source_x_m','source_y_m','source_z_m','release_rate','release_unit','concentration_unit','forcing_id','solver_sha256','operator_sha256','timebase_sha256','probe_contract_sha256','data_file','data_sha256']
    for s in range(6):
        x0=-1.1+0.44*s;y0=-.6+0.20*(s%3)
        for rep in range(4):
            run=f'H01_S{s}_R{rep}';filename=f'{run}.csv'
            manifest.append(dict(run_id=run,house='House01',wind='1,3-2,4_fast',source_id=f'S{s}',replicate_id=f'R{rep}',role='DISCOVERY',source_x_m=x0,source_y_m=y0,source_z_m=0.2,release_rate=1.0,release_unit='mg/s',concentration_unit='ppm',forcing_id='frozen_H01_wind',solver_sha256='a'*64,operator_sha256='b'*64,timebase_sha256='c'*64,probe_contract_sha256='d'*64,data_file=filename))
            data=[]
            for tid,t in enumerate(TIMES):
                for i,(x,y) in enumerate(pts):
                    # Deliberately simple Gaussian-shaped synthetic response;
                    # *not* a GADEN physical model or closed-loop result.
                    cx=x0+0.003*float(times[tid]);cy=y0+0.05*np.sin(times[tid]/50)
                    mean=(.45+.35*np.cos(tid*.17))*np.exp(-((x-cx)**2/.32+(y-cy)**2/.18))
                    value=max(0,float(mean+rng.normal(0,.004)))
                    data.append({'save_record_id':t,'probe_id':f'p{i:02d}','ppm':value})
            writecsv(root/filename,['save_record_id','probe_id','ppm'],data)
    timehash=hashlib.sha256((root/'timebase.csv').read_bytes()).hexdigest()
    probehash=hashlib.sha256((root/'probes.csv').read_bytes()).hexdigest()
    for r in manifest:
        r['timebase_sha256']=timehash;r['probe_contract_sha256']=probehash
        r['data_sha256']=hashlib.sha256((root/r['data_file']).read_bytes()).hexdigest()
    writecsv(root/'manifest.csv',fields,manifest)
    return manifest,fields

def expect_bad(fn,label):
    try:fn()
    except ContractFail:return
    raise AssertionError('Expected protective rejection: '+label)

def main():
  with tempfile.TemporaryDirectory() as d:
    root=Path(d);manifest,fields=make(root)
    banks,_=whitelisted_bank(root/'manifest.csv',root/'probes.csv',root/'timebase.csv',root)
    rows=mse_rankings(banks,0.01)
    assert len(rows)==6*4*3, len(rows)
    assert not any(x['target_in_candidate_refs'] for x in rows)
    corr={m:sum(x['is_top1_correct'] for x in rows if x['method']==m) for m in {x['method'] for x in rows}}
    assert corr['ordinary_fixed_emission_Gaussian']>=20,corr
    assert corr['ordinary_nonnegative_emission_profile_Gaussian']>=18,corr
    injected=copy.deepcopy(manifest);injected[0]['role']='SEALED_H03_CONFIRMATION'
    expect_bad(lambda:check_discovery(parse_bad(injected,fields,root)),'sealed role')
    injected=copy.deepcopy(manifest);injected[0]['forcing_id']='forbidden_other_wind'
    expect_bad(lambda:check_discovery(parse_bad(injected,fields,root)),'mismatched forcing')
    injected=copy.deepcopy(manifest);injected[0]['concentration_unit']='2D_hit_probability'
    expect_bad(lambda:check_discovery(parse_bad(injected,fields,root)),'false ppm')
    injected=copy.deepcopy(manifest);injected[0]['replicate_id']=injected[1]['replicate_id']
    expect_bad(lambda:check_discovery(parse_bad(injected,fields,root)),'duplicate replicate')
    injected=copy.deepcopy(manifest);injected[0]['house']='House03'
    expect_bad(lambda:check_discovery(parse_bad(injected,fields,root)),'sealed house')
    injected=copy.deepcopy(manifest);injected[0]['data_file']='../sealed/secret.csv'
    expect_bad(lambda:check_discovery(parse_bad(injected,fields,root)),'path traversal')
    # Actual exported value bytes must be checked, not just filenames/roles.
    datfile=root/manifest[0]['data_file']
    original=datfile.read_bytes()
    datfile.write_bytes(original+b'\n')
    expect_bad(lambda:whitelisted_bank(root/'manifest.csv',root/'probes.csv',root/'timebase.csv',root),'content SHA mismatch')
    datfile.write_bytes(original)
    # Detect forged probe metadata after hash was fixed.
    original_probes=(root/'probes.csv').read_bytes()
    (root/'probes.csv').write_bytes(original_probes+b'\n')
    expect_bad(lambda:whitelisted_bank(root/'manifest.csv',root/'probes.csv',root/'timebase.csv',root),'probe SHA mismatch')
    (root/'probes.csv').write_bytes(original_probes)
    # Illegal writer chronology should fail before concentration read.
    badtb=[r.copy() for r in __import__('e2_open_response_adapter').readcsv(root/'timebase.csv')];badtb[0]['clock_before_s']='1000'
    writecsv(root/'timebase.csv',['save_record_id','clock_before_s','active_wind_index','state_stage'],badtb)
    expect_bad(lambda:whitelisted_bank(root/'manifest.csv',root/'probes.csv',root/'timebase.csv',root),'timebase mismatch')
    print({'synthetic_runs':24,'synthetic_target_scored':72,'methods':3,'top1':corr,'protective_rejections':9,'physical_data_used':False,'result':'PASS_SYNTHETIC_ONLY'})

def parse_bad(rows,fields,root):
    writecsv(root/'bad_manifest.csv',fields,rows)
    return parse_manifest(root/'bad_manifest.csv')

if __name__=='__main__':main()
