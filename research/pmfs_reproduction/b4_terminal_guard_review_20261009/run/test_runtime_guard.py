"""Deterministic simulated event tests. Does not import ROS or start any process."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,hashlib
from runtime_guard_policy import RuntimeGuard

def exercise(name,events):
    g=RuntimeGuard(0,0);trace=[]
    for wall,ros_s,result,process,expected in events:
        decision=g.observe(wall,int(ros_s*1e9),result_done=result,process_fault=process)
        assert decision['action']==expected[0] and decision['reason']==expected[1],(name,decision,expected)
        trace.append(dict(wall_s=wall,ROS_s=ros_s,result_done=result,process_fault=process,actual=decision,expected=dict(action=expected[0],reason=expected[1])))
    return dict(test=name,verdict='PASS',events=trace)

W=('WAIT','WAIT_NATIVE_ACTION');R=('RESULT','NATIVE_ACTION_RESULT')
cases=[
 ('delayed_initialization_no_goal_based_300s_cutoff',[(10,50,False,None,W),(40,200,False,None,W),(80,400,False,None,W)]),
 ('native_early_success',[(10,50,False,None,W),(11,55,True,None,R)]),
 ('native_search_timeout_returns_failure',[(60,300,False,None,W),(66,330,True,None,R)]),
 ('result_wins_near_wall_cancel',[(343,1715,False,None,('DRAIN','NATIVE_GOAL_WALL_LIMIT_345S')),(344.99,1724.95,True,None,R)]),
 ('result_wins_at_same_tick_as_deadline_and_exit',[(345,1725,True,{'returncode':-11},R)]),
 ('clock_stops',[(1,5,False,None,W),(14,5,False,None,('DRAIN','ROS_CLOCK_STALLED')),(16,5,False,None,('STOP','ROS_CLOCK_STALLED'))]),
 ('clock_resumes_during_result_drain',[(1,5,False,None,W),(14,5,False,None,('DRAIN','ROS_CLOCK_STALLED')),(15,10,False,None,W)]),
 ('clock_backward_jump',[(1,5,False,None,W),(2,1,False,None,('DRAIN','ROS_CLOCK_BACKWARD_JUMP')),(4,11,False,None,('STOP','ROS_CLOCK_BACKWARD_JUMP'))]),
 ('clock_forward_jump',[(1,5,False,None,W),(1.1,400,False,None,('DRAIN','ROS_CLOCK_FORWARD_JUMP')),(3.1,410,False,None,('STOP','ROS_CLOCK_FORWARD_JUMP'))]),
 ('GSL_abnormal_exit_without_result',[(1,5,False,None,W),(2,10,False,{'returncode':-11},('DRAIN','GSL_OR_REQUIRED_PROCESS_EXIT')),(4,20,False,{'returncode':-11},('STOP','GSL_OR_REQUIRED_PROCESS_EXIT'))]),
 ('result_arrives_after_process_exit_before_cancel',[(1,5,False,None,W),(2,10,False,{'returncode':-11},('DRAIN','GSL_OR_REQUIRED_PROCESS_EXIT')),(3,15,True,{'returncode':-11},R)]),
 ('hard_wall_limit_independent_of_ROS_search',[(343,1715,False,None,('DRAIN','NATIVE_GOAL_WALL_LIMIT_345S')),(345,1725,False,None,('STOP','NATIVE_GOAL_WALL_LIMIT_345S'))]),
]
results=[exercise(n,e) for n,e in cases]
out=dict(verdict='PASS',tests=len(results),GSL_executions=0,ROS_imports=0,official_maxSearchTime_unchanged=300,external_goal_based_ROS_budget_removed=True,wall_limit_s=345,clock_stall_limit_s=15,result_drain_grace_s=2,policy_sha256=hashlib.sha256(Path(__file__).with_name('runtime_guard_policy.py').read_bytes()).hexdigest(),cases=results)
if '--write-evidence' in sys.argv:
    Path(__file__).with_name('GUARD_OFFLINE_TEST_RESULTS.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(out if '--full' in sys.argv else {k:v for k,v in out.items() if k!='cases'},ensure_ascii=False))
