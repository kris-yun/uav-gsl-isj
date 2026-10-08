"""Exactly four directly authorized sentinel rows. No E3 path, no retry."""
from pathlib import Path
import csv,hashlib,json,os,shutil,subprocess,time,traceback
ROOT=Path('/home/zyc/ros2_ws/m0_clean_support_r0_20261007/e2_sentinel')
GEN=Path('/home/zyc/ocb_r2_seeded_gaden/install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator');LIB=Path('/home/zyc/ocb_r2_seeded_gaden/install/gaden_common/lib/libgaden.so')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def dump(n,x):(ROOT/n).write_text(json.dumps(x,indent=2)+'\n')
def rss(p):return int(next(q for q in p.read_text().splitlines() if 'Maximum resident set size (kbytes)' in q).rsplit(':',1)[1])*1024
def prerequisites(M):
    m={r.split(':')[0]:int(r.split()[1])*1024 for r in Path('/proc/meminfo').read_text().splitlines() if len(r.split())>1 and r.split()[1].isdigit()}
    assert shutil.disk_usage(ROOT).free>=12*1024**3 and m['MemAvailable']>=3*1024**3
    assert sha(GEN)==M['generator_sha256'] and sha(LIB)==M['libgaden_sha256'] and sha(ROOT/'bin/native_e1_audit')==M['helper_sha256']
    for p,h in M['source_sha256'].items():assert sha(p)==h
    for q in M['asset_files']:assert sha(ROOT/q['path'])==q['sha256']
if __name__=='__main__':
    assert read(ROOT/'E2_PREQUALIFICATION.json')['status']=='E2_RUNTIME_PREREQUISITES_PASS'
    A=read(ROOT/'M0_E2_AUTHORIZATION.json');M=read(ROOT/'E2_ASSET_MANIFEST.json');seal=read(ROOT/'E2_EXECUTION_SEAL.json')
    assert not (ROOT/'E2_PROGRESS.json').exists()
    assert A['direct_user_authorization'] and not A['E3_authorized'] and len(M['runs'])==4 and [r['run_id'] for r in M['runs']]==A['allowed_run_ids']
    for name,h in seal['scripts_sha256'].items():assert sha(ROOT/name)==h,(name,'pre-run seal')
    assert sha(ROOT/'M0_UAV_ROUTE_POINTS.csv')==seal['route_sha256'];done=[];attempted=0;start=time.monotonic()
    try:
        for r in M['runs']:
            prerequisites(M);rid=r['run_id'];assert r['source_id']=='S0' and r['realization']=='1' and r['master_seed']=='2026100701'
            result=Path(r['effective_output_path']);assert result.resolve().is_relative_to(ROOT) and result.parent.name==rid and not result.exists()
            audit=ROOT/'audit'/rid;assert not audit.exists();audit.mkdir(parents=True);(audit/'tmp').mkdir()
            env=dict(os.environ,GADEN_RNG_SEED='2026100701',OMP_NUM_THREADS='1',OMP_DYNAMIC='FALSE',OMP_PROC_BIND='TRUE',ROS_DOMAIN_ID=str(M['ROS_DOMAIN_ID']),ROS_LOG_DIR=str(audit/'ros_logs'),TMPDIR=str(audit/'tmp'))
            attempted+=1;dump('E2_PROGRESS.json',{'status':'RUNNING_FOUR_SENTINEL_ONLY','attempted':attempted,'completed':len(done),'run_id':rid,'new_U0_runs':0,'E3_runs':0})
            s0=time.monotonic()
            with (audit/'simulation.stdout.log').open('wb') as f:code=subprocess.run(['/usr/bin/time','-v','-o',str(audit/'simulation.time.txt'),*r['argv']],env=env,stdout=f,stderr=subprocess.STDOUT).returncode
            sw=time.monotonic()-s0;assert code==0 and 'finished correctly!' in (audit/'simulation.stdout.log').read_text(errors='replace')
            assert (result/'RECORD_TIMELINE.tsv').exists() and (result/'iteration_0').exists();sr=rss(audit/'simulation.time.txt');assert sr<=2*1024**3
            ha=[str(ROOT/'bin/native_e1_audit'),'e1',r['project'],str(result),str(audit),str(ROOT/'M0_UAV_ROUTE_POINTS.csv')];s1=time.monotonic()
            with (audit/'extraction.stdout.log').open('wb') as f:code=subprocess.run(['/usr/bin/time','-v','-o',str(audit/'extraction.time.txt'),*ha],env=env,stdout=f,stderr=subprocess.STDOUT).returncode
            ew=time.monotonic()-s1;assert code==0;er=rss(audit/'extraction.time.txt');assert er<=2*1024**3
            prerequisites(M)
            actual={'run_id':rid,'wind_arm':r['wind_arm'],'source_id':'S0','realization':1,'master_seed':2026100701,'simulation_argv':r['argv'],'extraction_argv':ha,'runtime_env':{k:env[k] for k in ['GADEN_RNG_SEED','OMP_NUM_THREADS','OMP_DYNAMIC','OMP_PROC_BIND','ROS_DOMAIN_ID','ROS_LOG_DIR','TMPDIR','LD_LIBRARY_PATH']},'generator_sha256':sha(GEN),'libgaden_sha256':sha(LIB),'native_helper_sha256':sha(ROOT/'bin/native_e1_audit'),'wind_sha256':sha(Path(r['project'])/'wind/wind_iteration_0'),'sim_wall_s':sw,'extraction_wall_s':ew,'sim_peak_RSS_bytes':sr,'extraction_peak_RSS_bytes':er,'output_bytes':sum(p.stat().st_size for folder in [result,audit] for p in folder.rglob('*') if p.is_file()),'native_raw_path':str(result),'native_audit_path':str(audit),'simulation_exit_code':0,'extraction_exit_code':0}
            (audit/'RUN_MANIFEST.json').write_text(json.dumps(actual,indent=2)+'\n')
            with (audit/'RAW_OUTPUT_SHA256.csv').open('w') as f:
                w=csv.writer(f,lineterminator='\n');w.writerow(['path','bytes','sha256'])
                for folder in [result,audit]:
                    for p in sorted(folder.rglob('*')):
                        if p.is_file() and p.name!='RAW_OUTPUT_SHA256.csv':w.writerow([p.relative_to(ROOT).as_posix(),p.stat().st_size,sha(p)])
            done.append(actual);dump('E2_COMPLETED_RUNS.json',done);print(json.dumps({'sentinel_completed':len(done),'run_id':rid,'simulation_s':sw,'extraction_s':ew}),flush=True)
        dump('E2_PROGRESS.json',{'status':'FOUR_SENTINEL_COMPLETED_STOPPED_AWAITING_AUDIT','attempted':attempted,'completed':4,'new_U0_runs':0,'E3_runs':0,'remaining_28_launched':False,'wall_s':time.monotonic()-start});print('E2_FOUR_FINISHED_AND_STOPPED',flush=True)
    except Exception as e:
        dump('E2_PROGRESS.json',{'status':'M0_E2_PREREQUISITE_HOLD','attempted':attempted,'completed':len(done),'new_U0_runs':0,'E3_runs':0,'error':str(e),'traceback':traceback.format_exc()});raise
