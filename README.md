# Lab 1 Exercise: Program diffdrive_bot

**Name:** Hire Bikila  
**ID:** UGR/8021/16  
**Course:** Introduction to Robotics and Intelligent Systems  
**Program:** BSc in Software Engineering  
**Academic Year:** 2026  

---

## Overview

This repository contains the complete implementation of the Lab 1 exercise for `diffdrive_bot`. The project adds a depth camera and an IMU to the simulated robot in Gazebo Harmonic, defines custom ROS 2 communication interfaces, and implements custom control nodes culminating in an autonomous square-driving sequence coordinated via ROS 2 actions.

The repository holds four ROS 2 packages designed to build stand-alone in the `src` folder of any ROS 2 workspace:

1. **`diffdrive_bot`** (`ament_cmake`):
   - Robot description in URDF/Xacro (`urdf/diffdrive_bot.urdf.xacro`) with chassis, differential drive wheels, caster, lidar, front camera, rear depth camera, and IMU.
   - Simulation world (`worlds/obstacles.sdf`) with physics, sensors, and the `gz-sim-imu-system` plugin.
   - ROS-Gazebo bridge configuration (`config/bridge.yaml`).
   - Launch files and RViz visualization profiles.
   - Reference baseline controller and obstacle detection nodes.

2. **`lab_interfaces`** (`ament_cmake`):
   - Base lab interfaces: `ObstacleInfo.msg`, `SetSpeed.srv`, and `DriveDistance.action`.

3. **`my_robot_interfaces`** (`ament_cmake`):
   - Custom interface definitions:
     - `RobotStatus.msg`: publishes current movement state (`"forward"`, `"turning"`, `"stopped"`) and distance to nearest obstacle.
     - `SetTurnSpeed.srv`: dynamically configures turning speed with range validation.
     - `Rotate.action`: rotates the robot on the spot to a target angle in radians with real-time feedback.

4. **`my_robot_nodes`** (`ament_python`):
   - `turn_away`: Obstacle-reactive driver with dynamic parameters, custom status publishing, and service controls (`/turn_away_enable`, `/set_turn_speed`).
   - `rotate_server`: Multi-threaded action server for `/rotate` that tracks odometric yaw changes across the $[-\pi, \pi]$ boundary.
   - `square_driver`: Action client sequentially executing four pairs of `/drive_distance` and `/rotate` actions.
   - `square.launch.py`: Integrated launch file starting Gazebo simulation, bridge, RViz, `rotate_server`, and `square_driver`.

---

## Prerequisites & Requirements

- Ubuntu 22.04 LTS with ROS 2 Humble OR Ubuntu 24.04 LTS with ROS 2 Jazzy
- Gazebo Harmonic (`gz sim` 8.x)
- ROS 2 Gazebo packages (`ros_gz_bridge`, `ros_gz_sim`, `ros_gz_interfaces`)
- `xacro`, `tf2_ros`, `teleop_twist_keyboard`

---

## How to Build

Clone or place this repository folder into the `src` directory of your ROS 2 workspace:

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src
# Place or clone lab1_exercise here
cd ~/ros2_ws
colcon build --symlink-install
source install/setup.bash
```

All 4 packages will be discovered and built cleanly:
- `diffdrive_bot`
- `lab_interfaces`
- `my_robot_interfaces`
- `my_robot_nodes`

---

## Running and Checking Each Step

Make sure to source the workspace in every new terminal before running commands:
```bash
source /opt/ros/$ROS_DISTRO/setup.bash
source ~/ros2_ws/install/setup.bash
```

### Step 1: Depth Camera and IMU Validation

1. **Inspect robot model in RViz:**
   ```bash
   ros2 launch diffdrive_bot display.launch.py
   ```
   *Verify:* The depth camera appears on the back face of the robot, turned $180^\circ$ ($\pi$ rad) about the z-axis. The `depth_camera_link` and `imu_link` frames are present in the TF tree.

2. **Verify link transforms:**
   ```bash
   ros2 run tf2_ros tf2_echo base_link depth_camera_link
   ```
   *Expected Output:*
   - Translation: `[-0.215, 0.000, 0.000]` m (0.215 m behind the chassis center)
   - Rotation: in RPY (degree) `[0, 0, 180]` (RPY radians: `[0, 0, 3.142]`)

   ```bash
   ros2 run tf2_ros tf2_echo base_link imu_link
   ```
   *Expected Output:* Translation `[0, 0, 0]`, Rotation `[0, 0, 0]`.

3. **Start Gazebo simulation and check sensor topics:**
   ```bash
   ros2 launch diffdrive_bot gazebo.launch.py
   ```
   In separate terminals:
   - IMU publication rate (~50 Hz):
     ```bash
     ros2 topic hz /imu
     ```
   - IMU gravity and angular velocity readings:
     ```bash
     ros2 topic echo /imu
     ```
     (Reports `linear_acceleration.z ≈ 9.8 m/s^2` at rest).
   - Depth camera image & point cloud:
     ```bash
     ros2 topic echo /depth_camera/image --once
     ros2 topic hz /depth_camera/points
     ```

---

### Step 2, 3, 4, 5: `turn_away` Node

Start the simulation and detector in Terminal 1:
```bash
ros2 launch diffdrive_bot control.launch.py
```

In Terminal 2, start the `turn_away` node:
```bash
ros2 run my_robot_nodes turn_away
```

1. **Step 4 Check - Status publication:**
   In Terminal 3:
   ```bash
   ros2 topic echo /robot_status
   ```
   Initially, the state is `"stopped"` because the node starts switched off.

2. **Step 5 Check - Enable node via service:**
   ```bash
   ros2 service call /turn_away_enable std_srvs/srv/SetBool "{data: true}"
   ```
   The robot starts driving forward (`state: "forward"`). When approaching an obstacle, it stops linear motion and turns away on the spot (`state: "turning"`).

3. **Step 3 & 5 Check - Dynamic parameter & speed service:**
   Change forward speed dynamically via ROS 2 parameter:
   ```bash
   ros2 param set /turn_away forward_speed 0.4
   ```
   Call `/set_turn_speed` to test acceptance and validation:
   ```bash
   # Valid speed (accepted):
   ros2 service call /set_turn_speed my_robot_interfaces/srv/SetTurnSpeed "{turn_speed: 1.0}"

   # Speed exceeding max_turn_speed 1.5 rad/s (rejected):
   ros2 service call /set_turn_speed my_robot_interfaces/srv/SetTurnSpeed "{turn_speed: 3.0}"

   # Disable node and stop:
   ros2 service call /turn_away_enable std_srvs/srv/SetBool "{data: false}"
   ```

---

### Step 6: `rotate_server` Action Server

Start the simulation environment:
```bash
ros2 launch diffdrive_bot gazebo.launch.py
```

In Terminal 2, run the rotate action server:
```bash
ros2 run my_robot_nodes rotate_server
```

In Terminal 3, send a rotation goal (e.g., $1.57$ rad left):
```bash
ros2 action send_goal --feedback /rotate my_robot_interfaces/action/Rotate "{angle: 1.57}"
```
*Expected Output:*
The feedback increments progressively up to approximately $1.57$ rad, at which point the robot stops and the action reports success with the total radians turned.

---

### Step 7: Autonomous Square Driving

Launch the complete system in one command:
```bash
ros2 launch my_robot_nodes square.launch.py side_length:=0.8
```

The launch file loads Gazebo, RViz, bridge, `obstacle_detector`, `drive_distance_server`, `rotate_server`, and starts `square_driver`. The robot systematically executes:
1. Side 1: Drive forward 0.8 m $\rightarrow$ Rotate left 90°
2. Side 2: Drive forward 0.8 m $\rightarrow$ Rotate left 90°
3. Side 3: Drive forward 0.8 m $\rightarrow$ Rotate left 90°
4. Side 4: Drive forward 0.8 m $\rightarrow$ Rotate left 90°

At the conclusion, the robot returns accurately to its starting pose and logs completion.

To inspect node and topic graph while running:
```bash
rqt_graph
```

---

## Technical Notes & Observations

1. **Odometry Angle Wrapping in Rotation:**
   Directly subtracting start yaw from current yaw fails when turning past $\pm\pi$ (e.g. from $3.14$ to $-3.14$). In `rotate_server`, incremental yaw changes ($\Delta\theta = \text{atan2}(\sin(\theta_k - \theta_{k-1}), \cos(\theta_k - \theta_{k-1}))$) are integrated across successive odometry callbacks, guaranteeing seamless 360° continuity.

2. **Multi-Threaded Execution:**
   Action execution loops block the thread while running. If odometry subscriptions are handled on the same thread, odometry updates freeze. `rotate_server` employs a `MultiThreadedExecutor` and a `ReentrantCallbackGroup` so that `/odom` callbacks execute concurrently with the action loop.

3. **Gazebo Harmonic IMU System Plugin:**
   Gazebo Harmonic requires explicit loading of the `gz-sim-imu-system` in `worlds/obstacles.sdf`. Without this system plugin, IMU sensor links exist in the scene graph but emit no data.
