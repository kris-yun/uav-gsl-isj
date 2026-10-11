import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,hashlib,subprocess,os,time,psutil
W=Path(__file__).resolve().parent;B=W.parents[1]
M2=B/'outputs/PMFS_M2_PROCESS_OBSERVATION_DISCRIMINATION_20261010';O=B/'outputs/PMFS_RK0_RESPONSE_STATE_NECESSITY_20261010'
c=json.loads((O/'frozen_contract.json').read_text(encoding='utf-8'))
for n,h in c['executable_source_sha256'].items():assert hashlib.sha256((O/'source'/n).read_bytes()).hexdigest()==h,n
assert not (O/'EXECUTION_LEDGER.json').exists()
start=time.perf_counter();peak=0;diskpeak=0;stop=None;env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1')
with (O/'RUN.stdout').open('w',encoding='utf-8') as stdout,(O/'RUN.stderr').open('w',encoding='utf-8') as stderr:
    p=subprocess.Popen([sys.executable,'-B','-X','utf8',str(O/'source/run_rk0.py'),'--m2',str(M2),'--output',str(O)],stdout=stdout,stderr=stderr,env=env)
    q=psutil.Process(p.pid)
    while p.poll() is None:
        elapsed=time.perf_counter()-start
        try:
            peak=max(peak,q.memory_info().rss)
        except psutil.NoSuchProcess:pass
        disk=sum(f.stat().st_size for f in O.rglob('*') if f.is_file());diskpeak=max(diskpeak,disk)
        if elapsed>c['wall_limit_seconds']:stop='WALL_LIMIT'
        if peak>c['process_RSS_limit_bytes']:stop='RSS_LIMIT'
        if disk>c['new_disk_limit_bytes']:stop='DISK_LIMIT'
        if stop:
            p.terminate();p.wait(timeout=20);break
        time.sleep(.1)
    exitcode=p.wait()
ledger=dict(status='PASS_COMPLETED_FROZEN_READOUT_GATE' if exitcode==0 and stop is None else 'FAIL_STOP',
  exitcode=exitcode,resource_stop=stop,wall_seconds=time.perf_counter()-start,peak_RSS_bytes=peak,peak_output_bytes=diskpeak,
  contract_SHA256=hashlib.sha256((O/'frozen_contract.json').read_bytes()).hexdigest(),batch_entry_count=1,
  new_gas=0,new_CFD=0,new_ROS=0,new_native_candidate_forward=0,new_navigation=0,new_network_training=0,new_VM=0,
  own_child_process_running=p.poll() is None)
(O/'EXECUTION_LEDGER.json').write_text(json.dumps(ledger,indent=2)+'\n',encoding='utf-8')
print(json.dumps(ledger,indent=2))
if exitcode:print((O/'RUN.stderr').read_text(encoding='utf-8')[-7000:]);sys.exit(exitcode)
