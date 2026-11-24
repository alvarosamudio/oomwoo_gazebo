#!/usr/bin/env python3
"""
Cliff detector: turns the four simulated downward range sensors into the
cliff bitfield described in OOMWOO SOFTWARE_INTERFACES.md
(`/oomwoo/io/cliff`, "Cliff bitfield or future OOMWOO message").

Inputs  : cliff/<name> (sensor_msgs/LaserScan), one per sensor
Output  : /oomwoo/io/cliff (std_msgs/UInt8), published at `rate` Hz

Bit layout (bit set = cliff, or sensor stale/invalid -> fail safe):
  bit 0  front_left
  bit 1  front_right
  bit 2  side_left
  bit 3  side_right

A sensor reads "cliff" when any ray is farther than `threshold` metres,
is +inf (no floor within range) or NaN. -inf (closer than range_min, e.g.
thick carpet touching the sensor) is treated as floor.
"""
import math

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan
from std_msgs.msg import UInt8

SENSORS = ("front_left", "front_right", "side_left", "side_right")


def ray_is_cliff(r, threshold):
    if math.isnan(r):
        return True
    if math.isinf(r):
        return r > 0
    return r > threshold


def scan_is_cliff(ranges, threshold):
    """True if the scan sees a drop. An empty scan is invalid -> cliff."""
    if not ranges:
        return True
    return any(ray_is_cliff(r, threshold) for r in ranges)


def cliff_bits(states):
    """states: iterable of bools in SENSORS order -> int bitfield."""
    bits = 0
    for i, cliff in enumerate(states):
        if cliff:
            bits |= 1 << i
    return bits


class CliffDetector(Node):
    def __init__(self):
        super().__init__("cliff_detector")
        # Floor sits ~0.018 m below the sensors in the default URDF.
        self._threshold = self.declare_parameter("threshold", 0.045).value
        self._timeout = self.declare_parameter("timeout", 0.5).value
        rate = self.declare_parameter("rate", 50.0).value

        self._cliff = {name: True for name in SENSORS}
        self._stamp = {name: None for name in SENSORS}
        self._last_bits = None

        for name in SENSORS:
            self.create_subscription(
                LaserScan, f"cliff/{name}",
                lambda msg, n=name: self._on_scan(n, msg),
                qos_profile_sensor_data,
            )
        self._pub = self.create_publisher(UInt8, "/oomwoo/io/cliff", 10)
        self.create_timer(1.0 / rate, self._publish)

    def _on_scan(self, name, msg):
        self._cliff[name] = scan_is_cliff(list(msg.ranges), self._threshold)
        self._stamp[name] = self.get_clock().now()

    def _publish(self):
        now = self.get_clock().now()
        states = []
        for name in SENSORS:
            stamp = self._stamp[name]
            stale = stamp is None or (now - stamp).nanoseconds * 1e-9 > self._timeout
            states.append(stale or self._cliff[name])
        bits = cliff_bits(states)
        if bits != self._last_bits:
            active = [n for n, s in zip(SENSORS, states) if s]
            if active:
                self.get_logger().warn(f"cliff/stale: {', '.join(active)} (0x{bits:02x})")
            else:
                self.get_logger().info("all cliff sensors see floor")
            self._last_bits = bits
        self._pub.publish(UInt8(data=bits))


def main():
    rclpy.init()
    node = CliffDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
