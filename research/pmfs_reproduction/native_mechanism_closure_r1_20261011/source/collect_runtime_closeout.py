from common_n import *
import csv,numpy as np,shutil
code=r'''from pathlib import Path
import json,base64,subprocess,shutil
t=Path(REMOTE)
selected=['COLD_NATIVE_LEDGER.json','COLD_FRESH_LEDGER.json','COLD_STORAGE_RESERVATION.json','RESOURCE_CHECKS.jsonl','NATIVE_EXECUTION_LEDGER.json','COLD_NATIVE_TASKS.json','COLD_FRESH_TASKS.json','COLD_ENTRY_PROVENANCE.json','HISTORICAL_GSL_ELF_PROVENANCE.json','qualified_fresh_cold_literal_fixed.stderr','qualified_fresh_cold_literal_fixed.stdout','qualified_fresh_cold.stderr','cold_native_storagefix.stderr','cold_native_storagefix.stdout']
selected += [p.name for p in t.iterdir() if p.name.endswith('_LEDGER.json') and p.name not in selected]
files={n:base64.b64encode((t/n).read_bytes()).decode() for n in selected if (t/n).exists()}
ps=subprocess.run(['ps','-eo','pid,ppid,etimes,args'],capture_output=True,text=True,check=True).stdout
owned=[l for l in ps.splitlines() if str(t) in l and 'python3 -' not in l]
print(json.dumps({'files':files,'owned_processes':owned,'root_free':shutil.disk_usage(t).free,'RAM_binary_storage':True,'original_VM_left_running':True}))
'''.replace('REMOTE',repr(REMOTE))
r=json.loads((WORK/'final_runtime_ledger_capture.stdout').read_text()) if (WORK/'final_runtime_ledger_capture.stdout').exists() else json.loads(run_remote(code,'final_runtime_ledger_capture',45));f=CORE/'runtime_ledgers';f.mkdir(exist_ok=True)
for n,b in r.pop('files').items():(f/n).write_bytes(base64.b64decode(b))
dump(CORE/'RUNTIME_CLOSEOUT.json',r)
for ledger in ['COLD_NATIVE_LEDGER.json','COLD_FRESH_LEDGER.json']:assert load(f/ledger)['status'].startswith('PASS')
D=Path('D:/ZYC/A-gas/workspace/PMFS_NATIVE_MECHANISM_CLOSURE_R1_DATA_20261011')
for rel in ['fresh/GENERATION_LEDGER.json','factorial/GENERATION_LEDGER.json','FRESH_NATIVE_INPUT_FREEZE.json']:
 p=D/rel
 if p.exists():shutil.copy2(p,f/Path(rel).name if rel.startswith('fresh') else f/('FACTORIAL_'+Path(rel).name))
def rr(p):return list(csv.DictReader(Path(p).open(encoding='utf-8',newline='')))
historic=BASE/'outputs/PMFS_B4_OFFICIAL_TERMINAL_RESUMED_20261010/runtime/updates/update_2/input.csv'
new=D/'readout/B4_C7_0/A1_native_map/final_map.csv';a=rr(historic);b=rr(new);assert len(a)==len(b)
result={k:max(abs(float(x[k])-float(y[k])) for x,y in zip(a,b)) for k in ['logOdds','omega','confidence']};assert max(result.values())==0
dump(CORE/'B4_50BLOCK_NATIVE_MAP_ANCHOR.json',dict(status='PASS_EXACT',differences=result,historical_SHA256=sha(historic),same_native_operator=True))
for src in WORK.glob('*.py'):shutil.copy2(src,CORE/'source'/src.name)
(CORE/'source/portable').mkdir(parents=True,exist_ok=True)
shutil.copy2(WORK/'verify_native_mechanism_bundle.py',CORE/'source/portable/verify_native_mechanism_bundle.py')
print(json.dumps({'status':'RUNTIME_AND_SOURCE_CAPTURED','owned_processes':r['owned_processes'],'root_free':r['root_free']}))
