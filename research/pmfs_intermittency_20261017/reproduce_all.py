"""Standalone offline reproduction. Linux, Python scientific stack, GCC/CMake; no ROS/network."""
from pathlib import Path
import argparse,zipfile,shutil,subprocess,sys,json,hashlib,time,os,resource
p=argparse.ArgumentParser();p.add_argument('--out',required=True,type=Path);p.add_argument('--verify-only',action='store_true');a=p.parse_args();S=Path(__file__).resolve().parent;manifest=json.loads((S/'MANIFEST_SHA256.json').read_text());bad=[]
for name,d in manifest.items():
 q=S/name
 if not q.exists() or hashlib.sha256(q.read_bytes()).hexdigest()!=d['sha256']:bad.append(name)
assert not bad,bad
print('PASS',len(manifest),'package member hashes',flush=True)
if a.verify_only:sys.exit(0)
W=a.out.resolve();W.mkdir(exist_ok=False);R=W/'INTERMITTENCY_CAUSAL_AUDIT_20261017';shutil.copytree(S/'analysis/scripts',R/'scripts');shutil.copytree(S/'analysis/cpp',R/'cpp');(R/'results').mkdir();(R/'logs').mkdir()
for q in sorted((S/'evidence').glob('*.zip')):
 if q.name=='b4_anchor.zip':continue
 with zipfile.ZipFile(q) as z:
  for n in z.namelist():assert (W/n).resolve().is_relative_to(W),'unsafe archive member'
  z.extractall(W)
b=W/'B4_NATIVE_AUDIT_20261017';b.mkdir();shutil.copyfile(S/'evidence/b4_anchor.zip',b/'B4原生实查_间歇接触机制与逐格重放_20261017.zip')
P=W/'NATIVE_PMFS_WIND_RECOVERY_20261014/PORTABLE_DATA';X=P.parent;env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1');commands=[
 [sys.executable,str(R/'scripts/start_b4.py')],
 [sys.executable,str(X/'portable_recompute.py'),'--data',str(P),'--out',str(R/'results/native20_recomputed')],
 [sys.executable,str(X/'portable_clock_gate.py'),'--data',str(P),'--out',str(R/'results/clock20.json')],
 [sys.executable,str(X/'portable_geometry_gate.py'),'--data',str(P),'--out',str(R/'results/geometry20.json')],
 [sys.executable,str(X/'portable_wind_chain.py'),'--data',str(P),'--out',str(R/'results/wind20')],
 [sys.executable,str(R/'scripts/prepare_native.py')],
 ['cmake','-S',str(R/'cpp'),'-B',str(R/'build')],['cmake','--build',str(R/'build'),'-j2'],
 [sys.executable,str(R/'scripts/replay20.py')],
 [sys.executable,str(R/'scripts/controls20.py')],
 [sys.executable,str(R/'scripts/screen.py')],
 [sys.executable,str(R/'scripts/export_pid_no_ros.py')],
 [sys.executable,str(R/'scripts/stop_influence.py')],
 [sys.executable,str(R/'scripts/summarize.py')],
 ['ctest','--test-dir',str(R/'build'),'--output-on-failure']]
ledger=[]
for i,cmd in enumerate(commands):
 start=time.monotonic();before=resource.getrusage(resource.RUSAGE_CHILDREN);q=subprocess.run(cmd,env=env,capture_output=True,text=True);after=resource.getrusage(resource.RUSAGE_CHILDREN);(R/'logs'/f'{i:02d}.stdout').write_text(q.stdout);(R/'logs'/f'{i:02d}.stderr').write_text(q.stderr);row=dict(command=cmd,returncode=q.returncode,elapsed_s=time.monotonic()-start,child_user_s=after.ru_utime-before.ru_utime,child_system_s=after.ru_stime-before.ru_stime,cumulative_max_child_rss_kib=after.ru_maxrss);ledger.append(row);(R/'EXECUTION.json').write_text(json.dumps(ledger,indent=2));print(i,q.returncode,round(row['elapsed_s'],2),flush=True);assert q.returncode==0,row
got=json.loads((R/'results/FINAL_DECISION.json').read_text());want=json.loads((S/'analysis/results/FINAL_DECISION.json').read_text());assert got==want,(got,want)
(W/'PORTABLE_REPRODUCTION_PASS.json').write_text(json.dumps(dict(status='PASS_ALL_REPRODUCTION_COMMANDS',commands=len(commands),decision=got,new_worlds=0,new_ROS_episodes=0),indent=2));print('PASS standalone offline reproduction',flush=True)
