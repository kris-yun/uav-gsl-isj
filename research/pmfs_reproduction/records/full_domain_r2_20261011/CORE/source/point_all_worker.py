from pathlib import Path
import os,json,time,subprocess,signal,shutil,csv
T=Path(__file__).resolve().parent;D=Path('/mnt/hgfs/workspace/PMFS_FULL_DOMAIN_R2_DATA_20261011');P=json.loads((T/'REFERENCE_EXECUTION_CONTRACT.json').read_text());B=Path('/dev/shm/pmfs_r2/native_build/native_batch_entry');L=dict(status='WAITING_SERIAL_REFERENCES',records=[],native_forward_calls=0)
def dump(): (D/'N_POINT_ALL_LEDGER.json').write_text(json.dumps(L,indent=2))
dump()
while not (D/'REFERENCE_LEDGER.json').exists() or json.loads((D/'REFERENCE_LEDGER.json').read_text())['status']=='RUNNING':
 assert time.time()-P['entry_unix']<14400;time.sleep(2)
assert json.loads((D/'REFERENCE_LEDGER.json').read_text())['status'].startswith('PASS'),'Dependent input invalid; no native paired method started'
e=os.environ.copy();e.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',LD_LIBRARY_PATH=json.loads(Path('/home/zyc/ros2_ws/pmfs_native_mechanism_closure_r1_20261011/ACTUAL_BINARY_PROVENANCE.json').read_text())['LD_LIBRARY_PATH']);L['status']='RUNNING';dump()
try:
 for group in ['R0','R1']:
  out=D/'N_POINT_ALL'/group;out.parent.mkdir(exist_ok=True);start=time.monotonic();peak=0
  with (D/f'point_all_{group}.log').open('w') as f:
   p=subprocess.Popen([str(B),'point_all',str(T/'inputs'/group),str(T/'N_POINT_ALL_JOBS.csv'),str(out)],env=e,stdout=f,stderr=f,start_new_session=True)
   while p.poll() is None:
    rss=0
    for q in Path('/proc').glob('[0-9]*/status'):
     try:
      if os.getpgid(int(q.parent.name))==p.pid:rss+=next(int(r.split()[1])*1024 for r in q.read_text().splitlines() if r.startswith('VmRSS:'))
     except (OSError,StopIteration):pass
    peak=max(peak,rss)
    if rss>1610612736 or time.monotonic()-start>240 or time.time()-P['entry_unix']>14400:
     os.killpg(p.pid,signal.SIGINT);p.wait(timeout=10);raise RuntimeError('POINT_BUDGET_CAP')
    time.sleep(.1)
   assert p.returncode==0,(D/f'point_all_{group}.log').read_text()[-2000:]
  count=sum(len(list(csv.DictReader(q.open()))) for q in out.rglob('candidates.csv'));assert count==32;L['native_forward_calls']+=count;L['records'].append(dict(group=group,count=count,wall_s=time.monotonic()-start,sampled_peak_RSS=peak));dump()
 L['status']='PASS_ALL32_MATCHED_POINT_HYPOTHESES_2_STATES'
except Exception as ex:L.update(status='TECHNICAL_POINT_STOP',error=repr(ex))
finally:dump();print(json.dumps(L),flush=True)
