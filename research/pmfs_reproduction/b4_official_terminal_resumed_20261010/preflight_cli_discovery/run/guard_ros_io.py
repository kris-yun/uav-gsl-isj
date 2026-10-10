"""External-client I/O only. Keep the same executor servicing clock and sensors."""
import time,subprocess,json
import rclpy
def dump_parameters(node,target,output_path,timeout=12):
 start=time.monotonic();before=node.get_clock().now().nanoseconds;spins=0
 with output_path.open('w') as f:
  proc=subprocess.Popen(['ros2','param','dump',target],stdout=f,stderr=f)
  try:
   while proc.poll() is None and time.monotonic()-start<timeout:
    rclpy.spin_once(node,timeout_sec=.02);spins+=1
   if proc.poll() is None:raise RuntimeError('Parameter dump deadline '+target)
   if proc.returncode!=0:raise RuntimeError('Parameter dump failed '+target+' '+output_path.read_text()[-600:])
  finally:
   if proc.poll() is None:proc.terminate();proc.wait(timeout=2)
 # Flush already ready callbacks before accepting a clock or sensor freshness claim.
 flush=time.monotonic()+.15
 while time.monotonic()<flush:rclpy.spin_once(node,timeout_sec=.01);spins+=1
 return dict(target=target,returncode=proc.returncode,wall_seconds=time.monotonic()-start,executor_spin_calls=spins,ROS_before_ns=before,ROS_after_ns=node.get_clock().now().nanoseconds)
