"""Read-only subscriber preserving the exact map seen by Native."""
import json,sys,time
from pathlib import Path
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile,DurabilityPolicy,ReliabilityPolicy
from nav_msgs.msg import OccupancyGrid
def main():
    rclpy.init();node=Node('d0_lite_readonly_map_receipt');path=Path(sys.argv[1]);received=[]
    def callback(msg):
        received.append(True);o=msg.info.origin
        path.write_text(json.dumps(dict(frame_id=msg.header.frame_id,width=msg.info.width,height=msg.info.height,
            resolution=msg.info.resolution,origin=dict(x=o.position.x,y=o.position.y,z=o.position.z),
            origin_quaternion=[o.orientation.x,o.orientation.y,o.orientation.z,o.orientation.w],
            data=list(msg.data),source='/map exact ROS message; no plume query'),sort_keys=True)+'\n')
    sub=node.create_subscription(OccupancyGrid,'/map',callback,QoSProfile(depth=1,durability=DurabilityPolicy.TRANSIENT_LOCAL,reliability=ReliabilityPolicy.RELIABLE))
    deadline=time.monotonic()+60
    while not received and time.monotonic()<deadline:rclpy.spin_once(node,timeout_sec=.1)
    node.destroy_node();rclpy.shutdown()
    if not received:raise SystemExit('D0_LITE_MAP_NOT_RECEIVED')
if __name__=='__main__':main()
