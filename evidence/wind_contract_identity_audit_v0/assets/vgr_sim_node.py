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
from rclpy.executors import ExternalShutdownException
from rclpy.task import Future
from rclpy.node import Node
from rclpy.action import ActionServer, GoalResponse
from rclpy.qos import QoSProfile, DurabilityPolicy
from nav_msgs.msg import OccupancyGrid, MapMetaData, Path
from geometry_msgs.msg import PoseWithCovarianceStamped, Pose, PoseStamped, TransformStamped
from nav2_msgs.action import NavigateToPose
from olfaction_msgs.msg import GasSensor, Anemometer
from std_msgs.msg import Header
from std_msgs.msg import Bool
from rosgraph_msgs.msg import Clock
from builtin_interfaces.msg import Time as TimeMsg
from tf2_ros import TransformBroadcaster
from gaden_msgs.srv import FrameQuery
from std_srvs.srv import Trigger, SetBool

CPTP_AVAILABLE = False
try:
    from nav2_msgs.action import ComputePathToPose
    CPTP_AVAILABLE = True
except ImportError:
    pass

import numpy as np
import math
import re
from collections import deque
import os
import time
import json
import subprocess

GADEN_AVAILABLE = False
try:
    from gadentools.Simulation import Simulation as GadenSim
    from gadentools.Utils import Vector3 as GVec
    GADEN_AVAILABLE = True
except ImportError:
    pass

from .sensor_model import SensorModel
from .sim_timebase import DeterministicTimebase
from .mcos_motion_profiles import MotionLimits, generate_profile


class FrameQueryWorker(Node):
    """Dedicated node so the simulation callback can synchronously obtain one atomic frame."""
    def __init__(self):
        super().__init__('vgr_gaden_frame_client')
        self.client = self.create_client(FrameQuery, 'frame_query')
        if not self.client.wait_for_service(timeout_sec=10.0):
            raise RuntimeError('gaden_player /frame_query unavailable; refusing legacy fallback')

    def query(self, iteration, position):
        request = FrameQuery.Request()
        request.iteration = int(iteration)
        request.x, request.y, request.z = map(float, position)
        future = self.client.call_async(request)
        rclpy.spin_until_future_complete(self, future, timeout_sec=5.0)
        response = future.result() if future.done() else None
        if response is None or not response.valid:
            raise RuntimeError('gaden_player frame query failed: ' + (response.error_message if response else 'timeout'))
        wind = np.asarray([response.wind_u, response.wind_v, response.wind_w], dtype=float)
        if not np.isfinite(wind).all() or float(np.max(np.abs(wind))) > 1.0e4:
            raise RuntimeError(f'gaden_player returned invalid decoded wind: {wind.tolist()}')
        return float(response.concentration), wind

    def probe_domain(self, iteration):
        request = FrameQuery.Request()
        request.iteration = int(iteration)
        request.x = request.y = request.z = -1.0e9
        future = self.client.call_async(request)
        rclpy.spin_until_future_complete(self, future, timeout_sec=5.0)
        response = future.result() if future.done() else None
        if response is None:
            raise RuntimeError('gaden_player domain probe timed out')
        match = re.search(
            r'dimensions=\((\d+),(\d+),(\d+)\)\s+'
            r'min=\(([-+0-9.eE]+),([-+0-9.eE]+),([-+0-9.eE]+)\)\s+'
            r'cell_size=([-+0-9.eE]+)',
            response.error_message,
        )
        if response.valid or match is None:
            raise RuntimeError(
                'gaden_player domain probe returned an unexpected response: '
                + response.error_message
            )
        return {
            'dimensions': np.array(
                [int(match.group(1)), int(match.group(2)), int(match.group(3))],
                dtype=int,
            ),
            'min': np.array(
                [float(match.group(4)), float(match.group(5)), float(match.group(6))],
                dtype=float,
            ),
            'cell_size': float(match.group(7)),
        }



class RawQueryWorker:
    """Subprocess-backed raw snapshot query for H01 raw_house1_snapshot backend.

    Mirrors FrameQueryWorker.query(iteration, position) -> (concentration, wind),
    but reads the frozen GADEN snapshot through the compiled house1_raw_query
    executable instead of a live /frame_query service.
    """
    def __init__(self, executable, env_root, gas_results):
        if not executable or not os.path.isfile(executable):
            raise RuntimeError(f'raw_query_executable missing: {executable}')
        if not env_root or not os.path.isdir(env_root):
            raise RuntimeError(f'raw_env_root missing: {env_root}')
        if not gas_results or not os.path.isdir(gas_results):
            raise RuntimeError(f'raw_gas_results missing: {gas_results}')
        self._proc = subprocess.Popen(
            [executable, env_root, gas_results],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )

    def query(self, iteration, position):
        x, y, z = float(position[0]), float(position[1]), float(position[2])
        try:
            self._proc.stdin.write(f'{int(iteration)} {x} {y} {z}\n')
            self._proc.stdin.flush()
            line = self._proc.stdout.readline()
        except (BrokenPipeError, ValueError) as exc:
            raise RuntimeError(f'raw query subprocess failed: {exc}') from exc
        if not line:
            raise RuntimeError('raw query subprocess exited unexpectedly')
        parts = line.split()
        if len(parts) < 6 or parts[0] != 'OK':
            raise RuntimeError(f'raw query bad response: {line!r}')
        true_gas = float(parts[1])
        wind = np.array([float(parts[2]), float(parts[3]), float(parts[4])], dtype=float)
        if not np.isfinite(wind).all() or float(np.max(np.abs(wind))) > 1.0e4:
            raise RuntimeError(f'raw query returned invalid wind: {wind.tolist()}')
        return true_gas, wind



class VGRUAVSimNode(Node):
    def __init__(self):
        super().__init__('vgr_uav_sim')

        self.declare_parameter('vgr_data_path', '')
        self.declare_parameter('config_id', '2,4-1_fast')
        self.declare_parameter('flight_height', 0.3)
        self.declare_parameter('start_x', -5.0)
        self.declare_parameter('start_y', -5.0)
        self.declare_parameter('step_size', 0.3)
        self.declare_parameter('max_uav_speed', 1.5)
        self.declare_parameter('realtime_factor', 4.0)
        self.declare_parameter('allow_vertical_motion', False)
        self.declare_parameter('open_loop_profile', '')
        self.declare_parameter('motion_duration_s', 8.0)
        self.declare_parameter('motion_heading_rad', 0.0)
        self.declare_parameter('seed', 0)
        self.declare_parameter('sensor_model_mode', 'fopdt')
        self.declare_parameter('sensor_gain', 1.0)
        self.declare_parameter('sensor_baseline_ppm', 0.0)
        self.declare_parameter('sensor_tau_rise_s', 1.2)
        self.declare_parameter('sensor_tau_recovery_s', 1.2)
        self.declare_parameter('sensor_dead_time_s', 0.4)
        self.declare_parameter('sensor_noise_std_ppm', 0.0)
        self.declare_parameter('sensor_drift_rate_ppm_s', 0.0)
        self.declare_parameter('sensor_saturation_min_ppm', 0.0)
        self.declare_parameter('sensor_saturation_max_ppm', 1.0e6)
        self.declare_parameter('sensor_initial_state_ppm', 0.0)
        self.declare_parameter('sensor_initial_input_ppm', 0.0)
        self.declare_parameter('gaden_iteration_mode', 'seeded_time_replay')
        self.declare_parameter('gas_backend', 'gaden_player')
        self.declare_parameter('raw_query_executable', '/dev/shm/house1_raw_query')
        self.declare_parameter('raw_env_root', '')
        self.declare_parameter('raw_gas_results', '')
        self.declare_parameter('sensor_trace_file', '')
        self.declare_parameter('wind_trace_file', '')
        self.declare_parameter('pose_trace_file', '')
        self.declare_parameter('measurement_trace_file', '')
        self.declare_parameter('continuous_measurement_samples_file', '')
        self.declare_parameter('sensor_manifest_file', '')
        self.declare_parameter('sim_dt_s', 0.2)
        self.declare_parameter('sim_stop_at_s', -1.0)
        self.declare_parameter('nav_reduce_scale', 3)

        self.vgr_path = self.get_parameter('vgr_data_path').get_parameter_value().string_value
        self.config_id = self.get_parameter('config_id').get_parameter_value().string_value
        self.flight_height = self.get_parameter('flight_height').get_parameter_value().double_value
        self.step_size = self.get_parameter('step_size').get_parameter_value().double_value
        self.max_uav_speed = self.get_parameter('max_uav_speed').get_parameter_value().double_value
        self.realtime_factor = float(self.get_parameter('realtime_factor').value)
        self.allow_vertical_motion = bool(self.get_parameter('allow_vertical_motion').value)
        self.open_loop_profile_name = str(self.get_parameter('open_loop_profile').value)
        self.motion_duration_s = float(self.get_parameter('motion_duration_s').value)
        self.motion_heading_rad = float(self.get_parameter('motion_heading_rad').value)
        self.sim_dt_s = float(self.get_parameter('sim_dt_s').value)
        self.sim_stop_at_s = float(self.get_parameter('sim_stop_at_s').value)
        self.nav_reduce_scale = int(self.get_parameter('nav_reduce_scale').value)
        if self.sim_dt_s <= 0.0:
            raise ValueError('sim_dt_s must be positive')
        if self.realtime_factor <= 0.0:
            raise ValueError('realtime_factor must be positive')
        self.timebase = DeterministicTimebase(self.sim_dt_s, self.realtime_factor)
        self.wall_step_delay_s = self.timebase.wall_step_period_s

        start_x = self.get_parameter('start_x').get_parameter_value().double_value
        start_y = self.get_parameter('start_y').get_parameter_value().double_value

        self.seed = int(self.get_parameter('seed').value)
        self.rng = np.random.default_rng(self.seed)
        self.sensor_model = SensorModel(
            mode=str(self.get_parameter('sensor_model_mode').value),
            seed=self.seed,
            gain=float(self.get_parameter('sensor_gain').value),
            baseline=float(self.get_parameter('sensor_baseline_ppm').value),
            tau_rise_s=float(self.get_parameter('sensor_tau_rise_s').value),
            tau_recovery_s=float(self.get_parameter('sensor_tau_recovery_s').value),
            dead_time_s=float(self.get_parameter('sensor_dead_time_s').value),
            noise_std_ppm=float(self.get_parameter('sensor_noise_std_ppm').value),
            drift_rate_ppm_s=float(self.get_parameter('sensor_drift_rate_ppm_s').value),
            saturation_min_ppm=float(self.get_parameter('sensor_saturation_min_ppm').value),
            saturation_max_ppm=float(self.get_parameter('sensor_saturation_max_ppm').value),
            initial_state_ppm=float(self.get_parameter('sensor_initial_state_ppm').value),
            initial_input_ppm=float(self.get_parameter('sensor_initial_input_ppm').value),
        )
        self._sensor_trace_file = str(self.get_parameter('sensor_trace_file').value)
        self._wind_trace_file = str(self.get_parameter('wind_trace_file').value)
        self._pose_trace_file = str(self.get_parameter('pose_trace_file').value)
        self._measurement_trace_file = str(self.get_parameter('measurement_trace_file').value)
        self._continuous_measurement_samples_file = str(self.get_parameter('continuous_measurement_samples_file').value)
        self._sensor_manifest_file = str(self.get_parameter('sensor_manifest_file').value)
        self._trace_headers_written = False
        self.gas_backend = str(self.get_parameter('gas_backend').value)
        if self.gas_backend not in ('gaden_player', 'legacy_gadentools', 'raw_house1_snapshot'):
            raise ValueError(f'unsupported gas_backend={self.gas_backend}')
        self._frame_worker = FrameQueryWorker() if self.gas_backend == 'gaden_player' else None
        self._raw_query_worker = None
        self._frame_wind = np.zeros(3, dtype=float)

        self.get_logger().info(f'Loading VGR data from {self.vgr_path}, config={self.config_id}')

        self._load_occupancy()
        self._load_gaden()
        self._build_coarse_navigation_grid()
        self._write_sensor_manifest()

        self.uav_pos = np.array([start_x, start_y, self.flight_height])
        self.uav_yaw = 0.0
        self.step_count = 0
        self.t_sim_s = 0.0
        self.total_distance = 0.0
        self._last_trace_pos = self.uav_pos.copy()
        # Navigation callbacks never advance simulation time.  The single timer
        # below owns pose, gas, wind, FOPDT and /clock progression.
        self._nav_target = None
        self._nav_waypoints = []
        self._nav_final_target = None
        self._nav_goal_handle = None
        self._nav_completion_future = None
        self._nav_goal_prepared = False
        self.simulation_paused = True
        self.planner_paused = False
        self._last_advanced_step = 0
        self.open_loop_profile = self._prepare_open_loop_profile()
        self._initialize_trace_files()

        map_qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.map_pub = self.create_publisher(OccupancyGrid, '/map', map_qos)
        self.costmap_pub = self.create_publisher(OccupancyGrid, '/global_costmap/costmap', map_qos)
        self.pose_pub = self.create_publisher(PoseWithCovarianceStamped, '/amcl_pose', 1)
        self.gas_pub = self.create_publisher(GasSensor, '/PID/Sensor_reading', 1)
        self.wind_pub = self.create_publisher(Anemometer, '/Anemometer/WindSensor_reading', 1)
        self.clock_pub = self.create_publisher(Clock, '/clock', 10)
        self.tf_broadcaster = TransformBroadcaster(self)
        self.start_service = self.create_service(Trigger, 'start_simulation', self._start_simulation)
        self.pause_service = self.create_service(SetBool, 'set_simulation_paused', self._set_simulation_paused)
        self.create_subscription(Bool, 'opgsl_planner_busy', self._on_planner_busy, 1)

        self.nav_server = ActionServer(
            self,
            NavigateToPose,
            'navigate_to_pose',
            execute_callback=self._nav_callback,
            goal_callback=self._nav_goal_callback,
        )
        if CPTP_AVAILABLE:
            self.plan_server = ActionServer(self, ComputePathToPose, 'compute_path_to_pose',
                                            execute_callback=self._plan_callback)

        self.map_timer = self.create_timer(1.0, self._publish_map_once)
        self.sensor_timer = self.create_timer(self.wall_step_delay_s, self._simulation_tick)

        self.get_logger().info(
            f'UAV Sim v3 ready. Start=({start_x},{start_y}), '
            f'sim_dt={self.sim_dt_s:.3f}s, realtime_factor={self.realtime_factor:.2f}, '
            f'sensor={self.sensor_model.cfg.mode}, vertical_motion={self.allow_vertical_motion}, '
            f'open_loop_profile={self.open_loop_profile_name or "hover"}'
        )

    def _start_simulation(self, _request, response):
        self.simulation_paused = False
        response.success = True
        response.message = f'started at step={self.step_count}, t_sim={self.t_sim_s:.6f}'
        return response

    def _set_simulation_paused(self, request, response):
        self.simulation_paused = bool(request.data)
        response.success = True
        response.message = 'paused' if self.simulation_paused else 'resumed'
        return response

    def _on_planner_busy(self, message):
        self.planner_paused = bool(message.data)

    def _simulation_tick(self):
        # Paused state remains observable for deterministic readiness but never
        # advances time, sensor state, GADEN iteration or trace counters.
        advancing = not self.simulation_paused and not self.planner_paused
        # Keep ROS/action processing alive after the evidence horizon: freezing
        # the clock here can strand an in-flight NavigateToPose and prevent the
        # GSL terminal result from being emitted.  Close both the recorded and
        # published observation streams at the exact boundary so no gas/wind
        # evidence beyond the fixed budget can enter a measurement block.
        within_evidence_horizon = (
            self.sim_stop_at_s < 0.0 or self.t_sim_s < self.sim_stop_at_s
        )
        record = advancing and within_evidence_horizon
        publish_observation = (not advancing) or within_evidence_horizon
        self._publish_all(
            advance=advancing,
            record=record,
            publish_observation=publish_observation,
        )

    def _load_occupancy(self):
        import hashlib
        occ_file = os.path.join(self.vgr_path, 'OccupancyGrid3D.csv')
        with open(occ_file, 'rb') as f:
            occupancy_sha256 = hashlib.sha256(f.read()).hexdigest()
        with open(occ_file, 'r') as f:
            lines = f.readlines()

        env_min = env_max = num_cells = cell_size = None
        values = []
        for raw in lines:
            line = raw.strip()
            if not line or line == ';':
                continue
            if line.startswith('#env_min'):
                env_min = np.array([float(v) for v in line.split()[1:4]])
            elif line.startswith('#env_max'):
                env_max = np.array([float(v) for v in line.split()[1:4]])
            elif line.startswith('#num_cells'):
                num_cells = np.array([int(v) for v in line.split()[1:4]])
            elif line.startswith('#cell_size'):
                cell_size = float(line.split()[1])
            elif line.startswith('#'):
                continue
            else:
                row = [int(v) for v in line.split()]
                if any(v not in (0, 1, 2) for v in row):
                    raise RuntimeError(f'Unsupported occupancy value in {occ_file}')
                values.extend(row)

        if env_min is None or env_max is None or num_cells is None or cell_size is None:
            raise RuntimeError(f'Missing occupancy metadata in {occ_file}')
        nx, ny, nz = (int(v) for v in num_cells)
        expected_values = nx * ny * nz
        if len(values) != expected_values:
            raise RuntimeError(
                f'Occupancy value count mismatch in {occ_file}: '
                f'got {len(values)}, expected {expected_values}'
            )

        raw_grid_3d = np.asarray(values, dtype=np.uint8).reshape(nz, nx, ny)
        # GADEN occupancy uses 0 for free and non-zero values for blocked cells.
        # ROS OccupancyGrid must receive a binary 0/100 map, so normalize before
        # serialization rather than emitting invalid 200 values for raw value 2.
        grid_3d = (raw_grid_3d != 0).astype(np.uint8)
        z_idx = int((self.flight_height - env_min[2]) / cell_size)
        z_idx = max(0, min(z_idx, nz - 1))
        grid_2d = grid_3d[z_idx, :, :]
        obstacle_count = int(grid_2d.sum())
        free_count = int(grid_2d.size - obstacle_count)
        environment = str(getattr(self, 'environment_id', '')).lower()
        if ('house01' in environment or 'house03' in environment) and obstacle_count == 0:
            raise RuntimeError(f'All-free H01/H03 occupancy slice rejected: {occ_file}')

        self.env_min = env_min[:2]
        self.env_max = env_max[:2]
        self.z_min, self.z_max = float(env_min[2]), float(env_max[2])
        self.num_cells = num_cells
        self.cell_size = cell_size
        self.nx, self.ny = grid_2d.shape
        self.occupancy_2d = grid_2d.astype(np.float32)
        self.occupancy_3d = grid_3d
        self.occupancy_domain_original = {
            'min': self.env_min.copy(),
            'dimensions': np.array([self.nx, self.ny, nz], dtype=int),
            'cell_size': float(self.cell_size),
        }
        self.get_logger().info(
            f'Occupancy: {self.nx}x{self.ny} slice z_idx={z_idx} '
            f'(z={self.flight_height}m), free={free_count}, obstacle={obstacle_count}, '
            f'input_sha256={occupancy_sha256}'
        )

    def _restrict_occupancy_to_frame_domain(self, frame_domain):
        if abs(frame_domain['cell_size'] - self.cell_size) > 1.0e-9:
            raise RuntimeError(
                'occupancy/frame cell-size mismatch: '
                f'{self.cell_size} vs {frame_domain["cell_size"]}'
            )
        occupancy_min = self.env_min.copy()
        occupancy_max = occupancy_min + np.array([self.nx, self.ny]) * self.cell_size
        frame_min = frame_domain['min'][:2]
        frame_max = frame_min + frame_domain['dimensions'][:2] * frame_domain['cell_size']
        intersection_min = np.maximum(occupancy_min, frame_min)
        intersection_max = np.minimum(occupancy_max, frame_max)
        start = np.ceil(
            (intersection_min - occupancy_min) / self.cell_size - 1.0e-9
        ).astype(int)
        stop = np.floor(
            (intersection_max - occupancy_min) / self.cell_size + 1.0e-9
        ).astype(int)
        start = np.maximum(start, 0)
        stop = np.minimum(stop, np.array([self.nx, self.ny]))
        if np.any(stop <= start):
            raise RuntimeError(
                f'occupancy/frame domains do not overlap: occupancy='
                f'{occupancy_min.tolist()}..{occupancy_max.tolist()} frame='
                f'{frame_min.tolist()}..{frame_max.tolist()}'
            )
        self.occupancy_2d = self.occupancy_2d[
            start[0]:stop[0], start[1]:stop[1]
        ].copy()
        self.env_min = occupancy_min + start * self.cell_size
        self.nx, self.ny = self.occupancy_2d.shape
        self.env_max = self.env_min + np.array([self.nx, self.ny]) * self.cell_size
        self.frame_domain = frame_domain
        self.get_logger().info(
            'Sensor-safe occupancy intersection: '
            f'{self.nx}x{self.ny} min={self.env_min.tolist()} '
            f'max={self.env_max.tolist()}'
        )

    def _load_gaden(self):
        if self.gas_backend == 'raw_house1_snapshot':
            self._start_raw_query_backend()
            return
        if self.gas_backend == 'gaden_player':
            gas_base = os.path.join(self.vgr_path, 'gas_simulations', self.config_id)
            gas_dirs = sorted(
                d for d in os.listdir(gas_base)
                if d.startswith('FilamentSimulation')
                and os.path.isdir(os.path.join(gas_base, d))
            )
            if not gas_dirs:
                raise RuntimeError(f'No gas simulation found in {gas_base}')
            selected_gas_realization = gas_dirs[0]
            gas_dir = os.path.join(gas_base, selected_gas_realization)
            self.selected_gas_realization = selected_gas_realization
            self.selected_gas_realization_path = os.path.realpath(gas_dir)
            self.max_iteration = 0
            for fname in os.listdir(gas_dir):
                if not fname.startswith('iteration_'):
                    continue
                try:
                    suffix = fname.split('_', 1)[1]
                    idx = int(suffix.split('.', 1)[0])
                except (IndexError, ValueError):
                    continue
                self.max_iteration = max(self.max_iteration, idx)
            self.get_logger().info('Gas backend=gaden_player service=/frame_query')
            self.get_logger().info(
                f'GADEN realization={selected_gas_realization}, '
                f'max_iteration={self.max_iteration}'
            )
            frame_domain = self._frame_worker.probe_domain(
                min(self.max_iteration, 1196)
            )
            self._restrict_occupancy_to_frame_domain(frame_domain)
            return
        if not GADEN_AVAILABLE:
            self.get_logger().error('GADEN not available!')
            return

        gas_base = os.path.join(self.vgr_path, 'gas_simulations', self.config_id)
        gas_dirs = sorted(d for d in os.listdir(gas_base) if d.startswith('FilamentSimulation'))
        if not gas_dirs:
            self.get_logger().error(f'No gas simulation found in {gas_base}')
            return

        selected_gas_realization = gas_dirs[0]
        gas_dir = os.path.join(gas_base, selected_gas_realization)
        self.selected_gas_realization = selected_gas_realization
        self.selected_gas_realization_path = os.path.realpath(gas_dir)
        occ_file = os.path.join(self.vgr_path, 'OccupancyGrid3D.csv')

        self.gaden_sim = GadenSim(gas_dir, occ_file)
        self.max_iteration = 0
        for fname in os.listdir(gas_dir):
            if fname.startswith('iteration_'):
                try:
                    idx = int(fname.split('_')[1])
                    self.max_iteration = max(self.max_iteration, idx)
                except ValueError:
                    pass

        self._load_wind_csv()

        self.get_logger().info(
            f'GADEN loaded. realization={self.selected_gas_realization}, '
            f'path={self.selected_gas_realization_path}, max_iteration={self.max_iteration}'
        )
        self.get_logger().info(f'Wind iterations: {len(self.wind_iterations)}')

    def _start_raw_query_backend(self):
        raw_exe = str(self.get_parameter('raw_query_executable').value)
        raw_env_root = str(self.get_parameter('raw_env_root').value)
        raw_gas_results = str(self.get_parameter('raw_gas_results').value)
        if not raw_env_root:
            raw_env_root = self.vgr_path
        if not raw_gas_results:
            gas_base = os.path.join(self.vgr_path, 'gas_simulations', self.config_id)
            gas_dirs = sorted(
                d for d in os.listdir(gas_base)
                if d.startswith('FilamentSimulation')
                and os.path.isdir(os.path.join(gas_base, d))
            )
            if not gas_dirs:
                raise RuntimeError(f'No gas simulation found in {gas_base}')
            raw_gas_results = os.path.join(gas_base, gas_dirs[0])
        self.selected_gas_realization = os.path.basename(raw_gas_results)
        self.selected_gas_realization_path = os.path.realpath(raw_gas_results)
        self.max_iteration = 0
        for fname in os.listdir(raw_gas_results):
            if not fname.startswith('iteration_'):
                continue
            try:
                suffix = fname.split('_', 1)[1]
                idx = int(suffix.split('.', 1)[0])
            except (IndexError, ValueError):
                continue
            self.max_iteration = max(self.max_iteration, idx)
        self._raw_query_worker = RawQueryWorker(raw_exe, raw_env_root, raw_gas_results)
        self.get_logger().info(
            f'Gas backend=raw_house1_snapshot exec={raw_exe} '
            f'env_root={raw_env_root} gas_results={raw_gas_results} '
            f'max_iteration={self.max_iteration}'
        )

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
        mode = str(self.get_parameter('gaden_iteration_mode').value)
        return self.timebase.replay_iteration(self.max_iteration, self.seed, mode)

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

    def _prepare_open_loop_profile(self):
        if not self.open_loop_profile_name:
            return None
        profile = generate_profile(
            self.open_loop_profile_name,
            duration_s=self.motion_duration_s,
            dt_s=self.sim_dt_s,
            start_xy_m=(float(self.uav_pos[0]), float(self.uav_pos[1])),
            heading_rad=self.motion_heading_rad,
        )
        if not profile.satisfies(MotionLimits()):
            raise ValueError(
                f'open-loop profile {profile.name} violates the registered motion envelope'
            )
        blocked = [
            index for index, position in enumerate(profile.position_xy_m)
            if not self._is_position_free(float(position[0]), float(position[1]))
        ]
        if blocked:
            raise ValueError(
                f'open-loop profile {profile.name} intersects occupancy/out-of-bounds '
                f'at sample indices {blocked[:8]}'
            )
        return profile

    def _apply_open_loop_profile(self):
        if self.open_loop_profile is None:
            return
        index = min(self.step_count, self.open_loop_profile.time_s.size - 1)
        target = self.open_loop_profile.position_xy_m[index]
        velocity = self.open_loop_profile.velocity_xy_m_s[index]
        previous = self.uav_pos.copy()
        self.uav_pos[0] = float(target[0])
        self.uav_pos[1] = float(target[1])
        self.uav_pos[2] = self.flight_height
        self.total_distance += float(np.linalg.norm(self.uav_pos - previous))
        if np.linalg.norm(velocity) > 1e-12:
            self.uav_yaw = float(math.atan2(velocity[1], velocity[0]))

    @staticmethod
    def _ensure_parent(path):
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)

    def _write_sensor_manifest(self):
        if not self._sensor_manifest_file:
            return
        self._ensure_parent(self._sensor_manifest_file)
        payload = {
            "schema_version": "mcos-vgr-manifest-v1",
            "sim_dt_s": self.sim_dt_s,
            "realtime_factor": self.realtime_factor,
            "gaden_iteration_mode": str(self.get_parameter('gaden_iteration_mode').value),
            "gas_backend": self.gas_backend,
            "frame_query_service": "/frame_query" if self.gas_backend == "gaden_player" else None,
            "sensor": self.sensor_model.manifest(),
            "truth_policy": {
                "source_coordinates_published": False,
                "true_gas_trace_is_offline_diagnostic_only": True,
            },
            "spatial_domain": {
                "occupancy_original_min": self.occupancy_domain_original[
                    "min"
                ].tolist(),
                "occupancy_original_dimensions": self.occupancy_domain_original[
                    "dimensions"
                ].tolist(),
                "frame_min": self.frame_domain["min"].tolist()
                if hasattr(self, "frame_domain") else None,
                "frame_dimensions": self.frame_domain["dimensions"].tolist()
                if hasattr(self, "frame_domain") else None,
                "sensor_safe_map_min": self.env_min.tolist(),
                "sensor_safe_map_dimensions": [int(self.nx), int(self.ny)],
                "cell_size": float(self.cell_size),
            },
        }
        with open(self._sensor_manifest_file, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2, sort_keys=True)

    def _initialize_trace_files(self):
        import csv as _csv
        trace_specs = (
            (
                self._sensor_trace_file,
                ['t_sim_s','step','iteration','x','y','z','true_gas_ppm',
                 'measured_gas_ppm','sensor_mode','seed'],
            ),
            (
                self._wind_trace_file,
                ['t_sim_s','step','iteration','x','y','z','wind_u','wind_v',
                 'wind_w','wind_speed','wind_direction_rad','seed'],
            ),
            (
                self._pose_trace_file,
                ['t_sim_s','step','x','y','z','yaw','is_moving','seed'],
            ),
            (
                self._measurement_trace_file,
                ['t_sim_s','step','iteration','x','y','z','yaw','is_moving',
                 'true_gas_ppm','measured_gas_ppm','wind_u','wind_v','wind_w',
                 'wind_speed','wind_direction_rad','sensor_mode','seed'],
            ),
            (
                self._continuous_measurement_samples_file,
                ['t_sim_s','step','iteration','replay_time_s','x','y','z','raw_gas_ppm','fopdt_output_ppm','gas_query_time_ms','seed'],
            ),
        )
        for path, header in trace_specs:
            if not path:
                continue
            self._ensure_parent(path)
            with open(path, 'w', newline='') as f:
                _csv.writer(f).writerow(header)
        self._trace_headers_written = True

    def _sim_stamp(self):
        seconds, nanoseconds = self.timebase.stamp_parts()
        return TimeMsg(sec=seconds, nanosec=nanoseconds)

    def _sample_gas(self, iteration):
        query_started = time.perf_counter()
        if self.gas_backend == 'raw_house1_snapshot':
            true_gas, self._frame_wind = self._raw_query_worker.query(iteration, self.uav_pos)
            measured = self.sensor_model.process(true_gas, self.sim_dt_s)
            self._last_gas_query_time_ms = (time.perf_counter() - query_started) * 1000.0
            return true_gas, measured
        if self.gas_backend == 'gaden_player':
            true_gas, self._frame_wind = self._frame_worker.query(iteration, self.uav_pos)
            measured = self.sensor_model.process(true_gas, self.sim_dt_s)
            self._last_gas_query_time_ms = (time.perf_counter() - query_started) * 1000.0
            return true_gas, measured
        if not GADEN_AVAILABLE or not hasattr(self, 'gaden_sim'):
            true_gas = 0.0
        else:
            pos = GVec(self.uav_pos[0], self.uav_pos[1], self.uav_pos[2])
            try:
                true_gas = float(self.gaden_sim.getConcentration(iteration, pos))
            except Exception as e:
                self.get_logger().warn(f'getConcentration error: {e}')
                true_gas = 0.0
        measured = self.sensor_model.process(true_gas, self.sim_dt_s)
        self._last_gas_query_time_ms = (time.perf_counter() - query_started) * 1000.0
        if abs(self.sensor_model.time_s - self.t_sim_s) > 1e-9:
            raise RuntimeError(
                f'sensor/simulation clock mismatch: sensor={self.sensor_model.time_s}, '
                f'sim={self.t_sim_s}'
            )
        return true_gas, measured

    def _append_continuous_measurement_sample(self, iteration, true_gas, measured):
        if not self._continuous_measurement_samples_file:
            return
        import csv as _csv
        with open(self._continuous_measurement_samples_file, 'a', newline='') as f:
            _csv.writer(f).writerow([f'{self.t_sim_s:.6f}', self.step_count, iteration, f'{self.t_sim_s:.6f}',
                f'{self.uav_pos[0]:.4f}', f'{self.uav_pos[1]:.4f}', f'{self.uav_pos[2]:.4f}',
                f'{true_gas:.9f}', f'{measured:.9f}', f'{self._last_gas_query_time_ms:.6f}', self.seed])

    def _sample_wind(self, iteration):
        if self.gas_backend in ('gaden_player', 'raw_house1_snapshot'):
            return self._frame_wind.copy()
        return self._get_wind_at_position(iteration)

    def _append_sensor_trace(self, iteration, true_gas, measured):
        if not self._sensor_trace_file:
            return
        import csv as _csv
        with open(self._sensor_trace_file, 'a', newline='') as f:
            w = _csv.writer(f)
            w.writerow([f'{self.t_sim_s:.6f}', self.step_count, iteration,
                       f'{self.uav_pos[0]:.4f}', f'{self.uav_pos[1]:.4f}', f'{self.uav_pos[2]:.4f}',
                       f'{true_gas:.6f}', f'{measured:.6f}', self.sensor_model.cfg.mode, self.seed])

    def _append_wind_trace(self, iteration, wind):
        if not self._wind_trace_file:
            return
        import csv as _csv
        ws = float(np.linalg.norm(wind[:2]))
        wd = float(math.atan2(wind[1], wind[0]))
        with open(self._wind_trace_file, 'a', newline='') as f:
            w = _csv.writer(f)
            w.writerow([f'{self.t_sim_s:.6f}', self.step_count, iteration,
                       f'{self.uav_pos[0]:.4f}', f'{self.uav_pos[1]:.4f}', f'{self.uav_pos[2]:.4f}',
                       f'{wind[0]:.6f}', f'{wind[1]:.6f}', f'{wind[2]:.6f}',
                       f'{ws:.6f}', f'{wd:.6f}', self.seed])

    def _append_pose_trace(self, is_moving):
        if not self._pose_trace_file:
            return
        import csv as _csv
        with open(self._pose_trace_file, 'a', newline='') as f:
            w = _csv.writer(f)
            w.writerow([f'{self.t_sim_s:.6f}', self.step_count,
                       f'{self.uav_pos[0]:.4f}', f'{self.uav_pos[1]:.4f}', f'{self.uav_pos[2]:.4f}',
                       f'{self.uav_yaw:.4f}', int(is_moving), self.seed])

    def _append_measurement_trace(self, iteration, true_gas, measured, wind, is_moving):
        if not self._measurement_trace_file:
            return
        import csv as _csv
        wind_speed = float(np.linalg.norm(wind[:2]))
        wind_direction = float(math.atan2(wind[1], wind[0]))
        with open(self._measurement_trace_file, 'a', newline='') as f:
            _csv.writer(f).writerow([
                f'{self.t_sim_s:.6f}', self.step_count, iteration,
                f'{self.uav_pos[0]:.4f}', f'{self.uav_pos[1]:.4f}',
                f'{self.uav_pos[2]:.4f}', f'{self.uav_yaw:.4f}', int(is_moving),
                f'{true_gas:.6f}', f'{measured:.6f}',
                f'{wind[0]:.6f}', f'{wind[1]:.6f}', f'{wind[2]:.6f}',
                f'{wind_speed:.6f}', f'{wind_direction:.6f}',
                self.sensor_model.cfg.mode, self.seed,
            ])


    def _publish_map_once(self):
        msg = OccupancyGrid()
        msg.header = Header(stamp=self._sim_stamp(), frame_id='map')
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

    def _publish_all(
        self, advance=True, record=True, publish_observation=True
    ):
        if advance:
            expected_step = self.step_count + 1
            self._advance_navigation_one_step()
            self.step_count, self.t_sim_s = self.timebase.advance()
            if self.step_count != expected_step or self.step_count != self._last_advanced_step + 1:
                raise RuntimeError(f'non-monotone simulation step: {self._last_advanced_step}->{self.step_count}')
            if abs(self.t_sim_s - self.step_count * self.sim_dt_s) > 1e-12:
                raise RuntimeError(f'clock/step mismatch: step={self.step_count}, t={self.t_sim_s}')
            self._last_advanced_step = self.step_count
        # A paused readiness tick publishes the initial observation only.  In
        # particular it must not move an open-loop profile or call the FOPDT
        # transition, otherwise the algorithm sees a nonzero sensor time at
        # /clock==0 and the first replay frame becomes launch-order dependent.
        if advance:
            self._apply_open_loop_profile()
        now = self._sim_stamp()
        if advance:
            clock_msg = Clock()
            clock_msg.clock = now
            self.clock_pub.publish(clock_msg)

        iteration = self._get_iteration_for_step()
        true_gas = None
        measured_gas = None
        wind = None
        if publish_observation:
            if advance:
                true_gas, measured_gas = self._sample_gas(iteration)
            else:
                true_gas = float(self.sensor_model.cfg.initial_input_ppm)
                measured_gas = float(self.sensor_model.state_ppm)
                self._last_gas_query_time_ms = 0.0
            wind = self._sample_wind(iteration)
        is_moving = bool(np.linalg.norm(self.uav_pos - self._last_trace_pos) > 1e-9)
        if record:
            if not publish_observation:
                raise RuntimeError(
                    'record=True requires publish_observation=True'
                )
            self._append_sensor_trace(iteration, true_gas, measured_gas)
            self._append_continuous_measurement_sample(iteration, true_gas, measured_gas)
            self._append_wind_trace(iteration, wind)
            self._append_pose_trace(is_moving)
            self._append_measurement_trace(
                iteration, true_gas, measured_gas, wind, is_moving
            )
            self._last_trace_pos = self.uav_pos.copy()

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

        if publish_observation:
            gas_msg = GasSensor()
            gas_msg.header = Header(stamp=now, frame_id='base_link')
            gas_msg.technology = GasSensor.TECH_PID
            gas_msg.raw_units = GasSensor.UNITS_PPM
            gas_msg.raw = float(measured_gas)
            self.gas_pub.publish(gas_msg)

            wind_msg = Anemometer()
            wind_msg.header = Header(stamp=now, frame_id='map')
            wind_msg.wind_speed = float(np.linalg.norm(wind[:2]))
            wind_msg.wind_direction = float(math.atan2(wind[1], wind[0]))
            self.wind_pub.publish(wind_msg)

    def _finish_navigation(self, success):
        self._nav_target = None
        self._nav_waypoints = []
        self._nav_final_target = None
        if self._nav_completion_future is not None and not self._nav_completion_future.done():
            self._nav_completion_future.set_result(bool(success))

    def _advance_navigation_one_step(self):
        if self._nav_target is None:
            return
        remaining = float(self.timebase.maximum_motion_distance(self.max_uav_speed, self.step_size))
        eps = 1e-12
        while remaining > eps and self._nav_target is not None:
            direction = self._nav_target - self.uav_pos
            dist_xy = float(np.linalg.norm(direction[:2]))
            if dist_xy <= eps:
                if self._nav_waypoints:
                    self._nav_target = self._nav_waypoints.pop(0)
                    continue
                self._finish_navigation(True)
                return
            travel = min(remaining, dist_xy)
            step_dir = direction[:2] / dist_xy
            next_x = float(self.uav_pos[0] + step_dir[0] * travel)
            next_y = float(self.uav_pos[1] + step_dir[1] * travel)
            if not self._is_position_free(next_x, next_y):
                self.get_logger().error(
                    f'Waypoint execution geometry violation at ({next_x:.2f}, {next_y:.2f})'
                )
                self._finish_navigation(False)
                return
            self.total_distance += travel
            self.uav_pos[0] = next_x
            self.uav_pos[1] = next_y
            self.uav_pos[2] = self.flight_height
            self.uav_yaw = float(math.atan2(step_dir[1], step_dir[0]))
            remaining -= travel
            if travel >= dist_xy - eps:
                if self._nav_waypoints:
                    self._nav_target = self._nav_waypoints.pop(0)
                else:
                    self._finish_navigation(True)
                    return

    def _build_coarse_navigation_grid(self):
        scale = int(self.nav_reduce_scale)
        if scale <= 1:
            self.nav_env_min = self.env_min
            self.nav_cell_size = self.cell_size
            self.nav_nx = self.nx
            self.nav_ny = self.ny
            self.nav_occ = self.occupancy_2d
            self.get_logger().info(
                f'Navigation grid: fine {self.nx}x{self.ny} cell={self.cell_size:.4f} (reduce_scale={scale})'
            )
            return
        coarse_nx = self.nx // scale
        coarse_ny = self.ny // scale
        occ = np.ones((coarse_nx, coarse_ny), dtype=np.float32)
        fine = self.occupancy_2d
        for i in range(coarse_nx):
            for j in range(coarse_ny):
                block = fine[i * scale:(i + 1) * scale, j * scale:(j + 1) * scale]
                if block.size == scale * scale and float(block.sum()) == 0.0:
                    occ[i, j] = 0.0
        self.nav_env_min = self.env_min.copy()
        self.nav_cell_size = self.cell_size * scale
        self.nav_nx = coarse_nx
        self.nav_ny = coarse_ny
        self.nav_occ = occ
        free_n = int((occ == 0).sum())
        obs_n = int((occ != 0).sum())
        self.get_logger().info(
            f'Navigation grid: coarse {coarse_nx}x{coarse_ny} cell={self.nav_cell_size:.4f} '
            f'free={free_n} obstacle={obs_n} (reduce_scale={scale})'
        )

    def _is_position_free(self, x, y):
        ix = int((x - self.nav_env_min[0]) / self.nav_cell_size)
        iy = int((y - self.nav_env_min[1]) / self.nav_cell_size)
        if 0 <= ix < self.nav_nx and 0 <= iy < self.nav_ny:
            return self.nav_occ[ix, iy] == 0
        return False

    def _bfs_path(self, start_world, goal_world):
        """Return a full collision-free cell-center path on the coarse CPIR-aligned grid."""
        def to_grid(wx, wy):
            return int((wx - self.nav_env_min[0]) / self.nav_cell_size), int((wy - self.nav_env_min[1]) / self.nav_cell_size)
        def to_world(ix, iy):
            return self.nav_env_min[0] + (ix + 0.5) * self.nav_cell_size, self.nav_env_min[1] + (iy + 0.5) * self.nav_cell_size
        sx, sy = to_grid(start_world[0], start_world[1])
        gx, gy = to_grid(goal_world[0], goal_world[1])
        if not (0 <= sx < self.nav_nx and 0 <= sy < self.nav_ny and 0 <= gx < self.nav_nx and 0 <= gy < self.nav_ny):
            return []
        if self.nav_occ[sx, sy] != 0 or self.nav_occ[gx, gy] != 0:
            return []
        from collections import deque
        parent = {(sx, sy): None}
        queue = deque([(sx, sy)])
        neighbors = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]
        while queue:
            cx, cy = queue.popleft()
            if (cx, cy) == (gx, gy):
                break
            for ddx, ddy in neighbors:
                nx_, ny_ = cx + ddx, cy + ddy
                if not (0 <= nx_ < self.nav_nx and 0 <= ny_ < self.nav_ny):
                    continue
                if (nx_, ny_) in parent or self.nav_occ[nx_, ny_] != 0:
                    continue
                # Do not cut diagonally through an occupied corner.
                if ddx != 0 and ddy != 0:
                    if self.nav_occ[cx + ddx, cy] != 0 or self.nav_occ[cx, cy + ddy] != 0:
                        continue
                parent[(nx_, ny_)] = (cx, cy)
                queue.append((nx_, ny_))
        if (gx, gy) not in parent:
            return []
        cells = []
        cur = (gx, gy)
        while cur is not None:
            cells.append(cur)
            cur = parent[cur]
        cells.reverse()
        return [to_world(ix, iy) for ix, iy in cells]

    def _navigation_waypoints(self, target_pos):
        if not self._is_position_free(target_pos[0], target_pos[1]):
            return []
        world_path = self._bfs_path(self.uav_pos[:2], target_pos[:2])
        if not world_path:
            return []
        waypoints = [np.array([wx, wy, self.flight_height], dtype=float) for wx, wy in world_path]
        # First cell center is in the same free cell as the current pose.
        if waypoints and np.linalg.norm(waypoints[0][:2] - self.uav_pos[:2]) <= 1e-12:
            waypoints.pop(0)
        # Finish at the requested point inside the final free cell.
        if not waypoints or np.linalg.norm(waypoints[-1][:2] - target_pos[:2]) > 1e-12:
            waypoints.append(np.array(target_pos, dtype=float))
        return waypoints

    async def _plan_callback(self, goal_handle):
        gx = goal_handle.request.goal.pose.position.x
        gy = goal_handle.request.goal.pose.position.y
        self.get_logger().warn(f"PLAN_CB: called with goal=({gx:.2f},{gy:.2f})")
        goal = goal_handle.request.goal.pose.position
        path = Path()
        path.header.frame_id = "map"
        path.header.stamp = self._sim_stamp()
        if self._is_position_free(goal.x, goal.y):
            world_path = self._bfs_path(self.uav_pos[:2], [goal.x, goal.y])
        else:
            world_path = []
        for wx, wy in world_path:
            ps = PoseStamped()
            ps.header = path.header
            ps.pose.position.x = wx
            ps.pose.position.y = wy
            ps.pose.position.z = self.flight_height
            ps.pose.orientation.w = 1.0
            path.poses.append(ps)
        if world_path:
            last = path.poses[-1].pose.position
            if math.hypot(last.x - goal.x, last.y - goal.y) > 1e-12:
                ps = PoseStamped()
                ps.header = path.header
                ps.pose.position.x = goal.x
                ps.pose.position.y = goal.y
                ps.pose.position.z = self.flight_height
                ps.pose.orientation.w = 1.0
                path.poses.append(ps)
        result = ComputePathToPose.Result()
        result.path = path
        self.get_logger().warn(f"PLAN_CB: returning {len(path.poses)} poses")
        goal_handle.succeed()
        return result


    def _nav_goal_callback(self, goal_request):
        if self.open_loop_profile is not None:
            self._nav_goal_prepared = True
            self._nav_completion_future = None
            return GoalResponse.ACCEPT
        target = goal_request.pose.pose.position
        requested_z = target.z if abs(target.z) > 0.01 else self.flight_height
        if self.allow_vertical_motion:
            self.get_logger().error(
                'Vertical motion requested, but the audited bridge currently supports only fixed-altitude 2-D smoke tests'
            )
            return GoalResponse.REJECT
        if abs(requested_z - self.flight_height) > 1e-6:
            self.get_logger().warn(
                f'Rejecting unaudited altitude command z={requested_z:.3f}; holding fixed altitude z={self.flight_height:.3f}'
            )
        target_pos = np.array([target.x, target.y, self.flight_height], dtype=float)
        if not self._is_position_free(target.x, target.y):
            self.get_logger().warn(f'Rejecting obstacle navigation target ({target.x:.2f}, {target.y:.2f})')
            return GoalResponse.REJECT
        waypoints = self._navigation_waypoints(target_pos)
        if not waypoints:
            self.get_logger().warn(f'No collision-free path to navigation target ({target.x:.2f}, {target.y:.2f})')
            return GoalResponse.REJECT
        self._nav_final_target = target_pos.copy()
        self._nav_target = waypoints[0]
        self._nav_waypoints = [wp.copy() for wp in waypoints[1:]]
        self._nav_completion_future = Future()
        self._nav_goal_prepared = True
        self.get_logger().info(
            f'Prepared {1 + len(self._nav_waypoints)} collision-free navigation waypoints to ({target.x:.2f}, {target.y:.2f})'
        )
        return GoalResponse.ACCEPT

    async def _nav_callback(self, goal_handle):
        if self.open_loop_profile is not None:
            self.get_logger().warn(
                'Acknowledging NavigateToPose without changing pose because a '
                'deterministic MCOS open-loop profile owns the motion timeline'
            )
            self._nav_goal_prepared = False
            goal_handle.succeed()
            return NavigateToPose.Result()

        self.get_logger().info(
            f'UAV navigating in audited 2-D mode to '
            f'({self._nav_final_target[0]:.2f}, {self._nav_final_target[1]:.2f}, {self._nav_final_target[2]:.2f})'
        )

        # Await a ROS Future completed by the single simulation timer.  Do not
        # use asyncio.sleep(): rclpy action callbacks do not own an asyncio
        # event loop, and do not advance/publish from this callback.
        if not self._nav_goal_prepared or self._nav_completion_future is None:
            self.get_logger().error('Accepted navigation goal was not prepared deterministically')
            goal_handle.abort()
            return NavigateToPose.Result()
        completion_future = self._nav_completion_future
        self._nav_goal_prepared = False
        reached = await completion_future
        if goal_handle.is_cancel_requested:
            self._finish_navigation(False)
            goal_handle.canceled()
            return NavigateToPose.Result()
        if not reached:
            goal_handle.abort()
            return NavigateToPose.Result()
        goal_handle.succeed()
        return NavigateToPose.Result()


def main(args=None):
    rclpy.init(args=args)
    node = VGRUAVSimNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
