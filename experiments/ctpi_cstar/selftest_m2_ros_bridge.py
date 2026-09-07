"""ROS-normalized callback wiring test for the online M2 session."""
from __future__ import annotations

from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "closed_loop" / "ctpi"))
from cstar_m2_ros_bridge import CstarM2RosBridge
from cstar_m2_online import validate_law_shape
from cstar_reference import CPORouteLaw


class Provider:
    def predict(self, prefix, request):
        assert prefix and prefix[-1].stamp_ns == 0
        return CPORouteLaw.from_hazards([0.2, 0.3], [0.0, 0.1], [0.4, 0.4])


def main():
    frames = []
    bridge = CstarM2RosBridge(Provider(), frames.append)
    # Real ROS callback order is arbitrary; normalized ingress joins by stamp.
    for kind, values in (("wind", (1.0, 0.0)), ("pose", (0.0, 0.0)),
                         ("gas", (0.0,))):
        bridge.push_normalized(kind, 0, values)
    assert bridge.ready and bridge.stats.joined_frames == 1
    law = bridge.arm_route((0.0, 0.0), ((1.0, 0.0), (2.0, 0.0)))
    validate_law_shape(law, 2)
    for kind, values in (("gas", (0.1,)), ("wind", (1.0, 0.0)),
                         ("pose", (0.2, 0.0))):
        bridge.push_normalized(kind, 200_000_000, values)
    bridge.finish(200_000_000)
    assert bridge.stats.joined_frames == 2
    assert bridge.stats.predictions == 1 and bridge.stats.observations == 1
    assert [f.stamp_ns for f in frames] == [0, 200_000_000]
    print("CSTAR_M2_ROS_BRIDGE_SELFTEST PASS")


if __name__ == "__main__":
    main()
