# Run only inside the existing guest. Read-only, no ROS start or mutations.

from pathlib import Path
import json,hashlib,datetime,os,subprocess
T=Path('/home/zyc/pmfs_e3_native_validation_20261009')
pre=json.loads((T/'ENVIRONMENT_PREFLIGHT.json').read_text()) if (T/'ENVIRONMENT_PREFLIGHT.json').exists() else None
processes=[];unreadable=0;unreadable_owned=0;owned_limited=[]
for d in Path('/proc').iterdir():
 if not d.name.isdigit() or int(d.name)==os.getpid():continue
 try:
  env=(d/'environ').read_bytes().split(b'\0')
  if b'ROS_DOMAIN_ID=76' in env:
   raw=(d/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
   processes.append({'pid':int(d.name),'comm':(d/'comm').read_text().strip(),'command':raw})
 except (OSError,PermissionError):
  unreadable+=1
  try:
   if d.stat().st_uid==os.getuid():
    unreadable_owned+=1
    try:comm=(d/'comm').read_text().strip()
    except OSError:comm='unreadable'
    owned_limited.append({'pid':int(d.name),'comm':comm})
  except OSError:pass
paths={
 'GSL':Path('/home/zyc/pmfs_official_alignment_r5_20261009/ws/install/gsl_server/lib/gsl_server/gsl_actionserver_node'),
 'E3_RUN_RESULT':T/'RUN_RESULT.json',
 'E3_POSTERIOR':T/'runtime/updates/update_1/posterior.f64',
 'E3_RESULT_CSV':T/'runtime/native_results.csv',
 'E3_LAUNCH_LOG':T/'runtime/launch.log',
}
hashes={k:hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None for k,p in paths.items()}
corelocations=[T,T/'runtime',Path('/var/lib/systemd/coredump'),Path('/var/crash')]
cores=[]
for d in corelocations:
 try:
  if d.is_dir():
   for p in d.iterdir():
    if p.name.startswith('core') or ('gsl' in p.name.lower() and p.suffix in {'.crash','.core','.dump'}):
     cores.append({'path':str(p),'size':p.stat().st_size})
 except OSError as e:cores.append({'directory':str(d),'error_type':type(e).__name__})
try:
 q=subprocess.run(['coredumpctl','--no-pager','info','30258'],capture_output=True,text=True,timeout=10)
 coredump={'command':'coredumpctl --no-pager info 30258','exit_code':q.returncode,'stdout':q.stdout[-6000:],'stderr':q.stderr[-2000:]}
except FileNotFoundError:coredump={'available':False,'error_type':'FileNotFoundError'}
lib=subprocess.run(['ldd',str(paths['GSL'])],capture_output=True,text=True,check=True).stdout
libs={}
for line in lib.splitlines():
 if 'libstdc++' in line:
  path=Path(line.split('=>')[1].strip().split()[0]);libs[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
known_pids=[30182,30183,30196,30198,30200,30202,30204,30206,30208,30210,30214,30219,30223,30231,30242,30258,30398,30553]
result={'checked_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'read_only':True,'VM_reused':True,'new_ROS_runs':0,'new_goals':0,'domain':76,'domain_processes':processes,'unreadable_proc_entries':unreadable,'unreadable_owned_proc_entries':unreadable_owned,'owned_limited_processes':owned_limited,'own_user_uid':os.getuid(),'known_E3_pid_presence':{str(pid):Path('/proc',str(pid)).exists() for pid in known_pids},'GSL_pid_30258_present':Path('/proc/30258').exists(),'core_pattern':Path('/proc/sys/kernel/core_pattern').read_text().strip(),'bounded_core_files':cores,'coredumpctl':coredump,'hashes':hashes,'GSL_libstdcxx':libs}
print(json.dumps(result))
