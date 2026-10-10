"""Offline observer backlog regression and qualified-clock fault tests. No ROS."""
import sys
sys.dont_write_bytecode=True
import json,hashlib
from pathlib import Path
from runtime_guard_policy import RuntimeGuard
out=[]
def case(name,events):
 g=RuntimeGuard(0,55801567090);trace=[]
 for wall,ros,done,process,confirmed,expected in events:
  decision=g.observe(wall,int(ros*1e9),result_done=done,process_fault=process,confirmed_clock_discontinuity=confirmed)
  assert decision['action']==expected[0] and decision['reason']==expected[1],(name,decision,expected)
  trace.append(dict(wall_s=wall,ROS_s=ros,result_done=done,process_fault=process,confirmed_clock_discontinuity=confirmed,decision=decision))
 out.append(dict(test=name,verdict='PASS',events=trace))
W=('WAIT','WAIT_NATIVE_ACTION');R=('RESULT','NATIVE_ACTION_RESULT')
case('actual_recorded_first_guard_tick_is_client_catchup',[(.194343643,96.301331410,False,None,None,W),(2.19528411,106.301982515,False,None,None,W)])
case('long_initialization_does_not_spend_external_ROS_search_budget',[(80,455.8,False,None,None,W),(100,555.8,False,None,None,W)])
case('native_early_success',[(2,65,True,None,None,R)])
case('native_search_timeout_returned_failure',[(70,405.8,True,None,None,R)])
case('native_result_wins_at_same_time_as_clock_and_process_fault',[(345,1800,True,{'returncode':-11},'ROS_CLOCK_FORWARD_JUMP',R)])
case('near_cancel_result_arrives_during_drain',[(343,1770,False,None,None,('DRAIN','NATIVE_GOAL_WALL_LIMIT_345S')),(344.99,1780,True,None,None,R)])
case('hard_wall_deadline',[(343,1770,False,None,None,('DRAIN','NATIVE_GOAL_WALL_LIMIT_345S')),(345,1780,False,None,None,('STOP','NATIVE_GOAL_WALL_LIMIT_345S'))])
case('client_clock_stall',[(13,55.80156709,False,None,None,('DRAIN','ROS_CLOCK_STALLED')),(15,55.80156709,False,None,None,('STOP','ROS_CLOCK_STALLED'))])
case('client_clock_resumes',[(13,55.80156709,False,None,None,('DRAIN','ROS_CLOCK_STALLED')),(14,60.8,False,None,None,W)])
case('unqualified_backward_message_step_is_logged',[(1,50,False,None,None,W),(2,55,False,None,None,W)])
case('qualified_actual_publisher_backward_jump',[(1,50,False,None,'ROS_CLOCK_BACKWARD_JUMP',('DRAIN','ROS_CLOCK_BACKWARD_JUMP')),(3,55,False,None,None,('STOP','ROS_CLOCK_BACKWARD_JUMP'))])
case('qualified_actual_publisher_forward_jump',[(1,400,False,None,'ROS_CLOCK_FORWARD_JUMP',('DRAIN','ROS_CLOCK_FORWARD_JUMP')),(3,410,False,None,None,('STOP','ROS_CLOCK_FORWARD_JUMP'))])
case('GSL_exit_without_result',[(1,60,False,{'returncode':-11},None,('DRAIN','GSL_OR_REQUIRED_PROCESS_EXIT')),(3,70,False,{'returncode':-11},None,('STOP','GSL_OR_REQUIRED_PROCESS_EXIT'))])
case('late_native_result_after_process_exit',[(1,60,False,{'returncode':-11},None,('DRAIN','GSL_OR_REQUIRED_PROCESS_EXIT')),(2,65,True,{'returncode':-11},None,R)])
result=dict(verdict='PASS_OFFLINE_PROPOSAL_ONLY',tests=len(out),GSL_executions=0,applied_to_replacement_goal=False,third_goal_count=0,requires_qualified_publisher_evidence_for_jump_cancellation=True,policy_sha256=hashlib.sha256(Path(__file__).with_name('runtime_guard_policy.py').read_bytes()).hexdigest(),cases=out)
if '--write-evidence' in sys.argv:Path(__file__).with_name('PROPOSED_GUARD_TEST_RESULTS.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='cases'}))
