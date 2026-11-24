import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.conditions import IfCondition
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg = get_package_share_directory("oomwoo_gazebo_harmonic")

    world_arg = DeclareLaunchArgument(
        "world", default_value=os.path.join(pkg, "worlds", "living_room.sdf"),
        description="Gazebo world file"
    )
    rviz_arg = DeclareLaunchArgument(
        "rviz", default_value="true",
        description="Launch RViz"
    )

    spawn_args = [
        DeclareLaunchArgument(n, default_value=v, description=d)
        for n, v, d in (
            ("x", "0.0", "Spawn x [m]"),
            ("y", "0.0", "Spawn y [m]"),
            ("z", "0.0", "Spawn z [m] (e.g. 0.1 for cliff_test.sdf)"),
            ("yaw", "0.0", "Spawn yaw [rad]"),
        )
    ]

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
            ["for i in $(seq 1 30); do "
             "ros2 run ros_gz_sim create -name oomwoo -topic robot_description"
             " -x ", LaunchConfiguration("x"),
             " -y ", LaunchConfiguration("y"),
             " -z ", LaunchConfiguration("z"),
             " -Y ", LaunchConfiguration("yaw"),
             " && exit 0; sleep 1; done; exit 1"],
        ],
        output="screen",
    )

    # Publishes /oomwoo/io/cliff (UInt8 bitfield) from the 4 cliff sensors.
    cliff_detector = Node(
        package="oomwoo_gazebo_harmonic",
        executable="cliff_detector.py",
        name="cliff_detector",
        parameters=[{"use_sim_time": True}],
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
        *spawn_args,
        gz_server,
        bridge,
        robot_state_pub,
        spawn_entity,
        cliff_detector,
        rviz_node,
    ])
