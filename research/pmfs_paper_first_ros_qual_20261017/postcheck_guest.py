from pathlib import Path
import hashlib,json,os,subprocess
S=Path('/mnt/hgfs/workspace/PMFS_PAPER_FIRST_ROS_QUAL_20261017');V=Path('/home/zyc/ros2_ws/pmfs_paper_first_qual_20261017')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=[]
for p in sorted((S/'source_runtime').rglob('*')):
 if p.is_file():q=V/'src/gsl_server'/p.relative_to(S/'source_runtime');assert q.exists()and sha(p)==sha(q),str(q);manifest.append(dict(path=str(p.relative_to(S/'source_runtime')),sha256=sha(q)))
exe=V/'install/lib/gsl_server/gsl_actionserver_node';expected=json.loads((S/'BUILD_RESULT.json').read_text())['binary_sha256'];assert sha(exe)==expected
alive=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  cmd=(p/'cmdline').read_bytes()
  if b'pmfs_paper_first_qual_20261017'in cmd and b'postcheck_guest.py'not in cmd and b'python3 -'not in cmd and b'bash -c'not in cmd:alive.append(dict(pid=p.name,command=cmd.decode(errors='replace').replace('\0',' ')))
 except (FileNotFoundError,PermissionError,ProcessLookupError):pass
result=dict(status='PASS_FINAL_RUNTIME_SOURCE_BINARY_POSTCHECK',source_files=manifest,binary_sha256=sha(exe),active_owned_processes=alive,guest_free_bytes=__import__('shutil').disk_usage(V).free)
assert not alive,alive
(S/'FINAL_GUEST_POSTCHECK.json').write_text(json.dumps(result,indent=2));print(json.dumps(dict(status=result['status'],files=len(manifest),active_owned_processes=len(alive),guest_free_bytes=result['guest_free_bytes'])))
