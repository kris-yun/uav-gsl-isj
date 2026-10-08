"""Exactly the first eight frozen U0 rows. No intervention code path."""
from pathlib import Path
import csv,datetime,hashlib,json,os,resource,shutil,subprocess,time,traceback
ROOT=Path('/home/zyc/ros2_ws/m0_clean_support_r0_20261007');GEN=Path('/home/zyc/ocb_r2_seeded_gaden/install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator');LIB=Path('/home/zyc/ocb_r2_seeded_gaden/install/gaden_common/lib/libgaden.so')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def check_space():
    m={r.split(':')[0]:int(r.split()[1])*1024 for r in Path('/proc/meminfo').read_text().splitlines() if len(r.split())>1 and r.split()[1].isdigit()}
    assert shutil.disk_usage(ROOT).free>=12*1024**3 and m['MemAvailable']>=3*1024**3
def rss(path):
    text=path.read_text();line=next(q for q in text.splitlines() if 'Maximum resident set size (kbytes)' in q);return int(line.rsplit(':',1)[1])*1024
if __name__=='__main__':
    e0=json.loads((ROOT/'E0_QUALIFICATION.json').read_text());assert e0['status']=='M0_E0_RUNTIME_QUALIFIED' and e0['scientific_runs']==0
    M=json.loads((ROOT/'ASSET_MANIFEST.json').read_text());runs=M['base_runs_only'];assert len(runs)==8 and all(r['wind_arm']=='U0' for r in runs)
    if (ROOT/'E1_PROGRESS.json').exists():raise RuntimeError('No automatic rerun or resume of completed/failed campaign.')
    route=ROOT/'M0_UAV_ROUTE_POINTS.csv';assert sha(route)==json.loads((ROOT/'E1_EXECUTION_SEAL.json').read_text())['route_sha256']
    done=[];attempted=0;start=time.monotonic()
    try:
        for r in runs:
            check_space();assert sha(GEN)==e0['generator_sha256'] and sha(LIB)==e0['libgaden_sha256']
            for row in M['asset_files']:assert sha(ROOT/row['path'])==row['sha256']
            rid=r['run_id'];result=Path(r['effective_output_path']);assert result.resolve().is_relative_to(ROOT) and result.parent.name==rid and not result.exists()
            audit=ROOT/'e1_audit'/rid;audit.mkdir(parents=True);env=dict(os.environ,GADEN_RNG_SEED=r['master_seed'],OMP_NUM_THREADS='1',OMP_DYNAMIC='FALSE',OMP_PROC_BIND='TRUE',ROS_DOMAIN_ID=str(e0['selected_ROS_DOMAIN_ID']),ROS_LOG_DIR=str(audit/'ros_logs'),TMPDIR=str(audit/'tmp'));Path(env['TMPDIR']).mkdir()
            attempted+=1;dump(ROOT/'E1_PROGRESS.json',{'status':'RUNNING_U0_ONLY','attempted':attempted,'completed':len(done),'run_id':rid,'intervention_runs':0})
            argv=['/usr/bin/time','-v','-o',str(audit/'simulation.time.txt'),*r['argv']];s0=time.monotonic()
            with (audit/'simulation.stdout.log').open('wb') as log:code=subprocess.run(argv,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
            wall=time.monotonic()-s0;assert code==0,('native generator exit',code,rid)
            assert 'finished correctly!' in (audit/'simulation.stdout.log').read_text(errors='replace')
            assert (result/'RECORD_TIMELINE.tsv').exists() and (result/'iteration_0').exists()
            simrss=rss(audit/'simulation.time.txt');assert simrss<=2*1024**3
            helperargs=[str(ROOT/'bin/native_e1_audit'),'e1',str(ROOT/'projects/U0'),str(result),str(audit),str(route)]
            s1=time.monotonic()
            with (audit/'extraction.stdout.log').open('wb') as log:code=subprocess.run(['/usr/bin/time','-v','-o',str(audit/'extraction.time.txt'),*helperargs],env=env,stdout=log,stderr=subprocess.STDOUT).returncode
            extraction=time.monotonic()-s1;assert code==0,('native extraction/parity failure',code,rid)
            exrss=rss(audit/'extraction.time.txt');assert exrss<=2*1024**3
            actual={'run_id':rid,'source_id':r['source_id'],'realization':int(r['realization']),'master_seed':int(r['master_seed']),'wind_arm':'U0','simulation_argv':r['argv'],'extraction_argv':helperargs,'runtime_env':{k:env[k] for k in ['GADEN_RNG_SEED','OMP_NUM_THREADS','OMP_DYNAMIC','OMP_PROC_BIND','ROS_DOMAIN_ID','ROS_LOG_DIR','TMPDIR','LD_LIBRARY_PATH']},'generator_sha256':sha(GEN),'libgaden_sha256':sha(LIB),'native_helper_sha256':sha(ROOT/'bin/native_audit'),'sim_wall_s':wall,'extraction_wall_s':extraction,'sim_peak_RSS_bytes':simrss,'extraction_peak_RSS_bytes':exrss,'output_bytes':sum(p.stat().st_size for folder in [result,audit] for p in folder.rglob('*') if p.is_file()),'native_raw_path':str(result),'native_audit_path':str(audit),'simulation_exit_code':0,'extraction_exit_code':0}
            actual['native_helper_sha256']=sha(ROOT/'bin/native_e1_audit')
            dump(audit/'RUN_MANIFEST.json',actual)
            with (audit/'RAW_OUTPUT_SHA256.csv').open('w') as f:
                w=csv.writer(f,lineterminator='\n');w.writerow(['path','bytes','sha256'])
                for folder in [result,audit]:
                    for p in sorted(folder.rglob('*')):
                        if p.is_file() and p.name!='RAW_OUTPUT_SHA256.csv':w.writerow([p.relative_to(ROOT).as_posix(),p.stat().st_size,sha(p)])
            done.append(actual);dump(ROOT/'E1_PROGRESS.json',{'status':'RUNNING_U0_ONLY','attempted':attempted,'completed':len(done),'intervention_runs':0,'completed_ids':[x['run_id'] for x in done]})
            print(json.dumps({'completed_U0':len(done),'run_id':rid,'simulation_s':wall,'extraction_s':extraction}),flush=True)
        dump(ROOT/'E1_COMPLETED_RUNS.json',done);dump(ROOT/'E1_PROGRESS.json',{'status':'ALL8_U0_FINISHED_STOPPED_AWAITING_AUDIT','attempted':attempted,'completed':8,'intervention_runs':0,'wall_s':time.monotonic()-start,'auto_intervention':False})
        print('E1_ALL8_FINISHED_AND_STOPPED',flush=True)
    except Exception as e:
        dump(ROOT/'E1_PROGRESS.json',{'status':'M0_PREREQUISITE_HOLD','stage':'E1_RUNTIME','attempted':attempted,'completed':len(done),'intervention_runs':0,'error':str(e),'traceback':traceback.format_exc()});raise
