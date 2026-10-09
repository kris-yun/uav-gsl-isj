"""Recheck saved real ROS consumers and their predeclared gates; no ROS execution."""
import argparse,csv,json,math,hashlib
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parent);ap.add_argument('--out',type=Path,required=True)
a=ap.parse_args();root=a.root;out=a.out;out.mkdir(parents=True,exist_ok=True)
e=root/'evidence/real_ros';raw=e/'results'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def angle_diff(a,b):return abs(math.atan2(math.sin(a-b),math.cos(a-b)))
def write(name,data):(out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if (root/'SHA256SUMS.txt').exists():
    for line in (root/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        expected,name=line.split('  ',1);assert sha(root/name)==expected,name
contract=read(raw/'PRE_RUN_CONTRACT.json');cases=read(raw/'WIND_CASES_RAW.json')
assert read(raw/'RUN_COMPLETE.json')['completed'] and len(cases)==14
assert read(e/'BUILD_RESULT.json')['verdict']=='PASS'
assert read(e/'CORE_LIBRARY_BINDING.json')['core_map_matches_pinned_git']
assert not read(e/'PROCESS_CLEANUP.json')['test_executable_processes_remaining']
rows=[];clocks=[]
for c in cases:
    assert c['transport_received'],c['id']
    p=c['pmfs_consumer_fields'];g=c['gmrf_consumer_fields'];assert len(p)==15 and len(g)==18
    assert p[0:3]==g[0:3],c['id']
    assert int(p[0])==c['stamp_sec'] and int(p[1])==c['stamp_nanosec'] and p[2]==c['frame']
    expected=math.atan2(c['v'],c['u']);speed=math.hypot(c['u'],c['v'])
    xy=(c['x'],c['y']);pos_error=math.hypot(float(g[6])-xy[0],float(g[7])-xy[1])
    pmfs_pos_error=math.hypot(float(p[8])-xy[0],float(p[9])-xy[1])
    pe=angle_diff(float(p[12]),expected) if speed else None;ge=angle_diff(float(g[5]),expected) if speed else None
    consumer_diff=angle_diff(float(p[12]),float(g[5])) if speed else None
    stamp_ns=c['stamp_sec']*10**9+c['stamp_nanosec'];p_age=(int(p[13])-stamp_ns)/1e9;g_age=(int(g[10])-stamp_ns)/1e9
    p_tf_stamp=int(p[6])*10**9+int(p[7]);p_tf_delta=(p_tf_stamp-stamp_ns)/1e9
    grid_x=math.floor((c['x']+5)/.5);grid_y=math.floor((c['y']+5)/.5);expected_cell=grid_x+grid_y*20
    actual_cell=int(g[13]);grid_ok=actual_cell==expected_cell
    speed_ok=abs(float(p[11])-speed)<1e-6 and abs(float(g[3])-speed)<1e-6
    clock_ok=not c['publisher_use_sim_time'] and p[14]=='0' and g[11]=='0' and abs(p_age)<contract['clock_tolerance_s'] and abs(g_age)<contract['clock_tolerance_s']
    time_tf_ok=abs(p_tf_delta)<1e-9
    direction_ok=speed==0 or (pe<contract['angle_tolerance_rad'] and ge<contract['angle_tolerance_rad'])
    position_ok=pos_error<contract['position_tolerance_m'] and pmfs_pos_error<contract['position_tolerance_m'] and grid_ok
    status='PASS' if direction_ok and position_ok and clock_ok and time_tf_ok and speed_ok else 'FAIL'
    vector_error=math.hypot(float(g[16])-c['u'],float(g[17])-c['v'])
    if c['kind']=='N1':assert status=='PASS' and vector_error<1e-4,c['id']
    if c['kind']=='NEG_MAP_FRAME':assert float(g[6])==0 and float(g[7])==0 and not position_ok
    if c['kind']=='N0_FROM_SHARED':assert pe>3 and ge<1e-4
    if c['kind']=='NEG_MIXED_CLOCK':assert not clock_ok and p_age>1e9
    if c['kind']=='DIAG_DELAYED_TF':assert consumer_diff>1.5 and not time_tf_ok and g[6:8]==['1.25','1.25']
    estimate=c.get('estimated_wind_at_sensor',{});u=estimate.get('u',[None])[0];v=estimate.get('v',[None])[0]
    estimate_speed=math.hypot(u,v) if u is not None and v is not None else None
    rows.append(dict(case_id=c['id'],kind=c['kind'],expected_u=c['u'],expected_v=c['v'],expected_x=c['x'],expected_y=c['y'],sensor_yaw_rad=c['yaw'],
        frame=c['frame'],stamp_sec=c['stamp_sec'],stamp_nanosec=c['stamp_nanosec'],pmfs_avg_speed=float(p[11]),pmfs_avg_TO_rad=float(p[12]),gmrf_TO_rad=float(g[5]),
        pmfs_angle_error_rad=pe,gmrf_angle_error_rad=ge,consumer_angle_difference_rad=consumer_diff,gmrf_x=float(g[6]),gmrf_y=float(g[7]),gmrf_position_error_m=pos_error,
        expected_grid_index=expected_cell,actual_grid_index=actual_cell,gmrf_cell_center_x=float(g[14]),gmrf_cell_center_y=float(g[15]),gmrf_observation_count=int(g[12]),
        gmrf_inserted_u=float(g[16]),gmrf_inserted_v=float(g[17]),pmfs_TF_minus_message_stamp_s=p_tf_delta,pmfs_receipt_age_s=p_age,gmrf_receipt_age_s=g_age,
        field_estimated_u=u,field_estimated_v=v,field_estimated_speed=estimate_speed,field_accuracy_claim='NOT_QUALIFIED: convergence/accuracy not established',verdict=status))
    clocks.append(dict(case_id=c['id'],publisher_use_sim_time=c['publisher_use_sim_time'],publisher_parameter_evidence='fixture configuration plus actual emitted stamp; no parameter-service capture',
        pmfs_use_sim_time_observed=p[14]=='1',gmrf_use_sim_time_observed=g[11]=='1',consumer_parameter_evidence='get_parameter values captured inside callbacks',
        message_stamp_ns=stamp_ns,pmfs_node_now_ns=int(p[13]),gmrf_node_now_ns=int(g[10]),pmfs_TF_stamp_ns=p_tf_stamp,
        PMFS_TF_selection='latest (callback does not copy message stamp)',GMRF_TF_selection='message stamp',compatible_clock_domain=clock_ok,identical_TF_time=time_tf_ok))
with (out/'WIND_TOPIC_TF_CONSUMER_TEST.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
n1=[r for r in rows if r['kind']=='N1'];nonzero=[r for r in n1 if r['expected_u'] or r['expected_v']]
summary=dict(P0='PASS_FROZEN_NOT_REAUDITED',P1a='HOLD',P1b='HOLD_NOT_RUN_GATED_BY_P1a',
    fresh_N1=dict(cases=len(n1),nonzero_cases=len(nonzero),zero_cases=len(n1)-len(nonzero),verdict='PASS_FOR_FRESH_STATIONARY_TF_FIXTURES',
        max_PMFS_angle_error_rad=max(r['pmfs_angle_error_rad'] for r in nonzero),max_GMRF_angle_error_rad=max(r['gmrf_angle_error_rad'] for r in nonzero),
        max_GMRF_position_error_m=max(r['gmrf_position_error_m'] for r in n1),all_grid_indices_correct=True,
        max_receipt_age_s=max(max(r['pmfs_receipt_age_s'],r['gmrf_receipt_age_s']) for r in n1)),
    delayed_TF=dict(verdict='FAIL_FOR_TIMESTAMP_CONSISTENCY',consumer_angle_difference_rad=rows[-1]['consumer_angle_difference_rad'],
        message_to_PMFS_TF_delta_s=rows[-1]['pmfs_TF_minus_message_stamp_s'],PMFS_transformed_wind_pose_xy=[-1.75,2.25],GMRF_observation_xy=[1.25,1.25]),
    estimated_wind_field='HOLD: queried real map values, no converged-field accuracy PASS',
    scope='Real ROS/DDS + TF, unmodified upstream common wind callback + StopAndMeasure; GMRF node with passive trace; controlled fixed-input fixture, not complete original N0 launch or navigation',
    P2='NOT_RUN',P3='UNRESOLVED_NOT_RUN',new_gas_generation=False,new_CFD=False,new_network_training=False,
    existing_VM_started_by_this_task=False,existing_VM_shutdown_by_this_task=False)
write('R2_VERIFICATION_RESULTS.json',summary)
write('TF_CLOCK_MATRIX.json',dict(verdict='HOLD',numerical_gates=contract,actual_cases=clocks,clock_notice='TF lookup success alone does not prove compatible clock domains or timestamp semantics'))
print(json.dumps(summary,ensure_ascii=False,indent=2))
