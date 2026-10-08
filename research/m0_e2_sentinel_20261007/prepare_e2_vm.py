"""Runtime prequalification, zero simulations. Same assets, binaries and YAML."""
from pathlib import Path
import csv,hashlib,json,os,shutil,subprocess,traceback
import numpy as np
BASE=Path('/home/zyc/ros2_ws/m0_clean_support_r0_20261007');ROOT=BASE/'e2_sentinel'
GEN=Path('/home/zyc/ocb_r2_seeded_gaden/install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator');LIB=Path('/home/zyc/ocb_r2_seeded_gaden/install/gaden_common/lib/libgaden.so')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def dump(n,x):(ROOT/n).write_text(json.dumps(x,indent=2)+'\n')
def resources():
    m={q.split(':')[0]:int(q.split()[1])*1024 for q in Path('/proc/meminfo').read_text().splitlines() if len(q.split())>1 and q.split()[1].isdigit()}
    return {'disk_free_bytes':shutil.disk_usage(ROOT).free,'RAM_available_bytes':m['MemAvailable']}
try:
    assert ROOT.resolve()==ROOT and ROOT.is_relative_to(BASE)
    assert not (ROOT/'E2_PREQUALIFICATION.json').exists() and not (ROOT/'projects').exists()
    A=read(ROOT/'M0_E2_AUTHORIZATION.json');E0=read(BASE/'E0_QUALIFICATION.json');M=read(BASE/'ASSET_MANIFEST.json')
    ids=['m0r0_'+arm+'_S0_r01' for arm in ['A_on','A_off','B_shear','B_speed']]
    assert A['direct_user_authorization'] and A['allowed_run_ids']==ids and not A['E3_authorized']
    assert read(BASE/'E1_PROGRESS.json')['completed']==8 and read(BASE/'E1_PROGRESS.json')['intervention_runs']==0
    assert sha(GEN)==E0['generator_sha256'] and sha(LIB)==E0['libgaden_sha256']
    for p,h in E0['source_sha256'].items():assert sha(p)==h,p
    assert sha(BASE/'bin/native_audit')==E0['helper_sha256']
    H=read(ROOT/'PARENT_E1_HELPER_BUILD.json');assert sha(BASE/'bin/native_e1_audit')==H['binary_sha256']
    with (BASE/'NATIVE_ALL_FILES_SHA256.csv').open() as f:old=list(csv.DictReader(f))
    for q in old:assert sha(BASE/q['path'])==q['sha256'] and (BASE/q['path']).stat().st_size==int(q['bytes']),q['path']
    assert len(old)==2551
    res=resources();assert res['disk_free_bytes']>=12*1024**3 and res['RAM_available_bytes']>=3*1024**3
    deps={};ldds={}
    for p in [GEN,BASE/'bin/native_audit',BASE/'bin/native_e1_audit']:
        text=subprocess.check_output(['ldd',str(p)],text=True);assert 'not found' not in text;ldds[str(p)]=text
        binding=next(l for l in text.splitlines() if 'libgaden.so =>' in l);assert sha(Path(binding.split('=>')[1].split('(')[0].strip()))==E0['libgaden_sha256']
        for line in text.splitlines():
            for word in line.split():
                if word.startswith('/') and Path(word).is_file():deps[word]={'resolved':str(Path(word).resolve()),'bytes':Path(word).stat().st_size,'sha256':sha(word)}
    dump('RUNTIME_DEPENDENCY_SHA256.json',deps);dump('RUNTIME_LDD.json',ldds)
    (ROOT/'runtime_source_actual').mkdir();
    for p,h in E0['source_sha256'].items():shutil.copyfile(p,ROOT/'runtime_source_actual'/Path(p).name)
    (ROOT/'bin').mkdir()
    for name in ['native_audit','native_e1_audit']:shutil.copy2(BASE/'bin'/name,ROOT/'bin'/name)
    shutil.copyfile(BASE/'native_e1_audit.cpp',ROOT/'native_e1_audit.cpp');shutil.copyfile(BASE/'native_audit.cpp',ROOT/'native_audit.cpp')
    refid=A['reference_id'];refrows=[]
    for source,dest in [(BASE/'e1_audit'/refid,ROOT/'reference/audit'),(BASE/'projects/U0/simulations'/refid/'result',ROOT/'reference/result')]:
        dest.mkdir(parents=True)
        for p in sorted(source.rglob('*')):
            if p.is_file():
                target=dest/p.relative_to(source);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
                refrows.append({'original_E1_path':p.relative_to(BASE).as_posix(),'archived_path':target.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)})
    with (ROOT/'E1_REFERENCE_HASHES.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(refrows[0]),lineterminator='\n');w.writeheader();w.writerows(refrows)
    seed=str(A['master_seed']);noise={};runs=[];assets=[];stats={}
    shape=(96,160,240,3);free=np.zeros(shape[:3],bool);free[1:-1,1:-1,1:-1]=True;roi=np.zeros_like(free);roi[36:68,48:112,56:136]=True
    u0=np.fromfile(BASE/'projects/U0/wind/wind_iteration_0',dtype='<f4',offset=8).reshape(shape)
    for row in A['frozen_rows']:
        arm=row['wind_arm'];rid=row['run_id'];project=ROOT/'projects'/arm;(project/'wind').mkdir(parents=True);sim=project/'simulations'/rid;sim.mkdir(parents=True)
        for name in ['OccupancyGrid3D.csv','config.yaml','wind/wind_iteration_0']:
            original=BASE/'projects'/arm/name;target=project/name;assert sha(original)==next(q['sha256'] for q in M['asset_files'] if q['path']==original.relative_to(BASE).as_posix());shutil.copyfile(original,target)
        original=BASE/'projects/U0/simulations'/refid/'sim.yaml';shutil.copyfile(original,sim/'sim.yaml')
        readback=ROOT/'native_readback'/arm
        subprocess.run([str(ROOT/'bin/native_audit'),'e0',str(project),str(readback)],check=True,stdout=(ROOT/('readback_'+arm+'.log')).open('wb'),stderr=subprocess.STDOUT)
        wind=readback/'native_readback.wind';assert sha(wind)==row['expected_wind_sha256']==M['field_sha256'][arm]
        field=np.fromfile(wind,dtype='<f4',offset=8).reshape(shape);a=field.astype(float);delta=a-u0.astype(float);energy=np.sum(delta*delta,axis=3)
        div=((a[1:-1,1:-1,2:,0]-a[1:-1,1:-1,:-2,0])+(a[1:-1,2:,1:-1,1]-a[1:-1,:-2,1:-1,1])+(a[2:,1:-1,1:-1,2]-a[:-2,1:-1,1:-1,2]))/.5
        st={'readback_sha256':sha(wind),'global_vector_RMSE':float(np.sqrt(energy[free].mean())),'ROI_vector_RMSE':float(np.sqrt(energy[roi].mean())),'min_u':float(a[...,0].min()),'max_speed':float(np.sqrt((a*a).sum(axis=3)).max()),'max_error':float(np.sqrt(energy).max()),'max_div':float(abs(div).max()),'RMS_div':float(np.sqrt((div*div).mean()))}
        assert np.isfinite(field).all() and st['min_u']>=.02 and st['max_speed']<=.2 and st['max_error']<=.0500001 and st['max_div']<=1e-6 and st['RMS_div']<=1e-7
        for k in st:assert st[k]==E0['native_readback_stats'][arm][k],(arm,k)
        stats[arm]=st
        with (readback/'effective_params.tsv').open() as f:params=list(csv.DictReader(f,delimiter='\t'))
        assert len(params)==1;param=params[0]
        with (BASE/'e0_readback/U0/effective_params.tsv').open() as f:reference=next(q for q in csv.DictReader(f,delimiter='\t') if q['id']==refid)
        for k in reference:
            if k not in ['id','output']:assert param[k]==reference[k],(arm,k)
        assert param['id']==rid and param['output']==str(sim/'result') and not (sim/'result').exists()
        npth=ROOT/'noise'/arm;npth.parent.mkdir(exist_ok=True)
        subprocess.run([str(ROOT/'bin/native_e1_audit'),'noise',str(npth)],env=dict(os.environ,GADEN_RNG_SEED=seed),check=True,stdout=(ROOT/('noise_'+arm+'.log')).open('wb'))
        assert sha(npth)==E0['native_noise_table_bounds'][seed]['table_sequence_sha256'];noise[arm]={'sha256':sha(npth),'max_abs':float(abs(np.fromfile(npth,dtype='<f4')).max())}
        r=dict(row);r['argv']=[str(GEN),'--ros-args','-p','projectPath:='+str(project),'-p','simulationID:='+rid,'-p','sim_time:=140.0','-p','limitRate:=false','-p','verbose:=false','-r','__node:='+rid];r['effective_output_path']=str(sim/'result');r['project']=str(project);runs.append(r)
        for p in sorted(project.rglob('*')):
            if p.is_file():assets.append({'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)})
        del a,delta,energy,div,field
    for first,second in [('A_on','A_off'),('B_shear','B_speed')]:
        for key in ['global_vector_RMSE','ROI_vector_RMSE']:
            a,b=stats[first][key],stats[second][key];assert a>0 and b>0 and abs(a-b)<=1e-7 and abs(a-b)/max(a,b)<=1e-4
    used=set()
    for proc in Path('/proc').glob('[0-9]*'):
        try:
            for v in (proc/'environ').read_bytes().split(b'\0'):
                if v.startswith(b'ROS_DOMAIN_ID='):used.add(int(v.split(b'=')[1]))
        except (OSError,ValueError):pass
    domain=next(d for d in range(228,219,-1) if d not in used)
    dump('E2_ASSET_MANIFEST.json',{'runs':runs,'asset_files':assets,'generator_sha256':sha(GEN),'libgaden_sha256':sha(LIB),'helper_sha256':sha(ROOT/'bin/native_e1_audit'),'preflight_helper_sha256':sha(ROOT/'bin/native_audit'),'source_sha256':E0['source_sha256'],'ROS_DOMAIN_ID':domain})
    dump('E2_PREQUALIFICATION.json',{'status':'E2_RUNTIME_PREREQUISITES_PASS','new_scientific_runs':0,'original_E1_native_files_verified':len(old),'wind_readback':stats,'noise_table':noise,'resource_preflight':res,'output_leaves_previously_absent':True,'effective_parameters_match_U0':True,'occupancy_semantics_match_E0':True,'runtime_hashes_unchanged':True,'only_four_allowed':ids,'E3_authorized':False})
    print('E2_PREQUALIFICATION_PASS_NO_SCIENTIFIC_RUNS')
except Exception as e:
    dump('E2_PREQUALIFICATION.json',{'status':'M0_E2_PREREQUISITE_HOLD','new_scientific_runs':0,'error':str(e),'traceback':traceback.format_exc()});raise
