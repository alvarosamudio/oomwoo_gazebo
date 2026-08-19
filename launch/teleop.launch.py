import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg = get_package_share_directory("oomwoo_gazebo")

    topic_arg = DeclareLaunchArgument(
        "topic", default_value="cmd_vel",
        description="Output topic. Use cmd_vel_nav when the cmd_vel_mux "
                    "arbitration node is running (e.g. with nav2 or "
                    "oomwoo_recovery_safety)."
    )
    topic = LaunchConfiguration("topic")

    return LaunchDescription([
        topic_arg,
        Node(
            package="teleop_twist_keyboard",
            executable="teleop_twist_keyboard",
            name="teleop_twist_keyboard",
            output="screen",
            prefix="xterm -e",
            remappings=[("cmd_vel", topic)],
        ),
    ])
