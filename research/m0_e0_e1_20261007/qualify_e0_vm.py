"""Actual native asset/runtime qualification. Absolutely no gas simulation."""
from pathlib import Path
import csv,hashlib,json,os,shlex,shutil,subprocess,sys,traceback,datetime
import numpy as np
ROOT=Path('/home/zyc/ros2_ws/m0_clean_support_r0_20261007')
BUILD=Path('/home/zyc/ocb_r2_seeded_gaden');CORE=BUILD/'src/GADEN/gaden_common/third_party/gaden_core'
GEN=BUILD/'install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator';LIB=BUILD/'install/gaden_common/lib/libgaden.so'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(name,obj):(ROOT/name).write_text(json.dumps(obj,indent=2)+'\n')
def run(args,log):
    with (ROOT/log).open('wb') as f:subprocess.run(args,check=True,stdout=f,stderr=subprocess.STDOUT)
def resources():
    m={r.split(':')[0]:int(r.split()[1])*1024 for r in Path('/proc/meminfo').read_text().splitlines() if len(r.split())>1 and r.split()[1].isdigit()}
    return {'disk_free_bytes':shutil.disk_usage(ROOT).free,'RAM_available_bytes':m['MemAvailable']}
try:
    assert ROOT.resolve()==ROOT and ROOT.parent.resolve()==Path('/home/zyc/ros2_ws')
    M=json.loads((ROOT/'ASSET_MANIFEST.json').read_text());checks={};checks['generator']=sha(GEN)==M['runtime_contract']['intended_generator_sha256'];checks['libgaden']=sha(LIB)==M['runtime_contract']['intended_libgaden_sha256']
    source_hashes={}
    for name,relative in [('MathUtils.hpp','include/gaden/internal/'),('PointSource.hpp','include/gaden/datatypes/sources/'),('RunningSimulation.cpp','src/'),('Simulation.cpp','src/'),('WindSequence.cpp','src/'),('Environment.cpp','src/'),('GasSource.cpp','src/'),('GasTypes.hpp','include/gaden/datatypes/'),('EnvironmentConfigMetadata.cpp','src/'),('EnvironmentConfiguration.cpp','src/')]:
        p=CORE/relative/name;source_hashes[str(p)]=sha(p)
        expected_sources=json.loads((ROOT/'EXPECTED_FROZEN_NATIVE_SOURCE_SHA256.json').read_text())
        if name in expected_sources:checks[name]=sha(p)==expected_sources[name]
    source_hashes[str(BUILD/'src/GADEN/gaden_filament_simulator/src/filament_simulator.cpp')]=sha(BUILD/'src/GADEN/gaden_filament_simulator/src/filament_simulator.cpp')
    assert all(checks.values()),checks
    assert resources()['disk_free_bytes']>=12*1024**3 and resources()['RAM_available_bytes']>=3*1024**3,resources()
    for r in M['asset_files']:assert sha(ROOT/r['path'])==r['sha256'],r['path']
    for r in M['base_runs_only']:
        leaf=Path(r['effective_output_path']);assert leaf.resolve().is_relative_to(ROOT) and leaf.name=='result' and leaf.parent.name==r['run_id'] and not leaf.exists()
    compiler=(BUILD/'build/gaden_common/third_party/gaden_core/CMakeFiles/gaden.dir/flags.make').read_text().splitlines();includes=next(x.split(' = ',1)[1] for x in compiler if x.startswith('CXX_INCLUDES'))
    (ROOT/'bin').mkdir(exist_ok=True);bsc=BUILD/'build/gaden_common/third_party/gaden_core/third_party/libbsc'
    argv=['g++','-std=c++20','-O3','-DGADEN_ROS=1',*shlex.split(includes),str(ROOT/'native_audit.cpp'),'-L'+str(LIB.parent),'-Wl,-rpath,'+str(LIB.parent),'-Wl,-rpath,'+str(bsc),'-Wl,-rpath-link,'+str(bsc),'-lgaden','-o',str(ROOT/'bin/native_audit')]
    dump('HELPER_BUILD_ARGV.json',argv);run(argv,'helper_build.log')
    ldd=subprocess.check_output(['ldd',str(GEN)],text=True);helperldd=subprocess.check_output(['ldd',str(ROOT/'bin/native_audit')],text=True)
    (ROOT/'RUNTIME_LDD.txt').write_text(ldd+'\nHELPER\n'+helperldd)
    for text in [ldd,helperldd]:
        assert 'not found' not in text
        line=next(l for l in text.splitlines() if 'libgaden.so =>' in l);actual=Path(line.split('=>')[1].split('(')[0].strip());assert sha(actual)==M['runtime_contract']['intended_libgaden_sha256']
    stats={}
    dims=(96,160,240,3);free=np.zeros(dims[:3],dtype=bool);free[1:-1,1:-1,1:-1]=True;roi=np.zeros_like(free);roi[36:68,48:112,56:136]=True
    u0=None
    for arm in ['U0','A_on','A_off','B_shear','B_speed']:
        output=ROOT/'e0_readback'/arm
        run([str(ROOT/'bin/native_audit'),'e0',str(ROOT/'projects'/arm),str(output)],'e0_'+arm+'.log')
        p=output/'native_readback.wind';assert sha(p)==M['field_sha256'][arm]
        f=np.fromfile(p,dtype='<f4',offset=8).reshape(dims)
        if u0 is None:u0=f.copy()
        a=f.astype(float);error=a-u0.astype(float);en=np.sum(error*error,axis=3)
        div=((a[1:-1,1:-1,2:,0]-a[1:-1,1:-1,:-2,0])+(a[1:-1,2:,1:-1,1]-a[1:-1,:-2,1:-1,1])+(a[2:,1:-1,1:-1,2]-a[:-2,1:-1,1:-1,2]))/.5
        stat={'readback_sha256':sha(p),'global_vector_RMSE':float(np.sqrt(en[free].mean())),'ROI_vector_RMSE':float(np.sqrt(en[roi].mean())),'min_u':float(a[...,0].min()),'max_speed':float(np.sqrt((a*a).sum(axis=3)).max()),'max_error':float(np.sqrt(en).max()),'max_div':float(abs(div).max()),'RMS_div':float(np.sqrt((div*div).mean()))}
        assert np.isfinite(f).all() and stat['min_u']>=.02 and stat['max_speed']<=.2 and stat['max_error']<=.0500001 and stat['max_div']<=1e-6 and stat['RMS_div']<=1e-7
        stats[arm]=stat;del a,error,en,div,f
    for aa,bb in [('A_on','A_off'),('B_shear','B_speed')]:
        for v in ['global_vector_RMSE','ROI_vector_RMSE']:
            a,b=stats[aa][v],stats[bb][v];assert abs(a-b)<=1e-7 and abs(a-b)/max(a,b)<=1e-4
    with (ROOT/'e0_readback/U0/effective_params.tsv').open() as f:params=list(csv.DictReader(f,delimiter='\t'))
    assert {q['id'] for q in params}=={r['run_id'] for r in M['base_runs_only']}
    expected={'gas':12,'dt':float(np.float32(.1)),'wind_dt':1,'T':298,'P':1,'ppm':10,'sigma_cm':10,'gamma':15,'noise_input':float(np.float32(.01)),'release':10,'iterations':1400,'save':1,'save_dt':.5,'precalculate':0,'loop':0,'from':0,'to':0}
    for q in params:
        r=next(x for x in M['base_runs_only'] if x['run_id']==q['id'])
        for k,v in expected.items():assert float(q[k])==v,(q['id'],k,q[k],v)
        assert [float(q[k]) for k in ['x','y','z']]==[float(r[k]) for k in ['x_m','y_m','z_m']] and q['output']==r['effective_output_path']
    noise={};(ROOT/'noise').mkdir(exist_ok=True)
    for seed in range(2026100701,2026100705):
        env=dict(os.environ,GADEN_RNG_SEED=str(seed));p=ROOT/'noise'/str(seed)
        out=subprocess.check_output([str(ROOT/'bin/native_audit'),'noise',str(p)],env=env,text=True);noise[str(seed)]={'max_abs':float(out.split('NOISE_MAX ')[-1]),'table_sequence_sha256':sha(p)}
    used=set()
    for proc in Path('/proc').glob('[0-9]*'):
        try:
            for val in (proc/'environ').read_bytes().split(b'\0'):
                if val.startswith(b'ROS_DOMAIN_ID='):used.add(int(val.split(b'=')[1]))
        except (OSError,ValueError):pass
    domain=next(d for d in range(228,219,-1) if d not in used)
    R={'status':'M0_E0_RUNTIME_QUALIFIED','scientific_runs':0,'intervention_authorized':False,'generator_sha256':sha(GEN),'libgaden_sha256':sha(LIB),'source_sha256':source_hashes,'helper_sha256':sha(ROOT/'bin/native_audit'),'asset_manifest_sha256':sha(ROOT/'ASSET_MANIFEST.json'),'native_readback_stats':stats,'effective_parameters_verified':8,'native_noise_table_bounds':noise,'selected_ROS_DOMAIN_ID':domain,'resource_preflight':resources(),'output_paths_previously_nonexistent':True,'temperature_K_effective':298,'pressure_atm_effective':1,'entrypoint':'native project/YAML using unchanged generator and libgaden','no_new_GADEN_simulations_in_E0':True}
    dump('E0_QUALIFICATION.json',R);print(json.dumps({'status':R['status'],'science_runs':0,'native_winds_readback':5,'effective_configs':8,'ROS_DOMAIN_ID':domain},indent=2))
except Exception as e:
    dump('E0_QUALIFICATION.json',{'status':'M0_PREREQUISITE_HOLD','stage':'E0','science_runs':0,'error':str(e),'traceback':traceback.format_exc()});raise
