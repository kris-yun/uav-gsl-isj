from pathlib import Path
import hashlib,json,shutil,subprocess,sys,time
R=Path(__file__).resolve().parent;A=R/'analysis';A.mkdir(exist_ok=True)
commands=json.loads((R/'POSTFLIGHT_COMMANDS.json').read_text())if (R/'POSTFLIGHT_COMMANDS.json').exists()else[]
def run(argv,name):
 if any(x['argv']==argv and x['exit_code']==0 for x in commands):return
 attempt=1+sum(x['argv']==argv for x in commands)
 t=time.monotonic();q=subprocess.run(argv,capture_output=True)
 (A/(name+'.attempt'+str(attempt)+'.stdout')).write_bytes(q.stdout);(A/(name+'.attempt'+str(attempt)+'.stderr')).write_bytes(q.stderr)
 commands.append(dict(argv=argv,exit_code=q.returncode,wall_s=time.monotonic()-t))
 (R/'POSTFLIGHT_COMMANDS.json').write_text(json.dumps(commands,indent=2)+'\n')
 assert q.returncode==0,(name,q.returncode,q.stderr.decode(errors='replace'))
for name in ['verify_readout_guest.py','validate_rng_guest.py','check_existing_worlds.py','make_minimal_sample.py']:
 run([sys.executable,'-B',str(R/name)],name)
shutil.copyfile(R/'minimal_replay_score.py',R/'minimal_score_sample/replay_score.py')
run([sys.executable,'-B',str(R/'minimal_score_sample/replay_score.py')],'minimal_score_replay')
run(['bash',str(R/'WIND_AUDIT_SHELL.sh')],'wind_audit')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=json.loads((R/'PRECOMMIT.json').read_text());deps=json.loads((R/'DEPENDENCY_LIVE_MANIFEST.json').read_text());adapter=[]
for row in deps['roots']:assert sha(row['path'])==row['sha256']
for path,h in deps['libraries'].items():assert sha(path)==h,path
for row in p['source_files']:assert sha(R/'source_runtime'/row['path'])==row['sha256']
role=p['roles'][0]
for name in ['N1_launch.py','runtime_driver.py','RUN_SHELL.sh','CASE_META.json','AUTHOR_WALL_FILE_CADENCE.csv']:
 local=R/'cases'/role['id']/name;guest=Path(role['guest_path'])/name
 assert sha(local)==sha(guest),name;adapter.append(dict(file=name,sha256=sha(local)))
(R/'SOURCE_AND_DEPENDENCY_POSTCHECK.json').write_text(json.dumps(dict(status='PASS_SOURCE_BINARY_LIBRARIES_AND_EXECUTED_ADAPTER_COPIES',source_files=len(p['source_files']),libraries=len(deps['libraries']),binary_sha256=p['binary_sha256'],adapter_copies=adapter),indent=2)+'\n')
run([sys.executable,'-B',str(R/'verify_recovery.py')],'verify_recovery')
print((R/'FINAL_RECOVERY_GATE.json').read_text(),flush=True)
