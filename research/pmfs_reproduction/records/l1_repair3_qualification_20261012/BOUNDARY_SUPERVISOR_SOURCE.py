
from pathlib import Path
import subprocess,time,json,os,signal,hashlib,shutil
root=Path('/mnt/hgfs/workspace/PMFS_L1_REPAIR3_QUALIFICATION_20261012')
assert not (root/'COMPUTATION_ANCHOR.json').exists(), 'NO_REPAIR_OR_BUDGET_RESET'
conf=json.loads((root/'REPAIR3_FROZEN_CONTRACT.json').read_text())
assert hashlib.sha256((root/'REPAIR3_FROZEN_CONTRACT.json').read_bytes()).hexdigest()=='2576f444f8172b09291f0c15832409fe10d757294672a2b1640add68fa1fae3f'
for entry in Path('/proc').iterdir():
 if not entry.name.isdigit():continue
 try:args=(entry/'cmdline').read_bytes().split(b'\0');exe=args[0].decode(errors='replace');argv=b' '.join(args[:5]).decode(errors='replace')
 except (PermissionError,FileNotFoundError,ProcessLookupError):continue
 if 'l1_reference' in exe or ('python' in exe and any(x in argv for x in ('repair_boundary.py','repair_sampler.py','l1_prepare_wind.py','r4_generate.py','r4_infer.py'))):raise RuntimeError('CONFLICTING_SCIENTIFIC_PROCESS_STOP:'+argv)
env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',TMPDIR=str(root/'tmp'))
(root/'tmp').mkdir(exist_ok=False)
start=time.monotonic();anchor={'UTC':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),'monotonic_s':start,'pre_forward_total_cap_s':600,'whole_cap_s':900,'reservation_s':900,'gas_calls':0,'cumulative_repair':3}
(root/'COMPUTATION_ANCHOR.json').write_text(json.dumps(anchor,indent=2)+'\n')
def limit():
 import resource
 resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
 resource.setrlimit(resource.RLIMIT_CORE,(0,0))
peak=0;reason=None
with (root/'BOUNDARY.stdout.log').open('w') as stdout,(root/'BOUNDARY.stderr.log').open('w') as stderr:
 p=subprocess.Popen(['python3',str(root/'repair_boundary.py')],env=env,stdout=stdout,stderr=stderr,preexec_fn=limit,start_new_session=True)
 while p.poll() is None:
  elapsed=time.monotonic()-start
  try:
   status=Path(f'/proc/{p.pid}/status').read_text();rss=int(next(x for x in status.splitlines() if x.startswith('VmRSS:')).split()[1])*1024;peak=max(peak,rss)
  except (FileNotFoundError,StopIteration):pass
  disk=sum(x.stat().st_size for x in root.rglob('*') if x.is_file())
  if elapsed>=570:reason='BOUNDARY_STAGE_570S_HARD_STOP'
  elif peak>1024**3:reason='RSS_1GiB_HARD_STOP'
  elif disk>1024**3 or shutil.disk_usage(root).free<4*1024**3 or shutil.disk_usage('/').free<4*1024**3:reason='DISK_CAP_OR_RESERVE_HARD_STOP'
  if reason:
   os.killpg(p.pid,signal.SIGKILL);p.wait();break
  time.sleep(.1)
elapsed=time.monotonic()-start
receipt={'returncode':p.returncode,'hard_stop':reason,'stage_wall_s':elapsed,'monitor_peak_RSS_bytes':peak,'forward_calls':0,'native_goals':0,'retry':False}
(root/'BOUNDARY_SUPERVISOR_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt));print((root/'BOUNDARY.stdout.log').read_text()[-6000:]);print((root/'BOUNDARY.stderr.log').read_text()[-3000:])
