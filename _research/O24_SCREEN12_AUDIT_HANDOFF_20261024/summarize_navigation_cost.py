from pathlib import Path
import csv,json,math,zipfile
R=Path(__file__).resolve().parent
def summarize():
 records=json.loads((R/'BATCH_LEDGER.json').read_text());rows=[]
 for item in records:
  C=Path(item['archive']['source_case']);q=item['QA']
  def read(name):
   p=C/name
   if p.exists():return p.read_bytes()
   with zipfile.ZipFile(item['archive']['archive'])as z:
    try:return z.read(name)
    except KeyError:return None
  b=read('runtime/launch.log');log=b.decode(errors='replace')if b else''
  lines=[x for x in log.splitlines()if'bt_navigator]:'in x]
  b=read('runtime/robot_path.json');path=json.loads(b)if b else[]
  distance=sum(math.hypot(y[1]-x[1],y[2]-x[2])for x,y in zip(path,path[1:]))if isinstance(path,list)else None
  b=read('EXECUTION_COMPLETE.json');cost=json.loads(b)if b else{}
  b=read('RUN_RESULT.json');result=json.loads(b)if b else{}
  b=read('runtime/physical_clock_trace.csv');clock=list(csv.DictReader(b.decode().splitlines()))if b else[]
  start=result.get('goal_invocation_ROS_ns')
  observed_elapsed=(int(clock[-1]['receipt_ros_ns'])-start)/1e9 if clock and start is not None else None
  rows.append(dict(role=item['role'],case=q['case'],run_class=q['qualification'],
   bt_success_log_events=sum('Goal succeeded'in x for x in lines),
   bt_failed_log_events=sum('Goal failed'in x for x in lines),
   bt_cancel_log_events=sum('Goal was canceled'in x or'Goal canceled'in x for x in lines),
   nav_event_scope='Exact bt_navigator terminal log strings; not inferred from controller recovery attempts',
   pose_samples=len(path),sampled_path_length_xy_m=distance,
   consumed_windows=q.get('consumed_windows'),positive_windows=q.get('positive_windows'),
   source_updates=q.get('source_updates'),candidate_maps=q.get('candidate_maps'),
   goal_search_physical_s=q.get('search_physical_s'),goal_search_wall_s=q.get('search_wall_s'),
   observed_search_elapsed_to_last_service_ros_s=observed_elapsed,
   observed_elapsed_scope='Recorded ROS timestamp of last physical-query service minus actual goal invocation. Available for censored runs; separate from native declaration time.',
   whole_attempt_wall_s=cost.get('wall_s'),whole_attempt_child_CPU_s=cost.get('child_CPU_s'),
   declared=q.get('official_success'),source_domain=q.get('source_domain_class')))
 with(R/'NAVIGATION_AND_COST_SUMMARY.csv').open('w',newline='',encoding='utf-8-sig')as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 return rows
if __name__=='__main__':print(json.dumps(summarize(),indent=2))
