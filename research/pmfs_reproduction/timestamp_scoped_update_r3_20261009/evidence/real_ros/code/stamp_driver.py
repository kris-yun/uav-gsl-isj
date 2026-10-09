import os,json,math,time,subprocess,signal,base64
from pathlib import Path
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile,DurabilityPolicy,ReliabilityPolicy
from rclpy.serialization import serialize_message
from rclpy.time import Time
from olfaction_msgs.msg import Anemometer
from nav_msgs.msg import OccupancyGrid
from geometry_msgs.msg import TransformStamped
from tf2_msgs.msg import TFMessage
from tf2_ros import TransformBroadcaster,Buffer,TransformListener
from gmrf_msgs.srv import WindEstimation

TASK=Path(__file__).resolve().parent.parent;RESULTS=TASK/'results/stamp';RESULTS.mkdir(exist_ok=True)
assert not (RESULTS/'CASES.json').exists()
env=dict(os.environ,ROS_DOMAIN_ID='74',ROS_LOCALHOST_ONLY='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
os.environ.update(env)
(RESULTS/'PRE_RUN_CONTRACT.json').write_text(json.dumps(dict(angle_tolerance_rad=1e-4,position_tolerance_m=.01,age_limit_s=2,clock='all system/ROS use_sim_time=false',
    fixed_pose_drift_xy_limit=.01,fixed_pose_drift_yaw_limit=1e-4,domain=74,cases=['fresh0','fresh90','fresh33_nonorigin','delayed_rotate90','delayed_stable'],no_seed_change=True),indent=2))
def start(name,args,extra):
    log=(RESULTS/(name+'.log')).open('w');p=subprocess.Popen(args,env=dict(env,**extra),stdout=log,stderr=subprocess.STDOUT,start_new_session=True);return p,log
def stop(pair):
    p,log=pair
    if p.poll() is None:
        os.killpg(p.pid,signal.SIGINT)
        try:p.wait(timeout=5)
        except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=5)
    log.close()
def wrap(a):return math.atan2(math.sin(a),math.cos(a))
def lines(p):return p.read_text().splitlines() if p.exists() else []
rclpy.init();node=Node('r3_stamp_fixture');tf=TransformBroadcaster(node);buf=Buffer();listener=TransformListener(buf,node)
wire=(RESULTS/'ROS_MESSAGES_CDR.jsonl').open('w')
def record(topic,msg):wire.write(json.dumps(dict(topic=topic,receipt_ns=node.get_clock().now().nanoseconds,type=type(msg).__name__,cdr_base64=base64.b64encode(serialize_message(msg)).decode()))+'\n');wire.flush()
subs=[node.create_subscription(Anemometer,t,lambda m,t=t:record(t,m),20) for t in ['/r3/pmfs_to','/r3/gmrf_from']]
subs.append(node.create_subscription(TFMessage,'/tf',lambda m:record('/tf',m),100))
to=node.create_publisher(Anemometer,'/r3/pmfs_to',10);frm=node.create_publisher(Anemometer,'/r3/gmrf_from',10)
map_pub=node.create_publisher(OccupancyGrid,'/r3/map',QoSProfile(depth=1,durability=DurabilityPolicy.TRANSIENT_LOCAL,reliability=ReliabilityPolicy.RELIABLE))
grid=OccupancyGrid();grid.header.frame_id='map';grid.info.resolution=.5;grid.info.width=20;grid.info.height=20;grid.info.origin.position.x=-5.;grid.info.origin.position.y=-5.;grid.info.origin.orientation.w=1.;grid.data=[0]*400;map_pub.publish(grid)
current=None
def send_tf(stamp=None):
    if current is None:return
    frame,x,y,yaw=current;t=TransformStamped();t.header.frame_id='map';t.child_frame_id=frame;t.header.stamp=stamp or node.get_clock().now().to_msg()
    t.transform.translation.x=x;t.transform.translation.y=y;t.transform.translation.z=.5;t.transform.rotation.z=math.sin(yaw/2);t.transform.rotation.w=math.cos(yaw/2);tf.sendTransform(t)
def spin(seconds):
    end=time.monotonic()+seconds
    while time.monotonic()<end:send_tf();rclpy.spin_once(node,timeout_sec=.02)
def pose_at(frame,ns):
    t=buf.lookup_transform('map',frame,Time(nanoseconds=ns));q=t.transform.rotation
    yaw=math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))
    return dict(stamp_ns=t.header.stamp.sec*10**9+t.header.stamp.nanosec,x=t.transform.translation.x,y=t.transform.translation.y,yaw=yaw)
n0trace=RESULTS/'N0_original.csv';n1trace=RESULTS/'N1_stamped.csv';gtrace=RESULTS/'GMRF.csv'
p0=start('N0_original',[str(TASK/'pmfs_original'),'--ros-args','-r','__node:=r3_original','-p','anemometer_topic:=/r3/pmfs_to','-p','use_sim_time:=false'],dict(PMFS_R2_TRACE=str(n0trace)))
p1=start('N1_stamped',[str(TASK/'pmfs_stamped'),'--ros-args','-r','__node:=r3_stamped','-p','anemometer_topic:=/r3/pmfs_to','-p','use_sim_time:=false'],dict(PMFS_R2_TRACE=str(n1trace)))
fixtures=[dict(id='fresh0',x=1.25,y=1.25,yaw=0,u=1,v=0),dict(id='fresh90',x=-1.75,y=2.25,yaw=math.pi/2,u=0,v=1),dict(id='fresh33_nonorigin',x=-.75,y=.25,yaw=.5759586531581288,u=-1,v=0),dict(id='delayed_rotate90',x=1.25,y=1.25,yaw=0,u=1,v=0),dict(id='delayed_stable',x=-1.75,y=2.25,yaw=math.pi/2,u=0,v=-1)]
cases=[];gmrf=None
try:
    spin(.5)
    for f in fixtures:
        gmrf=start('GMRF_'+f['id'],['/home/zyc/pmfs_wind_one_update_r2_20261009/gmrf_wind_observed','--ros-args','-p','sensor_topic:=/r3/gmrf_from','-p','map_topic:=/r3/map','-p','use_sim_time:=false','-p','cell_size:=0.5','-p','exec_freq:=20.0','-p','visualize_gmrf:=false'],dict(GMRF_R2_TRACE=str(gtrace)))
        current=('r3_sensor_'+f['id'],float(f['x']),float(f['y']),float(f['yaw']))
        end=time.monotonic()+6
        while time.monotonic()<end:
            spin(.1)
            if to.get_subscription_count()>=3 and frm.get_subscription_count()>=2:break
        map_pub.publish(grid);spin(.3)
        stamp=node.get_clock().now().to_msg();stamp_ns=stamp.sec*10**9+stamp.nanosec;send_tf(stamp);spin(.2)
        if f['id']=='delayed_rotate90':current=(current[0],-1.75,2.25,math.pi/2);spin(.3)
        if f['id']=='delayed_stable':spin(.3)
        theta=math.atan2(f['v'],f['u']);speed=math.hypot(f['u'],f['v']);before=[len(lines(p)) for p in [n0trace,n1trace,gtrace]]
        m=Anemometer();m.header.frame_id=current[0];m.header.stamp=stamp;m.wind_speed=speed;m.wind_direction=wrap(theta-f['yaw']);to.publish(m)
        m2=Anemometer();m2.header=m.header;m2.wind_speed=speed;m2.wind_direction=wrap(theta+math.pi-f['yaw']);frm.publish(m2)
        end=time.monotonic()+5
        while time.monotonic()<end:
            spin(.05)
            if all(len(lines(p))>n for p,n in zip([n0trace,n1trace,gtrace],before)):break
        f.update(stamp_ns=stamp_ns,frame=current[0],publisher_use_sim_time=node.get_parameter('use_sim_time').value,N0=lines(n0trace)[-1].split(','),N1=lines(n1trace)[-1].split(','),GMRF=lines(gtrace)[-1].split(','))
        spin(.1)
        sample=pose_at(current[0],stamp_ns);f['TF_at_sample']=sample
        for variant,idx in [('N0',13),('N1',13),('GMRF',10)]:
            consume=pose_at(current[0],int(f[variant][idx]));f['TF_at_'+variant+'_consume']=consume
            f[variant+'_pose_drift_xy_m']=math.hypot(consume['x']-sample['x'],consume['y']-sample['y'])
            f[variant+'_pose_drift_yaw_rad']=abs(wrap(consume['yaw']-sample['yaw']))
        cases.append(f);(RESULTS/'CASES.json').write_text(json.dumps(cases,indent=2))
        stop(gmrf);gmrf=None
finally:
    if gmrf:stop(gmrf)
    stop(p0);stop(p1);wire.close();node.destroy_node();rclpy.shutdown()
(RESULTS/'COMPLETE.json').write_text(json.dumps(dict(cases=len(cases),complete=True)))
print('R3-A real ROS completed',len(cases),'paired cases')
