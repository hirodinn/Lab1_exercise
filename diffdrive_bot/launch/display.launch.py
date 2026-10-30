"""
View the lab robot model in RViz without Gazebo: robot_state_publisher publishes the
TF tree from the URDF, and joint_state_publisher_gui gives a slider per wheel.

Usage:
    ros2 launch diffdrive_bot display.launch.py
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_share = get_package_share_directory("diffdrive_bot")

    robot_description = ParameterValue(
        Command(["xacro ", os.path.join(pkg_share, "urdf", "diffdrive_bot.urdf.xacro")]),
        value_type=str,
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[{"robot_description": robot_description}],
        output="screen",
    )

    nodes = [robot_state_publisher]

    try:
        get_package_share_directory("joint_state_publisher_gui")
        nodes.append(
            Node(
                package="joint_state_publisher_gui",
                executable="joint_state_publisher_gui",
                output="screen",
            )
        )
    except Exception:
        pass

    nodes.append(rviz)

    return LaunchDescription(nodes)
