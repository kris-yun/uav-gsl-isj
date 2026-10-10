"""Read parameters through named ROS services while servicing the executor."""
import time,yaml
import rclpy
from rcl_interfaces.srv import ListParameters,GetParameters
def _value(v):
 field={0:None,1:'bool_value',2:'integer_value',3:'double_value',4:'string_value',5:'byte_array_value',6:'bool_array_value',7:'integer_array_value',8:'double_array_value',9:'string_array_value'}[v.type]
 if field is None:return None
 x=getattr(v,field)
 return list(x) if v.type>=5 else x
def dump_parameters(node,target,output_path,timeout=12):
 start=time.monotonic();before=node.get_clock().now().nanoseconds;spins=0
 clients=[node.create_client(ListParameters,target+'/list_parameters'),node.create_client(GetParameters,target+'/get_parameters')]
 def spin():
  nonlocal spins
  rclpy.spin_once(node,timeout_sec=.02);spins+=1
  if time.monotonic()-start>timeout:raise RuntimeError('Direct parameter service timeout '+target)
 def call(client,req):
  f=client.call_async(req)
  while not f.done():spin()
  if f.exception() is not None:raise f.exception()
  return f.result()
 try:
  while not all(c.service_is_ready() for c in clients):spin()
  q=ListParameters.Request();q.prefixes=[];q.depth=0;names=list(call(clients[0],q).result.names)
  assert names,'No resolved parameters from '+target
  q=GetParameters.Request();q.names=names;values=call(clients[1],q).values
  assert len(names)==len(values)
  params={n:_value(v) for n,v in zip(names,values)}
  output_path.write_text(yaml.safe_dump({target:{'ros__parameters':params}},sort_keys=True))
 finally:
  for c in clients:node.destroy_client(c)
 end=time.monotonic()+.1
 while time.monotonic()<end:spin()
 return dict(target=target,transport='DIRECT_NAMED_ROS_PARAMETER_SERVICES',CLI_daemon_used=False,returncode=0,parameter_count=len(params),wall_seconds=time.monotonic()-start,executor_spin_calls=spins,ROS_before_ns=before,ROS_after_ns=node.get_clock().now().nanoseconds)
