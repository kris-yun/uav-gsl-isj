"""VGR UAV Simulation Node v2 - Deterministic GADEN replay.

Fixes all fatal issues from v1:
A: Uses getConcentration(iteration, location) directly - deterministic iteration access
B: Gas and wind use the SAME iteration index
C: Wind direction published in map frame (not base_link)
D: Navigation checks obstacles via checkPositionForObstacles(), no teleportation
E: 2D occupancy built from fixed altitude slice, not min across all heights
F: Deterministic iteration stepping
"""
import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer
from rclpy.qos import QoSProfile, DurabilityPolicy
from nav_msgs.msg import OccupancyGrid, MapMetaData, Path
from geometry_msgs.msg import PoseWithCovarianceStamped, Pose, PoseStamped, TransformStamped
from nav2_msgs.action import NavigateToPose
from olfaction_msgs.msg import GasSensor, Anemometer
from std_msgs.msg import Header
from tf2_ros import TransformBroadcaster

CPTP_AVAILABLE = False
try:
    from nav2_msgs.action import ComputePathToPose
    CPTP_AVAILABLE = True
except ImportError:
    pass

import numpy as np
import math
from collections import deque
import os
import time

GADEN_AVAILABLE = False
try:
    from gadentools.Simulation import Simulation as GadenSim
    from gadentools.Utils import Vector3 as GVec
    GADEN_AVAILABLE = True
except ImportError:
    pass

from .sensor_model import SensorModel


class VGRUAVSimNode(Node):
    def __init__(self):
        super().__init__('vgr_uav_sim')

        self.declare_parameter('vgr_data_path', '')
        self.declare_parameter('config_id', '2,4-1_fast')
        self.declare_parameter('flight_height', 0.3)
        self.declare_parameter('start_x', -5.0)
        self.declare_parameter('start_y', -5.0)
        self.declare_parameter('step_size', 0.3)
        self.declare_parameter('move_delay', 0.05)
        self.declare_parameter('max_uav_speed', 1.5)
        self.declare_parameter('seed', 0)
        self.declare_parameter('sensor_model_mode', 'dynamic')
        self.declare_parameter('gaden_iteration_mode', 'seeded_time_replay')
        self.declare_parameter('sensor_trace_file', '')
        self.declare_parameter('wind_trace_file', '')
        self.declare_parameter('pose_trace_file', '')
        self.declare_parameter('sim_dt_s', 0.2)

        self.vgr_path = self.get_parameter('vgr_data_path').get_parameter_value().string_value
        self.config_id = self.get_parameter('config_id').get_parameter_value().string_value
        self.flight_height = self.get_parameter('flight_height').get_parameter_value().double_value
        self.step_size = self.get_parameter('step_size').get_parameter_value().double_value
        self.move_delay = self.get_parameter('move_delay').get_parameter_value().double_value
        self.max_uav_speed = self.get_parameter('max_uav_speed').get_parameter_value().double_value

        start_x = self.get_parameter('start_x').get_parameter_value().double_value
        start_y = self.get_parameter('start_y').get_parameter_value().double_value

        self.seed = int(self.get_parameter('seed').value)
        self.rng = np.random.default_rng(self.seed)
        self.sensor_model = SensorModel(mode=str(self.get_parameter('sensor_model_mode').value), seed=self.seed)
        self.sim_dt_s = float(self.get_parameter('sim_dt_s').value)
        self._sensor_trace_file = str(self.get_parameter('sensor_trace_file').value)
        self._wind_trace_file = str(self.get_parameter('wind_trace_file').value)
        self._pose_trace_file = str(self.get_parameter('pose_trace_file').value)
        self._trace_headers_written = False

        self.get_logger().info(f'Loading VGR data from {self.vgr_path}, config={self.config_id}')

        self._load_occupancy()
        self._load_gaden()

        self.uav_pos = np.array([start_x, start_y, self.flight_height])
        self.uav_yaw = 0.0
        self.step_count = 0
        self.total_distance = 0.0

        map_qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.map_pub = self.create_publisher(OccupancyGrid, '/map', map_qos)
        self.costmap_pub = self.create_publisher(OccupancyGrid, '/global_costmap/costmap', map_qos)
        self.pose_pub = self.create_publisher(PoseWithCovarianceStamped, '/amcl_pose', 1)
        self.gas_pub = self.create_publisher(GasSensor, '/PID/Sensor_reading', 1)
        self.wind_pub = self.create_publisher(Anemometer, '/Anemometer/WindSensor_reading', 1)
        self.tf_broadcaster = TransformBroadcaster(self)

        self.nav_server = ActionServer(self, NavigateToPose, 'navigate_to_pose',
                                       execute_callback=self._nav_callback)
        if CPTP_AVAILABLE:
            self.plan_server = ActionServer(self, ComputePathToPose, 'compute_path_to_pose',
                                            execute_callback=self._plan_callback)

        self.map_timer = self.create_timer(1.0, self._publish_map_once)
        self.sensor_timer = self.create_timer(0.2, self._publish_all)

        self.get_logger().info(f'UAV Sim v2 ready. Source={self.source_pos}, Start=({start_x},{start_y})')

    def _load_occupancy(self):
        occ_file = os.path.join(self.vgr_path, 'OccupancyGrid3D.csv')
        self.env_min = np.array([-7.55, -7.88])
        self.env_max = np.array([1.15, 3.471])
        self.num_cells = np.array([87, 114, 33])
        self.cell_size = 0.1
        self.z_min, self.z_max = -1.019, 2.232

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

        nx, ny, nz = int(self.num_cells[0]), int(self.num_cells[1]), int(self.num_cells[2])

        with open(occ_file, 'r') as f:
            all_lines = f.readlines()

        header_count = sum(1 for l in all_lines if l.startswith('#'))
        grid_3d = np.zeros((nz, nx, ny), dtype=int)
        z = 0
        row_in_layer = 0
        for i in range(header_count, len(all_lines)):
            line = all_lines[i].strip()
            if not line:
                if row_in_layer > 0:
                    z += 1
                    row_in_layer = 0
                continue
            if z >= nz:
                break
            vals = line.split()
            if len(vals) >= ny and row_in_layer < nx:
                grid_3d[z, row_in_layer, :] = [int(v) for v in vals[:ny]]
                row_in_layer += 1

        z_idx = int((self.flight_height - self.z_min) / self.cell_size)
        z_idx = max(0, min(z_idx, nz - 1))
        grid_2d = grid_3d[z_idx, :, :].T

        self.nx, self.ny = grid_2d.shape
        self.occupancy_2d = grid_2d.astype(np.float32)
        self.occupancy_3d = grid_3d

        self.get_logger().info(f'Occupancy: {self.nx}x{self.ny} 2D slice at z_idx={z_idx} (z={self.flight_height}m)')

    def _load_gaden(self):
        if not GADEN_AVAILABLE:
            self.get_logger().error('GADEN not available!')
            return

        gas_base = os.path.join(self.vgr_path, 'gas_simulations', self.config_id)
        gas_dirs = [d for d in os.listdir(gas_base) if d.startswith('FilamentSimulation')]
        if not gas_dirs:
            self.get_logger().error(f'No gas simulation found in {gas_base}')
            return

        gas_dir = os.path.join(gas_base, gas_dirs[0])
        occ_file = os.path.join(self.vgr_path, 'OccupancyGrid3D.csv')

        self.gaden_sim = GadenSim(gas_dir, occ_file)
        self.source_pos = np.array([self.gaden_sim.source_position.x,
                                     self.gaden_sim.source_position.y,
                                     self.gaden_sim.source_position.z])

        self.max_iteration = 0
        for fname in os.listdir(gas_dir):
            if fname.startswith('iteration_'):
                try:
                    idx = int(fname.split('_')[1])
                    self.max_iteration = max(self.max_iteration, idx)
                except ValueError:
                    pass

        self._load_wind_csv()

        self.get_logger().info(f'GADEN loaded. Source={self.source_pos}, max_iteration={self.max_iteration}')
        self.get_logger().info(f'Wind iterations: {len(self.wind_iterations)}')

    def _load_wind_csv(self):
        import csv
        wind_base = os.path.join(self.vgr_path, 'wind_simulations', self.config_id)
        self.wind_iterations = []
        if not os.path.exists(wind_base):
            self.get_logger().warn(f'Wind data not found at {wind_base}')
            return

        csv_files = sorted([f for f in os.listdir(wind_base)
                           if f.endswith('.csv') and not any(f.endswith(s) for s in ['_U', '_V', '_W'])])

        for csv_file in csv_files:
            filepath = os.path.join(wind_base, csv_file)
            u_list, v_list, w_list, x_list, y_list, z_list = [], [], [], [], [], []
            try:
                with open(filepath, 'r') as f:
                    reader = csv.reader(f)
                    next(reader)
                    for row in reader:
                        if len(row) >= 6:
                            u_list.append(float(row[0]))
                            v_list.append(float(row[1]))
                            w_list.append(float(row[2]))
                            x_list.append(float(row[3]))
                            y_list.append(float(row[4]))
                            z_list.append(float(row[5]))
                self.wind_iterations.append({
                    'u': np.array(u_list), 'v': np.array(v_list), 'w': np.array(w_list),
                    'x': np.array(x_list), 'y': np.array(y_list), 'z': np.array(z_list),
                })
            except Exception as e:
                self.get_logger().warn(f'Failed to load {csv_file}: {e}')

    def _get_iteration_for_step(self):
        if self.max_iteration <= 0:
            return 0
        mode = str(self.get_parameter('gaden_iteration_mode').value)
        if mode == 'fixed_debug':
            return min(1500, self.max_iteration)
        if mode == 'seeded_time_replay':
            usable = max(1, self.max_iteration - 1)
            offset = (7919 * (self.seed + 1)) % usable
            return int((offset + self.step_count) % usable)
        raise ValueError(f'unknown gaden_iteration_mode={mode}')

    def _get_wind_at_position(self, iteration):
        if not self.wind_iterations:
            return np.array([0.0, 0.0, 0.0])
        iter_idx = min(iteration, len(self.wind_iterations) - 1)
        wind_data = self.wind_iterations[iter_idx]
        dx = wind_data['x'] - self.uav_pos[0]
        dy = wind_data['y'] - self.uav_pos[1]
        dz = wind_data['z'] - self.uav_pos[2]
        dist = np.sqrt(dx**2 + dy**2 + dz**2)
        nearest_idx = np.argmin(dist)
        return np.array([wind_data['u'][nearest_idx], wind_data['v'][nearest_idx], wind_data['w'][nearest_idx]])

    def _sample_gas(self):
        if not GADEN_AVAILABLE or not hasattr(self, 'gaden_sim'):
            true_gas = 0.0
            iteration = 0
        else:
            iteration = self._get_iteration_for_step()
            pos = GVec(self.uav_pos[0], self.uav_pos[1], self.uav_pos[2])
            try:
                true_gas = float(self.gaden_sim.getConcentration(iteration, pos))
            except Exception as e:
                self.get_logger().warn(f'getConcentration error: {e}')
                true_gas = 0.0
        measured = self.sensor_model.process(true_gas, self.sim_dt_s)
        self._append_sensor_trace(iteration, true_gas, measured)
        return measured

    def _sample_wind(self):
        iteration = self._get_iteration_for_step()
        return self._get_wind_at_position(iteration)

    def _append_sensor_trace(self, iteration, true_gas, measured):
        if not self._sensor_trace_file:
            return
        import csv as _csv
        if not self._trace_headers_written:
            os.makedirs(os.path.dirname(self._sensor_trace_file), exist_ok=True)
            with open(self._sensor_trace_file, 'w', newline='') as f:
                w = _csv.writer(f)
                w.writerow(['t_ros_s','step','iteration','x','y','z','true_gas_ppm','measured_gas_ppm','sensor_mode','seed'])
            if self._wind_trace_file:
                os.makedirs(os.path.dirname(self._wind_trace_file), exist_ok=True)
                with open(self._wind_trace_file, 'w', newline='') as f:
                    w = _csv.writer(f)
                    w.writerow(['t_ros_s','step','iteration','x','y','z','wind_u','wind_v','wind_w','wind_speed','wind_direction_rad','seed'])
            if self._pose_trace_file:
                os.makedirs(os.path.dirname(self._pose_trace_file), exist_ok=True)
                with open(self._pose_trace_file, 'w', newline='') as f:
                    w = _csv.writer(f)
                    w.writerow(['t_ros_s','step','x','y','z','yaw','seed'])
            self._trace_headers_written = True
        t_ros = self.get_clock().now().nanoseconds / 1e9
        with open(self._sensor_trace_file, 'a', newline='') as f:
            w = _csv.writer(f)
            w.writerow([f'{t_ros:.3f}', self.step_count, iteration,
                       f'{self.uav_pos[0]:.4f}', f'{self.uav_pos[1]:.4f}', f'{self.uav_pos[2]:.4f}',
                       f'{true_gas:.6f}', f'{measured:.6f}', self.sensor_model.cfg.mode, self.seed])

    def _append_wind_trace(self, iteration, wind):
        if not self._wind_trace_file:
            return
        import csv as _csv
        t_ros = self.get_clock().now().nanoseconds / 1e9
        ws = float(np.linalg.norm(wind[:2]))
        wd = float(math.atan2(wind[1], wind[0]))
        with open(self._wind_trace_file, 'a', newline='') as f:
            w = _csv.writer(f)
            w.writerow([f'{t_ros:.3f}', self.step_count, iteration,
                       f'{self.uav_pos[0]:.4f}', f'{self.uav_pos[1]:.4f}', f'{self.uav_pos[2]:.4f}',
                       f'{wind[0]:.6f}', f'{wind[1]:.6f}', f'{wind[2]:.6f}',
                       f'{ws:.6f}', f'{wd:.6f}', self.seed])

    def _append_pose_trace(self):
        if not self._pose_trace_file:
            return
        import csv as _csv
        t_ros = self.get_clock().now().nanoseconds / 1e9
        with open(self._pose_trace_file, 'a', newline='') as f:
            w = _csv.writer(f)
            w.writerow([f'{t_ros:.3f}', self.step_count,
                       f'{self.uav_pos[0]:.4f}', f'{self.uav_pos[1]:.4f}', f'{self.uav_pos[2]:.4f}',
                       f'{self.uav_yaw:.4f}', self.seed])


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
        grid_flat = self.occupancy_2d.T.flatten()
        msg.data = [int(v * 100) for v in grid_flat]
        self.map_pub.publish(msg)
        self.costmap_pub.publish(msg)

    def _publish_all(self):
        now = self.get_clock().now().to_msg()

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

        tf_msg = TransformStamped()
        tf_msg.header = Header(stamp=now, frame_id='map')
        tf_msg.child_frame_id = 'base_link'
        tf_msg.transform.translation.x = float(self.uav_pos[0])
        tf_msg.transform.translation.y = float(self.uav_pos[1])
        tf_msg.transform.translation.z = float(self.uav_pos[2])
        tf_msg.transform.rotation.z = math.sin(self.uav_yaw / 2.0)
        tf_msg.transform.rotation.w = math.cos(self.uav_yaw / 2.0)
        self.tf_broadcaster.sendTransform(tf_msg)

        gas_msg = GasSensor()
        gas_msg.header = Header(stamp=now, frame_id='base_link')
        gas_msg.technology = GasSensor.TECH_PID
        gas_msg.raw_units = GasSensor.UNITS_PPM
        gas_msg.raw = float(self._sample_gas())
        self.gas_pub.publish(gas_msg)

        wind = self._sample_wind()
        iteration = self._get_iteration_for_step()
        self._append_wind_trace(iteration, wind)
        self._append_pose_trace()
        wind_msg = Anemometer()
        wind_msg.header = Header(stamp=now, frame_id='map')
        wind_msg.wind_speed = float(np.linalg.norm(wind[:2]))
        wind_msg.wind_direction = float(math.atan2(wind[1], wind[0]))
        self.wind_pub.publish(wind_msg)

        self.step_count += 1

    def _is_position_free(self, x, y):
        ix = int((x - self.env_min[0]) / self.cell_size)
        iy = int((y - self.env_min[1]) / self.cell_size)
        if 0 <= ix < self.nx and 0 <= iy < self.ny:
            return self.occupancy_2d[ix, iy] == 0
        return False

    def _bfs_path(self, start_world, goal_world):
        """BFS on 2D occupancy grid."""
        def to_grid(wx, wy):
            return int((wx - self.env_min[0]) / self.cell_size), int((wy - self.env_min[1]) / self.cell_size)
        def to_world(ix, iy):
            return self.env_min[0] + (ix + 0.5) * self.cell_size, self.env_min[1] + (iy + 0.5) * self.cell_size
        sx, sy = to_grid(start_world[0], start_world[1])
        gx, gy = to_grid(goal_world[0], goal_world[1])
        sx = max(0, min(sx, self.nx - 1))
        sy = max(0, min(sy, self.ny - 1))
        gx = max(0, min(gx, self.nx - 1))
        gy = max(0, min(gy, self.ny - 1))
        if self.occupancy_2d[gx, gy] != 0:
            best_dist = float("inf")
            best_cell = None
            for ddx in range(-5, 6):
                for ddy in range(-5, 6):
                    cx, cy = gx + ddx, gy + ddy
                    if 0 <= cx < self.nx and 0 <= cy < self.ny and self.occupancy_2d[cx, cy] == 0:
                        d = ddx*ddx + ddy*ddy
                        if d < best_dist:
                            best_dist = d
                            best_cell = (cx, cy)
            if best_cell is None: return []
            gx, gy = best_cell
        if self.occupancy_2d[sx, sy] != 0: return []
        from collections import deque
        visited = set()
        parent = {}
        queue = deque([(sx, sy)])
        visited.add((sx, sy))
        found = False
        while queue:
            cx, cy = queue.popleft()
            if cx == gx and cy == gy:
                found = True
                break
            for ddx, ddy in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
                nx_, ny_ = cx + ddx, cy + ddy
                if 0 <= nx_ < self.nx and 0 <= ny_ < self.ny and (nx_, ny_) not in visited and self.occupancy_2d[nx_, ny_] == 0:
                    visited.add((nx_, ny_))
                    parent[(nx_, ny_)] = (cx, cy)
                    queue.append((nx_, ny_))
        if not found: return []
        path_cells = []
        cell = (gx, gy)
        while cell != (sx, sy):
            path_cells.append(cell)
            cell = parent[cell]
        path_cells.append((sx, sy))
        path_cells.reverse()
        subsampled = [path_cells[j] for j in range(0, len(path_cells), 3)]
        if subsampled[-1] != path_cells[-1]: subsampled.append(path_cells[-1])
        return [to_world(cx, cy) for cx, cy in subsampled]

    async def _plan_callback(self, goal_handle):
        gx = goal_handle.request.goal.pose.position.x
        gy = goal_handle.request.goal.pose.position.y
        self.get_logger().warn(f"PLAN_CB: called with goal=({gx:.2f},{gy:.2f})")
        goal = goal_handle.request.goal.pose.position
        start = self.uav_pos
        path = Path()
        path.header.frame_id = "map"
        path.header.stamp = self.get_clock().now().to_msg()
        world_path = self._bfs_path(start[:2], [goal.x, goal.y])
        for wx, wy in world_path:
            ps = PoseStamped()
            ps.header = path.header
            ps.pose.position.x = wx
            ps.pose.position.y = wy
            ps.pose.position.z = self.flight_height
            ps.pose.orientation.w = 1.0
            path.poses.append(ps)
        result = ComputePathToPose.Result()
        result.path = path
        self.get_logger().warn(f"PLAN_CB: returning {len(path.poses)} poses")
        goal_handle.succeed()
        return result




    async def _nav_callback(self, goal_handle):
        target = goal_handle.request.pose.pose.position
        target_z = target.z if abs(target.z) > 0.01 else self.flight_height
        target_pos = np.array([target.x, target.y, target_z])

        if not self._is_position_free(target.x, target.y):
            self.get_logger().warn(f'Target ({target.x:.2f}, {target.y:.2f}) is in obstacle')
            direction = target_pos - self.uav_pos
            dist = np.linalg.norm(direction[:2])
            if dist > 0:
                for t in np.arange(0.9, 0.0, -0.1):
                    check_pos = self.uav_pos + direction * t
                    if self._is_position_free(check_pos[0], check_pos[1]):
                        target_pos = check_pos
                        break
                else:
                    self._publish_all()
                    goal_handle.succeed()
                    return NavigateToPose.Result()

        self.get_logger().info(f'UAV navigating to ({target_pos[0]:.2f}, {target_pos[1]:.2f})')

        effective_step = min(self.step_size, self.max_uav_speed * self.move_delay)
        max_steps = 2000

        for _ in range(max_steps):
            direction = target_pos - self.uav_pos
            dist_xy = np.linalg.norm(direction[:2])
            if dist_xy < effective_step:
                break

            step_dir = direction[:2] / dist_xy * effective_step
            next_x = self.uav_pos[0] + step_dir[0]
            next_y = self.uav_pos[1] + step_dir[1]

            if not self._is_position_free(next_x, next_y):
                self.get_logger().warn(f'Obstacle at ({next_x:.2f}, {next_y:.2f}), stopping')
                break

            self.total_distance += effective_step
            self.uav_pos[0] = next_x
            self.uav_pos[1] = next_y
            self.uav_pos[2] = target_pos[2]  # respect algorithm altitude choice
            self.uav_yaw = math.atan2(step_dir[1], step_dir[0])
            self.uav_pos[0] = np.clip(self.uav_pos[0], self.env_min[0], self.env_max[0])
            self.uav_pos[1] = np.clip(self.uav_pos[1], self.env_min[1], self.env_max[1])
            self._publish_all()
            time.sleep(self.move_delay)

        self._publish_all()
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
