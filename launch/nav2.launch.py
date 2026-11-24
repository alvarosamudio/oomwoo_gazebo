import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg = get_package_share_directory("oomwoo_gazebo_harmonic")
    nav2_bringup = get_package_share_directory("nav2_bringup")
    nav2_map_server = get_package_share_directory("nav2_map_server")
    nav2_params = os.path.join(pkg, "config", "navigation.yaml")
    default_map = os.path.join(pkg, "config", "map.yaml")

    use_sim_time = LaunchConfiguration("use_sim_time", default="true")
    map_yaml = LaunchConfiguration("map", default=default_map)

    return LaunchDescription([
        DeclareLaunchArgument(
            "map", default_value=default_map,
            description="Full path to map YAML file. "
                        "Pass an empty string (map:='') to rely on SLAM's /map instead."
        ),
        DeclareLaunchArgument(
            "use_sim_time", default_value="true",
            description="Use simulation time"
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(nav2_bringup, "launch", "localization_launch.py")
            ),
            launch_arguments={
                "use_sim_time": use_sim_time,
                "params_file": nav2_params,
                "map": map_yaml,
                "autostart": "true",
            }.items(),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(nav2_bringup, "launch", "navigation_launch.py")
            ),
            launch_arguments={
                "use_sim_time": use_sim_time,
                "params_file": nav2_params,
                "autostart": "true",
            }.items(),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(nav2_map_server, "launch", "map_saver_server.launch.py")
            ),
        ),
        # cmd_vel arbitration: Nav2 publishes to cmd_vel_nav and the mux owns
        # the final cmd_vel (recovery/safety commands win while active).
        Node(
            package="oomwoo_recovery_safety",
            executable="cmd_vel_mux",
            name="cmd_vel_mux",
            output="screen",
        ),
    ])
