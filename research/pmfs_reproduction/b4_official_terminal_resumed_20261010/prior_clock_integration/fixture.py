import rclpy,time
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
