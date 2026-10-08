"""28-only E3. Qualify EACH arm BEFORE starting the next. No retries."""
from pathlib import Path
import csv,hashlib,json,os,shutil,subprocess,time,traceback
from qualify_run import qualify,rows
R=Path('/home/zyc/ros2_ws/m0_clean_support_r0_20261007/e3_final');GEN=Path('/home/zyc/ocb_r2_seeded_gaden/install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator');LIB=Path('/home/zyc/ocb_r2_seeded_gaden/install/gaden_common/lib/libgaden.so')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def dump(n,x):(R/n).write_text(json.dumps(x,indent=2)+'\n')
def rss(p):return int(next(q for q in p.read_text().splitlines() if 'Maximum resident set size (kbytes)' in q).rsplit(':',1)[1])*1024
def check(M):
    mem={q.split(':')[0]:int(q.split()[1])*1024 for q in Path('/proc/meminfo').read_text().splitlines() if len(q.split())>1 and q.split()[1].isdigit()};assert shutil.disk_usage(R).free>=12*1024**3 and mem['MemAvailable']>=3*1024**3
    assert sha(GEN)==M['generator_sha256'] and sha(LIB)==M['libgaden_sha256'] and sha(R/'bin/native_e1_audit')==M['helper_sha256']
    for p,h in M['source_sha256'].items():assert sha(p)==h
    for q in M['asset_files']:assert sha(R/q['path'])==q['sha256']
if __name__=='__main__':
    assert read(R/'E3_PREQUALIFICATION.json')['status']=='E3_RUNTIME_PREREQUISITES_PASS';assert not (R/'E3_PROGRESS.json').exists()
    A=read(R/'E3_AUTHORIZATION.json');M=read(R/'E3_ASSET_MANIFEST.json');seal=read(R/'E3_EXECUTION_SEAL.json');assert len(M['runs'])==28 and [q['run_id'] for q in M['runs']]==A['allowed_run_ids']
    for n,h in seal['scripts_sha256'].items():assert sha(R/n)==h,(n,'sealed code')
    D=read(R/'frozen/M0_DOMAIN_ROI_GUARD_CONTRACT.json');S=read(R/'frozen/M0_SOURCE_CONTRACT.json');geometry=rows(R/'M0_UAV_ROUTE_POINTS.csv');assert sha(R/'M0_UAV_ROUTE_POINTS.csv')==seal['route_sha256']
    done=[];attempted=0;start=time.monotonic()
    try:
        for row in M['runs']:
            check(M);rid=row['run_id'];result=Path(row['effective_output_path']);audit=R/'audit'/rid;assert result.resolve().is_relative_to(R) and result.parent.name==rid and not result.exists() and not audit.exists();audit.mkdir(parents=True);(audit/'tmp').mkdir()
            env=dict(os.environ,GADEN_RNG_SEED=row['master_seed'],OMP_NUM_THREADS='1',OMP_DYNAMIC='FALSE',OMP_PROC_BIND='TRUE',ROS_DOMAIN_ID=str(M['ROS_DOMAIN_ID']),ROS_LOG_DIR=str(audit/'ros_logs'),TMPDIR=str(audit/'tmp'));attempted+=1
            dump('E3_PROGRESS.json',{'status':'RUNNING_28_ONLY','attempted':attempted,'qualified_completed':len(done),'run_id':rid,'new_U0_runs':0,'automatic_retry':False})
            s=time.monotonic()
            with (audit/'simulation.stdout.log').open('wb') as log:code=subprocess.run(['/usr/bin/time','-v','-o',str(audit/'simulation.time.txt'),*row['argv']],env=env,stdout=log,stderr=subprocess.STDOUT).returncode
            simwall=time.monotonic()-s;assert code==0 and 'finished correctly!' in (audit/'simulation.stdout.log').read_text(errors='replace');assert (result/'RECORD_TIMELINE.tsv').exists();simrss=rss(audit/'simulation.time.txt');assert simrss<=2*1024**3
            helper=[str(R/'bin/native_e1_audit'),'e1',row['project'],str(result),str(audit),str(R/'M0_UAV_ROUTE_POINTS.csv')];s=time.monotonic()
            with (audit/'extraction.stdout.log').open('wb') as log:code=subprocess.run(['/usr/bin/time','-v','-o',str(audit/'extraction.time.txt'),*helper],env=env,stdout=log,stderr=subprocess.STDOUT).returncode
            exwall=time.monotonic()-s;assert code==0;exrss=rss(audit/'extraction.time.txt');assert exrss<=2*1024**3;check(M)
            qstart=time.monotonic();rep,records=qualify(row,audit,result,row['reference_audit'],D,S,M['wind_readback_stats'][row['wind_arm']],M['noise_tables'][row['master_seed']],geometry)
            assert sha(Path(row['project'])/'wind/wind_iteration_0')==row['expected_wind_sha256'];assert sha(R/'noise'/row['master_seed'])==M['noise_tables'][row['master_seed']]['table_sequence_sha256']
            (audit/'QUALIFICATION.json').write_text(json.dumps(rep,indent=2)+'\n')
            with (audit/'ALL_RECORD_SUPPORT.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(records[0]),lineterminator='\n');w.writeheader();w.writerows(records)
            assert rep['qualified'],(rid,rep['failures'])
            actual={'run_id':rid,'wind_arm':row['wind_arm'],'source_id':row['source_id'],'realization':int(row['realization']),'master_seed':int(row['master_seed']),'native_audit_path':str(audit),'native_raw_path':str(result),'simulation_argv':row['argv'],'extraction_argv':helper,'runtime_env':{k:env[k] for k in ['GADEN_RNG_SEED','OMP_NUM_THREADS','OMP_DYNAMIC','OMP_PROC_BIND','ROS_DOMAIN_ID','ROS_LOG_DIR','TMPDIR','LD_LIBRARY_PATH']},'generator_sha256':sha(GEN),'libgaden_sha256':sha(LIB),'helper_sha256':sha(R/'bin/native_e1_audit'),'wind_sha256':sha(Path(row['project'])/'wind/wind_iteration_0'),'sim_wall_s':simwall,'extraction_wall_s':exwall,'qualification_wall_s':time.monotonic()-qstart,'sim_peak_RSS_bytes':simrss,'extraction_peak_RSS_bytes':exrss,'output_bytes':sum(p.stat().st_size for d in [result,audit] for p in d.rglob('*') if p.is_file()),'qualified':True,'qualification':rep}
            (audit/'RUN_MANIFEST.json').write_text(json.dumps(actual,indent=2)+'\n')
            with (audit/'RAW_OUTPUT_SHA256.csv').open('w') as f:
                w=csv.writer(f,lineterminator='\n');w.writerow(['path','bytes','sha256'])
                for d in [result,audit]:
                    for p in sorted(d.rglob('*')):
                        if p.is_file() and p.name!='RAW_OUTPUT_SHA256.csv':w.writerow([p.relative_to(R).as_posix(),p.stat().st_size,sha(p)])
            done.append(actual);dump('E3_COMPLETED_RUNS.json',done);print(json.dumps({'qualified_new_runs':len(done),'run_id':rid,'min_3sigma_margin_m':rep['minimum_3sigma_margin_m'],'parity_max_diff':rep['native_parity_max_abs_diff']}),flush=True)
        dump('E3_PROGRESS.json',{'status':'ALL28_QUALIFIED_STOPPED_AWAITING_FINAL_EVALUATION','attempted':attempted,'qualified_completed':28,'new_U0_runs':0,'total_M0_runs':40,'wall_s':time.monotonic()-start,'no_additional_simulations':True});print('E3_ALL28_QUALIFIED_SIMULATION_STOPPED',flush=True)
    except Exception as e:
        dump('E3_PROGRESS.json',{'status':'M0_PREREQUISITE_HOLD','attempted':attempted,'qualified_completed':len(done),'error':str(e),'traceback':traceback.format_exc(),'no_retry':True,'final_scientific_scoring_blocked':True});raise
