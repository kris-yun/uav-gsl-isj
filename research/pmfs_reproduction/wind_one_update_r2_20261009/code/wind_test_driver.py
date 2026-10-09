"""Bounded real ROS/DDS/TF fixtures; never launches navigation or gas generation."""
import os,json,math,time,subprocess,signal,hashlib,base64
from pathlib import Path
import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import QoSProfile,DurabilityPolicy,ReliabilityPolicy
from rclpy.serialization import serialize_message
from olfaction_msgs.msg import Anemometer
from nav_msgs.msg import OccupancyGrid
from geometry_msgs.msg import TransformStamped
from tf2_msgs.msg import TFMessage
from tf2_ros import TransformBroadcaster
from gmrf_msgs.srv import WindEstimation
from rosgraph_msgs.msg import Clock

TASK=Path(__file__).resolve().parent.parent
RESULTS=TASK/'results';RESULTS.mkdir(exist_ok=True)
pmfs_trace=RESULTS/'pmfs_consumer.csv';gmrf_trace=RESULTS/'gmrf_consumer.csv'
assert not pmfs_trace.exists() and not gmrf_trace.exists(), 'Do not overwrite a frozen run'
env=dict(os.environ,ROS_DOMAIN_ID='73',ROS_LOCALHOST_ONLY='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',PMFS_R2_TRACE=str(pmfs_trace),GMRF_R2_TRACE=str(gmrf_trace))
os.environ.update(env)
contract=dict(positions=[[1.25,1.25],[-1.75,2.25]],yaws=[0,math.pi/2],wind_vectors=[[1,0],[0,1],[-1,0],[0,-1],[0,0]],angle_tolerance_rad=1e-4,position_tolerance_m=0.01,clock_tolerance_s=2,
    grid=dict(origin=[-5,-5],resolution=.5,width=20,height=20),sensor_noise=0,domain=73,
    N1_clock='publisher, PMFS and GMRF use_sim_time=false; physical system-clock message stamps',
    N0_scope='controlled unadapted FROM-message interface probe, NOT complete original official launch',
    negative_controls=['map frame with no sensor position','mixed clock publisher true/consumers false','stale message stamp with newer moving sensor TF'],P1b_requires_P1a=True)
(RESULTS/'PRE_RUN_CONTRACT.json').write_text(json.dumps(contract,indent=2))
def start(name,args):
    log=(RESULTS/(name+'.log')).open('w')
    p=subprocess.Popen(args,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    return p,log
def stop(pair):
    p,log=pair
    if p.poll() is None:
        os.killpg(p.pid,signal.SIGINT)
        try:p.wait(timeout=5)
        except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=5)
    log.close()
def wrap(a):return math.atan2(math.sin(a),math.cos(a))
def count(p):return len(p.read_text().splitlines()) if p.exists() else 0
rclpy.init()
node=Node('r2_physical_wind_fixture')
sensor_clock=Node('r2_sim_clock_negative_fixture',parameter_overrides=[Parameter('use_sim_time',value=True)])
echo=(RESULTS/'ROS_WIRE_MESSAGES.jsonl').open('w')
def record(topic,msg):
    echo.write(json.dumps(dict(topic=topic,receipt_system_ns=node.get_clock().now().nanoseconds,type=type(msg).__name__,cdr_base64=base64.b64encode(serialize_message(msg)).decode()))+'\n');echo.flush()
subscriptions=[node.create_subscription(Anemometer,t,lambda m,t=t:record(t,m),20) for t in ['/r2/pmfs_to','/r2/gmrf_from']]
subscriptions.append(node.create_subscription(TFMessage,'/tf',lambda m:record('/tf',m),50))
tf=TransformBroadcaster(node)
to=node.create_publisher(Anemometer,'/r2/pmfs_to',10);frm=node.create_publisher(Anemometer,'/r2/gmrf_from',10)
qos=QoSProfile(depth=1,durability=DurabilityPolicy.TRANSIENT_LOCAL,reliability=ReliabilityPolicy.RELIABLE)
map_pub=node.create_publisher(OccupancyGrid,'/r2/map',qos);clock_pub=node.create_publisher(Clock,'/clock',10)
grid=OccupancyGrid();grid.header.frame_id='map';grid.info.resolution=.5;grid.info.width=20;grid.info.height=20;grid.info.origin.position.x=-5.;grid.info.origin.position.y=-5.;grid.info.origin.orientation.w=1.;grid.data=[0]*400
map_pub.publish(grid)
def spin(seconds):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        rclpy.spin_once(node,timeout_sec=.02);rclpy.spin_once(sensor_clock,timeout_sec=0.)
def transform(frame,x,y,yaw,stamp):
    t=TransformStamped();t.header.frame_id='map';t.child_frame_id=frame;t.header.stamp=stamp
    t.transform.translation.x=float(x);t.transform.translation.y=float(y);t.transform.translation.z=.5
    t.transform.rotation.z=math.sin(yaw/2);t.transform.rotation.w=math.cos(yaw/2);tf.sendTransform(t)
def publish(pub,frame,stamp,speed,angle):
    m=Anemometer();m.header.frame_id=frame;m.header.stamp=stamp;m.wind_speed=float(speed);m.wind_direction=float(angle);pub.publish(m)
def wait_lines(before,timeout=5):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        spin(.05)
        if count(pmfs_trace)>before[0] and count(gmrf_trace)>before[1]:return True
    return False
pmfs=start('pmfs_wind_probe',[str(TASK/'pmfs_wind_probe'),'--ros-args','-p','use_sim_time:=false'])
cases=[]
gmrf=None
try:
    spin(.6)
    fixtures=[]
    for pos_i,(x,y) in enumerate(contract['positions']):
        for wind_i,(u,v) in enumerate(contract['wind_vectors']):
            fixtures.append(dict(id=f'N1_P{pos_i}_W{wind_i}',kind='N1',x=x,y=y,yaw=contract['yaws'][pos_i],u=u,v=v))
    fixtures += [dict(id='NEG_MAP_FRAME',kind='NEG_MAP_FRAME',x=1.25,y=1.25,yaw=0,u=1,v=0),
                 dict(id='N0_FROM_SHARED',kind='N0_FROM_SHARED',x=1.25,y=1.25,yaw=0,u=1,v=0),
                 dict(id='NEG_MIXED_CLOCK',kind='NEG_MIXED_CLOCK',x=1.25,y=1.25,yaw=0,u=1,v=0),
                 dict(id='DIAG_DELAYED_TF',kind='DIAG_DELAYED_TF',x=1.25,y=1.25,yaw=0,u=1,v=0)]
    for fixture in fixtures:
        gmrf=start('gmrf_'+fixture['id'],[str(TASK/'gmrf_wind_observed'),'--ros-args','-p','sensor_topic:=/r2/gmrf_from','-p','map_topic:=/r2/map','-p','use_sim_time:=false','-p','cell_size:=0.5','-p','exec_freq:=20.0','-p','visualize_gmrf:=false'])
        deadline=time.monotonic()+6
        while time.monotonic()<deadline:
            spin(.1)
            if frm.get_subscription_count()>=2:break
        grid.header.stamp=node.get_clock().now().to_msg();map_pub.publish(grid);spin(.3)
        x,y,yaw=fixture['x'],fixture['y'],fixture['yaw'];frame='sensor_'+fixture['id']
        stamp=node.get_clock().now().to_msg()
        if fixture['kind']=='NEG_MIXED_CLOCK':
            clock=Clock();clock.clock.sec=100;clock_pub.publish(clock);spin(.2);stamp=sensor_clock.get_clock().now().to_msg()
            fixture['publisher_use_sim_time']=True
        else:fixture['publisher_use_sim_time']=False
        transform(frame,x,y,yaw,stamp);spin(.2)
        if fixture['kind']=='DIAG_DELAYED_TF':
            transform(frame,-1.75,2.25,math.pi/2,node.get_clock().now().to_msg());spin(.2)
            fixture['newer_TF']=[-1.75,2.25,math.pi/2]
        u,v=fixture['u'],fixture['v'];speed=math.hypot(u,v);angle=math.atan2(v,u)
        to_angle=wrap(angle-yaw);from_angle=wrap(angle+math.pi-yaw)
        if fixture['kind']=='N0_FROM_SHARED':to_angle=from_angle
        if fixture['kind']=='NEG_MAP_FRAME':frame='map';to_angle=angle;from_angle=wrap(angle+math.pi)
        before=(count(pmfs_trace),count(gmrf_trace))
        publish(to,frame,stamp,speed,to_angle);publish(frm,frame,stamp,speed,from_angle)
        fixture.update(frame=frame,stamp_sec=stamp.sec,stamp_nanosec=stamp.nanosec,pmfs_published_angle=to_angle,gmrf_published_angle=from_angle,
            pmfs_use_sim_time=False,gmrf_use_sim_time=False,transport_received=wait_lines(before))
        if fixture['transport_received']:
            fixture['pmfs_consumer_fields']=pmfs_trace.read_text().splitlines()[-1].split(',')
            fixture['gmrf_consumer_fields']=gmrf_trace.read_text().splitlines()[-1].split(',')
            client=node.create_client(WindEstimation,'WindEstimation')
            if client.wait_for_service(timeout_sec=2):
                req=WindEstimation.Request();req.x=[float(x)];req.y=[float(y)];future=client.call_async(req);end=time.monotonic()+3
                while time.monotonic()<end and not future.done():spin(.05)
                if future.done() and future.result():
                    res=future.result();fixture['estimated_wind_at_sensor']=dict(u=list(res.u),v=list(res.v),var_u=list(res.var_u),var_v=list(res.var_v),cov_uv=list(res.cov_uv),map_width=res.map_width)
            node.destroy_client(client)
        cases.append(fixture);(RESULTS/'WIND_CASES_RAW.json').write_text(json.dumps(cases,indent=2,allow_nan=True))
        stop(gmrf);gmrf=None;spin(.1)
finally:
    if gmrf:stop(gmrf)
    stop(pmfs);echo.close();node.destroy_node();sensor_clock.destroy_node();rclpy.shutdown()
(RESULTS/'RUN_COMPLETE.json').write_text(json.dumps(dict(cases=len(cases),completed=True,native_navigation=False,gas_generation=False)))
print('Completed',len(cases),'real ROS wind/TF fixtures')
