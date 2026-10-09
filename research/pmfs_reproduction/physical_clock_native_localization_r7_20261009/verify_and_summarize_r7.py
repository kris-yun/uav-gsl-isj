"""Read-only evidence verification and summary. Requires numpy and PyYAML.
python verify_and_summarize_r7.py [--write-summary]
The optional summary writes outside raw runtime files; no ROS or simulation.
"""
from pathlib import Path
import json,csv,math,hashlib,sys,struct
import numpy as np
import yaml
p=Path(__file__).resolve().parent
def js(n):return json.loads((p/n).read_text(encoding='utf-8'))
run=js('run/RUN_RESULT.json');assert run['native_goal_count']==1 and run['result']=='NATIVE_ACTION_RETURNED'
assert run['localization_success'] is False and run['fixture_messages_injected']==0
with (p/'C1_PHYSICAL_FRAME_TIME.csv').open() as f:times=[float(r['physical_snapshot_time_s']) for r in csv.DictReader(f)]
with (p/'runtime/physical_clock_trace.csv').open() as f:clock=list(csv.DictReader(f))
assert clock and len(times)==1803
lags=[];errors=[];services=0
for r in clock:
    now=int(r['receipt_ros_ns']);anchor=int(r['anchor_ros_ns']);target=float(r['target_internal_s']);frame=int(r['frame'])
    expected=times[500]+(now-anchor)/1e9
    errors.append(abs(target-expected));assert abs(target-expected)<1e-9
    assert int(np.searchsorted(times,target,side='right')-1)==frame
    assert abs(float(r['frame_internal_s'])-times[frame])<1e-9
    assert times[frame]<=target<times[frame+1]
    lags.append(target-times[frame]);services+=r['reason'].endswith('service')
    assert int(r['wind_index'])==10
wind=js('WIND_QUERY_FILE_VERIFICATION.json');assert wind['max_abs_difference']==0
for line in (p/'runtime/raw_ros_cdr.jsonl').open():
    wire=json.loads(line)
    if wire['topic']=='/PioneerP3DX/map':break
else:raise AssertionError('Missing actual ROS map message')
data=bytes.fromhex(wire['cdr_hex'])[4:];position=0
def read(fmt):
    global position
    size=struct.calcsize(fmt);align=min(size,8);position=(position+align-1)//align*align
    v=struct.unpack_from('<'+fmt,data,position)[0];position+=size;return v
read('i');read('I');length=read('I');position+=length
read('i');read('I');res=read('f');width,height=read('I'),read('I')
origin=[read('d') for _ in range(3)];quat=[read('d') for _ in range(4)];length=read('I')
actual=np.frombuffer(data[position:position+length],dtype='i1').reshape(height,width)
pgm=(p/'official_C1/_occupancy.pgm').read_bytes();cursor=0
def token():
    global cursor
    while True:
        while pgm[cursor] in b' \t\r\n':cursor+=1
        if pgm[cursor]==35:cursor=pgm.index(b'\n',cursor)+1
        else:break
    start=cursor
    while pgm[cursor] not in b' \t\r\n':cursor+=1
    return pgm[start:cursor]
assert token()==b'P5';pw,ph,maximum=int(token()),int(token()),int(token())
if pgm[cursor:cursor+2]==b'\r\n':cursor+=2
else:cursor+=1
pixels=np.frombuffer(pgm[cursor:],dtype='u1').reshape(ph,pw)
expected_map=np.flipud(np.where(pixels>255*.9,0,np.where(pixels<255*.1,100,-1))).astype('i1')
assert np.array_equal(actual,expected_map) and [width,height]==[830,1190] and quat==[0,0,0,1]
assert hashlib.sha256(pgm).hexdigest()=='89db81d550448723452eec4c085a593848e5a01c945d2ed4863a6fcbadd6bbd6'
registry=js('C1_RAW_FRAME_SHA256_REFERENCE.json');after=js('RAW_C1_AFTER_RUN_SHA256.json');assert registry==after
assert len(after)==1803
with (p/'runtime/measurement_events.csv').open() as f:events=list(csv.reader(f))
grouped=[]
for row in events:
    stamp,gas,ws,wd,x,y,k,n=row;k=int(k)
    if not grouped or grouped[-1]['counter']!=k:grouped.append(dict(counter=k,rows=[]))
    grouped[-1]['rows'].append(row)
stops=[]
for g in grouped:
    rows=g['rows'];k=g['counter'];gas=[float(r[1]) for r in rows]
    stops.append(dict(stop=k+1,counter=k,blocks=len(rows),ROS_first_s=int(rows[0][0])/1e9,ROS_last_s=int(rows[-1][0])/1e9,x=float(rows[0][4]),y=float(rows[0][5]),gas_min=min(gas),gas_max=max(gas),positive_blocks=sum(x>=.1 for x in gas),source_update_trigger=k>=5 and k%3==0))
updates=sorted((p/'runtime/updates').glob('update_*'));assert len(updates)==1 and (updates[0]/'COMPLETE.txt').exists()
u=updates[0];m=json.loads((u/'metadata.json').read_text())
posterior=np.frombuffer((u/'posterior.f64').read_bytes(),dtype='<f8')
with (u/'input.csv').open() as f:inputs=list(csv.DictReader(f))
mask=np.array([int(r['occupancy']) for r in inputs]);assert np.all(posterior>=0) and abs(posterior.sum()-1)<1e-12
xy=np.array([[float(r['x']),float(r['y'])] for r in inputs]) if 'x' in inputs[0] else np.array([[m['origin_x']+(i%m['width']+.5)*m['cell_size'],m['origin_y']+(i//m['width']+.5)*m['cell_size']] for i in range(len(inputs))])
truth=np.array([0.,-1.]);index=int((truth[0]-m['origin_x'])/m['cell_size'])+int((truth[1]-m['origin_y'])/m['cell_size'])*m['width']
assert mask[index]==0 and posterior[index]==0
mean=np.sum(xy*posterior[:,None],axis=0);meanerror=np.linalg.norm(mean-truth)
maximum=posterior.max();ties=np.flatnonzero(posterior==maximum);chosen=int(ties[0]);tieerrors=np.linalg.norm(xy[ties]-truth,axis=1)
fields=(p/'runtime/native_results.csv').read_text().split();assert fields[0]=='FAILED'
assert abs(meanerror-float(fields[3]))<2e-5
path=np.array(js('runtime/robot_path.json'));distance=np.linalg.norm(np.diff(path[:,1:3],axis=0),axis=1).sum()
params=yaml.safe_load((p/'runtime/resolved_GSL_parameters.yaml').read_text())['/PioneerP3DX/GSL']['ros__parameters']
for k,v in [('maxSearchTime',300.),('sourceDiscriminationPower',.3),('initialExplorationMoves',5),('stepsSourceUpdate',3),('use_sim_time',True)]:assert params[k]==v
assert js('OWN_DOMAIN_AFTER_RUN.json')['active_pids']==[]
summary=dict(verdict='PHYSICAL_PLAYBACK_ALIGNMENT_PASS_NATIVE_LOCALIZATION_FAILED',native_goals=1,native_search_sim_s=float(fields[2]),native_goal_wall_s=run['wall_seconds'],official_basic_sim_speed=5,
    actual_robot_distance_m=float(distance),completed_measurement_stops=len(stops),measurement_blocks=len(events),positive_blocks=sum(s['positive_blocks'] for s in stops),
    source_updates=len(updates),saved_candidate_simulations=sum(1 for _ in csv.DictReader((u/'candidates.csv').open())),
    source_update_stamp_ROS_s=m['stamp_ns']/1e9,posterior_mean_xy=mean.tolist(),posterior_mean_error_m=float(meanerror),
    native_top5percent_mean_error_m=float(fields[4]),native_final_variance=float(fields[6]),convergence_variance_threshold=params['convergence_thr'],
    MAP_tie_count=len(ties),MAP_canonical_first_row_xy=xy[chosen].tolist(),MAP_canonical_error_m=float(tieerrors[0]),MAP_tie_error_range_m=[float(tieerrors.min()),float(tieerrors.max())],
    true_source_cell_supported=False,clock_trace_rows=len(clock),gas_wind_service_trace_rows=services,max_clock_formula_error_s=max(errors),
    max_discrete_frame_hold_age_s=max(lags),no_future_frame_consumed=True,actual_frame_clock_alignment='PASS',
    raw_1803_frames_unchanged=True,wind_service_matches_actual_file=True,localization_success=False,
    actual_ROS_map_equals_pinned_official_PGM=True,
    source_of_failure_causal_assignment='UNRESOLVED_SINGLE_RUN_WITH_AUTHOR_SUPPORT_AND_UPDATE_RULES',
    historical_author_original_pipeline_reproduction=False,variant='N1_ENGINEERING_TIME_AND_WIND_ALIGNMENT',teardown='POST_RESULT_GSL_EXIT_MINUS6_KNOWN_HOLD',
    new_gas_generation_in_R7=False,VM_left_running=True,own_domain_processes_remaining=0)
if '--write-summary' in sys.argv:
    (p/'R7_RESULT.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    with (p/'MEASUREMENT_TIMELINE.csv').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=stops[0]);w.writeheader();w.writerows(stops)
manifest=p/'SHA256_MANIFEST.json'
if manifest.exists():
    for n,h in js('SHA256_MANIFEST.json').items():assert hashlib.sha256((p/n).read_bytes()).hexdigest()==h,n
print(json.dumps(summary))
