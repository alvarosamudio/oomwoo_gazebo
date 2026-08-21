import json
import threading
import time

import pytest
import rclpy
from geometry_msgs.msg import Twist
from ros_gz_interfaces.msg import Contact, Contacts, Entity
from std_msgs.msg import Bool, String

from oomwoo_recovery_safety.recovery_node import RecoverySafetyNode

TEST_TIMEOUT = 5.0


@pytest.fixture
def safety_node():
    rclpy.init()
    node = RecoverySafetyNode()
    thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    thread.start()
    yield node
    node.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()


def _wait_for_subscribers(pub, count=1, timeout=TEST_TIMEOUT):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if pub.get_subscription_count() >= count:
            return True
        time.sleep(0.05)
    return False


def _wait_for(predicate, timeout=TEST_TIMEOUT):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.05)
    return False


def _make_contacts(collision1_name, collision2_name):
    contacts = Contacts()
    contact = Contact()
    contact.collision1.name = collision1_name
    contact.collision2.name = collision2_name
    contacts.contacts.append(contact)
    return contacts


def test_bumper_contact_triggers_backup(safety_node):
    received = []
    safety_node.create_subscription(
        Twist, "cmd_vel_priority", lambda msg: received.append(msg), 10)
    pub = safety_node.create_publisher(Contacts, "bumper_left", 10)

    assert _wait_for_subscribers(pub)

    pub.publish(_make_contacts("bumper_left_collision", "wall_01::link"))

    assert _wait_for(lambda: len(received) >= 1)
    assert received[0].linear.x < 0.0
    assert received[0].linear.x == pytest.approx(-0.12)


def test_ground_plane_contact_is_ignored(safety_node):
    received = []
    safety_node.create_subscription(
        Twist, "cmd_vel_priority", lambda msg: received.append(msg), 10)
    pub = safety_node.create_publisher(Contacts, "bumper_left", 10)

    assert _wait_for_subscribers(pub)

    pub.publish(_make_contacts("bumper_left_collision", "ground_plane::link"))

    assert not _wait_for(lambda: len(received) >= 1, timeout=1.0)


def test_e_stop_pauses_and_reports_status(safety_node):
    received = []
    safety_node.create_subscription(
        String, "oomwoo/status", lambda msg: received.append(msg.data), 10)
    pub = safety_node.create_publisher(Bool, "oomwoo/safety/e_stop", 10)

    assert _wait_for_subscribers(pub)

    msg = Bool()
    msg.data = True
    pub.publish(msg)

    assert _wait_for(lambda: len(received) >= 1)
    payload = json.loads(received[-1])
    assert payload["reason_code"] == "E_STOP"
    assert payload["state"] == "paused"
    assert payload["recoverable"] is False
