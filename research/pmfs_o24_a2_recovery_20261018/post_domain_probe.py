from pathlib import Path
import json,os,time
from isolation_guard import inventory,require_vacant
R=Path(__file__).resolve().parent
require_vacant(inventory(225,exclude={os.getpid()}),R/'DOMAIN_POST_GRAPH_PROCESS_GATE.json')
import rclpy
os.environ['ROS_DOMAIN_ID']='225';rclpy.init();node=rclpy.create_node('o24_isolation_probe')
snapshots=[];t=time.monotonic()
while time.monotonic()-t<3.0:
 rclpy.spin_once(node,timeout_sec=.1)
 snapshots.append(dict(elapsed_s=time.monotonic()-t,nodes=node.get_node_names_and_namespaces()))
seen={(name,ns)for r in snapshots for name,ns in r['nodes']}
foreign=[x for x in seen if x!=('o24_isolation_probe','/')]
services=node.get_service_names_and_types();node.destroy_node();rclpy.shutdown()
result=dict(status='PASS_DOMAIN_GRAPH_VACANT'if not foreign else 'FAIL_DOMAIN_GRAPH_OCCUPIED',domain=225,discovery_s=time.monotonic()-t,foreign_nodes=foreign,snapshots=snapshots,services=services,native_GSL_goals=0,new_gas_worlds=0)
(R/'DOMAIN_POST_GRAPH_GATE.json').write_text(json.dumps(result,indent=2)+'\n')
assert not foreign,foreign
print(json.dumps(dict(status=result['status'],domain=225,native_GSL_goals=0)))
