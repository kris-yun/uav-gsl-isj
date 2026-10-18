from pathlib import Path
import csv,hashlib,json,math
R=Path(__file__).resolve().parent;A=R/'analysis'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def rows(p):return list(csv.DictReader(p.open(encoding='utf-8')))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=load(R/'PRECOMMIT.json');role=p['roles'][0];F=R/'cases'/role['id'];rt=F/'runtime';actual=load(R/'RECOVERY_COMPLETE.json')
assert p['total_goal_cap']==1 and p['technical_retry_cap']==0 and actual['result']['native_goal_count']==1
assert actual['result']['result']=='NATIVE_ACTION_RETURNED',actual['result']
assert actual['exit_code']==0
for x in p['source_files']:assert sha(R/'source_runtime'/x['path'])==x['sha256']
gate=load(rt/'BASELINE_PARAMETER_GATE.json');assert gate['checked']==p['expected_parameters']
ident=load(rt/'NATIVE_EXECUTABLE_IDENTITY.json');assert len(ident)==1 and ident[0]['sha256']==p['binary_sha256']
assert load(R/'WORLD_INPUT_GATE.json')['status']=='PASS_BOTH_EXISTING_WORLD_ALL_FRAME_SHA256'
assert load(A/'WIND_SEMANTICS_AUDIT.json')['status']=='SAVED_MESSAGE_AND_TF_DIAGNOSTIC_COMPLETE'
assert load(R/'SOURCE_AND_DEPENDENCY_POSTCHECK.json')['status']=='PASS_SOURCE_BINARY_LIBRARIES_AND_EXECUTED_ADAPTER_COPIES'
for name in ['DOMAIN_CONTROLLER_PRE_GATE.json','DOMAIN_PROBE_PROCESS_GATE.json','DOMAIN_PRECHECK_PROCESS_INVENTORY.json','DOMAIN_POST_RUN_PROCESS_GATE.json']:
 s=load(R/name);assert s['vacant']and s['domain']==225
assert load(rt/'IMMEDIATE_PRE_DDS_GATE.json')['vacant']
assert load(R/'DOMAIN_GRAPH_GATE.json')['status']=='PASS_DOMAIN_GRAPH_VACANT'
assert load(R/'DOMAIN_POST_GRAPH_GATE.json')['status']=='PASS_DOMAIN_GRAPH_VACANT'
monitor=load(R/'PROCESS_OWNERS_AND_MONITOR.json');assert not monitor['unowned_domain_processes']
assert all(not x['unowned']for x in monitor['monitor'])
windows=rows(rt/'native_window_consumption.csv');consumed=[x for x in windows if x['status']=='CONSUMED']
assert all(int(x['gas_count'])>0 and int(x['wind_count'])>0 for x in consumed)
assert all(x['status']in ['CONSUMED','WAIT_EMPTY_OBSERVATION']for x in windows)
e=rows(A/'O24_EPISODES.csv');assert len(e)==1;e=e[0]
q=rows(A/'NATIVE_REPLAY_PARITY.csv');assert len(q)==int(e['source_updates'])
assert max(float(x['posterior_max_abs_error'])for x in q)<1e-10
assert max(float(x['map_score_max_relative_error'])for x in q)<1e-10
cpp=rows(A/'O24_NATIVE_CPP_READOUT.csv')[-1]
if e['native_declared']=='True':
 for x,y in [('native_Top5_error_m','top5_error_m'),('native_mean_error_m','mean_error_m'),('native_variance_m2','variance_m2')]:assert math.isclose(float(e[x]),float(cpp[y]),rel_tol=8e-6,abs_tol=8e-6)
rr=load(A/'RNG_STREAM_REPLAY_RESULTS.json');assert rr['status']=='PASS_RECORDED_STREAM_REPLAY_NOT_FULL_TRAJECTORY_REPRODUCTION'
assert len(rr['rows'])==1 and rr['rows'][0]['candidate_records']==int(e['candidate_calls'])
assert actual['post_free_bytes']>p['guest_free_floor_bytes']
out=dict(status='PASS_AUTHORIZED_SINGLE_A2_ISOLATION_RECOVERY_SOURCE_AND_PARAMETERS_UNCHANGED',role=role,episode=e,source_files=len(p['source_files']),binary_sha256=p['binary_sha256'],process_environment_and_DDS_graph_gates='PASS_PRE_AND_POST',domain_owner_monitor_samples=len(monitor['monitor']),domain_owner_processes=len(monitor['owners']),foreign_domain_processes=0,RNG_stream_replay=rr['status'],consumed_windows=len(consumed),empty_waits=len(windows)-len(consumed),new_native_goals=1,additional_retries=0,new_worlds=0,AIMMD=0,previous_A2_R02='PERMANENT_HOLD_RECORD_RETAINED_NOT_RELABELED',paper_performance='HOLD_NOT_30_RUN_REPRODUCTION',limits=['Original local-GMRF information protocol and mixed clock mapping limits remain.','Source-faithful public port with disclosed engineering adaptations, not exact author experimental implementation.','Readable environment inventory plus direct graph probes and owner monitoring do not grant root access to protected system helper environments; explicit exceptions retained.'])
(R/'FINAL_RECOVERY_GATE.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out,ensure_ascii=False))
