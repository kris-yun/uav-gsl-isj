"""Strict stamped online-input join for V2; no inference and no truth inputs.

This does not start the simulator or alter any legacy ROS controller. The optional
ROS entry point records aligned frames and publishes startup readiness. Both the
predictor and startup launcher must consume this contract before a V2 run is valid.
Wind is the LOCAL stamped anemometer reading, not an invented full wind field.
"""
from __future__ import annotations

from dataclasses import dataclass
import argparse
import json
import math


@dataclass(frozen=True)
class Frame:
    stamp_ns: int
    pose_xy: tuple[float, float]
    gas_ppm: float
    wind_uv: tuple[float, float]


class StampedIngress:
    """Join by message stamp, never by callback order or latest robot pose.

    Repeated paused-clock publications are accepted only if identical to the
    last message on that topic; they produce no additional evidence. All unique
    positive-stamp observations are consumed exactly once. No interpolation,
    gap filling or resetting a late stream is allowed. Queue limit is a resource
    limit, not a statistical parameter. Readiness proves aligned t=0 inputs only,
    NOT readiness of the source estimator or validity of its initial gas field.
    """
    kinds = {"pose", "gas", "wind"}

    def __init__(self, cadence_ns=200_000_000, max_pending=500,
                 initial_sensor_ppm=0.0):
        if type(cadence_ns) is not int or cadence_ns <= 0:
            raise ValueError("cadence must be a positive integer")
        if type(max_pending) is not int or max_pending < 1:
            raise ValueError("max_pending must be a positive integer")
        if not math.isfinite(initial_sensor_ppm) or initial_sensor_ppm < 0:
            raise ValueError("invalid initial sensor state")
        self.cadence_ns = cadence_ns
        self.max_pending = max_pending
        self.initial_sensor_ppm = initial_sensor_ppm
        self.next_stamp = 0
        self.pending = {}
        self.last_seen = {kind: -1 for kind in self.kinds}
        self.last_value = {}
        self.identical_repeats = 0
        self.failed = False

    @property
    def ready(self):
        return not self.failed and self.next_stamp > 0

    def push(self, kind: str, stamp_ns: int, values) -> list[Frame]:
        if self.failed:
            raise ValueError("V2_INGRESS_ALREADY_FAILED")
        try:
            return self._push(kind, stamp_ns, values)
        except (ValueError, TypeError, OverflowError):
            self.failed = True  # malformed streams cannot silently resume
            raise

    def _push(self, kind, stamp_ns, values):
        if kind not in self.kinds or type(stamp_ns) is not int or stamp_ns < 0:
            raise ValueError("V2_INGRESS_INVALID_KEY")
        value = tuple(float(v) for v in values)
        if len(value) != (1 if kind == "gas" else 2) or not all(map(math.isfinite, value)):
            raise ValueError("V2_INGRESS_INVALID_VALUE")
        if kind == "gas" and value[0] < 0:
            raise ValueError("V2_INGRESS_NEGATIVE_GAS")
        if stamp_ns % self.cadence_ns:
            raise ValueError("V2_INGRESS_OFF_CADENCE")
        if stamp_ns == self.last_seen[kind]:
            if value != self.last_value[kind]:
                raise ValueError("V2_INGRESS_CONFLICTING_SAME_STAMP")
            self.identical_repeats += 1
            return []
        expected = 0 if self.last_seen[kind] < 0 else self.last_seen[kind] + self.cadence_ns
        if stamp_ns != expected:
            raise ValueError("V2_INGRESS_TOPIC_GAP_OR_DUPLICATE")
        if stamp_ns == 0 and kind == "gas" and value[0] != self.initial_sensor_ppm:
            raise ValueError("V2_INGRESS_WRONG_INITIAL_SENSOR_STATE")
        if stamp_ns not in self.pending and len(self.pending) >= self.max_pending:
            raise ValueError("V2_INGRESS_PENDING_LIMIT")
        self.last_seen[kind] = stamp_ns
        self.last_value[kind] = value
        self.pending.setdefault(stamp_ns, {})[kind] = value
        frames = []
        while len(self.pending.get(self.next_stamp, {})) == 3:
            joined = self.pending.pop(self.next_stamp)
            frames.append(Frame(self.next_stamp, joined["pose"], joined["gas"][0], joined["wind"]))
            self.next_stamp += self.cadence_ns
        return frames

    def finish(self, final_stamp_ns: int):
        """Terminal completeness: no pending rows or unreceived tail samples."""
        if (type(final_stamp_ns) is not int or final_stamp_ns < 0
                or final_stamp_ns % self.cadence_ns or not self.ready
                or self.pending or self.next_stamp != final_stamp_ns + self.cadence_ns):
            self.failed = True
            raise ValueError("V2_INGRESS_INCOMPLETE_HORIZON")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, help="New exclusive-create JSONL audit file")
    parser.add_argument("--pose-topic", default="/amcl_pose")
    parser.add_argument("--gas-topic", default="/PID/Sensor_reading")
    parser.add_argument("--wind-topic", default="/Anemometer/WindSensor_reading")
    parser.add_argument("--final-stamp-ns", type=int, default=240_000_000_000)
    args, ros_args = parser.parse_known_args()
    if args.final_stamp_ns < 0 or args.final_stamp_ns % 200_000_000:
        parser.error("final stamp must be a nonnegative multiple of 200000000 ns")
    # ROS is optional for pure CPU tests, and no package install is attempted.
    import rclpy
    from rclpy.node import Node
    from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy
    from geometry_msgs.msg import PoseWithCovarianceStamped
    from olfaction_msgs.msg import GasSensor, Anemometer
    from std_msgs.msg import Bool

    rclpy.init(args=ros_args)
    ingress = StampedIngress()
    complete = False
    with open(args.output, "x", encoding="utf-8") as audit:
        class IngressNode(Node):
            def __init__(self):
                super().__init__("ctpi_v2_stamped_ingress")
                qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL,
                                 reliability=ReliabilityPolicy.RELIABLE)
                self.ready_pub = self.create_publisher(Bool, "/ctpi_v2_ingress_ready", qos)
                self.ready_pub.publish(Bool(data=False))
                self.subs = [
                    self.create_subscription(PoseWithCovarianceStamped, args.pose_topic, self.pose, 500),
                    self.create_subscription(GasSensor, args.gas_topic, self.gas, 500),
                    self.create_subscription(Anemometer, args.wind_topic, self.wind, 500),
                ]

            def record(self, item):
                audit.write(json.dumps(item, allow_nan=False) + "\n")
                audit.flush()

            def accept(self, kind, msg, value):
                nonlocal complete
                stamp = msg.header.stamp.sec * 1_000_000_000 + msg.header.stamp.nanosec
                try:
                    frames = ingress.push(kind, stamp, value)
                    for f in frames:
                        self.record({"event": "frame", **f.__dict__})
                        if f.stamp_ns == 0:
                            self.ready_pub.publish(Bool(data=True))
                        if f.stamp_ns == args.final_stamp_ns:
                            ingress.finish(args.final_stamp_ns)
                            self.record({"event": "complete", "final_stamp_ns": f.stamp_ns,
                                         "identical_repeats_ignored": ingress.identical_repeats})
                            complete = True
                except (ValueError, TypeError, OverflowError) as exc:
                    self.ready_pub.publish(Bool(data=False))
                    self.record({"event": "invalid", "kind": kind, "stamp_ns": stamp, "error": str(exc)})
                    raise

            def pose(self, msg):
                if msg.header.frame_id != "map":
                    self.reject_envelope("pose", "V2_INGRESS_POSE_FRAME")
                self.accept("pose", msg, (msg.pose.pose.position.x, msg.pose.pose.position.y))

            def gas(self, msg):
                if msg.raw_units != GasSensor.UNITS_PPM:
                    self.reject_envelope("gas", "V2_INGRESS_GAS_UNITS")
                self.accept("gas", msg, (msg.raw,))

            def wind(self, msg):
                if (msg.header.frame_id != "map" or not math.isfinite(msg.wind_speed)
                        or msg.wind_speed < 0 or not math.isfinite(msg.wind_direction)):
                    self.reject_envelope("wind", "V2_INGRESS_WIND_FRAME_OR_SPEED")
                self.accept("wind", msg, (msg.wind_speed * math.cos(msg.wind_direction),
                                          msg.wind_speed * math.sin(msg.wind_direction)))

            def reject_envelope(self, kind, error):
                ingress.failed = True
                self.ready_pub.publish(Bool(data=False))
                self.record({"event": "invalid", "kind": kind, "error": error})
                raise ValueError(error)

        node = IngressNode()
        try:
            while rclpy.ok() and not complete:
                rclpy.spin_once(node, timeout_sec=1.0)
        finally:
            node.ready_pub.publish(Bool(data=False))
            node.destroy_node()
            rclpy.shutdown()
    if not complete:
        raise RuntimeError("V2_INGRESS_ENDED_WITHOUT_COMPLETE_HORIZON")


if __name__ == "__main__":
    main()
