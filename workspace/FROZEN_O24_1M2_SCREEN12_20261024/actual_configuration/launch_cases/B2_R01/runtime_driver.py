from pathlib import Path
import os,json,time,subprocess,signal,math,copy,traceback,datetime,shutil
import rclpy
from rclpy.node import Node
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.qos import QoSProfile,DurabilityPolicy,ReliabilityPolicy
from rclpy.action import ActionClient
from rclpy.serialization import serialize_message
from rosgraph_msgs.msg import Clock
from tf2_msgs.msg import TFMessage
from geometry_msgs.msg import PoseWithCovarianceStamped,Twist
from nav_msgs.msg import OccupancyGrid
from olfaction_msgs.msg import GasSensor,Anemometer
from gaden_msgs.srv import GasPosition,WindPosition
from lifecycle_msgs.srv import GetState
from gsl_actions.action import DoGSL
from tf2_ros import Buffer,TransformListener

T=Path('/home/zyc/ros2_ws/research_runs/o24_paper_screen12_20261024/cases/B2_R01');R=Path('/mnt/hgfs/workspace/O24_PAPER_SCREEN12_20261024/cases/B2_R01/runtime');R.mkdir(exist_ok=True)
META=json.loads((T/'CASE_META.json').read_text())
assert not (T/'RUN_STARTED.json').exists()
os.environ.update(ROS_DOMAIN_ID='228',OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='1',PMFS_R5_CAPTURE=str(R/'updates'),PMFS_R5_CONSUMERS=str(R/'consumer_messages.csv'),PMFS_R5_EVENTS=str(R/'measurement_events.csv'),PMFS_R5_PLAYER=str(R/'player_frames.csv'))
os.environ['NATIVE_PMFS_WINDOW_TRACE']=str(R/'native_window_consumption.csv')
os.environ['NATIVE_PMFS_POSTERIOR_TRACE']=str(R/'native_posterior_updates.csv')
os.environ['NATIVE_PMFS_CANDIDATE_AUDIT']=str(R/'native_candidate_maps')
os.environ['O24_RNG_TRACE']=str(R/'native_rng_states.jsonl')
processes=[]
def start(name,cmd,extra=None):
 env=os.environ.copy();env.update(extra or {});f=(R/(name+'.log')).open('w');p=subprocess.Popen(cmd,stdout=f,stderr=f,env=env,start_new_session=True);processes.append((name,p,f));return p
def stop_all():
 rows=[]
 for name,p,f in reversed(processes):
  row=dict(name=name,pid=p.pid)
  for sig,wait in [(signal.SIGINT,5),(signal.SIGTERM,3),(signal.SIGKILL,3)]:
   if p.poll()is not None:break
   try:os.killpg(p.pid,sig)
   except ProcessLookupError:break
   try:p.wait(timeout=wait)
   except subprocess.TimeoutExpired:continue
  row['returncode']=p.poll();rows.append(row);f.close()
 (R/'DRIVER_SHUTDOWN.json').write_text(json.dumps(rows,indent=2))

status=dict(case=META['case'],input_class=META['audit_profile'],physical_qualification='WIND_FULL_ARRAY_AND_SHORT_RUNTIME_GATE_PASS_CONSUMER_AUDIT_PENDING',native_goal_count=0,fixture_messages_injected=0,generated_gas_data=0,processes=[])
wire=__import__('gzip').open(R/'raw_ros_cdr.jsonl.gz','wt',compresslevel=1);counts={};latest={};pose_path=[];cmd_nonzero=0
def record(topic,msg):
 counts[topic]=counts.get(topic,0)+1;latest[topic]=msg
 # Full raw messages retained; no reduction.
 keep=True
 if keep:wire.write(json.dumps(dict(topic=topic,receipt_ns=node.get_clock().now().nanoseconds,cdr_hex=serialize_message(msg).hex()))+'\n')

# Reject all matching-domain processes, without executable-name filters.
import sys
sys.path.insert(0,'/mnt/hgfs/workspace/O24_PAPER_SCREEN12_20261024')
from isolation_guard import inventory, require_vacant
require_vacant(inventory(228,exclude={os.getpid()}),R/'IMMEDIATE_PRE_DDS_GATE.json')

rclpy.init();node=Node('b4_capture_and_wind_adapter',parameter_overrides=[rclpy.parameter.Parameter('use_sim_time',value=True)])
buffer=Buffer();listener=TransformListener(buffer,node)
to=node.create_publisher(Anemometer,'/native20/wind_to',20)
def wind(m):
 record('/PioneerP3DX/Anemometer/WindSensor_reading',m);n=copy.deepcopy(m);n.wind_direction=math.atan2(math.sin(m.wind_direction+math.pi),math.cos(m.wind_direction+math.pi));to.publish(n);record('/native20/wind_to',n)
def pose(m):
 record('/PioneerP3DX/ground_truth',m);p=m.pose.pose.position;pose_path.append([m.header.stamp.sec+m.header.stamp.nanosec/1e9,p.x,p.y,p.z])
def cmd(m):
 global cmd_nonzero
 record('/PioneerP3DX/cmd_vel',m);cmd_nonzero+=abs(m.linear.x)+abs(m.angular.z)>1e-5
subs=[node.create_subscription(Anemometer,'/PioneerP3DX/Anemometer/WindSensor_reading',wind,100),node.create_subscription(GasSensor,'/PioneerP3DX/PID/Sensor_reading',lambda m:record('/PioneerP3DX/PID/Sensor_reading',m),100),node.create_subscription(PoseWithCovarianceStamped,'/PioneerP3DX/ground_truth',pose,100),node.create_subscription(Twist,'/PioneerP3DX/cmd_vel',cmd,100),node.create_subscription(TFMessage,'/tf',lambda m:record('/tf',m),100),node.create_subscription(Clock,'/clock',lambda m:record('/clock',m),QoSProfile(depth=100,reliability=ReliabilityPolicy.BEST_EFFORT)),node.create_subscription(TFMessage,'/tf_static',lambda m:record('/tf_static',m),QoSProfile(depth=100,durability=DurabilityPolicy.TRANSIENT_LOCAL)),node.create_subscription(OccupancyGrid,'/PioneerP3DX/map',lambda m:record('/PioneerP3DX/map',m),QoSProfile(depth=1,durability=DurabilityPolicy.TRANSIENT_LOCAL))]
service_group=ReentrantCallbackGroup()
raw_gas=node.create_client(GasPosition,'/native20/raw_odor_value',callback_group=service_group)
raw_wind=node.create_client(WindPosition,'/native20/raw_wind_value',callback_group=service_group)
service_log=(R/'service_queries.jsonl').open('w')
service_serial=0
async def forward_query(kind,client,request,response):
 global service_serial
 serial=service_serial;service_serial+=1
 before=node.get_clock().now().nanoseconds
 request_hex=serialize_message(request).hex()
 result=await client.call_async(request)
 service_log.write(json.dumps(dict(serial=serial,kind=kind,request_ns=before,response_ns=node.get_clock().now().nanoseconds,x=list(request.x),y=list(request.y),z=list(request.z),request_cdr_hex=request_hex,response_cdr_hex=serialize_message(result).hex()))+'\n')
 return result
async def gas_proxy(req,resp):return await forward_query('GasPosition',raw_gas,req,resp)
async def wind_proxy(req,resp):return await forward_query('WindPosition',raw_wind,req,resp)
gas_server=node.create_service(GasPosition,'/odor_value',gas_proxy,callback_group=service_group)
wind_server=node.create_service(WindPosition,'/wind_value',wind_proxy,callback_group=service_group)
gas=node.create_client(GasPosition,'/odor_value',callback_group=service_group);air=node.create_client(WindPosition,'/wind_value',callback_group=service_group);action=ActionClient(node,DoGSL,'/PioneerP3DX/gsl_server')
lifecycle={n:node.create_client(GetState,'/PioneerP3DX/'+n+'/get_state') for n in ['map_server','planner_server','controller_server','bt_navigator','behavior_server']}
def call(client,req,timeout=4):
 if not client.wait_for_service(timeout_sec=timeout):raise RuntimeError('service unavailable '+client.srv_name)
 f=client.call_async(req);end=time.time()+timeout
 while time.time()<end and not f.done():rclpy.spin_once(node,timeout_sec=.05)
 if not f.done():raise RuntimeError('service timeout '+client.srv_name)
 return f.result()
def snapshot_parameters(target,filename):
 from rcl_interfaces.srv import ListParameters,GetParameters
 from rosidl_runtime_py.convert import message_to_ordereddict
 lc=node.create_client(ListParameters,target+'/list_parameters',callback_group=service_group)
 lr=ListParameters.Request();lr.depth=100
 names=list(call(lc,lr,timeout=8).result.names)
 gc=node.create_client(GetParameters,target+'/get_parameters',callback_group=service_group)
 gr=GetParameters.Request();gr.names=names
 values=call(gc,gr,timeout=12).values
 (R/filename).write_text(json.dumps(dict(node=target,names=names,values=[message_to_ordereddict(v)for v in values],capture='DirectROSparameterServices_noCLI'),indent=2))

def save_status():
 status.update(counts=counts,nonzero_cmd_vel_messages=int(cmd_nonzero),pose_samples=len(pose_path),processes=[dict(name=n,pid=p.pid,returncode=p.poll()) for n,p,_ in processes]);(T/'RUNTIME_STATUS.json').write_text(json.dumps(status,indent=2))
try:
 launch=start('launch',['ros2','launch',str(T/'N1_launch.py'),'scenario:=B','simulation:=B2','method:=PMFS'])
 gmrf=start('gmrf',['/home/zyc/ros2_ws/pmfs_official_repro_audit_20261016/install_paper_gmrf_tfqualified_2024/lib/gmrf_wind_mapping/gmrf_wind_mapping_node','--ros-args','-p','use_sim_time:=true','-p','sensor_topic:=/PioneerP3DX/Anemometer/WindSensor_reading','-p','map_topic:=/PioneerP3DX/map','-p','cell_size:=0.25','-p','exec_freq:=2.0'],{'GMRF_R2_TRACE':str(R/'GMRF_consumed.csv')})
 before=time.time()
 while time.time()-before<70:
  rclpy.spin_once(node,timeout_sec=.1)
  if launch.poll() is not None:raise RuntimeError('launch exited before preflight')
  if time.time()-before>=15 and not (R/'STARTUP_LIFECYCLE_DIAGNOSIS.json').exists():
   try:
    zz={n:call(c,GetState.Request()).current_state.label for n,c in lifecycle.items()};(R/'STARTUP_LIFECYCLE_DIAGNOSIS.json').write_text(json.dumps(zz,indent=2))
   except Exception as exc:(R/'STARTUP_LIFECYCLE_DIAGNOSIS.json').write_text(json.dumps(dict(error=str(exc))))
  if time.time()-before>=12 and counts.get('/native20/wind_to',0)>=10 and counts.get('/PioneerP3DX/PID/Sensor_reading',0)>=10 and counts.get('/PioneerP3DX/map',0)>0 and action.server_is_ready():break
 else:raise RuntimeError('preflight missing sensor/map/action output')
 states={n:call(c,GetState.Request()).current_state.label for n,c in lifecycle.items()}
 if any(x!='active' for x in states.values()):raise RuntimeError('Nav2 lifecycle not active '+str(states))
 tf=buffer.lookup_transform('map','PioneerP3DX_anemometer_frame',rclpy.time.Time());pos=tf.transform.translation
 rq=GasPosition.Request();rq.x=[float(pos.x)];rq.y=[float(pos.y)];rq.z=[float(pos.z)];g=call(gas,rq)
 rq=WindPosition.Request();rq.x=[float(pos.x)];rq.y=[float(pos.y)];rq.z=[float(pos.z)];w=call(air,rq)
 assert all(math.isfinite(v) for v in [*w.u,*w.v,*w.w]),'nonfinite wind'
 assert len(g.positions)==1 and all(math.isfinite(v) and v>=0 for v in g.positions[0].concentration),'nonfinite gas'
 assert abs(pos.z-META['sensor_xyz'][2])<1e-5,'sensor elevation mismatch'
 pre=dict(lifecycle=states,sensor_xyz=[pos.x,pos.y,pos.z],gas_types=list(g.gas_type),gas_ppm=list(g.positions[0].concentration),wind_uvw=[list(w.u),list(w.v),list(w.w)],ROS_DOMAIN_ID=228,sim_clock_ns=node.get_clock().now().nanoseconds,input_class=status['input_class'],B4_physics_qualification=status['physical_qualification'])
 # Before the single goal, verify native raw message types, frames, stamps and stationary TF.
 pid=latest['/PioneerP3DX/PID/Sensor_reading'];an=latest['/PioneerP3DX/Anemometer/WindSensor_reading']
 assert pid.raw_units==pid.UNITS_PPM and pid.technology==pid.TECH_PID and math.isfinite(pid.raw) and pid.raw>=0
 ages={}
 for label,msg in [('PID',pid),('anemometer',an)]:
  stamp=msg.header.stamp.sec*1000000000+msg.header.stamp.nanosec
  age=(node.get_clock().now().nanoseconds-stamp)/1e9
  assert stamp>0 and 0<=age<2,(label,age)
  ages[label]=age
 assert pid.header.frame_id=='PioneerP3DX_pid_frame' and an.header.frame_id=='PioneerP3DX_anemometer_frame'
 assert abs(pos.x-META['sensor_xyz'][0])<1e-3 and abs(pos.y-META['sensor_xyz'][1])<1e-3
 # Read the physically bound source neighborhood only as qualification; not fed to PMFS.
 probe=GasPosition.Request();probe.x=[float(META['source_xyz'][0])];probe.y=[float(META['source_xyz'][1])];probe.z=[float(META['source_xyz'][2])];pconc=call(gas,probe)
 assert all(math.isfinite(v) and v>=0 for v in pconc.positions[0].concentration)
 # Source metadata/geometry qualified independently; zero instantaneous source-neighborhood concentration is retained, not used to select a favorable frame.
 for n in ['gaden_player','PioneerP3DX/PID','PioneerP3DX/Anemometer','basic_sim']:
  snapshot_parameters('/'+n,'preflight_'+n.replace('/','_')+'_parameters.json')
 pre.update(message_age_sim_seconds=ages,PID_units='ppm',PID_model=30,PID_response='sum ppm; correction_factors=false from pinned code/default; resolved dump saved',probe_source_neighborhood_ppm=list(pconc.positions[0].concentration),probe_is_input_to_algorithm=False,gas_frame_binding='physical_clock_trace.csv records wall-file cadence, actual physical snapshot times in original_physical_frame_timeline',sensor_frames=[pid.header.frame_id,an.header.frame_id],native_goal_count=0)
 navmap=latest['/PioneerP3DX/map'];rawmap=bytes((int(v)&255)for v in navmap.data)
 (R/'navigation_map.s8').write_bytes(rawmap)
 assert __import__('hashlib').sha256(rawmap).hexdigest()==META['expected_navigation_map_sha256'],'OFFICIAL_MAP_IDENTITY_MISMATCH'
 (R/'NAVIGATION_MAP_METADATA.json').write_text(json.dumps(dict(width=navmap.info.width,height=navmap.info.height,resolution=navmap.info.resolution,origin_x=navmap.info.origin.position.x,origin_y=navmap.info.origin.position.y,occupancy_sha256=__import__('hashlib').sha256(rawmap).hexdigest()),indent=2))
 (R/'PREFLIGHT.json').write_text(json.dumps(pre,indent=2));status['preflight']='PASS';save_status()
 # Existing data exhaustion is a wall-file-cadence censor, not a PMFS failure.
 import csv
 timeline=list(csv.DictReader(Path(META['player']['r7_frame_time_csv']).open()))
 clock_rows=list(csv.DictReader((R/'physical_clock_trace.csv').open()))
 anchor=int(clock_rows[-1]['anchor_ros_ns'])
 data_end_system_s=anchor/1e9+float(timeline[-1]['physical_snapshot_time_s'])-float(timeline[int(META['player']['initial_iteration'])]['physical_snapshot_time_s'])-.3
 (R/'PLAYBACK_POLICY.json').write_text(json.dumps(dict(official_cyclic=META['official_playback_loop'],data_end_system_s=data_end_system_s,clock_domain='shared_ROS_physical_time',cyclic_data_are_not_independent_new_realizations=True),indent=2))


 # Require the recorded public-example5x robot-clock slope and wall receptor cadence.
 # Synchronous ros2 parameter dumps pause this observer's executor. Drain its
 # queued TimeSource/sensor callbacks before measuring the clock slope.
 drain_until=time.monotonic()+3.0
 while time.monotonic()<drain_until:rclpy.spin_once(node,timeout_sec=.001)
 first_system=time.monotonic();first_ros=node.get_clock().now().nanoseconds
 basegas=counts.get('/PioneerP3DX/PID/Sensor_reading',0)
 basewind=counts.get('/PioneerP3DX/Anemometer/WindSensor_reading',0)
 while time.monotonic()-first_system<2.0:rclpy.spin_once(node,timeout_sec=.02)
 wall_delta=time.monotonic()-first_system;ros_delta=(node.get_clock().now().nanoseconds-first_ros)/1e9
 gas_rate=(counts.get('/PioneerP3DX/PID/Sensor_reading',0)-basegas)/ros_delta
 wind_rate=(counts.get('/PioneerP3DX/Anemometer/WindSensor_reading',0)-basewind)/ros_delta
 assert .8<ros_delta/wall_delta<1.2,('clock rate mismatch',ros_delta/wall_delta)
 assert gas_rate*ros_delta/wall_delta>=7.0 and wind_rate*ros_delta/wall_delta>=14.0,('sensor wall cadence mismatch',gas_rate,wind_rate)
 (R/'CLOCK_SENSOR_RATE_PREFLIGHT.json').write_text(json.dumps(dict(wall_delta_s=wall_delta,ROS_delta_s=ros_delta,real_time_factor=ros_delta/wall_delta,gas_samples_per_ROS_second=gas_rate,wind_samples_per_ROS_second=wind_rate,stop_window_physical_s=.4,expected_robot_clock_window_s=.4,gas_samples_per_wall_second=gas_rate*ros_delta/wall_delta,wind_samples_per_wall_second=wind_rate*ros_delta/wall_delta),indent=2))

 # Verify the exact native executable and local GMRF before admitting one goal.
 expected_binary=Path('/home/zyc/ros2_ws/pmfs_o24_port_gmrf_20261018/gsl_actionserver_node')
 candidates=[]
 for proc in Path('/proc').iterdir():
  if not proc.name.isdigit():continue
  try:
   exe=(proc/'exe').resolve()
   if exe==expected_binary.resolve() and b'ROS_DOMAIN_ID=228' in (proc/'environ').read_bytes().split(b'\0'):
    env=(proc/'environ').read_bytes().split(b'\0')
    assert b'OMP_NUM_THREADS=4'in env
    candidates.append(dict(pid=int(proc.name),exe=str(exe),sha256=__import__('hashlib').sha256(exe.read_bytes()).hexdigest(),OMP_NUM_THREADS=4))
  except (PermissionError,FileNotFoundError,ProcessLookupError):pass
 assert len(candidates)==1,('native executable identity',candidates)
 (R/'NATIVE_EXECUTABLE_IDENTITY.json').write_text(json.dumps(candidates,indent=2))
 if not META['audit_setting']['ground_truth_wind']:
  from gmrf_wind_mapping.srv import WindEstimation
  gc=node.create_client(WindEstimation,'/WindEstimation',callback_group=service_group)
  gr=WindEstimation.Request();gr.x=[float(pos.x)];gr.y=[float(pos.y)]
  ge=call(gc,gr,timeout=8)
  assert len(ge.u)==1 and len(ge.v)==1 and math.isfinite(ge.u[0])and math.isfinite(ge.v[0]),'GMRF qualification failed'
  accepted=list(csv.DictReader((R/'GMRF_consumed.csv').open()))
  assert len(accepted)>=3,'GMRF accepted too few valid sensor observations'
  assert all(abs(float(z['x'])-META['sensor_xyz'][0])<1e-3 and abs(float(z['y'])-META['sensor_xyz'][1])<1e-3 for z in accepted),'GMRF startup observation outside actual sensor pose'
  assert counts.get('/PioneerP3DX/Anemometer/WindSensor_reading',0)>=10
  (R/'LOCAL_GMRF_PREFLIGHT.json').write_text(json.dumps(dict(source='2024 GMRF estimator with missingTF rejection and passive accepted-observation trace; local wind and original2024 map',observed_sensor_messages=counts.get('/PioneerP3DX/Anemometer/WindSensor_reading',0),actual_accepted_callbacks=len(accepted),internal_callback_count_not_instrumented=False,estimated_at_robot=[ge.u[0],ge.v[0]],true_field_fed_to_GMRF=False),indent=2))


 trace_rows=list(csv.DictReader((R/'physical_clock_trace.csv').open()))
 assert len(trace_rows)>3,'PLAYER_CLOCK_TRACE_INSUFFICIENT'
 (R/'CLOCK_PROTOCOL_SCOPE.json').write_text(json.dumps(dict(identity=META['experiment_identity'],all_three_clocks_shared=True,continuous_saved_physical_timeline=True,looping=False,paper_exact_author_run=False),indent=2))

 assert isinstance(node.get_clock().now().nanoseconds,int),'ROS_TIME_PROPERTY_TYPE'
 # Preflight does not trigger a candidate update. One and only one real GSL goal.
 (T/'RUN_STARTED.json').write_text(json.dumps(dict(wall_time=time.time(),ROS_ns=node.get_clock().now().nanoseconds,native_goal_count=1,input_class=status['input_class'],maxSearchTime=1e9,max_goal_wall_s=1100.,PMFS_manuscript_maximum_seconds=None)))
 status['goal_invocation_ROS_ns']=node.get_clock().now().nanoseconds;status['native_goal_count']=1;goal=DoGSL.Goal();goal.gsl_method='PMFS';sent=action.send_goal_async(goal)
 end=time.time()+10
 while not sent.done() and time.time()<end:rclpy.spin_once(node,timeout_sec=.1)
 if not sent.done() or not sent.result().accepted:raise RuntimeError('GSL goal not accepted')
 handle=sent.result();result=handle.get_result_async();starttime=time.time();status['goal_accepted']=True
 dump_started=False;last_status=0
 deadline=time.time()+1100.0 # Resource watchdog only; normal stopping is native variance.
 while not result.done() and time.time()<deadline:
  rclpy.spin_once(node,timeout_sec=.05)
  if data_end_system_s is not None and node.get_clock().now().nanoseconds/1e9>=data_end_system_s:
   status['resource_stop_reason']='EXISTING_CONTINUOUS_PHYSICAL_RECORDING_EXHAUSTED';handle.cancel_goal_async();raise RuntimeError('External data recording ended; not a PMFS scientific failure or manuscript time cutoff')
  if shutil.disk_usage('/home/zyc').free<1024**3 or shutil.disk_usage('/mnt/hgfs/workspace').free<512*1024**2:
   status['resource_stop_reason']='DISK_RESERVE_REACHED';handle.cancel_goal_async();raise RuntimeError('External resource reserve reached')
  if time.time()-last_status>5:save_status();last_status=time.time()
  if not dump_started and time.time()-starttime>1:
   snapshot_parameters('/PioneerP3DX/GSL','resolved_GSL_parameters.json')
   pp=json.loads((R/'resolved_GSL_parameters.json').read_text())
   values={}
   for k,v in zip(pp['names'],pp['values']):
    values[k]=v['bool_value'] if v['type']==1 else v['integer_value'] if v['type']==2 else v['double_value'] if v['type']==3 else v['string_value']
   missing=[k for k in META['expected_parameters']if k not in values]
   if missing:
    (R/'PARAMETER_DECLARATION_WAIT.json').write_text(json.dumps(dict(missing=missing,elapsed_after_goal_s=time.time()-starttime),indent=2))
    if time.time()-starttime>20:raise RuntimeError('REQUIRED_PARAMETERS_NOT_DECLARED:'+str(missing))
   else:
    for k,v in META['expected_parameters'].items():
     assert values[k]==v,('RESOLVED_BASELINE_PARAMETER_MISMATCH',k,values.get(k),v)
    (R/'BASELINE_PARAMETER_GATE.json').write_text(json.dumps(dict(status='PASS_ACTUAL_NODE_PARAMETER_VALUES',checked=META['expected_parameters']),indent=2))
    dump_started=True
  if not Path('/proc/'+str(candidates[0]['pid'])+'/exe').exists():
   status['technical_reason']='NATIVE_PROCESS_EXITED_WITHOUT_ACTION_RESULT';raise RuntimeError('Native process exited before action result; technical evidence retained')
  if launch.poll() is not None and not result.done():
   for _ in range(20):rclpy.spin_once(node,timeout_sec=.1)
   if not result.done():raise RuntimeError('launch exited during native goal')
 if not result.done():
  status['result']='OUTER_TIMEOUT';handle.cancel_goal_async()
 else:
  q=result.result();status.update(result='NATIVE_ACTION_RETURNED',action_status=int(q.status),localization_success=bool(q.result.success),wall_seconds=time.time()-starttime)
except Exception as e:
 status.update(result='RUNTIME_ERROR',error=str(e),traceback=traceback.format_exc())
finally:
 save_status();stop_all();wire.close();service_log.close();(R/'robot_path.json').write_text(json.dumps(pose_path));save_status();(T/'RUN_RESULT.json').write_text(json.dumps(status,indent=2));# All child groups stopped, CDR/service sinks closed, paths/status/result saved. Avoid rclpy destructor waiting on a cancelled service future.
 os._exit(0)
