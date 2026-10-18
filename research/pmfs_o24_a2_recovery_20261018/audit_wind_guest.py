from pathlib import Path
import bisect,csv,gzip,json,math,statistics
from rclpy.serialization import deserialize_message
from olfaction_msgs.msg import Anemometer
from tf2_msgs.msg import TFMessage
from gaden_msgs.srv import WindPosition
R=Path(__file__).resolve().parent;out=R/'analysis'
def wrap(a):return math.atan2(math.sin(a),math.cos(a))
def mul(a,b):
 x,y,z,w=a;X,Y,Z,W=b
 return (w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,w*Z+x*Y-y*X+z*W,w*W-x*X-y*Y-z*Z)
def yaw(q):x,y,z,w=q;return math.atan2(2*(w*z+x*y),1-2*(y*y+z*z))
def qmsg(q):return (q.x,q.y,q.z,q.w)
def stamp(s):return s.sec*10**9+s.nanosec
def quant(a):a=sorted(a);return dict(n=len(a),median=a[len(a)//2],max=a[-1],mean=statistics.mean(a))if a else dict(n=0)
allrows=[]
for role in sorted(p.name for p in (R/'cases').iterdir()if (p/'RUN_RESULT.json').exists()):
 d=R/'cases'/role/'runtime';raw={};converted={};static={};dynamic={};frames={}
 with gzip.open(d/'raw_ros_cdr.jsonl.gz','rt')as f:
  for line in f:
   a=json.loads(line);topic=a['topic']
   if topic in ['/PioneerP3DX/Anemometer/WindSensor_reading','/native20/wind_to']:
    m=deserialize_message(bytes.fromhex(a['cdr_hex']),Anemometer);key=stamp(m.header.stamp);(raw if topic.startswith('/Pioneer')else converted).setdefault(key,[]).append(m);frames[key]=m.header.frame_id
   elif topic in ['/tf','/tf_static']:
    m=deserialize_message(bytes.fromhex(a['cdr_hex']),TFMessage)
    for t in m.transforms:
     row=(stamp(t.header.stamp),t.header.frame_id,qmsg(t.transform.rotation))
     if topic=='/tf_static':static[t.child_frame_id]=row
     else:dynamic.setdefault(t.child_frame_id,[]).append(row)
 for key,a in dynamic.items():a.sort(key=lambda x:x[0])
 def transform(child,t,depth=0):
  assert depth<12
  if child=='map':return (0.,0.,0.,1.)
  if child in static:e=static[child]
  else:
   a=dynamic[child];i=bisect.bisect_right(a,t,key=lambda r:r[0])-1;e=a[max(0,i)]
  return mul(transform(e[1],t,depth+1),e[2])
 pair=[]
 for t,aa in raw.items():
  if t not in converted:continue
  for a,b in zip(aa,converted[t]):pair.append(abs(wrap(float(b.wind_direction)-float(a.wind_direction)-math.pi)))
 assert len(pair)>.95*sum(len(a)for a in raw.values())and max(pair)<3e-7
 accepted=list(csv.DictReader((d/'GMRF_consumed.csv').open()));errors=[];details=[];zero_vectors=0
 for a in accepted:
  t=int(a['message_stamp_ns']);receipt=int(a['receipt_ros_ns'])
  if t not in raw:continue
  matches=[m for m in raw[t]if float(m.wind_speed)==float(a['speed'])]
  assert matches,('SAVED_GMRF_WIND_MESSAGE_NOT_MATCHED',role,t,float(a['speed']),[float(m.wind_speed)for m in raw[t]])
  m=matches[0];half=.5*float(m.wind_direction);local=(0.,0.,math.sin(half),math.cos(half))
  if float(a['speed'])==0:
   # Explicit author branch: zero speed sets direction0. Its angle is not evidence of a direction-transform error.
   assert float(a['downwind_map_rad'])==0;zero_vectors+=1;continue
  assert abs(float(a['speed'])-float(m.wind_speed))<1e-12
  # Native GMRF asks TF for its latest available transform, not the logging receipt time.
  # Search the observed message-to-callback interval plus one recorded TF predecessor.
  # This establishes consistency with saved TF; it does not recover the exact transform owner.
  times={t,receipt}
  for seq in dynamic.values():
   ts=[r[0]for r in seq];lo=max(0,bisect.bisect_right(ts,t)-1);hi=bisect.bisect_right(ts,receipt)
   times.update(ts[lo:hi])
  e=[]
  for candidate_time in times:
   globalq=mul(transform(m.header.frame_id,candidate_time),local)
   expected=wrap(yaw(globalq)+3.14159);e.append(abs(wrap(float(a['downwind_map_rad'])-expected)))
  errors.append(min(e));details.append(dict(role=role,message_stamp_ns=t,min_TF_timing_bracket_angle_error_rad=min(e),speed=float(a['speed'])))
 wind_values=[];cardinalities=[]
 with (d/'service_queries.jsonl').open()as f:
  for line in f:
   a=json.loads(line)
   if a['kind']=='WindPosition':
    msg=deserialize_message(bytes.fromhex(a['response_cdr_hex']),WindPosition.Response)
    cardinalities.append(len(a['x']));wind_values.extend(math.hypot(u,v)for u,v in zip(msg.u,msg.v))
 assert wind_values and max(wind_values)>1e-5
 result=dict(role=role,sensor_messages=sum(len(a)for a in raw.values()),duplicate_header_stamps=sum(len(a)-1 for a in raw.values()),paired_downwind_adapter=quant(pair),GMRF_accepted_callbacks=len(accepted),GMRF_nonzero_callbacks_with_saved_sensor=len(errors),GMRF_zero_vector_direction0=zero_vectors,GMRF_transform_min_bracket_error=quant(errors),GMRF_callbacks_above_0p2rad=sum(e>.2 for e in errors),TF_check='Observed message-to-callback interval plus one TF predecessor; consistency, not proof of exact TF owner',world_true_wind_query_cardinalities=sorted(set(cardinalities)),world_sensor_wind_magnitude_min=min(wind_values),world_sensor_wind_magnitude_max=max(wind_values),world_sensor_wind_zero_fraction=sum(v<1e-12 for v in wind_values)/len(wind_values),baseline_built_without_GADEN_truth_wind_support=True)
 allrows.append(result)
 with (out/(role+'_WIND_TRANSFORM_LATEST_TF.csv')).open('w',newline='')as f:
  if details:w=csv.DictWriter(f,fieldnames=list(details[0]));w.writeheader();w.writerows(details)
(out/'WIND_SEMANTICS_AUDIT.json').write_text(json.dumps(dict(status='SAVED_MESSAGE_AND_TF_DIAGNOSTIC_COMPLETE',rows=allrows),indent=2))
print(json.dumps(allrows),flush=True)
