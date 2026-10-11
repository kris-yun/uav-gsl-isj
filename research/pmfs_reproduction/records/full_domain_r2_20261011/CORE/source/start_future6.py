from common_r2 import *
assert load(CORE/'DEVELOPMENT_GATE_RESULT.json')['future_new_gas_allowed']
assert sha(CORE/'inference_inputs/ALL_CANDIDATE_PREDICTIONS.npz')==load(CORE/'PREDICTOR_LIBRARY_FREEZE.json')['sha256']
jobs=[]
for j in load(CORE/'evaluation_only/FUTURE6_PREREGISTRATION.json')['jobs']:jobs.append(dict(j,id=j['oid'],source_index=j['true_region'],replicate=int(j['oid'][-1])%2,role='independent_new_observation_not_reference'))
src=(WORK/'reference_worker.py').read_text();src=src.replace("J=json.loads((T/'REFERENCE_JOBS_PREREGISTRATION.json').read_text())","J=json.loads((T/'FUTURE_OBSERVATION_JOBS.json').read_text())")
src=src.replace("gas_calls=1,reference_calls=0","gas_calls=65,reference_calls=0,observation_calls=0")
src=src.replace("D/'REFERENCE_LEDGER.json'","D/'FUTURE_OBSERVATION_LEDGER.json'").replace("D/'references'/job['id']","D/'observations'/job['id']").replace("L['reference_calls']+=1","L['observation_calls']+=1")
src=src.replace("L['status']='PASS_ALL_REGISTERED_REFERENCES_AND_PREFIXES'","L['status']='PASS_ALL_SIX_PREREGISTERED_OBSERVATIONS'")
# The existing exact physical generator, time/index checks, and all numeric query records remain unchanged.
# Reference-like full maps are kept as RAW only and never inserted into the candidate predictor library.
native='''
  nstart=time.monotonic();cold=Path('/mnt/hgfs/workspace/PMFS_NATIVE_MECHANISM_CLOSURE_R1_DATA_20261011/cold_inputs/DERIVED');nb=Path('/dev/shm/nmc_cold/native_cold_entry')
  assert sh(nb)=='490114422d661bbbe3ed6173f36b800b4880ac80812a16513124988ae3ba5c06'
  ni=rows(cold/'rng.csv')[0];assert ni['ready']=='0' and ni['phase']=='0' and ni['engine']=='470211272'
  ncost=run([str(nb),'history',str(cold),str(dest/'PUBLIC_B_RECEIVER_EVENTS.csv'),str(dest/'N0')],dest/'N0.log',env_native,job['id']+'_qualified_cold_N0')
  rec['native_N0_cost']=ncost;dump(dest/'QUALIFICATION.json',rec)
'''
src=src.replace("dump(dest/'QUALIFICATION.json',rec);L['records'].append(rec)",native+"  L['records'].append(rec)")
dump(CORE/'FUTURE_EXECUTION_FREEZE.json',dict(status='FROZEN_BEFORE_NEW_OBSERVATIONS',candidate_prediction_SHA256=sha(CORE/'inference_inputs/ALL_CANDIDATE_PREDICTIONS.npz'),inference_code_SHA256=sha(WORK/'infer_source_matrix.py'),development_gate_SHA256=sha(CORE/'DEVELOPMENT_GATE_RESULT.json'),source_count=32,new_observations=6,no_reference_role_for_new_banks=True,nativeN0='Qualified original cold wrapper, actual core and Gaussian notready initialstate',all_reference_predictions_frozen=True))
compile(src,'future6worker','exec');(WORK/'future6_worker.py').write_text(src,encoding='utf-8')
files={'future6_worker.py':src.encode(),'FUTURE_OBSERVATION_JOBS.json':json.dumps(jobs).encode()}
code="""import subprocess
p=subprocess.Popen(['python3',str(t/'future6_worker.py')],stdout=(t/'future6.stdout').open('w'),stderr=(t/'future6.stderr').open('w'),start_new_session=True)
print(json.dumps(dict(pid=p.pid,observations=6,no_new_reference_selection=True)))
"""
r=json.loads(upload(files,code,'start6_precommitted_observations_after_development_gate',45));dump(CORE/'FUTURE_STARTED.json',r);print(json.dumps(r))
