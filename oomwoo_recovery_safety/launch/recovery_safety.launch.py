from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    mux_arg = DeclareLaunchArgument(
        "mux", default_value="true",
        description="Launch the cmd_vel_mux arbitration node. Set to false "
                    "when nav2.launch.py is already running (it includes its own mux)."
    )
    mux = LaunchConfiguration("mux")

    return LaunchDescription(
        [
            mux_arg,
            Node(
                package="oomwoo_recovery_safety",
                executable="cmd_vel_mux",
                name="cmd_vel_mux",
                output="screen",
                condition=IfCondition(mux),
            ),
            Node(
                package="oomwoo_recovery_safety",
                executable="recovery_safety_node",
                name="recovery_safety",
                output="screen",
            ),
        ]
    )
