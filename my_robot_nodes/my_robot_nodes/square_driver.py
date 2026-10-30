#!/usr/bin/env python3
"""Action client node that drives the robot around a square by alternately calling
the drive_distance and rotate action servers four times."""

import math
import sys

import rclpy
from action_msgs.msg import GoalStatus
from rclpy.action import ActionClient
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node

from lab_interfaces.action import DriveDistance
from my_robot_interfaces.action import Rotate


class SquareDriver(Node):

    def __init__(self):
        super().__init__("square_driver")
        self.declare_parameter("side_length", 0.5)

        self.drive_client = ActionClient(self, DriveDistance, "drive_distance")
        self.rotate_client = ActionClient(self, Rotate, "rotate")

    def run(self):
        side_length = self.get_parameter("side_length").value
        quarter_turn = math.pi / 2.0  # quarter turn to the left (positive rad)

        self.get_logger().info("Waiting for /drive_distance and /rotate action servers...")
        if not self.drive_client.wait_for_server(timeout_sec=60.0):
            self.get_logger().error("drive_distance action server not available!")
            return
        if not self.rotate_client.wait_for_server(timeout_sec=60.0):
            self.get_logger().error("rotate action server not available!")
            return

        self.get_logger().info(f"Action servers ready. Driving square with side_length = {side_length:.2f} m")

        for side in range(1, 5):
            # 1. Drive forward along current side
            self.get_logger().info(f"Side {side}/4: Driving forward {side_length:.2f} m...")
            drive_goal = DriveDistance.Goal()
            drive_goal.distance = float(side_length)

            send_future = self.drive_client.send_goal_async(drive_goal)
            rclpy.spin_until_future_complete(self, send_future)
            goal_handle = send_future.result()
            if not goal_handle or not goal_handle.accepted:
                self.get_logger().error(f"Drive goal rejected on side {side}")
                return

            result_future = goal_handle.get_result_async()
            rclpy.spin_until_future_complete(self, result_future)
            res = result_future.result()
            if res.status != GoalStatus.STATUS_SUCCEEDED or not res.result.reached:
                self.get_logger().error(f"Drive failed on side {side} (status {res.status})")
                return
            self.get_logger().info(f"Side {side}/4: Drive completed (travelled {res.result.travelled:.2f} m)")

            # 2. Rotate quarter turn left (positive angle)
            self.get_logger().info(f"Side {side}/4: Rotating left 90 deg ({quarter_turn:.2f} rad)...")
            rotate_goal = Rotate.Goal()
            rotate_goal.angle = float(quarter_turn)

            send_future = self.rotate_client.send_goal_async(rotate_goal)
            rclpy.spin_until_future_complete(self, send_future)
            goal_handle = send_future.result()
            if not goal_handle or not goal_handle.accepted:
                self.get_logger().error(f"Rotate goal rejected on side {side}")
                return

            result_future = goal_handle.get_result_async()
            rclpy.spin_until_future_complete(self, result_future)
            res = result_future.result()
            if res.status != GoalStatus.STATUS_SUCCEEDED:
                self.get_logger().error(f"Rotate failed on side {side} (status {res.status})")
                return
            self.get_logger().info(f"Side {side}/4: Rotation completed (turned {res.result.turned:.2f} rad)")

        self.get_logger().info("Square driving complete! Finished all 4 sides.")


def main(args=None):
    rclpy.init(args=args)
    node = SquareDriver()
    try:
        node.run()
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
