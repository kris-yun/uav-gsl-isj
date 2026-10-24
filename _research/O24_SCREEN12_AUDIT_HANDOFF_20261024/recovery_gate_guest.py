"""Read-only isolation recovery. No native goal, seed, or algorithm changes."""
from pathlib import Path
import datetime,json,os,subprocess,sys,time
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R))
from isolation_guard import inventory,require_vacant
D=R/'recovery/B2_R04_ISOLATION_INTERRUPT'
D.mkdir(parents=True,exist_ok=True)
for i in (1,2):
    require_vacant(inventory(228,exclude={os.getpid()}),D/f'CURRENT_PROCESS_GATE_{i}.json')
    if i==1:time.sleep(2)
C=R/'cases/B2_R04'
G=D/'POST_GRAPH_RECOVERY'
G.mkdir(exist_ok=False)
shell=(C/'RUN_SHELL.sh').read_text()
old='exec python3 -B '+str(C/'runtime_driver.py')
assert old in shell
shell=shell.replace(old,'exec python3 -B '+str(R/'graph_probe.py')+' '+str(G))
p=D/'RECOVERY_GRAPH.sh';p.write_text(shell)
q=subprocess.run(['bash',str(p)],capture_output=True,timeout=30)
(D/'GRAPH_STDOUT.log').write_bytes(q.stdout)
(D/'GRAPH_STDERR.log').write_bytes(q.stderr)
assert q.returncode==0,q.stderr.decode(errors='replace')
plan=json.loads((R/'PREREGISTERED_SCREEN12_R2_INPUT_FINAL.json').read_text())
import hashlib
assert hashlib.sha256(Path(plan['binary_path']).read_bytes()).hexdigest()==plan['binary_sha256']
verdict=dict(status='PASS_CURRENT_DOMAIN_VACANT_FROZEN_BINARY_UNCHANGED',
 UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
 historical_B2_R04_isolation_proof='UNRESOLVED_AND_NOT_RETROACTIVELY_APPROVED',
 historical_unreadable_process_pid=56261,
 historical_unreadable_process='OpenSSH sftp-server; environment unreadable at capture, not proof of ROS interference',
 no_guard_relaxed=True,new_native_goals=0)
(D/'RECOVERY_GATE.json').write_text(json.dumps(verdict,indent=2)+'\n')
print(json.dumps(verdict))
