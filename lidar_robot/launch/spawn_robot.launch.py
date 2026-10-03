import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    IncludeLaunchDescription,
    TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch.actions import ExecuteProcess


def generate_launch_description():
    pkg_share = get_package_share_directory('lidar_robot')

    xacro_file = os.path.join(pkg_share, 'urdf', 'robot.urdf.xacro')
    world_file = os.path.join(pkg_share, 'worlds', 'empty.world')

    robot_description = ParameterValue(
        Command(['xacro ', xacro_file]),
        value_type=str
    )

    # 1. Robot State Publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': True,
        }],
        output='screen'
    )

    # 2. Gazebo Sim
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('ros_gz_sim'),
                'launch', 'gz_sim.launch.py'
            )
        ),
        launch_arguments={
            'gz_args': f'-r {world_file}'
        }.items()
    )

    # 3. Spawn robot
    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-topic', 'robot_description',
            '-name', 'lidar_robot',
            '-z', '0.05'
        ],
        output='screen'
    )

    # 4. Bridge ROS 2 <-> Gazebo
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
            '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
        ],
        parameters=[{'use_sim_time': True}],
        output='screen'
    )

    # 5. RViz2
    rviz_config = os.path.join(pkg_share, 'rviz', 'robot.rviz')
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': True}],
        output='screen'
    )

    spawn_delayed = TimerAction(
        period=3.0,
        actions=[spawn_robot]
    )

    rviz_delayed = TimerAction(
        period=4.0,
        actions=[rviz]
    )

    # === Force lidar entity initialization after spawn ===
    force_lidar_init = ExecuteProcess(
        cmd=['gz', 'model', '-m', 'lidar_robot', '-l', 'lidar_link'],
        output='screen',
        shell=True,
    )

    delayed_force_cmd = TimerAction(
        period=3.0,  # Chờ 3 giây sau khi spawn
        actions=[force_lidar_init],
    )
    
    return LaunchDescription([
        robot_state_publisher,
        gz_sim,
        spawn_delayed,
        bridge,
        rviz_delayed,
        delayed_force_cmd,  # ← Thêm dòng này
    ])