"""Deserialize only a frozen past local-wind/TF/clock projection, without ROS launch."""
from pathlib import Path
import csv,gzip,json,math,time,hashlib,resource
from rclpy.serialization import deserialize_message
from olfaction_msgs.msg import Anemometer
from tf2_msgs.msg import TFMessage
from rosgraph_msgs.msg import Clock
from rclpy.time import Time
from rclpy.duration import Duration
from tf2_ros import Buffer

ROOT=Path('/mnt/hgfs/workspace/PMFS_C1B_LOCAL_INITIAL_STATE_AUDIT_20261011')
def ns(t):return int(t.sec)*10**9+int(t.nanosec)
def frame_ok(f):
    f=f.lstrip('/')
    if any(t in f.lower() for t in ['source','plume','emitter','filament']):return False
    return f in ['map','odom','world','base_link','base_footprint'] or f.startswith('PioneerP3DX')

def main():
    started=time.monotonic();resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
    scope=json.loads((ROOT/'C1B_INPUT_SCOPE_FREEZE.json').read_text())
    cutoff=scope['cutoff_receipt_ROS_ns']
    clock_meta=json.loads((ROOT/'C1B_ALLOWED_HISTORY_AND_CLOCK.json').read_text())
    anchor=clock_meta['ROS_player_anchor_ns'];t500=clock_meta['frame500_physical_s']
    buffer=Buffer(cache_time=Duration(seconds=1000))
    wind=[];tf_count=0;tf_bad=0;clock_count=0;last_clock=None;clock_back=0;future_stamp=0;tf_frames=set()
    sanitized=(ROOT/'C1B_SANITIZED_PAST_INPUTS.jsonl.gz')
    with gzip.open(ROOT/'allowed_prefix_transport.jsonl.gz','rt',encoding='utf8') as f,gzip.open(sanitized,'wt',encoding='utf8') as out:
        for line in f:
            o=json.loads(line);receipt=int(o['receipt_ns']);assert receipt<=cutoff
            topic=o['topic'];raw=bytes.fromhex(o['cdr_hex'])
            if topic in ['/tf','/tf_static']:
                msg=deserialize_message(raw,TFMessage)
                for tr in msg.transforms:
                    if not frame_ok(tr.header.frame_id) or not frame_ok(tr.child_frame_id):tf_bad+=1;continue
                    ts=ns(tr.header.stamp)
                    if ts>receipt or ts>cutoff:future_stamp+=1;continue
                    if topic=='/tf_static':buffer.set_transform_static(tr,'archived_prefix')
                    else:buffer.set_transform(tr,'archived_prefix')
                    tf_count+=1;tf_frames.update([tr.header.frame_id,tr.child_frame_id])
                    out.write(json.dumps({'kind':topic,'receipt_ns':receipt,'stamp_ns':ts,'parent':tr.header.frame_id,'child':tr.child_frame_id,'translation':[tr.transform.translation.x,tr.transform.translation.y,tr.transform.translation.z],'rotation':[tr.transform.rotation.x,tr.transform.rotation.y,tr.transform.rotation.z,tr.transform.rotation.w]})+'\n')
            elif topic=='/clock':
                c=deserialize_message(raw,Clock);v=ns(c.clock);clock_count+=1
                if last_clock is not None and v<last_clock:clock_back+=1
                last_clock=v
                out.write(json.dumps({'kind':'clock','receipt_ns':receipt,'clock_ns':v})+'\n')
            elif topic.endswith('WindSensor_reading'):
                m=deserialize_message(raw,Anemometer);ts=ns(m.header.stamp)
                if ts>receipt or ts>cutoff:future_stamp+=1;continue
                if not frame_ok(m.header.frame_id):continue
                r={'receipt_ns':receipt,'stamp_ns':ts,'frame':m.header.frame_id,'speed_m_s':float(m.wind_speed),'FROM_rad_sensor':float(m.wind_direction),'TF_at_message_stamp':'NOT_AVAILABLE_AT_RECEIPT'}
                # Respect received TF prefix; never ask a later TF to explain an earlier input.
                try:
                    tr=buffer.lookup_transform('map',m.header.frame_id,Time.from_msg(m.header.stamp))
                    q=tr.transform.rotation
                    yaw=math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))
                    phi=float(m.wind_direction)+math.pi+yaw
                    r.update(TF_at_message_stamp='PASS_RECEIPT_PREFIX',TO_rad_map=math.atan2(math.sin(phi),math.cos(phi)),map_xyz=[tr.transform.translation.x,tr.transform.translation.y,tr.transform.translation.z])
                except Exception as e:r['TF_error_class']=type(e).__name__
                r['physical_stamp_s']=t500+(ts-anchor)/1e9 if ts>=anchor else None
                r['physical_epoch_bound']=ts>=anchor
                wind.append(r);out.write(json.dumps({'kind':'local_wind',**r})+'\n')
            else:
                # Adapted wind is a duplicate of the raw event; do not count a second observation.
                assert topic=='/b4/wind_to'
    # Delayed TF that arrived before the initialization cutoff may legitimately
    # explain a past wind. It must be distinguished from availability at receipt.
    for r in wind:
        try:
            tr=buffer.lookup_transform('map',r['frame'],Time(nanoseconds=r['stamp_ns']))
            q=tr.transform.rotation;yaw=math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))
            phi=r['FROM_rad_sensor']+math.pi+yaw
            r.update(TF_at_initialization_cutoff='PASS_PAST_STAMP',cutoff_TO_rad_map=math.atan2(math.sin(phi),math.cos(phi)),cutoff_map_xyz=[tr.transform.translation.x,tr.transform.translation.y,tr.transform.translation.z])
        except Exception as e:r.update(TF_at_initialization_cutoff='UNAVAILABLE',cutoff_TF_error_class=type(e).__name__)
    with (ROOT/'C1B_PAST_LOCAL_WIND.csv').open('w',encoding='utf8',newline='') as f:
        cols=['receipt_ns','stamp_ns','frame','speed_m_s','FROM_rad_sensor','TF_at_message_stamp','TO_rad_map','map_xyz','TF_error_class','physical_stamp_s','physical_epoch_bound','TF_at_initialization_cutoff','cutoff_TO_rad_map','cutoff_map_xyz','cutoff_TF_error_class']
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(wind)
    bound=[r for r in wind if r['physical_epoch_bound']]
    ready=[r for r in bound if r['TF_at_message_stamp']=='PASS_RECEIPT_PREFIX']
    stamps=[r['stamp_ns'] for r in wind]
    out={'cutoff_receipt_ns':cutoff,'wind_rows':len(wind),'wind_frame_names':sorted(set(r['frame'] for r in wind)),'first_wind_stamp_ns':min(stamps),'last_wind_stamp_ns':max(stamps),'bound_wind_rows':len(bound),'bound_with_causal_TF_rows':len(ready),'bound_with_TF_at_cutoff_rows':sum(r['TF_at_initialization_cutoff']=='PASS_PAST_STAMP' for r in bound),'first_bound_physical_s':min(r['physical_stamp_s'] for r in bound),'last_bound_physical_s':max(r['physical_stamp_s'] for r in bound),'first_ready_physical_s':min((r['physical_stamp_s'] for r in ready),default=None),'TF_transforms':tf_count,'TF_frames':sorted(tf_frames),'TF_excluded_frames':tf_bad,'future_stamps_rejected':future_stamp,'clock_messages':clock_count,'clock_backward_steps':clock_back,'maximum_wind_receipt_age_s':max((r['receipt_ns']-r['stamp_ns'])/1e9 for r in wind),'no_gas_deserialized':True,'no_future_wind_deserialized':True,'no_CFD_read':True,'ROS_nodes_started':0,'physics_calls':0,'active_wall_s':time.monotonic()-started,'max_RSS_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'sanitized_sha256':hashlib.sha256(sanitized.read_bytes()).hexdigest(),'sanitized_bytes':sanitized.stat().st_size}
    (ROOT/'C1B_PAST_DECODE_RECEIPT.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out))

if __name__=='__main__':main()
