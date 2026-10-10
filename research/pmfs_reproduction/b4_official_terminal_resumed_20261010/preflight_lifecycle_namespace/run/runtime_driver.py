from pathlib import Path
import os,json,time,subprocess,signal,math,copy,traceback,re
from runtime_guard_policy import RuntimeGuard
from guard_ros_io import dump_parameters
from service_startup_gate import expose_if_backends_ready
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

T=Path('/home/zyc/pmfs_b4_official_terminal_final_20261010');R=T/'runtime';R.mkdir(exist_ok=True)
assert not (T/'RUN_STARTED.json').exists()
os.environ.update(ROS_DOMAIN_ID='82',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',PMFS_R5_CAPTURE=str(R/'updates'),PMFS_R5_CONSUMERS=str(R/'consumer_messages.csv'),PMFS_R5_EVENTS=str(R/'measurement_events.csv'),PMFS_R5_PLAYER=str(R/'player_frames.csv'))
processes=[]
def start(name,cmd,extra=None):
 env=os.environ.copy();env.update(extra or {});f=(R/(name+'.log')).open('w');p=subprocess.Popen(cmd,stdout=f,stderr=f,env=env,start_new_session=True);processes.append((name,p,f));return p
def stop_all():
 for name,p,f in reversed(processes):
  try: os.killpg(p.pid,signal.SIGINT)
  except ProcessLookupError: pass
 for name,p,f in reversed(processes):
  try:p.wait(timeout=8)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=8)
  f.close()

status=dict(input_class='ONE_B4_OFFICIAL_PARAMETERS_N1_ENGINEERING_ALIGNMENT',B4_physics_qualification='PASS_SOURCE_GEOMETRY_WIND_TIME_SIDECAR_N1',native_goal_count=0,fixture_messages_injected=0,generated_gas_data=0,processes=[])
wire=(R/'raw_ros_cdr.jsonl').open('w');counts={};latest={};pose_path=[];cmd_nonzero=0;last_receipt_wall={}
def record(topic,msg):
 counts[topic]=counts.get(topic,0)+1;latest[topic]=msg;last_receipt_wall[topic]=time.monotonic()
 # Full raw messages retained; no reduction.
 keep=True
 if keep:wire.write(json.dumps(dict(topic=topic,receipt_ns=node.get_clock().now().nanoseconds,cdr_hex=serialize_message(msg).hex()))+'\n');wire.flush()

rclpy.init();node=Node('b4_capture_and_wind_adapter',parameter_overrides=[rclpy.parameter.Parameter('use_sim_time',value=True)])
buffer=Buffer();listener=TransformListener(buffer,node)
to=node.create_publisher(Anemometer,'/b4/wind_to',20)
def wind(m):
 record('/PioneerP3DX/Anemometer/WindSensor_reading',m);n=copy.deepcopy(m);n.wind_direction=math.atan2(math.sin(m.wind_direction+math.pi),math.cos(m.wind_direction+math.pi));to.publish(n);record('/b4/wind_to',n)
def pose(m):
 record('/PioneerP3DX/ground_truth',m);p=m.pose.pose.position;pose_path.append([m.header.stamp.sec+m.header.stamp.nanosec/1e9,p.x,p.y,p.z])
def cmd(m):
 global cmd_nonzero
 record('/PioneerP3DX/cmd_vel',m);cmd_nonzero+=abs(m.linear.x)+abs(m.angular.z)>1e-5
subs=[node.create_subscription(Anemometer,'/PioneerP3DX/Anemometer/WindSensor_reading',wind,100),node.create_subscription(GasSensor,'/PioneerP3DX/PID/Sensor_reading',lambda m:record('/PioneerP3DX/PID/Sensor_reading',m),100),node.create_subscription(PoseWithCovarianceStamped,'/PioneerP3DX/ground_truth',pose,100),node.create_subscription(Twist,'/PioneerP3DX/cmd_vel',cmd,100),node.create_subscription(TFMessage,'/tf',lambda m:record('/tf',m),100),node.create_subscription(Clock,'/clock',lambda m:record('/clock',m),QoSProfile(depth=100,reliability=ReliabilityPolicy.BEST_EFFORT)),node.create_subscription(TFMessage,'/tf_static',lambda m:record('/tf_static',m),QoSProfile(depth=100,durability=DurabilityPolicy.TRANSIENT_LOCAL)),node.create_subscription(OccupancyGrid,'/PioneerP3DX/map',lambda m:record('/PioneerP3DX/map',m),QoSProfile(depth=1,durability=DurabilityPolicy.TRANSIENT_LOCAL))]
service_group=ReentrantCallbackGroup()
raw_gas=node.create_client(GasPosition,'/b4/raw_odor_value',callback_group=service_group)
raw_wind=node.create_client(WindPosition,'/b4/raw_wind_value',callback_group=service_group)
service_log=(R/'service_queries.jsonl').open('w')
service_serial=0
async def forward_query(kind,client,request,response):
 global service_serial
 serial=service_serial;service_serial+=1
 before=node.get_clock().now().nanoseconds
 request_hex=serialize_message(request).hex()
 assert client.service_is_ready(),kind+' raw backend lost before forwarding'
 result=await client.call_async(request)
 service_log.write(json.dumps(dict(serial=serial,kind=kind,request_ns=before,response_ns=node.get_clock().now().nanoseconds,x=list(request.x),y=list(request.y),z=list(request.z),request_cdr_hex=request_hex,response_cdr_hex=serialize_message(result).hex()))+'\n');service_log.flush()
 return result
async def gas_proxy(req,resp):return await forward_query('GasPosition',raw_gas,req,resp)
async def wind_proxy(req,resp):return await forward_query('WindPosition',raw_wind,req,resp)
gas_server=None;wind_server=None
proxy_creators=[lambda:node.create_service(GasPosition,'/odor_value',gas_proxy,callback_group=service_group),lambda:node.create_service(WindPosition,'/wind_value',wind_proxy,callback_group=service_group)]
gas=node.create_client(GasPosition,'/odor_value',callback_group=service_group);air=node.create_client(WindPosition,'/wind_value',callback_group=service_group);action=ActionClient(node,DoGSL,'/PioneerP3DX/gsl_server')
lifecycle={n:node.create_client(GetState,'/PioneerP3DX/'+n+'/get_state') for n in ['map_server','planner_server','controller_server','bt_navigator','behavior_server']}
def call(client,req,timeout=4):
 if not client.wait_for_service(timeout_sec=timeout):raise RuntimeError('service unavailable '+client.srv_name)
 f=client.call_async(req);end=time.time()+timeout
 while time.time()<end and not f.done():rclpy.spin_once(node,timeout_sec=.05)
 if not f.done():raise RuntimeError('service timeout '+client.srv_name)
 return f.result()
def save_status():
 status.update(counts=counts,nonzero_cmd_vel_messages=int(cmd_nonzero),pose_samples=len(pose_path),processes=[dict(name=n,pid=p.pid,returncode=p.poll()) for n,p,_ in processes]);(T/'RUNTIME_STATUS.tmp').write_text(json.dumps(status,indent=2));(T/'RUNTIME_STATUS.tmp').replace(T/'RUNTIME_STATUS.json')
try:
 launch=start('launch',['ros2','launch',str(T/'N1_B4_launch.py'),'scenario:=B','simulation:=B4','method:=PMFS'])
 gmrf=start('gmrf',['/home/zyc/pmfs_wind_one_update_r2_20261009/gmrf_wind_observed','--ros-args','-p','use_sim_time:=true','-p','sensor_topic:=/PioneerP3DX/Anemometer/WindSensor_reading','-p','map_topic:=/PioneerP3DX/map','-p','cell_size:=0.25','-p','exec_freq:=10.0'],{'GMRF_R2_TRACE':str(R/'GMRF_consumed.csv')})
 before=time.time();last_preflight_status=0
 while time.time()-before<70:
  rclpy.spin_once(node,timeout_sec=.1)
  if launch.poll() is not None:raise RuntimeError('launch exited before preflight')
  if gas_server is None:
   exposed=expose_if_backends_ready([raw_gas,raw_wind],proxy_creators)
   if exposed is not None:
    gas_server,wind_server=exposed;status['raw_backends_ready_before_proxy_exposure']=True;status['proxy_exposed_ROS_ns']=node.get_clock().now().nanoseconds
  if time.time()-last_preflight_status>5:
   status['preflight_stage']='WAIT_NATIVE_SENSORS_MAP_ACTION';status['action_server_ready']=action.server_is_ready();status['native_lifecycle_services_ready']={n:c.service_is_ready() for n,c in lifecycle.items()};status['node_graph']=node.get_node_names_and_namespaces();save_status();last_preflight_status=time.time()
  if time.time()-before>=12 and counts.get('/b4/wind_to',0)>=10 and counts.get('/PioneerP3DX/PID/Sensor_reading',0)>=10 and counts.get('/PioneerP3DX/map',0)>0 and action.server_is_ready():break
 else:raise RuntimeError('preflight missing sensor/map/action output')
 states={n:call(c,GetState.Request()).current_state.label for n,c in lifecycle.items()}
 if any(x!='active' for x in states.values()):raise RuntimeError('Nav2 lifecycle not active '+str(states))
 tf=buffer.lookup_transform('map','PioneerP3DX_anemometer_frame',rclpy.time.Time());pos=tf.transform.translation
 rq=GasPosition.Request();rq.x=[float(pos.x)];rq.y=[float(pos.y)];rq.z=[float(pos.z)];g=call(gas,rq)
 rq=WindPosition.Request();rq.x=[float(pos.x)];rq.y=[float(pos.y)];rq.z=[float(pos.z)];w=call(air,rq)
 assert all(math.isfinite(v) for v in [*w.u,*w.v,*w.w]),'nonfinite wind'
 assert len(g.positions)==1 and all(math.isfinite(v) and v>=0 for v in g.positions[0].concentration),'nonfinite gas'
 assert abs(pos.z+.2)<1e-5,'sensor elevation mismatch'
 pre=dict(lifecycle=states,sensor_xyz=[pos.x,pos.y,pos.z],gas_types=list(g.gas_type),gas_ppm=list(g.positions[0].concentration),wind_uvw=[list(w.u),list(w.v),list(w.w)],ROS_DOMAIN_ID=82,sim_clock_ns=node.get_clock().now().nanoseconds,input_class=status['input_class'],B4_physics_qualification=status['B4_physics_qualification'])
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
 assert abs(pos.x+.9)<1e-3 and abs(pos.y-.15)<1e-3
 # Read the physically bound source neighborhood only as qualification; not fed to PMFS.
 probe=GasPosition.Request();probe.x=[-3.2];probe.y=[-3.3];probe.z=[-.5];pconc=call(gas,probe)
 assert all(math.isfinite(v) and v>=0 for v in pconc.positions[0].concentration)
 assert sum(pconc.positions[0].concentration)>0,'No valid generated gas response at release neighborhood'
 parameter_dumps=[]
 for n in ['gaden_player','PioneerP3DX/PID','PioneerP3DX/Anemometer','basic_sim']:
  parameter_dumps.append(dump_parameters(node,'/'+n,R/('preflight_'+n.replace('/','_')+'_parameters.yaml')))
 # All qualification claims are refreshed AFTER the parameter-service work.
 end=time.monotonic()+3
 while time.monotonic()<end:
  rclpy.spin_once(node,timeout_sec=.01)
  pid=latest['/PioneerP3DX/PID/Sensor_reading'];an=latest['/PioneerP3DX/Anemometer/WindSensor_reading']
  now_ros=node.get_clock().now().nanoseconds
  ages={label:(now_ros-msg.header.stamp.sec*1000000000-msg.header.stamp.nanosec)/1e9 for label,msg in [('PID',pid),('anemometer',an)]}
  clock_receipt_age=time.monotonic()-last_receipt_wall.get('/clock',0)
  if all(0<=v<1 for v in ages.values()) and clock_receipt_age<.15:break
 else:raise RuntimeError('Fresh clock/sensors not available immediately before goal '+str(ages))
 assert pid.raw_units==pid.UNITS_PPM and pid.technology==pid.TECH_PID and math.isfinite(pid.raw) and pid.raw>=0
 assert pid.header.frame_id=='PioneerP3DX_pid_frame' and an.header.frame_id=='PioneerP3DX_anemometer_frame'
 pre.update(raw_backends_ready_before_proxy_exposure=status['raw_backends_ready_before_proxy_exposure'],proxy_exposed_ROS_ns=status['proxy_exposed_ROS_ns'],parameter_dumps=parameter_dumps,freshness_checked_after_parameter_dumps=True,clock_receipt_wall_age_s=clock_receipt_age,sim_clock_ns=now_ros)
 pre.update(message_age_sim_seconds=ages,PID_units='ppm',PID_model=30,PID_response='sum ppm; correction_factors=false from pinned code/default; resolved dump saved',probe_source_neighborhood_ppm=list(pconc.positions[0].concentration),probe_is_input_to_algorithm=False,gas_frame_binding='physical_clock_trace.csv',sensor_frames=[pid.header.frame_id,an.header.frame_id],native_goal_count=0)
 (R/'PREFLIGHT.json').write_text(json.dumps(pre,indent=2));status['preflight']='PASS';save_status()
 # Preflight does not trigger a candidate update. One and only one real GSL goal.
 (T/'RUN_STARTED.json').write_text(json.dumps(dict(wall_time=time.time(),guard_start_monotonic=time.monotonic(),ROS_ns=node.get_clock().now().nanoseconds,native_goal_count=1,input_class=status['input_class'],maxSearchTime=300.,max_goal_wall_s=345)))
 status['goal_invocation_ROS_ns']=node.get_clock().now().nanoseconds;goal_guard_started_wall=time.monotonic();status['guard_started_monotonic']=goal_guard_started_wall;status['native_goal_count']=1;goal=DoGSL.Goal();goal.gsl_method='PMFS';sent=action.send_goal_async(goal)
 end=time.time()+10
 while not sent.done() and time.time()<end:rclpy.spin_once(node,timeout_sec=.1)
 if not sent.done() or not sent.result().accepted:raise RuntimeError('GSL goal not accepted')
 handle=sent.result();result=handle.get_result_async();starttime=time.time();status['goal_accepted']=True
 guard=RuntimeGuard(goal_guard_started_wall,status['goal_invocation_ROS_ns']);guardlog=(R/'guard_events.jsonl').open('w');fault=None;last_fault_check=0
 dump_started=False;last_status=0
 while not result.done():
  rclpy.spin_once(node,timeout_sec=.05)
  now=time.monotonic()
  if now-last_fault_check>=.5:
   last_fault_check=now
   for n,p,_ in processes:
    if n in ('launch','gmrf') and p.poll() is not None:fault={'name':n,'returncode':p.poll()}
   text=(R/'launch.log').read_text(errors='replace')
   match=re.search(r'\[([^]]+)\]: process has died \[pid (\d+), exit code (-?\d+)',text)
   if match:fault={'name':match.group(1),'pid':int(match.group(2)),'returncode':int(match.group(3))}
  decision=guard.observe(now,node.get_clock().now().nanoseconds,result_done=result.done(),process_fault=fault)
  guardlog.write(json.dumps(dict(monotonic_wall=now,wall_elapsed=now-goal_guard_started_wall,ROS_ns=node.get_clock().now().nanoseconds,result_done=result.done(),process_fault=fault,decision=decision,unqualified_clock_warnings=guard.unqualified_clock_warnings))+'\n');guardlog.flush()
  if decision['action']=='RESULT':break
  if decision['action']=='STOP':
   # Same-thread final future check prevents cancelling a result already received.
   if result.done():break
   status.update(resource_stop_reason=decision['reason'],guard_stop_ROS_ns=node.get_clock().now().nanoseconds,cancellation_requested=True)
   cancel=handle.cancel_goal_async();drain_until=time.monotonic()+2
   while not result.done() and time.monotonic()<drain_until:rclpy.spin_once(node,timeout_sec=.05)
   if result.done():
    raw=result.result();status['action_result_after_guard_cancel']={'action_status':int(raw.status),'success':bool(raw.result.success)}
   status['cancel_response_received']=cancel.done()
   raise RuntimeError('Independent external safety guard: '+decision['reason'])
  if time.time()-last_status>5:save_status();last_status=time.time()
  if not dump_started and 'INITIALIZATON COMPLETED' in (R/'launch.log').read_text(errors='replace'):
   status['native_initialization_observed_ROS_ns']=node.get_clock().now().nanoseconds;status['native_initialization_observed_monotonic']=time.monotonic()
   start('parameter_dump',['python3',str(T/'parameter_capture.py')]);dump_started=True
 guardlog.close()
 if not result.done():raise RuntimeError('Guard loop ended without a native future')
 else:
  q=result.result();status.update(result='NATIVE_ACTION_RETURNED',action_status=int(q.status),localization_success=bool(q.result.success),wall_seconds=time.time()-starttime,goal_wall_elapsed_monotonic=time.monotonic()-goal_guard_started_wall,official_result_received_ROS_ns=node.get_clock().now().nanoseconds,external_cancel_requested=False)
except Exception as e:
 status.update(result='RUNTIME_ERROR',error=str(e),traceback=traceback.format_exc())
finally:
 save_status();stop_all();wire.close();service_log.close();(R/'robot_path.json').write_text(json.dumps(pose_path));save_status();(T/'RUN_RESULT.json').write_text(json.dumps(status,indent=2));node.destroy_node();rclpy.shutdown()
