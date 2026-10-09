import os,json,csv,math,time,subprocess,signal,hashlib,base64
from pathlib import Path
import rclpy
from rclpy.node import Node
from rclpy.time import Time
from rclpy.qos import QoSProfile,DurabilityPolicy,ReliabilityPolicy
from rclpy.serialization import serialize_message
from geometry_msgs.msg import TransformStamped,PoseWithCovarianceStamped
from olfaction_msgs.msg import GasSensor,Anemometer
from nav_msgs.msg import OccupancyGrid
from tf2_msgs.msg import TFMessage
from tf2_ros import TransformBroadcaster,Buffer,TransformListener
from std_msgs.msg import String

TASK=Path(__file__).resolve().parent.parent
PARAM=json.loads((TASK/'input/PARAMETERS.json').read_text())
RESULTS=TASK/'driver';RESULTS.mkdir(exist_ok=True)
assert not (TASK/'native/NATIVE_COMPLETE.json').exists()
os.environ.update(ROS_DOMAIN_ID='75',ROS_LOCALHOST_ONLY='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
env=dict(os.environ)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def start(name,args,extra={}):
    f=(RESULTS/(name+'.log')).open('w');p=subprocess.Popen(args,env=dict(env,**extra),stdout=f,stderr=subprocess.STDOUT,start_new_session=True);return p,f
def stop(pair):
    p,f=pair
    if p.poll() is None:
        os.killpg(p.pid,signal.SIGINT)
        try:p.wait(timeout=5)
        except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=5)
    f.close()
def csvrows(p):
    if not p.exists():return []
    with p.open() as f:return list(csv.DictReader(f))

rclpy.init();node=Node('r4_fresh_fixture');broadcaster=TransformBroadcaster(node);buffer=Buffer();listener=TransformListener(buffer,node)
wire=(RESULTS/'ROS_WIRE_CDR.jsonl').open('w');record_tf=True
def record(topic,msg):
    if topic=='/tf' and not record_tf:return
    wire.write(json.dumps(dict(topic=topic,receipt_ns=node.get_clock().now().nanoseconds,type=type(msg).__name__,cdr_base64=base64.b64encode(serialize_message(msg)).decode()))+'\n');wire.flush()
subs=[node.create_subscription(t,topic,lambda m,topic=topic:record(topic,m),100) for t,topic in [(GasSensor,'/r4/gas'),(Anemometer,'/r4/pmfs_to'),(Anemometer,'/r4/gmrf_from'),(PoseWithCovarianceStamped,'/r4/pose'),(TFMessage,'/tf')]]
gas=node.create_publisher(GasSensor,'/r4/gas',20);to=node.create_publisher(Anemometer,'/r4/pmfs_to',20);frm=node.create_publisher(Anemometer,'/r4/gmrf_from',20);pose=node.create_publisher(PoseWithCovarianceStamped,'/r4/pose',20);trigger=node.create_publisher(String,'/r4/trigger',10)
map_pub=node.create_publisher(OccupancyGrid,'/r4/map',QoSProfile(depth=1,durability=DurabilityPolicy.TRANSIENT_LOCAL,reliability=ReliabilityPolicy.RELIABLE))
maprows=csvrows(TASK/'input/occupancy.csv');m=maprows[0];grid=OccupancyGrid();grid.header.frame_id='map';grid.info.width=int(m['grid_width']);grid.info.height=int(m['grid_height']);grid.info.resolution=float(m['cell_size']);grid.info.origin.position.x=float(m['origin_x']);grid.info.origin.position.y=float(m['origin_y']);grid.info.origin.orientation.w=1.;grid.data=[0 if r['occupancy']=='Free' else 100 for r in maprows]
def tf(stamp=None):
    t=TransformStamped();t.header.frame_id='map';t.header.stamp=stamp or node.get_clock().now().to_msg();t.child_frame_id='r4_sensor';t.transform.translation.x=PARAM['robot_x'];t.transform.translation.y=PARAM['robot_y'];t.transform.translation.z=PARAM['sensor_z'];t.transform.rotation.z=math.sin(PARAM['sensor_yaw']/2);t.transform.rotation.w=math.cos(PARAM['sensor_yaw']/2);broadcaster.sendTransform(t)
def spin(seconds,send_tf=True):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        if send_tf:tf()
        rclpy.spin_once(node,timeout_sec=.02)
def wait(predicate,timeout,reason):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        spin(.05)
        if native and native[0].poll() is not None:raise RuntimeError('native exited before completion: '+reason)
        if predicate():return
    raise RuntimeError(reason)
def pose_at(ns):
    t=buffer.lookup_transform('map','r4_sensor',Time(nanoseconds=ns));q=t.transform.rotation;yaw=math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z));return dict(stamp_ns=t.header.stamp.sec*10**9+t.header.stamp.nanosec,x=t.transform.translation.x,y=t.transform.translation.y,z=t.transform.translation.z,yaw=yaw)
native=gmrf=None;status={'run_id':PARAM['run_id'],'input_class':PARAM['input_class'],'native_successful_updates':0,'preflight_schema_corrections':2,'pretrigger_input_validation_corrections':2,'environment_crash_retries':0}
try:
    build=json.loads((TASK/'ENTRY_BUILD_RESULT.json').read_text());assert build['verdict']=='PASS'
    native=start('native',[str(TASK/'native_capture'),str(TASK/'input'),str(TASK/'native'),'--ros-args','-p','use_sim_time:=false'])
    gmrf=start('gmrf',['/home/zyc/pmfs_wind_one_update_r2_20261009/gmrf_wind_observed','--ros-args','-p','sensor_topic:=/r4/gmrf_from','-p','map_topic:=/r4/map','-p','use_sim_time:=false','-p','cell_size:='+m['cell_size'],'-p','exec_freq:=20.0','-p','visualize_gmrf:=false'],dict(GMRF_R2_TRACE=str(RESULTS/'GMRF_consumed.csv')))
    map_pub.publish(grid)
    wait(lambda:(TASK/'native/READY_SCHEMA.json').exists(),30,'capture schema not ready')
    schema=json.loads((TASK/'native/READY_SCHEMA.json').read_text());assert schema['pid']==native[0].pid and schema['coarse_leaves']>=2 and schema['grid_cells']==1102 and schema['threads']==1
    tree=csvrows(TASK/'native/coarse_tree.csv');assert len(tree)==schema['coarse_leaves']
    cover=[0]*1102
    for leaf in tree:
        assert leaf['value']=='1' and leaf['parent_id']=='ROOT' and leaf['has_children']=='0'
        for j in range(int(leaf['origin_j']),int(leaf['origin_j'])+int(leaf['size_j'])):
            for i in range(int(leaf['origin_i']),int(leaf['origin_i'])+int(leaf['size_i'])):
                assert 0<=i<29 and 0<=j<38;cover[i+j*29]+=1
    assert all(c==(1 if r['occupancy']=='Free' else 0) for c,r in zip(cover,maprows))
    required=['leaf_samples','rng_engine','gaussian_cache','unblurred_hit_map','blurred_hit_map','raw_score','local_refinement_tree','normalization','final_posterior'];assert schema['native_update_hooks']==required
    required_header=['serial','candidate_id','origin_i','origin_j','size_i','size_j','rng_before','rng_after','gaussian_ready_before','gaussian_index_before','gaussian_index_after','point_count','score','logscore','map_file','points_file']
    assert (TASK/'native/candidates.csv').read_text().splitlines()[0].split(',')==required_header
    assert (TASK/'native/raw_consumed_messages.csv').read_text().splitlines()[0].split(',')==['kind','message_id','block_id','stamp_ns','frame_id','receipt_ns','raw','raw_units','ppm','speed','local_direction','map_TO_direction','returned_TF_stamp_ns','sample_TF_stamp_ns','sample_x','sample_y','sample_yaw','consumer_latest_TF_stamp_ns','consumer_x','consumer_y','consumer_yaw','pose_drift_xy_m','pose_drift_yaw_rad']
    pre=dict(schema=schema,source_class='real native PID/ELF',ELF_SHA256=build['ELF_SHA256'],input_SHA256={p.name:sha(p) for p in (TASK/'input').iterdir()},candidate_schema_fields=required_header,all_sinks_open=True,tolerances=PARAM['tolerances'],raw_policy='exactly three gas and three wind messages per StopAndMeasure block; no temporal resampling',source_truth_used=False,preflight_ns=node.get_clock().now().nanoseconds)
    (RESULTS/'PRE_RUN_SCHEMA_VALIDATION.json').write_text(json.dumps(pre,indent=2))
    map_pub.publish(grid)
    wait(lambda:gas.get_subscription_count()>=2 and to.get_subscription_count()>=2 and frm.get_subscription_count()>=2 and pose.get_subscription_count()>=2 and trigger.get_subscription_count()>=1,30,'ROS subscriptions not discovered')
    spin(.2)
    p=PoseWithCovarianceStamped();p.header.frame_id='map';p.header.stamp=node.get_clock().now().to_msg();p.pose.pose.position.x=PARAM['robot_x'];p.pose.pose.position.y=PARAM['robot_y'];p.pose.pose.position.z=PARAM['sensor_z'];p.pose.pose.orientation.w=1.;pose.publish(p);spin(.15)
    u,v=PARAM['measured_wind_u'],PARAM['measured_wind_v'];speed=math.hypot(u,v);theta=math.atan2(v,u)
    for block,values in enumerate(PARAM['blocks'],1):
        for value in values:
            stamp=node.get_clock().now().to_msg();tf(stamp);spin(.1)
            g=GasSensor();g.header.frame_id='r4_sensor';g.header.stamp=stamp;g.technology=g.TECH_PID;g.manufacturer=g.MANU_UNKNOWN;g.mpn=g.MPN_UNKNOWN;g.raw=float(value);g.raw_units=g.UNITS_PPM;gas.publish(g)
            w=Anemometer();w.header=g.header;w.sensor_label='SYNTHETIC_FIXTURE';w.wind_speed=speed;w.wind_direction=math.atan2(math.sin(theta-PARAM['sensor_yaw']),math.cos(theta-PARAM['sensor_yaw']));to.publish(w)
            f=Anemometer();f.header=g.header;f.sensor_label='SYNTHETIC_FIXTURE';f.wind_speed=speed;f.wind_direction=math.atan2(math.sin(theta+math.pi-PARAM['sensor_yaw']),math.cos(theta+math.pi-PARAM['sensor_yaw']));frm.publish(f);spin(.12)
        wait(lambda:len(csvrows(TASK/'native/measurement_events.csv'))>=block,15,'StopAndMeasure block not processed')
    spin(.2)
    raw=csvrows(TASK/'native/raw_consumed_messages.csv');assert len(raw)==18
    tftrace=[]
    for r in raw:
        assert all(value!='' for value in r.values())
        s=pose_at(int(r['stamp_ns']));c=pose_at(int(r['receipt_ns']));drift=math.hypot(c['x']-s['x'],c['y']-s['y']);dyaw=abs(math.atan2(math.sin(c['yaw']-s['yaw']),math.cos(c['yaw']-s['yaw'])))
        assert drift<PARAM['tolerances']['position_m'] and dyaw<PARAM['tolerances']['angle_rad'];assert 0<=(int(r['receipt_ns'])-int(r['stamp_ns']))/1e9<PARAM['tolerances']['message_age_s']
        tftrace.append(dict(kind=r['kind'],message_id=r['message_id'],block_id=r['block_id'],sample=s,receipt=c,drift_xy_m=drift,drift_yaw_rad=dyaw))
    (RESULTS/'TF_AT_SAMPLE_AND_RECEIPT.json').write_text(json.dumps(tftrace,indent=2))
    glines=(RESULTS/'GMRF_consumed.csv').read_text().splitlines();assert len(glines)==9
    for number,line in enumerate(glines,1):
        r=line.split(',');assert int(r[8])==1 and int(r[9])==1 and int(r[11])==0 and int(r[12])==number
        assert math.hypot(float(r[6])-PARAM['robot_x'],float(r[7])-PARAM['robot_y'])<.01
        assert math.hypot(float(r[14])-float(r[6]),float(r[15])-float(r[7]))<=float(m['cell_size'])/math.sqrt(2)+1e-6
        assert abs(math.atan2(math.sin(float(r[5])-theta),math.cos(float(r[5])-theta)))<1e-4
    (RESULTS/'INPUT_READY_TO_TRIGGER.json').write_text(json.dumps(dict(raw_members=18,blocks=3,TF_records=18,GMRF_members=9,schema_and_new_inputs='PASS',trigger_ns=node.get_clock().now().nanoseconds),indent=2))
    trigger.publish(String(data='RUN_P1B_NATIVE_CAPTURE_R4'));spin(.15);record_tf=False
    end=time.monotonic()+900
    while time.monotonic()<end:
        rclpy.spin_once(node,timeout_sec=.1)
        if (TASK/'native/NATIVE_COMPLETE.json').exists():break
        if native[0].poll() is not None:raise RuntimeError('native process exited during source update')
    else:raise RuntimeError('native source update exceeded 900 seconds')
    complete=json.loads((TASK/'native/NATIVE_COMPLETE.json').read_text());assert complete['native_source_updates']==1
    native[0].wait(timeout=10);assert native[0].returncode==0
    status.update(native_successful_updates=1,native_PID=native[0].pid,native_capture_complete=complete)
    stop(gmrf);gmrf=None
    for name in ['offline_forward','offline_control']:
        q=start(name,[str(TASK/name),str(TASK/'input'),str(TASK/'native'),str(TASK/(name+'_result'))])
        try:q[0].wait(timeout=900)
        except subprocess.TimeoutExpired:stop(q);raise RuntimeError(name+' exceeded 900 seconds')
        q[1].close()
        if q[0].returncode:raise RuntimeError(name+' actual replay failed')
    status['execution']='COMPLETE_NATIVE_FORWARD_AND_CLEAN_CONTROL'
except Exception as e:
    status['execution']='ERROR';status['error']=repr(e);raise
finally:
    if gmrf:stop(gmrf)
    if native:stop(native)
    wire.close();node.destroy_node();rclpy.shutdown();(RESULTS/'DRIVER_RESULT.json').write_text(json.dumps(status,indent=2))
print(json.dumps(status))
