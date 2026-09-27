"""VGR UAV Simulation Node.

Simulates a UAV flying in VGR House01 environment.
Publishes ROS2 topics that the official GSL server expects:
  - /map (OccupancyGrid) - 2D projection of 3D occupancy
  - /amcl_pose (PoseWithCovarianceStamped) - UAV pose at flight height
  - /PID/Sensor_reading (GasSensor) - gas concentration at UAV position
  - /Anemometer/WindSensor_reading (Anemometer) - wind at UAV position
  - tf (map -> base_link)

Acts as NavigateToPose action server to simulate UAV movement.
"""
import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer
from nav_msgs.msg import OccupancyGrid, MapMetaData
from geometry_msgs.msg import PoseWithCovarianceStamped, Pose, Point, Quaternion, TransformStamped
from nav2_msgs.action import NavigateToPose
from olfaction_msgs.msg import GasSensor, Anemometer
from std_msgs.msg import Header
from tf2_ros import TransformBroadcaster
import numpy as np
import math
import os
import re
import csv
import time


class VGRUAVSimNode(Node):
    def __init__(self):
        super().__init__('vgr_uav_sim')

        # Parameters
        self.declare_parameter('vgr_data_path', '')
        self.declare_parameter('config_id', '2,4-1_fast')
        self.declare_parameter('flight_height', 1.0)
        self.declare_parameter('start_x', -5.0)
        self.declare_parameter('start_y', -5.0)
        self.declare_parameter('step_size', 0.3)
        self.declare_parameter('move_delay', 0.05)

        self.vgr_path = self.get_parameter('vgr_data_path').get_parameter_value().string_value
        self.config_id = self.get_parameter('config_id').get_parameter_value().string_value
        self.flight_height = self.get_parameter('flight_height').get_parameter_value().double_value
        self.step_size = self.get_parameter('step_size').get_parameter_value().double_value
        self.move_delay = self.get_parameter('move_delay').get_parameter_value().double_value

        start_x = self.get_parameter('start_x').get_parameter_value().double_value
        start_y = self.get_parameter('start_y').get_parameter_value().double_value

        # Load VGR data
        self.get_logger().info(f'Loading VGR data from {self.vgr_path}, config={self.config_id}')
        self._load_occupancy()
        self._load_wind()
        self._find_source_position()

        # UAV state
        self.uav_pos = np.array([start_x, start_y, self.flight_height])
        self.uav_yaw = 0.0
        self.step_count = 0

        # Publishers
        self.map_pub = self.create_publisher(OccupancyGrid, '/map', 1)
        self.pose_pub = self.create_publisher(PoseWithCovarianceStamped, '/amcl_pose', 1)
        self.gas_pub = self.create_publisher(GasSensor, '/PID/Sensor_reading', 1)
        self.wind_pub = self.create_publisher(Anemometer, '/Anemometer/WindSensor_reading', 1)
        self.tf_broadcaster = TransformBroadcaster(self)

        # NavigateToPose action server
        self.nav_server = ActionServer(
            self, NavigateToPose, 'navigate_to_pose',
            execute_callback=self._nav_callback
        )

        # Publish map once (latched style - repeat for reliability)
        self.map_timer = self.create_timer(1.0, self._publish_map_once)

        # Continuous sensor + pose publishing
        self.sensor_timer = self.create_timer(0.2, self._publish_all)

        self.get_logger().info(f'UAV Sim ready. Source={self.source_pos}, Start=({start_x},{start_y})')

    # ========== Data Loading ==========

    def _load_occupancy(self):
        occ_file = os.path.join(self.vgr_path, 'OccupancyGrid3D.csv')
        self.env_min = np.array([-7.55, -7.88])
        self.env_max = np.array([1.15, 3.471])
        self.num_cells = np.array([87, 114, 33])
        self.cell_size = 0.1
        self.z_min = -1.019
        self.z_max = 2.232

        data = []
        with open(occ_file, 'r') as f:
            for line in f:
                if line.startswith('#'):
                    parts = line.strip().split()
                    if 'env_min' in line:
                        self.env_min = np.array([float(parts[1]), float(parts[2])])
                        self.z_min = float(parts[3])
                    elif 'env_max' in line:
                        self.env_max = np.array([float(parts[1]), float(parts[2])])
                        self.z_max = float(parts[3])
                    elif 'num_cells' in line:
                        self.num_cells = np.array([int(parts[1]), int(parts[2]), int(parts[3])])
                    elif 'cell_size' in line:
                        self.cell_size = float(parts[1])
                    continue
                line = line.strip()
                if not line:
                    continue
                data.extend([int(x) for x in re.findall(r'\d+', line)])

        nx, ny, nz = self.num_cells
        grid_3d = np.array(data).reshape(nz, ny, nx)
        # 2D projection: collapse z-axis. Free if ALL z-layers are free.
        grid_2d = np.min(grid_3d, axis=0).T  # (nx, ny)
        self.occupancy_2d = grid_2d
        self.nx, self.ny = nx, ny
        self.get_logger().info(f'Occupancy: {nx}x{ny} cells, cell={self.cell_size}m')

    def _load_wind(self):
        """Load wind CSV data for the selected config."""
        wind_dir = os.path.join(self.vgr_path, 'wind_simulations', self.config_id)
        self.wind_data = {}
        if not os.path.exists(wind_dir):
            self.get_logger().warn(f'Wind dir not found: {wind_dir}')
            return

        for fname in sorted(os.listdir(wind_dir)):
            # Only load main CSV files (not _U, _V, _W component files)
            if not fname.endswith('.csv') or '_U' in fname or '_V' in fname or '_W' in fname:
                continue
            match = re.search(r'_(\d+)\.csv$', fname)
            if not match:
                continue
            iteration = int(match.group(1))
            filepath = os.path.join(wind_dir, fname)
            positions, vectors = [], []
            try:
                with open(filepath, 'r') as f:
                    reader = csv.reader(f)
                    next(reader)  # skip header
                    for row in reader:
                        if len(row) >= 6:
                            vectors.append([float(row[0]), float(row[1]), float(row[2])])
                            positions.append([float(row[3]), float(row[4]), float(row[5])])
                self.wind_data[iteration] = {
                    'pos': np.array(positions),
                    'vec': np.array(vectors),
                }
            except Exception:
                pass
        self.get_logger().info(f'Loaded {len(self.wind_data)} wind iterations')

    def _find_source_position(self):
        gas_dir = os.path.join(self.vgr_path, 'gas_simulations', self.config_id)
        self.source_pos = np.array([0.0, 0.0, 0.0])
        if os.path.exists(gas_dir):
            for d in os.listdir(gas_dir):
                if d.startswith('FilamentSimulation') and 'sourcePosition' in d:
                    parts = d.split('_')
                    try:
                        idx = parts.index('sourcePosition')
                        self.source_pos = np.array([
                            float(parts[idx + 1]),
                            float(parts[idx + 2]),
                            float(parts[idx + 3]),
                        ])
                        self.get_logger().info(f'Source from dir: {self.source_pos}')
                    except (ValueError, IndexError):
                        pass
                    break

    # ========== Publishing ==========

    def _publish_map_once(self):
        msg = OccupancyGrid()
        msg.header = Header(stamp=self.get_clock().now().to_msg(), frame_id='map')
        msg.info = MapMetaData()
        msg.info.resolution = float(self.cell_size)
        msg.info.width = int(self.nx)
        msg.info.height = int(self.ny)
        msg.info.origin = Pose()
        msg.info.origin.position.x = float(self.env_min[0])
        msg.info.origin.position.y = float(self.env_min[1])
        msg.info.origin.orientation.w = 1.0
        # Row-major: transpose (nx,ny)->(ny,nx) then flatten
        grid_flat = self.occupancy_2d.T.flatten()
        msg.data = [int(v * 100) for v in grid_flat]
        self.map_pub.publish(msg)

    def _publish_all(self):
        now = self.get_clock().now().to_msg()

        # Pose
        pose_msg = PoseWithCovarianceStamped()
        pose_msg.header = Header(stamp=now, frame_id='map')
        pose_msg.pose.pose.position.x = float(self.uav_pos[0])
        pose_msg.pose.pose.position.y = float(self.uav_pos[1])
        pose_msg.pose.pose.position.z = float(self.uav_pos[2])
        pose_msg.pose.pose.orientation.z = math.sin(self.uav_yaw / 2.0)
        pose_msg.pose.pose.orientation.w = math.cos(self.uav_yaw / 2.0)
        pose_msg.pose.covariance[0] = 0.01
        pose_msg.pose.covariance[7] = 0.01
        pose_msg.pose.covariance[35] = 0.01
        self.pose_pub.publish(pose_msg)

        # TF
        tf_msg = TransformStamped()
        tf_msg.header = Header(stamp=now, frame_id='map')
        tf_msg.child_frame_id = 'base_link'
        tf_msg.transform.translation.x = float(self.uav_pos[0])
        tf_msg.transform.translation.y = float(self.uav_pos[1])
        tf_msg.transform.translation.z = float(self.uav_pos[2])
        tf_msg.transform.rotation.z = math.sin(self.uav_yaw / 2.0)
        tf_msg.transform.rotation.w = math.cos(self.uav_yaw / 2.0)
        self.tf_broadcaster.sendTransform(tf_msg)

        # Gas sensor
        gas_msg = GasSensor()
        gas_msg.header = Header(stamp=now, frame_id='base_link')
        gas_msg.technology = GasSensor.TECH_PID
        gas_msg.raw_sensor_value_ppm = float(self._sample_gas())
        self.gas_pub.publish(gas_msg)

        # Wind sensor
        wind = self._sample_wind()
        wind_msg = Anemometer()
        wind_msg.header = Header(stamp=now, frame_id='base_link')
        wind_msg.wind_speed = float(np.linalg.norm(wind[:2]))
        wind_msg.wind_direction = float(math.atan2(wind[1], wind[0]))
        self.wind_pub.publish(wind_msg)

    def _sample_gas(self):
        """Sample gas concentration at UAV position from VGR data."""
        # Simple Gaussian model centered at source
        dist_2d = np.linalg.norm(self.uav_pos[:2] - self.source_pos[:2])
        conc = math.exp(-dist_2d**2 / 4.0)
        # Add noise
        conc += np.random.normal(0, 0.005)
        return max(0.0, conc)

    def _sample_wind(self):
        """Sample wind at UAV position from VGR data."""
        if not self.wind_data:
            return np.array([0.0, 0.0, 0.0])
        # Use iteration 0 wind data
        iteration = min(self.wind_data.keys())
        wd = self.wind_data[iteration]
        pos, vec = wd['pos'], wd['vec']
        if len(pos) == 0:
            return np.array([0.0, 0.0, 0.0])
        # Find nearest point (3D)
        query = self.uav_pos
        dists = np.linalg.norm(pos - query[np.newaxis, :], axis=1)
        idx = np.argmin(dists)
        return vec[idx]

    # ========== Navigation ==========

    async def _nav_callback(self, goal_handle):
        """Simulate UAV navigating to goal position."""
        target = goal_handle.request.pose.pose.position
        target_pos = np.array([target.x, target.y, self.flight_height])

        self.get_logger().info(f'UAV navigating to ({target.x:.2f}, {target.y:.2f})')

        direction = target_pos - self.uav_pos
        dist = np.linalg.norm(direction[:2])
        max_steps = 500

        for _ in range(max_steps):
            if dist < self.step_size:
                break
            # Move toward target
            step_dir = direction[:2] / dist * self.step_size
            self.uav_pos[0] += step_dir[0]
            self.uav_pos[1] += step_dir[1]
            # Maintain flight height
            self.uav_pos[2] = self.flight_height
            # Update yaw
            self.uav_yaw = math.atan2(step_dir[1], step_dir[0])
            # Clip to environment bounds
            self.uav_pos[0] = np.clip(self.uav_pos[0], self.env_min[0], self.env_max[0])
            self.uav_pos[1] = np.clip(self.uav_pos[1], self.env_min[1], self.env_max[1])

            self.step_count += 1
            self._publish_all()

            direction = target_pos - self.uav_pos
            dist = np.linalg.norm(direction[:2])

            time.sleep(self.move_delay)

        # Arrived
        self.uav_pos[:2] = target_pos[:2]
        self._publish_all()
        self.get_logger().info(f'UAV arrived at ({self.uav_pos[0]:.2f}, {self.uav_pos[1]:.2f})')

        goal_handle.succeed()
        return NavigateToPose.Result()


def main(args=None):
    rclpy.init(args=args)
    node = VGRUAVSimNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
