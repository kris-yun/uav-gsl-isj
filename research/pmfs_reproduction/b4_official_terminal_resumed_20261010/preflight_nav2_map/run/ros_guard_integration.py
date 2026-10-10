"""Actual ROS clock + parameter-service regression. No GSL or gas simulation."""
import sys
sys.dont_write_bytecode=True
import os,time,json,subprocess,signal,hashlib
from pathlib import Path
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile,ReliabilityPolicy
from rosgraph_msgs.msg import Clock
from runtime_guard_policy import RuntimeGuard
from guard_ros_io import dump_parameters
P=Path(__file__).resolve().parent/'integration';P.mkdir(exist_ok=True)
assert not (P/'ROS_INTEGRATION_RESULT.json').exists()
fixture=r'''import rclpy,time
from pathlib import Path
from rclpy.node import Node
from rosgraph_msgs.msg import Clock
rclpy.init();n=Node('guard_fixture_parameters');n.declare_parameter('fixture_only',True)
p=n.create_publisher(Clock,'/clock',1000);start=time.monotonic()
def tick():
 mode=Path(__file__).resolve().parent.joinpath('phase').read_text().strip()
 if mode=='STOP':return
 elapsed=(time.monotonic()-start)*5+100
 if mode=='FORWARD':elapsed+=200
 if mode=='BACKWARD':elapsed-=20
 m=Clock();m.clock.sec=int(elapsed);m.clock.nanosec=int((elapsed-int(elapsed))*1e9);p.publish(m)
n.create_timer(.02,tick)
try:rclpy.spin(n)
finally:n.destroy_node();rclpy.shutdown()
'''
(P/'fixture.py').write_text(fixture);(P/'phase').write_text('NORMAL')
f=(P/'publisher.stdout').open('w');e=(P/'publisher.stderr').open('w')
p=subprocess.Popen(['python3',str(P/'fixture.py')],stdout=f,stderr=e,start_new_session=True)
rclpy.init();n=Node('guard_integration_client',parameter_overrides=[rclpy.parameter.Parameter('use_sim_time',value=True)])
clocks=[];events=[];cases=[]
def clock(m):clocks.append(dict(wall=time.monotonic(),ROS_ns=m.clock.sec*10**9+m.clock.nanosec))
sub=n.create_subscription(Clock,'/clock',clock,QoSProfile(depth=1000,reliability=ReliabilityPolicy.BEST_EFFORT))
def spin(duration):
 end=time.monotonic()+duration
 while time.monotonic()<end:rclpy.spin_once(n,timeout_sec=.01)
def case(name,**extra):cases.append(dict(name=name,verdict='PASS',**extra))
try:
 spin(1.5);assert len(clocks)>10
 dumps=[]
 for i in range(4):dumps.append(dump_parameters(n,'/guard_fixture_parameters',P/f'param_{i}.yaml'))
 assert all(d['returncode']==0 and d['executor_spin_calls']>0 and d['ROS_after_ns']>d['ROS_before_ns'] for d in dumps)
 assert all('fixture_only: true' in (P/f'param_{i}.yaml').read_text() for i in range(4))
 case('four_direct_ROS_parameter_reads_keep_executor_live',dumps=dumps)
 # Deliberately stop the CLIENT executor; the publisher continues steadily.
 init=n.get_clock().now().nanoseconds;before=time.monotonic();g=RuntimeGuard(before,init)
 time.sleep(3);receipt_before=len(clocks);spin(.3);now=time.monotonic();ros=n.get_clock().now().nanoseconds
 # Apply the problematic first-poll interval from attempt 2 to a real captured catchup.
 decision=g.observe(before+.194343643,ros)
 assert decision['action']=='WAIT' and g.unqualified_clock_warnings
 fresh=clocks[receipt_before:];deltas=[(b['ROS_ns']-a['ROS_ns'])/1e9 for a,b in zip(clocks,clocks[1:])]
 assert (ros-init)/1e9>10 and max(deltas)<.5 and min(deltas)>0
 case('actual_client_backlog_is_not_publisher_jump',client_catchup_s=(ros-init)/1e9,publisher_adjacent_max_s=max(deltas),decision=decision,warnings=g.unqualified_clock_warnings,queued_messages_drained=len(fresh))
 # Live forward/backward publisher events remain auditable warnings until qualified.
 for phase in ['FORWARD','BACKWARD','NORMAL']:
  old=n.get_clock().now().nanoseconds;g=RuntimeGuard(time.monotonic(),old)
  (P/'phase').write_text(phase);spin(.15)
  d=g.observe(time.monotonic(),n.get_clock().now().nanoseconds)
  assert d['action']=='WAIT'
  events.append(dict(phase=phase,decision=d,warnings=g.unqualified_clock_warnings))
 case('live_clock_steps_logged_without_confusing_client_sampling_with_source_evidence',events=events)
 # True clock halt still invokes the independent monotonic safety guard.
 (P/'phase').write_text('STOP');spin(.2);g=RuntimeGuard(time.monotonic(),n.get_clock().now().nanoseconds)
 stop_end=time.monotonic()+16;decisions=[]
 while time.monotonic()<stop_end:
  rclpy.spin_once(n,timeout_sec=.05)
  d=g.observe(time.monotonic(),n.get_clock().now().nanoseconds);decisions.append(d)
  if d['action']=='STOP':break
 assert decisions[-1]=={'action':'STOP','reason':'ROS_CLOCK_STALLED'}
 case('actual_ROS_clock_halt_is_bounded',last_decision=decisions[-1],wall_elapsed_s=time.monotonic()-g.started_wall)
 result=dict(verdict='PASS_ACTUAL_ROS_INTEGRATION_NO_GSL_GOAL',cases=cases,GSL_processes_started=0,GSL_goals_sent=0,gas_generation=0,ROS_DOMAIN_ID=int(os.environ['ROS_DOMAIN_ID']),policy_sha256=hashlib.sha256(Path(__file__).with_name('runtime_guard_policy.py').read_bytes()).hexdigest(),IO_helper_sha256=hashlib.sha256(Path(__file__).with_name('guard_ros_io.py').read_bytes()).hexdigest())
except Exception as ex:
 import traceback
 result=dict(verdict='FAIL_ACTUAL_ROS_INTEGRATION',error=str(ex),traceback=traceback.format_exc(),cases=cases,GSL_goals_sent=0)
finally:
 n.destroy_node();rclpy.shutdown();os.killpg(p.pid,signal.SIGINT);p.wait(timeout=5);f.close();e.close()
 (P/'clock_receipts.json').write_text(json.dumps(clocks));(P/'ROS_INTEGRATION_RESULT.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
assert result['verdict'].startswith('PASS'),result
