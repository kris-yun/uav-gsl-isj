from pathlib import Path
import csv,hashlib,json,math,shutil,statistics
R=Path(__file__).resolve().parent;A=R/'analysis'
def read(p):return list(csv.DictReader(p.open(encoding='utf-8')))
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
plan=load(R/'PRECOMMIT.json');build=load(R/'BUILD_RESULT.json')
for row in plan['source_files']:assert sha(R/'source_runtime'/row['path'])==row['sha256'],row['path']
source_names={x['path']for x in plan['source_files']}
assert source_names=={x.relative_to(R/'source_runtime').as_posix()for x in (R/'source_runtime').rglob('*')if x.is_file()}
assert sha(R/'binaries/gsl_actionserver_node')==build['binary_sha256']
batch=load(R/'BATCH_COMPLETE.json');assert batch['recorded']==batch['requested']==4
assert load(R/'POST_RUN_GUEST_GATE.json')['status'].startswith('PASS_')
replay=load(A/'RNG_STREAM_REPLAY_RESULTS.json');assert replay['status']=='PASS_RECORDED_STREAM_REPLAY_NOT_FULL_TRAJECTORY_REPRODUCTION'
eps=read(A/'O24_EPISODES.csv');assert len(eps)==4
rows=[];cpp=read(A/'O24_NATIVE_CPP_READOUT.csv')
for role,e in zip(plan['roles'],eps):
 F=R/'cases'/role['id'];rt=F/'runtime';gate=load(rt/'BASELINE_PARAMETER_GATE.json');res=load(F/'RUN_RESULT.json')
 assert gate['status']=='PASS_ACTUAL_NODE_PARAMETER_VALUES'and res['result']=='NATIVE_ACTION_RETURNED'
 for k,v in plan['parameters'].items():assert gate['checked'][k]==v,(role['id'],k)
 rr=next(x for x in replay['rows']if x['role']==role['id']);assert rr['status']=='PASS_ALL_RECORDED_CANDIDATE_RANDOM_STREAMS'
 count=len(read(rt/'native_candidate_maps.csv'));assert count==rr['candidate_records']==int(e['candidate_calls'])
 windows=read(rt/'native_window_consumption.csv');valid=[w for w in windows if w['status']=='CONSUMED'];wait=[w for w in windows if w['status']!='CONSUMED']
 assert all(int(w['gas_count'])>0 and int(w['wind_count'])>0 for w in valid)
 assert all(w['status']=='WAIT_EMPTY_OBSERVATION'for w in wait)
 final=[x for x in cpp if x['role']==role['id']][-1]
 for k,j in [('native_Top5_error_m','top5_error_m'),('native_mean_error_m','mean_error_m'),('native_variance_m2','variance_m2')]:
  assert math.isclose(float(e[k]),float(final[j]),rel_tol=8e-6,abs_tol=8e-6),(role['id'],k,e[k],final[j])
 assert float(final['variance_m2'])<1.5
 rows.append(dict(role=role['id'],parameters='PASS',candidate_records=count,stream_replay='PASS',final_native_CPP_readout='PASS_WITH_NATIVE_TEXT_PRINTING_PRECISION',valid_windows=len(valid),empty_guard_events=wait))
assert sum(x['candidate_records']for x in rows)==4345
assert sum(len(x['empty_guard_events'])for x in rows)==1
parity=read(A/'NATIVE_REPLAY_PARITY.csv');assert len(parity)==28
max_p=max(float(x['posterior_max_abs_error'])for x in parity);max_a=max(float(x['linear_alpha_max_abs_error'])for x in parity);max_score=max(float(x['map_score_max_relative_error'])for x in parity)
assert max_p<1e-10 and max_a<2e-15 and max_score<1e-10
isolation=load(R/'DOMAIN_ISOLATION_AUDIT.json');assert isolation['status']=='HOLD_A2_R02_DOMAIN225_PREEXISTING_LIFECYCLE_MANAGER_COLLISION'
for row in rows:row['domain_isolation']='HOLD_CONFIRMED_HISTORICAL_DOMAIN_COLLISION'if row['role']=='O24G_A2_R02'else 'NO_CONFIRMED_COLLISION_IN_SAVED_AND_POST_RUN_PROCESS_RECORDS_PRECHECK_INCOMPLETE'
gate=dict(status='HOLD_ROS_ISOLATION_A2_R02_BUILD_AND_RNG_PASS_FOUR_RAW_EPISODES_RETAINED',source_manifest_files=len(plan['source_files']),build_exit_codes=[x['exit_code']for x in build['commands']],binary_sha256=build['binary_sha256'],roles=rows,source_updates=28,candidate_records=4345,posterior_max_abs_error=max_p,linear_alpha_max_abs_error=max_a,map_score_max_relative_error=max_score,GO_scope='Source build, native parameter binding and recorded RNG streams PASS. All four real episodes remain raw evidence. Overall clean ROS qualification HOLD due confirmed preexisting lifecycle manager on A2 R02 domain225; no numerical parity test removes this runtime confound.',paper_performance='HOLD',new_worlds=0,AIMMD=0,technical_retries=0)
(R/'FINAL_QUALIFICATION_GATE.json').write_text(json.dumps(gate,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(gate,ensure_ascii=False))
