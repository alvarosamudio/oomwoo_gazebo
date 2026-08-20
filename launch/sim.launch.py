import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.conditions import IfCondition
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg = get_package_share_directory("oomwoo_gazebo")

    world_arg = DeclareLaunchArgument(
        "world", default_value=os.path.join(pkg, "worlds", "living_room.sdf"),
        description="Gazebo world file"
    )
    rviz_arg = DeclareLaunchArgument(
        "rviz", default_value="true",
        description="Launch RViz"
    )

    world = LaunchConfiguration("world")
    rviz = LaunchConfiguration("rviz")

    gz_server = ExecuteProcess(
        cmd=["gz", "sim", "-r", world],
        output="screen",
        additional_env={"GZ_SIM_RESOURCE_PATH": os.path.join(pkg, "sdf")},
    )

    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        parameters=[os.path.join(pkg, "config", "gz_bridge.yaml"),
                    {"use_sim_time": True}],
        output="screen",
    )

    robot_state_pub = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[{
            "robot_description": Command(
                ["xacro ", os.path.join(pkg, "urdf", "robot.urdf.xacro")]
            ),
            "use_sim_time": True,
        }],
    )

    # `create` retries internally until the world service is up, but exits
    # non-zero if robot_description is not published yet. Retry the whole
    # spawn so slow machines / headless rendering do not lose the robot.
    spawn_entity = ExecuteProcess(
        cmd=[
            "bash", "-c",
            "for i in $(seq 1 30); do "
            "ros2 run ros_gz_sim create -name oomwoo -topic robot_description "
            "-x 0 -y 0 -Y 0 && exit 0; "
            "sleep 1; done; exit 1",
        ],
        output="screen",
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        arguments=["-d", os.path.join(pkg, "rviz", "oomwoo.rviz")],
        condition=IfCondition(rviz),
    )

    return LaunchDescription([
        world_arg,
        rviz_arg,
        gz_server,
        bridge,
        robot_state_pub,
        spawn_entity,
        rviz_node,
    ])
