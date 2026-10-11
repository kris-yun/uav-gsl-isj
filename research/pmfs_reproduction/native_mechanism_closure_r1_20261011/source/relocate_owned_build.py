from common_n import *
code=r'''
import shutil,hashlib,os,subprocess,time
t=Path(TARGET);data=Path(DATA);data.mkdir(exist_ok=False)
ram=Path('/dev/shm/pmfs_native_mechanism_closure_r1_20261011');ram.mkdir(exist_ok=False)
backup=data/'compiled_preservation';backup.mkdir()
items=[]
def sh(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for n in ['native_entry','entry.o']:
 p=t/n;assert p.resolve().is_relative_to(t.resolve()) and p.is_file() and not p.is_symlink()
 h=sh(p);a=ram/n;b=backup/n;shutil.copy2(p,a);shutil.copy2(p,b)
 assert sh(a)==h==sh(b)
 p.unlink();p.symlink_to(a)
 items.append(dict(original=str(p),RAM=str(a),preserved=str(b),SHA256=h,bytes=a.stat().st_size))
assert shutil.disk_usage(t).free>=4294967296
(t/'NATIVE_EXECUTION_LEDGER.FIRST_ROOT_RESERVE_STOP.json').write_bytes((t/'NATIVE_EXECUTION_LEDGER.json').read_bytes())
(t/'native_worker.FIRST_ROOT_RESERVE_STOP.stdout').write_bytes((t/'native_worker.stdout').read_bytes())
(t/'native_worker.FIRST_ROOT_RESERVE_STOP.stderr').write_bytes((t/'native_worker.stderr').read_bytes())
out=t/'native_results/E3_saved_map_scores'
assert not out.exists() or not any(out.iterdir())
if out.exists():out.rename(t/'native_results/E3_saved_map_scores.FIRST_EMPTY_STOP')
result=dict(status='PASS_ONLY_OWN_NEW_BUILD_ARTIFACTS_RELOCATED',items=items,root_free_bytes=shutil.disk_usage(t).free,
 old_files_modified=0,first_forward_calls=0,old_physical_calls=0,temporary_RAM_bytes=sum(i['bytes'] for i in items),data_path=str(data))
(t/'OWN_BUILD_RELOCATION.json').write_text(json.dumps(result,indent=2))
p=subprocess.Popen(['python3',str(t/'native_worker.py')],stdout=(t/'native_worker.RESTART1.stdout').open('w'),stderr=(t/'native_worker.RESTART1.stderr').open('w'),start_new_session=True)
result['retry_worker_pid']=p.pid;print(json.dumps(result,indent=2))
'''.replace('TARGET',repr(REMOTE)).replace('DATA',repr(DATA))
r=json.loads(run_remote('from pathlib import Path\nimport json\n'+code,'RESTORE_RESERVE_OWN_BUILD_ONLY',60));dump(CORE/'OWN_BUILD_RELOCATION.json',r)
rep=load(CORE/'TECHNICAL_REPAIRS.json');rep['repairs'].append(dict(kind='Own compiled90MB binary exhausted reserved root margin',attempts=1,action='Hash-preserving RAM relocation and permanent shared-disk copy of only current native_entry and entry.o; native0forward calls before retry',scientific_definition_changed=False));dump(CORE/'TECHNICAL_REPAIRS.json',rep)
print(json.dumps(r,indent=2))
