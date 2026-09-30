"""Copy one already-generated run to task-owned VM staging; never launch GADEN."""
import hashlib,json,subprocess,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
freeze=json.loads((ROOT/'freeze/D0_LITE_PRE_TARGET_FREEZE.json').read_text());case=freeze['case']
run_id=case['run_id'];source=Path(case['archive_path']);out=Path(freeze['output_root']);out.mkdir(parents=True,exist_ok=True)
tar=out/(run_id+'_input.tar.gz')
assert not tar.exists(),'existing transfer artifact must not be overwritten'
with tarfile.open(tar,'w:gz',compresslevel=1) as f:f.add(source,arcname=run_id,recursive=True)
digest=hashlib.sha256(tar.read_bytes()).hexdigest()
key='C:/Users/50176/.ssh/id_ed25519_vm';dest='zyc@192.168.111.128';vm='/home/zyc/d1a_common_replay_20260930'
def call(cmd):subprocess.run(cmd,check=True)
call(['scp','-i',key,str(tar),dest+':'+vm+'/'])
for p in [ROOT/'run_native_vm.py',ROOT/'d1a_native.launch.py',ROOT/'capture_map_vm.py',ROOT/'freeze/D1A_RUNLIST_64.tsv']:
    call(['scp','-i',key,str(p),dest+':'+vm+'/'])
cmd=f"python3 -c \"import hashlib,pathlib; p=pathlib.Path('{vm}/{tar.name}'); assert hashlib.sha256(p.read_bytes()).hexdigest()=='{digest}'\" && mkdir -p {vm}/input && tar -xzf {vm}/{tar.name} -C {vm}/input"
call(['ssh','-i',key,'-o','BatchMode=yes',dest,cmd])
(out/'INPUT_TRANSFER_RECEIPT.json').write_text(json.dumps(dict(run_id=run_id,archive=source.as_posix(),transfer_tar_sha256=digest,
    bytes=tar.stat().st_size,VM_copy_sha_verified=True,original_retained=True,generator_executions=0),indent=2)+'\n')
print('EXISTING_PLUME_STAGED',run_id,flush=True)
