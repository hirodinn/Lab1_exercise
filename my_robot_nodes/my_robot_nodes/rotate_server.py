#!/usr/bin/env python3
"""Action server that rotates the robot on the spot for a specified angle, measured
with wheel odometry yaw, reporting feedback while turning."""

import math
import time

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor
from rclpy.node import Node

from my_robot_interfaces.action import Rotate


def yaw_from_quaternion(q):
    """Rotation about the vertical axis, in rad, of an orientation quaternion."""
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))


def angle_difference(target, current):
    """target - current, wrapped to [-pi, pi] so the difference is the shortest angle."""
    return math.atan2(math.sin(target - current), math.cos(target - current))


class RotateServer(Node):

    def __init__(self):
        super().__init__("rotate_server")
        self.declare_parameter("turn_speed", 0.5)

        self.yaw = None

        group = ReentrantCallbackGroup()
        self.cmd_vel = self.create_publisher(Twist, "cmd_vel", 10)
        self.create_subscription(Odometry, "odom", self.on_odom, 10, callback_group=group)
        self.action_server = ActionServer(
            self, Rotate, "rotate",
            execute_callback=self.execute,
            goal_callback=self.on_goal,
            cancel_callback=lambda goal_handle: CancelResponse.ACCEPT,
            callback_group=group,
        )

    def on_odom(self, msg: Odometry):
        self.yaw = yaw_from_quaternion(msg.pose.pose.orientation)

    def on_goal(self, goal):
        if abs(goal.angle) < 1e-5 or self.yaw is None:
            self.get_logger().info("Rejecting rotate goal (zero angle or no odometry yet)")
            return GoalResponse.REJECT
        return GoalResponse.ACCEPT

    def execute(self, goal_handle):
        target_angle = goal_handle.request.angle
        target_abs = abs(target_angle)
        direction = 1.0 if target_angle > 0.0 else -1.0
        turn_speed = self.get_parameter("turn_speed").value

        self.get_logger().info(f"Rotating {target_angle:.2f} rad at {turn_speed:.2f} rad/s")

        twist = Twist()
        twist.angular.z = direction * turn_speed
        feedback = Rotate.Feedback()
        result = Rotate.Result()

        last_yaw = self.yaw
        total_turned = 0.0

        while rclpy.ok():
            curr_yaw = self.yaw
            delta = angle_difference(curr_yaw, last_yaw)
            last_yaw = curr_yaw
            total_turned += delta

            result.turned = total_turned

            if goal_handle.is_cancel_requested:
                self.cmd_vel.publish(Twist())
                goal_handle.canceled()
                self.get_logger().info(f"Rotation canceled after {total_turned:.2f} rad")
                return result

            # Stop when we have turned through the target magnitude
            if abs(total_turned) >= target_abs:
                break

            self.cmd_vel.publish(twist)
            feedback.turned = total_turned
            goal_handle.publish_feedback(feedback)
            time.sleep(0.05)

        self.cmd_vel.publish(Twist())
        goal_handle.succeed()
        result.turned = total_turned
        self.get_logger().info(f"Rotation succeeded, turned {result.turned:.2f} rad")
        return result


def main(args=None):
    rclpy.init(args=args)
    node = RotateServer()
    try:
        rclpy.spin(node, executor=MultiThreadedExecutor())
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == "__main__":
    main()
