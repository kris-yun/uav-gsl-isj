"""Enforce one RK2 comparison: 600s, 1GiB RSS/output, progress watchdog."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import argparse,subprocess,time,json,os,hashlib
import psutil
def main(parent,out):
    started=out/'EXECUTION_STARTED.json';assert not started.exists(),'Refuse second unapproved entry'
    contract=json.loads((out/'contract.json').read_text(encoding='utf-8'))
    digest=hashlib.sha256((out/'contract.json').read_bytes()).hexdigest()
    assert digest==(out/'PRE_RUN_CONTRACT_SHA256.txt').read_text().split()[0]
    started.write_text(json.dumps(dict(entry_count=1,contract_SHA256=digest,wall_start_unix=time.time()),indent=2)+'\n',encoding='utf-8')
    env=dict(os.environ)
    for k in ['OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS','NUMEXPR_NUM_THREADS']:env[k]='1'
    env['PYTHONDONTWRITEBYTECODE']='1'
    command=[sys.executable,'-B','-X','utf8',str(out/'source/run_rk2.py'),'--parent',str(parent),'--out',str(out)]
    beginning=time.perf_counter();peak=0;stop=None;last_size_poll=0.;output_size=0;latest_sequence=0;last_progress=beginning;next_note=beginning+60
    with (out/'RUN.stdout').open('w',encoding='utf-8') as so,(out/'RUN.stderr').open('w',encoding='utf-8') as se:
        p=subprocess.Popen(command,stdout=so,stderr=se,env=env)
        while p.poll() is None:
            now=time.perf_counter()
            try:
                process=psutil.Process(p.pid);rss=process.memory_info().rss+sum(c.memory_info().rss for c in process.children(recursive=True));peak=max(peak,rss)
            except psutil.NoSuchProcess:rss=0
            progress={}
            if (out/'PROGRESS.json').exists():
                try:progress=json.loads((out/'PROGRESS.json').read_text(encoding='utf-8'))
                except json.JSONDecodeError:progress={}
                if progress.get('sequence',0)!=latest_sequence:
                    latest_sequence=progress['sequence'];last_progress=now
            if now-last_size_poll>=2:
                output_size=sum(q.stat().st_size for q in out.rglob('*') if q.is_file());last_size_poll=now
            if now-beginning>contract['wall_limit_s']:stop='WALL_LIMIT_600S'
            elif peak>contract['RSS_limit_bytes']:stop='RSS_LIMIT_1GIB'
            elif output_size>contract['output_limit_bytes']:stop='OUTPUT_LIMIT_1GIB'
            elif now-last_progress>120:stop='TWO_60S_INTERVALS_NO_PROGRESS'
            if now>=next_note:
                print(json.dumps(dict(wall_s=now-beginning,RSS_MiB=rss/1024**2,latest_progress=progress),ensure_ascii=False),flush=True);next_note+=60
            if stop:
                try:
                    process=psutil.Process(p.pid)
                    for c in process.children(recursive=True):c.terminate()
                    process.terminate()
                except psutil.NoSuchProcess:pass
                break
            time.sleep(.2)
        try:code=p.wait(timeout=5)
        except subprocess.TimeoutExpired:p.kill();code=p.wait()
    ledger=dict(status='PASS_ONE_BOUNDED_COMPARISON_COMPLETED' if code==0 and stop is None else 'STOP_BOUNDED_COMPARISON',entry_count=1,
        exitcode=code,resource_stop=stop,wall_s=time.perf_counter()-beginning,peak_RSS_bytes=peak,
        output_bytes_before_ledger=sum(q.stat().st_size for q in out.rglob('*') if q.is_file()),new_physics=0,new_GADEN_CFD_ROS_VM_navigation_or_network_training=0,
        source_query_and_statistical_model_fits_are_new=True,child_running=False,command=command,contract_SHA256=digest)
    (out/'EXECUTION_LEDGER.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(ledger,ensure_ascii=False,indent=2),flush=True)
    return 0 if ledger['status'].startswith('PASS') else 1
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--parent',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();raise SystemExit(main(a.parent,a.out))
