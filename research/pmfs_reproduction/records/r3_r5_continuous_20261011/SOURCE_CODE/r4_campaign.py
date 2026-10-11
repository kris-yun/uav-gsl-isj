"""One authorized bounded batch. Guards child processes, preserves every artifact."""
import datetime,hashlib,json,os,pathlib,subprocess,sys,time,shutil
import psutil
BASE=pathlib.Path(__file__).resolve().parents[1];OUT=BASE/'outputs/PMFS_R3_R5_CONTINUOUS_20261011'
def main():
    for f in ['R4_INTERFACE_PREFLIGHT.json','R4_NUMERICAL_QUALIFICATION.json']:
        assert json.loads((OUT/f).read_text(encoding='utf-8'))['status']=='PASS' if f.startswith('R4_INTERFACE') else (OUT/f).exists()
    if (OUT/'R4_BATCH_START.json').exists():raise RuntimeError('Batch already started: resume requires checkpoint audit, no blind rerun')
    started=time.monotonic();receipt={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'parent_pid':os.getpid(),'batch_wall_limit_s':14400,'task_count':36,'source_files_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (BASE/'work').glob('r4_*.py')}}
    (OUT/'R4_BATCH_START.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');peak=0;stage='NOT_STARTED';process=None
    try:
        for stage,args in [('generate',['r4_generate.py']),('infer_development',['r4_infer.py','development']),('evaluate_development',['r4_evaluate.py','development']),('infer_heldout',['r4_infer.py','heldout']),('evaluate_heldout',['r4_evaluate.py','heldout'])]:
            stdout=(OUT/f'R4_BATCH_{stage}.stdout.log').open('w',encoding='utf-8');stderr=(OUT/f'R4_BATCH_{stage}.stderr.log').open('w',encoding='utf-8')
            env=os.environ.copy();env.update(OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
            process=subprocess.Popen([sys.executable,'-B','-X','utf8',str(BASE/'work'/args[0]),*args[1:]],cwd=BASE,stdout=stdout,stderr=stderr,env=env)
            print(json.dumps({'stage':stage,'pid':process.pid}),flush=True)
            while process.poll() is None:
                try:rss=psutil.Process(process.pid).memory_info().rss
                except psutil.NoSuchProcess:rss=0
                peak=max(peak,rss);wall=time.monotonic()-started;free=shutil.disk_usage(OUT).free
                size=sum(f.stat().st_size for f in (OUT/'raw').rglob('*') if f.is_file()) if (OUT/'raw').exists() else 0
                if rss>1073741824 or wall>14400 or free<4294967296 or size>8589934592:raise RuntimeError(f'GUARD_STOP rss={rss} wall={wall} free={free} output={size}')
                (OUT/'R4_BATCH_LIVE.json').write_text(json.dumps({'stage':stage,'wall_s':wall,'peak_RSS_bytes':peak,'output_bytes':size,'child_pid':process.pid},indent=2)+'\n',encoding='utf-8')
                time.sleep(2)
            stdout.close();stderr.close()
            if process.returncode!=0:raise RuntimeError(f'{stage} exited {process.returncode}; see immutable stderr')
        status='BATCH_COMPLETED_NO_RETRY'
    except BaseException as e:
        if process and process.poll() is None:process.terminate();process.wait(timeout=10)
        status='STOP_'+str(e)
        raise
    finally:
        (OUT/'R4_BATCH_RECEIPT.json').write_text(json.dumps({'status':status,'last_stage':stage,'wall_s':time.monotonic()-started,'peak_RSS_bytes':peak,'VM_processes_started':0,'new_physics_batch_count':1,'reruns':0},indent=2)+'\n',encoding='utf-8')
    print(status,flush=True)
if __name__=='__main__':main()
