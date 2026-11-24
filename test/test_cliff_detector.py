"""Unit tests for the pure cliff-detection logic (no ROS graph needed)."""
import importlib.util
import math
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "oomwoo_gazebo_harmonic", "cliff_detector.py")


def _stub_ros():
    """Allow running the tests outside a sourced ROS environment."""
    try:
        import rclpy  # noqa: F401
        return
    except ImportError:
        pass
    mods = {
        "rclpy": {}, "rclpy.node": {"Node": object},
        "rclpy.qos": {"qos_profile_sensor_data": None},
        "sensor_msgs": {}, "sensor_msgs.msg": {"LaserScan": object},
        "std_msgs": {}, "std_msgs.msg": {"UInt8": object},
    }
    for name, attrs in mods.items():
        mod = types.ModuleType(name)
        mod.__dict__.update(attrs)
        sys.modules.setdefault(name, mod)


_stub_ros()
_spec = importlib.util.spec_from_file_location("cliff_detector", SRC)
cd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cd)

T = 0.045


def test_floor_is_not_cliff():
    assert not cd.scan_is_cliff([0.018, 0.019, 0.017], T)


def test_drop_beyond_threshold_is_cliff():
    assert cd.scan_is_cliff([0.018, 0.12, 0.018], T)


def test_out_of_range_is_cliff():
    assert cd.scan_is_cliff([math.inf, math.inf, math.inf], T)


def test_nan_is_cliff_fail_safe():
    assert cd.scan_is_cliff([0.018, math.nan, 0.018], T)


def test_too_close_is_floor():
    assert not cd.scan_is_cliff([-math.inf, 0.004, -math.inf], T)


def test_empty_scan_is_cliff():
    assert cd.scan_is_cliff([], T)


def test_bitfield_layout():
    assert cd.cliff_bits([False, False, False, False]) == 0
    assert cd.cliff_bits([True, False, False, False]) == 0b0001
    assert cd.cliff_bits([False, True, False, True]) == 0b1010
    assert cd.cliff_bits([True] * 4) == 0b1111
    assert cd.SENSORS == ("front_left", "front_right", "side_left", "side_right")
