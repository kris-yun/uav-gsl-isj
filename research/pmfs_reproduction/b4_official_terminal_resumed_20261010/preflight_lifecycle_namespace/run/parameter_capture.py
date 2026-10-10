from pathlib import Path
import rclpy,json
from rclpy.node import Node
from guard_ros_io import dump_parameters
t=Path(__file__).resolve().parent;rclpy.init();n=Node('b4_direct_parameter_recorder')
try:
 evidence=[dump_parameters(n,'/PioneerP3DX/GSL',t/'runtime/resolved_GSL_parameters.yaml'),dump_parameters(n,'/gaden_player',t/'runtime/resolved_player_parameters.yaml')]
 (t/'runtime/DIRECT_PARAMETER_CAPTURE.json').write_text(json.dumps(evidence,indent=2));print(json.dumps(evidence))
finally:n.destroy_node();rclpy.shutdown()
