from common_r2 import *
import numpy as np,csv,shutil,sys
def rows(p):return list(csv.DictReader(Path(p).open(encoding='utf-8',newline='')))
def wc(p,rs):
 with Path(p).open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rs[0]),lineterminator='\n');w.writeheader();w.writerows(rs)
facts={};rr=rows(CORE/'RECEPTOR_METRICS.csv');fr=rows(CORE/'FUTURE_RECEPTOR_METRICS.csv')
for phase,data in [('development',rr),('future',fr)]:
 out=[]
 for method in ['O0-centre','O1-PID']:
  r=[r for r in data if r['blocks']=='50' and r['reference_group']=='R01' and r['method']==method];out.append(dict(method=method,meanBrier=float(np.mean([float(x['Brier']) for x in r])),count=len(r)))
 facts[phase+'_Brier']=out
sen=rows(CORE/'FUTURE_REFERENCE_SENSITIVITY.csv');facts['future_single_reference_sensitivity']={m:dict(mean_NLL_abs_difference=float(np.mean([float(r['reference_NLL_absolute_difference']) for r in sen if r['method']==m and r['blocks']=='50'])),top_region_differs=sum(r['same_top_region']=='False' for r in sen if r['method']==m and r['blocks']=='50')) for m in ['P3-O0','P3-O1','E-event','A1-map']}
facts['finite_equivalence']=[dict(plan=q['plan'],blocks=q['blocks'],marginal_classes=len(q['event_marginal_classes']),full_two_reference_sequence_classes=len(q['two_reference_full_sequence_classes']),A1_mean_classes=len(q['A1_mean_map_classes']),largest_event_class=max(map(len,q['event_marginal_classes']))) for q in load(CORE/'EVENT_EQUIVALENCE.json') if q['blocks']==50]
history=[];events={}
for ob in load(CORE/'inference_inputs/OBSERVATION_REGISTRY.json')+load(CORE/'future_inference_inputs/OBSERVATION_REGISTRY.json'):
 oid=ob['oid']
 if oid=='B4':history.append(dict(oid=oid,mode='originalROSAction',first_convergence_blocks=50,source_updates=3,fixed_end_blocks=50,first_success=True,native_official_Error='5.11158',result='originalsuccess=true unchanged'));continue
 d=HOST/'observations'/oid/'N0' if oid.startswith('Z') else R1RAW/'support/native'/('FRESH_N0_'+oid if oid.startswith('X') else 'N0_'+oid)
 r=rows(d/'update_ledger.csv');first=next((x for x in r if x['official_rule_first_convergence']=='1'),None);history.append(dict(oid=oid,mode='controlledfixedhistory_nativecore_noAction',first_convergence_blocks=first['blocks'] if first else '',source_updates=len(r),fixed_end_blocks=50,first_success=bool(first),native_official_Error='',result='continuesaftervariancegatebyregistereddiagnosticcontract'))
 if oid.startswith('Z'):
  e=rows(HOST/'observations'/oid/'PUBLIC_B_RECEIVER_EVENTS.csv');events[oid]=[int(x['event_hit']) for x in e]
wc(CORE/'N0_FIRST_CONVERGENCE_AND_FIXED_ENDPOINT.csv',history);facts['six_observation_unique_binary_histories']=len({tuple(e) for e in events.values()});facts['six_positive_block_counts']={k:sum(v) for k,v in events.items()};dump(CORE/'SCIENTIFIC_FACTS.json',facts)
parent=CORE/'parent_qualified_snippets';parent.mkdir()
for name in ['BASELINE_CONTRACT.json','QUALIFIED_N0_COMPLETE_MAP_RESULTS.csv','QUALIFIED_FRESH_N0_COMPLETE_MAP_RESULTS.csv','COLD_FIRST_ANCHOR.json','COLD_ENTRY_PROVENANCE.json','QUALIFIED_N_POINT_PREDICTIONS_FREEZE.json']:shutil.copy2(R1/name,parent/name)
original=BASE/'outputs/PMFS_B4_OFFICIAL_TERMINAL_RESUMED_20261010/runtime';shutil.copy2(original/'native_results.csv',parent/'originalB4_native_results.csv');shutil.copy2(original/'measurement_events.csv',parent/'originalB4_measurement_events.csv')
rawindex=[]
for p in sorted(HOST.rglob('*')):
 if p.is_file():rawindex.append(dict(relative_path=p.relative_to(HOST).as_posix(),bytes=p.stat().st_size,sha256=sha(p),carried_in_RAW=(RAW/p.relative_to(HOST)).is_file()))
wc(CORE/'EXTERNAL_TASK_ARTIFACT_SHA256.csv',rawindex)
code="""from pathlib import Path
import json,os,subprocess,shutil,time,hashlib
t=Path(%r);d=Path(%r);ps=subprocess.run(['ps','-eo','pid,ppid,stat,args'],capture_output=True,text=True,check=True).stdout;owned=[r for r in ps.splitlines() if str(t) in r and 'python3 -' not in r and 'defunct' not in r]
live=[r for r in owned if any(s in r for s in ['reference_worker.py','point_all_worker.py','future6_worker.py'])];assert not live,live
print(json.dumps(dict(status='OWNED_GENERATION_AND_NATIVE_WORKERS_ENDED',live_owned_workers=live,VM_left_running=True,other_tasks_untouched=True,root_free=shutil.disk_usage(t).free,shared_free=shutil.disk_usage(d).free,owned_data_bytes=sum(p.stat().st_size for p in d.rglob('*') if p.is_file()),wall_unix=time.time(),no_CFD_noNav_noTraining=True,librarySHA=hashlib.sha256(Path('/home/zyc/pmfs_m2_process_observation_20261010/libgaden.so').read_bytes()).hexdigest())))
"""%(REMOTE,DATA)
r=json.loads(remote(code,'final_owned_worker_and_library_resource_check',60));assert r['root_free']>=4294967296 and r['shared_free']>=4294967296 and r['owned_data_bytes']<8589934592 and r['librarySHA']=='ed042a1c317a0350e3e1bd701c3ac1e1ab3df23a9807612fd6e91f9234be76c6';r['elapsed_s']=r['wall_unix']-load(WORK/'ENTRY_TIME.json')['start_unix'];dump(CORE/'FINAL_RUNTIME_STATE.json',r);print(json.dumps({'facts':facts,'elapsed_min':r['elapsed_s']/60}))
