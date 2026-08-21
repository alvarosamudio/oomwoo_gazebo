import threading
import time

import pytest
import rclpy
from geometry_msgs.msg import Twist

from oomwoo_recovery_safety.cmd_vel_mux import CmdVelMux

SHORT_TIMEOUT = 0.3
TEST_TIMEOUT = 5.0


@pytest.fixture
def mux_node():
    rclpy.init()
    node = CmdVelMux(priority_timeout=SHORT_TIMEOUT, nav_timeout=SHORT_TIMEOUT)
    thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    thread.start()
    yield node
    node.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()


def _wait_for(predicate, timeout=TEST_TIMEOUT):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.05)
    return False


def _wait_for_subscribers(pub, timeout=TEST_TIMEOUT):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if pub.get_subscription_count() >= 1:
            return True
        time.sleep(0.05)
    return False


def _last_x(received):
    return received[-1].linear.x if received else None


def test_priority_overrides_nav(mux_node):
    received = []
    mux_node.create_subscription(Twist, "cmd_vel", lambda msg: received.append(msg), 10)
    nav_pub = mux_node.create_publisher(Twist, "cmd_vel_nav", 10)
    priority_pub = mux_node.create_publisher(Twist, "cmd_vel_priority", 10)

    assert _wait_for_subscribers(nav_pub)
    assert _wait_for_subscribers(priority_pub)

    nav = Twist()
    nav.linear.x = 0.3
    nav_pub.publish(nav)
    assert _wait_for(lambda: _last_x(received) == 0.3)

    priority = Twist()
    priority.linear.x = -0.12
    priority_pub.publish(priority)

    assert _wait_for(lambda: _last_x(received) == -0.12)


def test_nav_forwarded_when_priority_stale(mux_node):
    received = []
    mux_node.create_subscription(Twist, "cmd_vel", lambda msg: received.append(msg), 10)
    nav_pub = mux_node.create_publisher(Twist, "cmd_vel_nav", 10)
    priority_pub = mux_node.create_publisher(Twist, "cmd_vel_priority", 10)

    assert _wait_for_subscribers(nav_pub)
    assert _wait_for_subscribers(priority_pub)

    stale = Twist()
    stale.linear.x = -0.5
    priority_pub.publish(stale)
    time.sleep(SHORT_TIMEOUT + 0.2)

    nav = Twist()
    nav.linear.x = 0.3
    nav_pub.publish(nav)

    assert _wait_for(lambda: _last_x(received) == 0.3)


def test_zero_when_all_sources_stale(mux_node):
    received = []
    mux_node.create_subscription(Twist, "cmd_vel", lambda msg: received.append(msg), 10)
    nav_pub = mux_node.create_publisher(Twist, "cmd_vel_nav", 10)

    assert _wait_for_subscribers(nav_pub)

    nav = Twist()
    nav.linear.x = 0.3
    nav_pub.publish(nav)
    assert _wait_for(lambda: _last_x(received) == 0.3)

    time.sleep(SHORT_TIMEOUT + 0.2)

    assert _wait_for(lambda: _last_x(received) == 0.0)
