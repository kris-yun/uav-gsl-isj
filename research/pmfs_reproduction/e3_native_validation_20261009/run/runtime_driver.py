from pathlib import Path
import os,json,time,subprocess,signal,math,copy,traceback
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

T=Path('/home/zyc/pmfs_e3_native_validation_20261009');R=T/'runtime';R.mkdir(exist_ok=True)
assert not (T/'RUN_STARTED.json').exists()
os.environ.update(ROS_DOMAIN_ID='76',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',PMFS_R5_CAPTURE=str(R/'updates'),PMFS_R5_CONSUMERS=str(R/'consumer_messages.csv'),PMFS_R5_EVENTS=str(R/'measurement_events.csv'),PMFS_R5_PLAYER=str(R/'player_frames.csv'))
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

status=dict(input_class='ONE_E3_OFFICIAL_PARAMETERS_N1_ENGINEERING_ALIGNMENT',E3_physics_qualification='PASS_SOURCE_GEOMETRY_WIND_TIME_SIDECAR_N1',native_goal_count=0,fixture_messages_injected=0,generated_gas_data=0,processes=[])
wire=(R/'raw_ros_cdr.jsonl').open('w');counts={};latest={};pose_path=[];cmd_nonzero=0
def record(topic,msg):
 counts[topic]=counts.get(topic,0)+1;latest[topic]=msg
 # Full raw messages retained; no reduction.
 keep=True
 if keep:wire.write(json.dumps(dict(topic=topic,receipt_ns=node.get_clock().now().nanoseconds,cdr_hex=serialize_message(msg).hex()))+'\n');wire.flush()

rclpy.init();node=Node('e3_capture_and_wind_adapter',parameter_overrides=[rclpy.parameter.Parameter('use_sim_time',value=True)])
buffer=Buffer();listener=TransformListener(buffer,node)
to=node.create_publisher(Anemometer,'/e3/wind_to',20)
def wind(m):
 record('/PioneerP3DX/Anemometer/WindSensor_reading',m);n=copy.deepcopy(m);n.wind_direction=math.atan2(math.sin(m.wind_direction+math.pi),math.cos(m.wind_direction+math.pi));to.publish(n);record('/e3/wind_to',n)
def pose(m):
 record('/PioneerP3DX/ground_truth',m);p=m.pose.pose.position;pose_path.append([m.header.stamp.sec+m.header.stamp.nanosec/1e9,p.x,p.y,p.z])
def cmd(m):
 global cmd_nonzero
 record('/PioneerP3DX/cmd_vel',m);cmd_nonzero+=abs(m.linear.x)+abs(m.angular.z)>1e-5
subs=[node.create_subscription(Anemometer,'/PioneerP3DX/Anemometer/WindSensor_reading',wind,100),node.create_subscription(GasSensor,'/PioneerP3DX/PID/Sensor_reading',lambda m:record('/PioneerP3DX/PID/Sensor_reading',m),100),node.create_subscription(PoseWithCovarianceStamped,'/PioneerP3DX/ground_truth',pose,100),node.create_subscription(Twist,'/PioneerP3DX/cmd_vel',cmd,100),node.create_subscription(TFMessage,'/tf',lambda m:record('/tf',m),100),node.create_subscription(Clock,'/clock',lambda m:record('/clock',m),QoSProfile(depth=100,reliability=ReliabilityPolicy.BEST_EFFORT)),node.create_subscription(TFMessage,'/tf_static',lambda m:record('/tf_static',m),QoSProfile(depth=100,durability=DurabilityPolicy.TRANSIENT_LOCAL)),node.create_subscription(OccupancyGrid,'/PioneerP3DX/map',lambda m:record('/PioneerP3DX/map',m),QoSProfile(depth=1,durability=DurabilityPolicy.TRANSIENT_LOCAL))]
service_group=ReentrantCallbackGroup()
raw_gas=node.create_client(GasPosition,'/e3/raw_odor_value',callback_group=service_group)
raw_wind=node.create_client(WindPosition,'/e3/raw_wind_value',callback_group=service_group)
service_log=(R/'service_queries.jsonl').open('w')
service_serial=0
async def forward_query(kind,client,request,response):
 global service_serial
 serial=service_serial;service_serial+=1
 before=node.get_clock().now().nanoseconds
 request_hex=serialize_message(request).hex()
 result=await client.call_async(request)
 service_log.write(json.dumps(dict(serial=serial,kind=kind,request_ns=before,response_ns=node.get_clock().now().nanoseconds,x=list(request.x),y=list(request.y),z=list(request.z),request_cdr_hex=request_hex,response_cdr_hex=serialize_message(result).hex()))+'\n');service_log.flush()
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
def save_status():
 status.update(counts=counts,nonzero_cmd_vel_messages=int(cmd_nonzero),pose_samples=len(pose_path),processes=[dict(name=n,pid=p.pid,returncode=p.poll()) for n,p,_ in processes]);(T/'RUNTIME_STATUS.json').write_text(json.dumps(status,indent=2))
try:
 launch=start('launch',['ros2','launch',str(T/'N1_E3_launch.py'),'scenario:=E','simulation:=E3','method:=PMFS'])
 gmrf=start('gmrf',['/home/zyc/pmfs_wind_one_update_r2_20261009/gmrf_wind_observed','--ros-args','-p','use_sim_time:=true','-p','sensor_topic:=/PioneerP3DX/Anemometer/WindSensor_reading','-p','map_topic:=/PioneerP3DX/map','-p','cell_size:=0.25','-p','exec_freq:=10.0'],{'GMRF_R2_TRACE':str(R/'GMRF_consumed.csv')})
 before=time.time()
 while time.time()-before<70:
  rclpy.spin_once(node,timeout_sec=.1)
  if launch.poll() is not None:raise RuntimeError('launch exited before preflight')
  if time.time()-before>=12 and counts.get('/e3/wind_to',0)>=10 and counts.get('/PioneerP3DX/PID/Sensor_reading',0)>=10 and counts.get('/PioneerP3DX/map',0)>0 and action.server_is_ready():break
 else:raise RuntimeError('preflight missing sensor/map/action output')
 states={n:call(c,GetState.Request()).current_state.label for n,c in lifecycle.items()}
 if any(x!='active' for x in states.values()):raise RuntimeError('Nav2 lifecycle not active '+str(states))
 tf=buffer.lookup_transform('map','PioneerP3DX_anemometer_frame',rclpy.time.Time());pos=tf.transform.translation
 rq=GasPosition.Request();rq.x=[float(pos.x)];rq.y=[float(pos.y)];rq.z=[float(pos.z)];g=call(gas,rq)
 rq=WindPosition.Request();rq.x=[float(pos.x)];rq.y=[float(pos.y)];rq.z=[float(pos.z)];w=call(air,rq)
 assert all(math.isfinite(v) for v in [*w.u,*w.v,*w.w]),'nonfinite wind'
 assert len(g.positions)==1 and all(math.isfinite(v) and v>=0 for v in g.positions[0].concentration),'nonfinite gas'
 assert abs(pos.z-.5)<1e-5,'sensor elevation mismatch'
 pre=dict(lifecycle=states,sensor_xyz=[pos.x,pos.y,pos.z],gas_types=list(g.gas_type),gas_ppm=list(g.positions[0].concentration),wind_uvw=[list(w.u),list(w.v),list(w.w)],ROS_DOMAIN_ID=76,sim_clock_ns=node.get_clock().now().nanoseconds,input_class=status['input_class'],E3_physics_qualification=status['E3_physics_qualification'])
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
 assert abs(pos.x+3)<1e-3 and abs(pos.y-4.5)<1e-3
 # Read the physically bound source neighborhood only as qualification; not fed to PMFS.
 probe=GasPosition.Request();probe.x=[-4.];probe.y=[-1.9];probe.z=[.7];pconc=call(gas,probe)
 assert all(math.isfinite(v) and v>=0 for v in pconc.positions[0].concentration)
 assert sum(pconc.positions[0].concentration)>0,'No valid generated gas response at release neighborhood'
 for n in ['gaden_player','PioneerP3DX/PID','PioneerP3DX/Anemometer','basic_sim']:
  with (R/('preflight_'+n.replace('/','_')+'_parameters.yaml')).open('w') as f:
   subprocess.run(['ros2','param','dump','/'+n],stdout=f,stderr=f,timeout=8)
 pre.update(message_age_sim_seconds=ages,PID_units='ppm',PID_model=30,PID_response='sum ppm; correction_factors=false from pinned code/default; resolved dump saved',probe_source_neighborhood_ppm=list(pconc.positions[0].concentration),probe_is_input_to_algorithm=False,gas_frame_binding='physical_clock_trace.csv',sensor_frames=[pid.header.frame_id,an.header.frame_id],native_goal_count=0)
 (R/'PREFLIGHT.json').write_text(json.dumps(pre,indent=2));status['preflight']='PASS';save_status()
 # Preflight does not trigger a candidate update. One and only one real GSL goal.
 (T/'RUN_STARTED.json').write_text(json.dumps(dict(wall_time=time.time(),native_goal_count=1,input_class=status['input_class'])))
 status['native_goal_count']=1;goal=DoGSL.Goal();goal.gsl_method='PMFS';sent=action.send_goal_async(goal)
 end=time.time()+10
 while not sent.done() and time.time()<end:rclpy.spin_once(node,timeout_sec=.1)
 if not sent.done() or not sent.result().accepted:raise RuntimeError('GSL goal not accepted')
 handle=sent.result();result=handle.get_result_async();starttime=time.time();status['goal_accepted']=True
 dump_started=False;last_status=0
 while not result.done() and time.time()-starttime<345:
  rclpy.spin_once(node,timeout_sec=.05)
  if time.time()-last_status>5:save_status();last_status=time.time()
  if not dump_started and time.time()-starttime>10:
   start('parameter_dump',['bash','-lc','ros2 param dump /PioneerP3DX/GSL > '+str(R/'resolved_GSL_parameters.yaml')+'; ros2 param dump /gaden_player > '+str(R/'resolved_player_parameters.yaml')]);dump_started=True
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
 save_status();stop_all();wire.close();service_log.close();(R/'robot_path.json').write_text(json.dumps(pose_path));save_status();(T/'RUN_RESULT.json').write_text(json.dumps(status,indent=2));node.destroy_node();rclpy.shutdown()
