"""Bound the one authorized RK1 arithmetic batch; never start ROS or a VM."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import argparse,json,time,subprocess,os,hashlib
import psutil
def size(root):return sum(p.stat().st_size for p in root.rglob('*') if p.is_file())
def main(parent,out):
    c=json.loads((out/'contract.json').read_text(encoding='utf-8'));assert not (out/'EXECUTION_STARTED.json').exists()
    stamp=dict(batch_entry_count=1,contract_SHA256=hashlib.sha256((out/'contract.json').read_bytes()).hexdigest())
    (out/'EXECUTION_STARTED.json').write_text(json.dumps(stamp,indent=2)+'\n',encoding='utf-8')
    env=os.environ.copy()
    for name in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:env[name]='1'
    started=time.perf_counter();peak=0;disk=0;stopped=None
    with (out/'RUN.stdout').open('w',encoding='utf-8') as stdout,(out/'RUN.stderr').open('w',encoding='utf-8') as stderr:
        cmd=[sys.executable,'-B','-X','utf8',str(out/'source/run_rk1.py'),'--parent',str(parent),'--out',str(out)]
        child=subprocess.Popen(cmd,stdout=stdout,stderr=stderr,env=env);pp=psutil.Process(child.pid)
        while child.poll() is None:
            try:peak=max(peak,pp.memory_info().rss)
            except psutil.NoSuchProcess:pass
            disk=max(disk,size(out));elapsed=time.perf_counter()-started
            if elapsed>c['wall_limit_s']:stopped='WALL_LIMIT'
            elif peak>c['RSS_limit_bytes']:stopped='RSS_LIMIT'
            elif disk>c['new_output_limit_bytes']:stopped='OUTPUT_DISK_LIMIT'
            if stopped:
                child.terminate()
                try:child.wait(timeout=5)
                except subprocess.TimeoutExpired:child.kill();child.wait()
                break
            time.sleep(.1)
        code=child.wait()
    ledger=dict(status='PASS_COMPLETED_ONE_ARITHMETIC_BATCH' if code==0 and stopped is None else 'STOP_RUNTIME_OR_RESOURCE',contract_SHA256=stamp['contract_SHA256'],batch_entry_count=1,exitcode=code,resource_stop=stopped,wall_s=time.perf_counter()-started,peak_RSS_bytes=peak,output_bytes_before_ledger=size(out),peak_output_bytes=disk,own_child_running=child.poll() is None,executed_command=cmd,new_phi_queries=0,new_GADEN=0,new_CFD=0,new_ROS=0,new_VM=0,new_navigation=0,new_network_training=0,kernel_tables_fitted=8 if code==0 else 'SEE_PARTIAL_STDOUT',native_input_files_modified=False)
    (out/'EXECUTION_LEDGER.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(ledger,ensure_ascii=False,indent=2));return 0 if code==0 and stopped is None else 1
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--parent',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();raise SystemExit(main(a.parent,a.out))
