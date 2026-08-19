"""
Priority multiplexer for /cmd_vel arbitration.

Implements the OOMWOO SOFTWARE_INTERFACES.md requirement that direct motion
commands must define arbitration so that no two nodes fight over /cmd_vel.

Priority sources publish to `cmd_vel_priority` (recovery/safety nodes) and
keep authority while their last message is fresher than `priority_timeout`.
Nav2 (velocity smoother + collision monitor) and teleop publish to
`cmd_vel_nav`. The mux forwards the highest-priority fresh source; when every
source is stale it publishes zero so a dead publisher can never keep the
robot moving (fail-safe).
"""
from time import monotonic

from geometry_msgs.msg import Twist
from rclpy.node import Node


class CmdVelMux(Node):
    def __init__(self, priority_timeout: float = 2.0, nav_timeout: float = 1.0):
        super().__init__("cmd_vel_mux")
        self._priority_timeout = priority_timeout
        self._nav_timeout = nav_timeout

        self._priority_msg: Twist | None = None
        self._priority_stamp: float | None = None
        self._nav_msg: Twist | None = None
        self._nav_stamp: float | None = None

        self._pub = self.create_publisher(Twist, "cmd_vel", 10)
        self.create_subscription(Twist, "cmd_vel_priority", self._priority_cb, 10)
        self.create_subscription(Twist, "cmd_vel_nav", self._nav_cb, 10)
        self.create_timer(0.05, self._timer_cb)

    def _priority_cb(self, msg: Twist):
        self._priority_msg = msg
        self._priority_stamp = monotonic()

    def _nav_cb(self, msg: Twist):
        self._nav_msg = msg
        self._nav_stamp = monotonic()

    def _timer_cb(self):
        now = monotonic()
        if self._is_fresh(self._priority_stamp, self._priority_timeout):
            self._pub.publish(self._priority_msg)
        elif self._is_fresh(self._nav_stamp, self._nav_timeout):
            self._pub.publish(self._nav_msg)
        else:
            self._pub.publish(Twist())

    @staticmethod
    def _is_fresh(stamp: float | None, timeout: float) -> bool:
        return stamp is not None and monotonic() - stamp <= timeout


def main(args=None):
    import rclpy
    from rclpy.executors import ExternalShutdownException
    from rclpy.exceptions import ROSInterruptException

    rclpy.init(args=args)
    node = CmdVelMux()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException, ROSInterruptException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
