"""ROS startup regression only. Fixtures are not input to PMFS. No GSL goal."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,time,hashlib
import rclpy
from rclpy.node import Node
from rclpy.executors import SingleThreadedExecutor
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.serialization import serialize_message
from gaden_msgs.srv import GasPosition,WindPosition
from service_startup_gate import expose_if_backends_ready
P=Path(__file__).resolve().parent/'service_startup_test';P.mkdir(exist_ok=True)
rclpy.init();node=Node('service_startup_regression');group=ReentrantCallbackGroup();executor=SingleThreadedExecutor();executor.add_node(node)
rawgas=node.create_client(GasPosition,'/fixture/raw_odor',callback_group=group);rawwind=node.create_client(WindPosition,'/fixture/raw_wind',callback_group=group)
consumer=node.create_client(GasPosition,'/fixture/odor',callback_group=group)
windconsumer=node.create_client(WindPosition,'/fixture/wind',callback_group=group)
counts={'gas':0,'wind':0};backresponses={};messages=[]
def gas_backend(req,res):
 counts['gas']+=1;res.gas_type=['smoke'];backresponses['gas']=serialize_message(res).hex();return res
def wind_backend(req,res):
 counts['wind']+=1;res.u=[1.25]*len(req.x);res.v=[-.5]*len(req.x);res.w=[0.0]*len(req.x);backresponses['wind']=serialize_message(res).hex();return res
async def gas_proxy(req,res):return await rawgas.call_async(req)
async def wind_proxy(req,res):return await rawwind.call_async(req)
creators=[lambda:node.create_service(GasPosition,'/fixture/odor',gas_proxy,callback_group=group),lambda:node.create_service(WindPosition,'/fixture/wind',wind_proxy,callback_group=group)]
started=time.monotonic();before=[]
try:
 while time.monotonic()-started<.7:
  executor.spin_once(timeout_sec=.02)
  exposed=expose_if_backends_ready([rawgas,rawwind],creators);assert exposed is None
  assert not consumer.service_is_ready() and not windconsumer.service_is_ready()
  before.append(time.monotonic()-started)
 backgas=node.create_service(GasPosition,'/fixture/raw_odor',gas_backend,callback_group=group)
 # One ready backend is deliberately insufficient: no partially available proxy.
 deadline=time.monotonic()+3
 while not rawgas.service_is_ready() and time.monotonic()<deadline:executor.spin_once(timeout_sec=.02)
 assert rawgas.service_is_ready()
 assert expose_if_backends_ready([rawgas,rawwind],creators) is None
 backwind=node.create_service(WindPosition,'/fixture/raw_wind',wind_backend,callback_group=group)
 deadline=time.monotonic()+4;exposed=None
 while exposed is None and time.monotonic()<deadline:
  executor.spin_once(timeout_sec=.02);exposed=expose_if_backends_ready([rawgas,rawwind],creators)
 assert exposed is not None
 for c,typ,kind in [(consumer,GasPosition,'gas'),(windconsumer,WindPosition,'wind')]:
  deadline=time.monotonic()+4
  while not c.service_is_ready() and time.monotonic()<deadline:executor.spin_once(timeout_sec=.02)
  assert c.service_is_ready()
  req=typ.Request();req.x=[-.9];req.y=[.15];req.z=[-.2]
  future=c.call_async(req);deadline=time.monotonic()+4
  while not future.done() and time.monotonic()<deadline:executor.spin_once(timeout_sec=.02)
  assert future.done() and future.exception() is None
  cdr=serialize_message(future.result()).hex();assert cdr==backresponses[kind]
  messages.append({'kind':kind,'response_CDR_matches_backend':True,'response_cdr_hex':cdr})
 assert counts=={'gas':1,'wind':1}
 result=dict(verdict='PASS_ACTUAL_ROS_SERVICE_STARTUP_GATE',backends_initially_unavailable=True,proxy_not_exposed_before_both_ready=True,early_consumer_no_dropped_request=True,first_gas_and_wind_roundtrip_pass=True,responses_byte_exact=True,fixture_only=True,GSL_processes_started=0,GSL_goals_sent=0,gas_generation=0,gate_sha256=hashlib.sha256(Path(__file__).with_name('service_startup_gate.py').read_bytes()).hexdigest(),messages=messages,counts=counts,pre_ready_poll_count=len(before))
except Exception as e:
 import traceback
 result=dict(verdict='FAIL_ACTUAL_ROS_SERVICE_STARTUP_GATE',error=str(e),traceback=traceback.format_exc(),GSL_goals_sent=0)
finally:
 executor.remove_node(node);node.destroy_node();executor.shutdown();rclpy.shutdown()
 (P/'RESULT.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
assert result['verdict'].startswith('PASS'),result
