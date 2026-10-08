"""E3 runtime preflight and exact native/YAML materialization; zero gas runs."""
from pathlib import Path
import csv,hashlib,json,os,shutil,subprocess,traceback
import numpy as np
from qualify_run import qualify,rows
BASE=Path('/home/zyc/ros2_ws/m0_clean_support_r0_20261007');OLD2=BASE/'e2_sentinel';R=BASE/'e3_final';GEN=Path('/home/zyc/ocb_r2_seeded_gaden/install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator');LIB=Path('/home/zyc/ocb_r2_seeded_gaden/install/gaden_common/lib/libgaden.so')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(n,x):(R/n).write_text(json.dumps(x,indent=2)+'\n')
def resources():
    mem={q.split(':')[0]:int(q.split()[1])*1024 for q in Path('/proc/meminfo').read_text().splitlines() if len(q.split())>1 and q.split()[1].isdigit()}
    return {'disk_free_bytes':shutil.disk_usage(R).free,'RAM_available_bytes':mem['MemAvailable']}
try:
    assert not (R/'E3_PREQUALIFICATION.json').exists() and not (R/'projects').exists();assert R.resolve()==R and R.is_relative_to(BASE)
    A=read(R/'E3_AUTHORIZATION.json');E0=read(BASE/'E0_QUALIFICATION.json');M0=read(BASE/'ASSET_MANIFEST.json');H=read(R/'PARENT_E1_HELPER_BUILD.json')
    assert A['direct_user_authorization'] and len(A['allowed_rows'])==28 and len(set(A['allowed_run_ids']))==28
    old1=read(BASE/'E1_COMPLETED_RUNS.json');old2=read(OLD2/'E2_COMPLETED_RUNS.json');done={q['run_id'] for q in old1+old2};assert len(done)==12 and done==set(A['previous_completed_ids'])
    assert [q['run_id'] for q in A['all_frozen_rows'] if q['run_id'] not in done]==A['allowed_run_ids']
    assert sha(GEN)==E0['generator_sha256'] and sha(LIB)==E0['libgaden_sha256'];assert not os.environ.get('LD_PRELOAD')
    for p,h in E0['source_sha256'].items():assert sha(p)==h
    previous={}
    for folder in [BASE,OLD2]:
        manifest=rows(folder/'NATIVE_ALL_FILES_SHA256.csv')
        for q in manifest:assert sha(folder/q['path'])==q['sha256'] and (folder/q['path']).stat().st_size==int(q['bytes']),q['path']
        previous[str(folder)]=len(manifest)
    for q in rows(R/'frozen/M0_R0_FILES_SHA256.csv'):assert sha(R/'frozen'/q['path'])==q['sha256']
    res=resources();assert res['disk_free_bytes']>=12*1024**3 and res['RAM_available_bytes']>=3*1024**3
    (R/'bin').mkdir();(R/'runtime_source_actual').mkdir()
    for name in ['native_audit','native_e1_audit']:shutil.copy2(BASE/'bin'/name,R/'bin'/name)
    assert sha(R/'bin/native_audit')==E0['helper_sha256'] and sha(R/'bin/native_e1_audit')==H['binary_sha256']
    for p,h in E0['source_sha256'].items():shutil.copyfile(p,R/'runtime_source_actual'/Path(p).name)
    for name in ['native_audit.cpp','native_e1_audit.cpp']:shutil.copyfile(BASE/name,R/name)
    deps={};ldd={}
    for p in [GEN,R/'bin/native_audit',R/'bin/native_e1_audit']:
        text=subprocess.check_output(['ldd',str(p)],text=True);assert 'not found' not in text;binding=next(s for s in text.splitlines() if 'libgaden.so =>' in s);assert sha(Path(binding.split('=>')[1].split('(')[0].strip()))==E0['libgaden_sha256'];ldd[str(p)]=text
        for line in text.splitlines():
            for word in line.split():
                if word.startswith('/') and Path(word).is_file():deps[word]={'resolved':str(Path(word).resolve()),'bytes':Path(word).stat().st_size,'sha256':sha(word)}
    write('RUNTIME_LDD.json',ldd);write('RUNTIME_DEPENDENCY_SHA256.json',deps)
    runs=[];assets=[];stats={};shape=(96,160,240,3);free=np.zeros(shape[:3],bool);free[1:-1,1:-1,1:-1]=True;roi=np.zeros_like(free);roi[36:68,48:112,56:136]=True
    u0=np.fromfile(BASE/'projects/U0/wind/wind_iteration_0',dtype='<f4',offset=8).reshape(shape)
    baseparams={q['id']:q for q in rows(BASE/'e0_readback/U0/effective_params.tsv','\t')}
    for arm in ['U0','A_on','A_off','B_shear','B_speed']:
        project=R/'projects'/arm;(project/'wind').mkdir(parents=True);(project/'simulations').mkdir()
        for name in ['OccupancyGrid3D.csv','config.yaml','wind/wind_iteration_0']:
            original=BASE/'projects'/arm/name;assert sha(original)==next(q['sha256'] for q in M0['asset_files'] if q['path']==original.relative_to(BASE).as_posix());shutil.copyfile(original,project/name)
        selected=[q for q in A['allowed_rows'] if q['wind_arm']==arm]
        for row in selected:
            rid=row['run_id'];refid='m0r0_U0_'+row['source_id']+'_r'+str(row['realization']).zfill(2);sim=project/'simulations'/rid;sim.mkdir();shutil.copyfile(BASE/'projects/U0/simulations'/refid/'sim.yaml',sim/'sim.yaml')
            assert not (sim/'result').exists();new=dict(row);new.update({'project':str(project),'effective_output_path':str(sim/'result'),'reference_audit':str(BASE/'e1_audit'/refid),'argv':[str(GEN),'--ros-args','-p','projectPath:='+str(project),'-p','simulationID:='+rid,'-p','sim_time:=140.0','-p','limitRate:=false','-p','verbose:=false','-r','__node:='+rid]});runs.append(new)
        out=R/'native_readback'/arm
        with (R/('readback_'+arm+'.log')).open('wb') as log:subprocess.run([str(R/'bin/native_audit'),'e0',str(project),str(out)],stdout=log,stderr=subprocess.STDOUT,check=True)
        wind=out/'native_readback.wind';assert sha(wind)==M0['field_sha256'][arm];field=np.fromfile(wind,dtype='<f4',offset=8).reshape(shape);a=field.astype(float);err=a-u0.astype(float);energy=(err*err).sum(axis=3);div=((a[1:-1,1:-1,2:,0]-a[1:-1,1:-1,:-2,0])+(a[1:-1,2:,1:-1,1]-a[1:-1,:-2,1:-1,1])+(a[2:,1:-1,1:-1,2]-a[:-2,1:-1,1:-1,2]))/.5
        st={'readback_sha256':sha(wind),'global_vector_RMSE':float(np.sqrt(energy[free].mean())),'ROI_vector_RMSE':float(np.sqrt(energy[roi].mean())),'min_u':float(a[...,0].min()),'max_speed':float(np.sqrt((a*a).sum(axis=3)).max()),'max_error':float(np.sqrt(energy).max()),'max_div':float(abs(div).max()),'RMS_div':float(np.sqrt((div*div).mean()))}
        assert np.isfinite(field).all() and st['min_u']>=.02 and st['max_speed']<=.2 and st['max_error']<=.0500001 and st['max_div']<=1e-6 and st['RMS_div']<=1e-7
        assert st==E0['native_readback_stats'][arm];stats[arm]=st
        params=rows(out/'effective_params.tsv','\t');assert len(params)==len(selected)
        for q in params:
            row=next(x for x in selected if x['run_id']==q['id']);refid='m0r0_U0_'+row['source_id']+'_r'+str(row['realization']).zfill(2)
            for key,v in baseparams[refid].items():
                if key not in ['id','output']:assert q[key]==v,(q['id'],key)
            assert q['output']==str(project/'simulations'/q['id']/'result')
        for p in sorted(project.rglob('*')):
            if p.is_file():assets.append({'path':p.relative_to(R).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)})
        del a,err,energy,div,field
    assert [q['run_id'] for q in runs]==A['allowed_run_ids']
    for first,second in [('A_on','A_off'),('B_shear','B_speed')]:
        for key in ['global_vector_RMSE','ROI_vector_RMSE']:
            x,y=stats[first][key],stats[second][key];assert x>0 and y>0 and abs(x-y)<=1e-7 and abs(x-y)/max(x,y)<=1e-4
    (R/'noise').mkdir();noise={}
    for seed in [2026100701,2026100702,2026100703,2026100704]:
        p=R/'noise'/str(seed)
        with (R/('noise_'+str(seed)+'.log')).open('wb') as log:subprocess.run([str(R/'bin/native_e1_audit'),'noise',str(p)],env=dict(os.environ,GADEN_RNG_SEED=str(seed)),stdout=log,check=True)
        assert sha(p)==E0['native_noise_table_bounds'][str(seed)]['table_sequence_sha256'];noise[str(seed)]={'max_abs':float(abs(np.fromfile(p,dtype='<f4')).max()),'table_sequence_sha256':sha(p)}
    domain=read(R/'frozen/M0_DOMAIN_ROI_GUARD_CONTRACT.json');source=read(R/'frozen/M0_SOURCE_CONTRACT.json');geom=rows(R/'M0_UAV_ROUTE_POINTS.csv');history=[];hq=[]
    for row in A['all_frozen_rows']:
        rid=row['run_id']
        if rid not in done:continue
        manifest=next(q for q in old1+old2 if q['run_id']==rid);audit=Path(manifest['native_audit_path']);result=Path(manifest['native_raw_path']);ref=BASE/'e1_audit'/('m0r0_U0_'+row['source_id']+'_r'+str(row['realization']).zfill(2));report,_=qualify(row,audit,result,ref,domain,source,stats[row['wind_arm']],noise[row['master_seed']],geom);assert report['qualified'],(rid,report['failures']);hq.append(report)
        history.append({'frozen_row':row,'audit':str(audit),'result':str(result),'sim_yaml':str(result.parent/'sim.yaml'),'manifest':manifest})
    used=set()
    for proc in Path('/proc').glob('[0-9]*'):
        try:
            for v in (proc/'environ').read_bytes().split(b'\0'):
                if v.startswith(b'ROS_DOMAIN_ID='):used.add(int(v.split(b'=')[1]))
        except (OSError,ValueError):pass
    domainid=next(d for d in range(228,219,-1) if d not in used)
    write('E3_HISTORY_INDEX.json',history);write('E3_HISTORY_REQUALIFICATION.json',hq)
    write('E3_ASSET_MANIFEST.json',{'runs':runs,'asset_files':assets,'generator_sha256':sha(GEN),'libgaden_sha256':sha(LIB),'helper_sha256':sha(R/'bin/native_e1_audit'),'source_sha256':E0['source_sha256'],'ROS_DOMAIN_ID':domainid,'wind_readback_stats':stats,'noise_tables':noise})
    write('E3_PREQUALIFICATION.json',{'status':'E3_RUNTIME_PREREQUISITES_PASS','new_scientific_runs':0,'prior_native_manifests_verified':previous,'prior12_requalified':len(hq),'actual_winds_readback':5,'effective_yaml_configs_verified':28,'all_result_leaves_absent':True,'resources':resources(),'R0_39_unchanged':True,'scientific_design_changes':0});print('E3_PREQUALIFICATION_PASS_NO_SCIENTIFIC_RUNS')
except Exception as e:
    write('E3_PREQUALIFICATION.json',{'status':'M0_PREREQUISITE_HOLD','stage':'E3_PREFLIGHT','new_scientific_runs':0,'error':str(e),'traceback':traceback.format_exc()});raise
