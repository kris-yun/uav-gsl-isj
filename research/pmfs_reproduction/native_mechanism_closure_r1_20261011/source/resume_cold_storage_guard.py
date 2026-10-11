from common_n import *
src=(CORE/'source/cold_native_worker.py').read_text()
old="base_storage=sum(p.stat().st_size for p in root.rglob('*') if p.is_file() and not p.is_symlink())+315529864+1073741824"
new="""wind_links=json.loads((root/'OWN_WIND_STORAGE_DEDUPLICATION.json').read_text())['records']
excluded={str(root/'factorial'/r['logical_directory'].split('/factorial/')[1]) for r in wind_links}
base_bytes=0
for directory,dirs,files in os.walk(root):
 dirs[:]=[n for n in dirs if str(Path(directory)/n) not in excluded]
 for n in files:
  p=Path(directory)/n
  if not p.is_symlink():base_bytes+=p.stat().st_size
base_storage=base_bytes+315529864+1073741824
(t/'COLD_STORAGE_RESERVATION.json').write_text(json.dumps({'unique_campaign_bytes':base_bytes,'external_approved_binary_bytes':315529864,'future_reserved_bytes':1073741824,'conservative_total':base_storage}))"""
assert old in src;src=src.replace(old,new)
code='''from pathlib import Path
import os,signal,subprocess,json
t=Path(REMOTE);old=t/'COLD_NATIVE_LEDGER.json'
assert not old.exists(),'Existing primary computations already started: preserve and inspect rather than rerun'
try:os.killpg(OLDPID,signal.SIGTERM)
except ProcessLookupError:pass
p=subprocess.Popen(['python3',str(t/'cold_native_worker_storage_fix.py')],stdout=(t/'cold_native_storagefix.stdout').open('w'),stderr=(t/'cold_native_storagefix.stderr').open('w'),start_new_session=True)
print(json.dumps({'pid':p.pid,'repair':'count shared identical CFD input storage once; cache immutable physical bank footprint','previous_primary_forward_calls':0}))
'''.replace('REMOTE',repr(REMOTE)).replace('OLDPID',str(load(CORE/'COLD_NATIVE_STARTED.json')['pid']))
r=json.loads(upload({'cold_native_worker_storage_fix.py':src.encode()},code,'cold_storage_count_fix_no_science_reruns',45));dump(CORE/'COLD_STORAGE_GUARD_REPAIR.json',r);(CORE/'source/cold_native_worker_storage_fix.py').write_text(src,encoding='utf-8');print(json.dumps(r))
