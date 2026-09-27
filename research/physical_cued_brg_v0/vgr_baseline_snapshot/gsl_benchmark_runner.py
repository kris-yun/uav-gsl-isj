"""GSL Benchmark Runner - triggers official GSL algorithms and collects results.

Sends DoGSL action goals to the GSL server, monitors the result,
and records metrics for each run.
"""
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from gsl_actions.action import DoGSL
from geometry_msgs.msg import PoseWithCovarianceStamped
import csv
import time
import os
import json
import math
import numpy as np


class GSLBenchmarkRunner(Node):
    def __init__(self):
        super().__init__('gsl_benchmark_runner')

        self.declare_parameter('algorithm', 'PMFS')
        self.declare_parameter('output_csv', '/tmp/gsl_run_result.csv')
        self.declare_parameter('timeout_sec', 120.0)
        self.declare_parameter('success_radius_1m', 1.0)
        self.declare_parameter('success_radius_2m', 2.0)
        self.declare_parameter('source_x', 0.0)
        self.declare_parameter('source_y', 0.0)
        self.declare_parameter('source_z', 0.0)
        self.declare_parameter('seed', 0)
        self.declare_parameter('budget_fraction', 1.0)
        self.declare_parameter('config_id', '2,4-1_fast')

        self.algorithm = self.get_parameter('algorithm').get_parameter_value().string_value
        self.output_csv = self.get_parameter('output_csv').get_parameter_value().string_value
        self.timeout = self.get_parameter('timeout_sec').get_parameter_value().double_value
        self.source = np.array([
            self.get_parameter('source_x').get_parameter_value().double_value,
            self.get_parameter('source_y').get_parameter_value().double_value,
            self.get_parameter('source_z').get_parameter_value().double_value,
        ])
        self.seed = self.get_parameter('seed').get_parameter_value().integer_value
        self.budget_fraction = self.get_parameter('budget_fraction').get_parameter_value().double_value
        self.config_id = self.get_parameter('config_id').get_parameter_value().string_value

        # Track robot position
        self.current_pose = None
        self.pose_sub = self.create_subscription(
            PoseWithCovarianceStamped, '/amcl_pose', self._pose_callback, 10
        )

        # GSL action client
        self.gsl_client = ActionClient(self, DoGSL, 'gsl_server')

        # Metrics tracking
        self.min_distance = float('inf')
        self.positions = []
        self.start_time = None
        self.declaration = None

        # Start benchmark after a short delay
        self.create_timer(3.0, self._run_once)

    def _pose_callback(self, msg):
        pos = msg.pose.pose.position
        self.current_pose = np.array([pos.x, pos.y, pos.z])
        if self.source is not None:
            dist = np.linalg.norm(self.current_pose[:2] - self.source[:2])
            self.min_distance = min(self.min_distance, dist)
            self.positions.append(self.current_pose.copy())

    def _run_once(self):
        """Run one benchmark trial. Only fires once."""
        # Cancel timer to prevent re-firing
        for t in self._timers:
            t.cancel()

        self.get_logger().info(f'Running {self.algorithm} (seed={self.seed}, bf={self.budget_fraction})')
        self.start_time = time.time()

        # Wait for GSL server
        if not self.gsl_client.wait_for_server(timeout_sec=10.0):
            self.get_logger().error('GSL server not available!')
            self._save_result(error='gsl_server_not_available')
            rclpy.shutdown()
            return

        # Send goal
        goal = DoGSL.Goal()
        goal.gsl_method = self.algorithm

        self.get_logger().info(f'Sending goal: {self.algorithm}')
        future = self.gsl_client.send_goal_async(goal)
        future.add_done_callback(self._goal_response)

    def _goal_response(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error(f'Goal rejected for {self.algorithm}')
            self._save_result(error='goal_rejected')
            rclpy.shutdown()
            return

        self.get_logger().info(f'Goal accepted for {self.algorithm}')
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self._result_callback)

        # Set timeout
        self.create_timer(self.timeout, self._timeout_callback)

    def _result_callback(self, future):
        elapsed = time.time() - self.start_time if self.start_time else 0
        result = future.result()
        self.get_logger().info(f'{self.algorithm} completed in {elapsed:.1f}s')

        # Compute metrics
        success_1m = 1 if self.min_distance <= 1.0 else 0
        success_2m = 1 if self.min_distance <= 2.0 else 0
        path_length = self._compute_path_length()

        self._save_result(
            elapsed=elapsed,
            success_1m=success_1m,
            success_2m=success_2m,
            path_length=path_length,
        )
        rclpy.shutdown()

    def _timeout_callback(self):
        elapsed = time.time() - self.start_time if self.start_time else 0
        self.get_logger().warn(f'{self.algorithm} timed out after {elapsed:.1f}s')
        success_1m = 1 if self.min_distance <= 1.0 else 0
        success_2m = 1 if self.min_distance <= 2.0 else 0
        path_length = self._compute_path_length()

        self._save_result(
            elapsed=elapsed,
            success_1m=success_1m,
            success_2m=success_2m,
            path_length=path_length,
            timed_out=True,
        )
        rclpy.shutdown()

    def _compute_path_length(self):
        if len(self.positions) < 2:
            return 0.0
        total = 0.0
        for i in range(1, len(self.positions)):
            total += np.linalg.norm(self.positions[i][:2] - self.positions[i-1][:2])
        return total

    def _save_result(self, elapsed=0, success_1m=0, success_2m=0,
                     path_length=0, error=None, timed_out=False):
        result = {
            'method': f'official_{self.algorithm}',
            'source_repo': 'MAPIRlab/GasSourceLocalization',
            'source_commit': '4e141e162551e674f2f30ddb8859136c72139aac',
            'algorithm_name_from_repo': self.algorithm,
            'config_id': self.config_id,
            'seed': self.seed,
            'budget_fraction': self.budget_fraction,
            'source_x': float(self.source[0]),
            'source_y': float(self.source[1]),
            'source_z': float(self.source[2]),
            'min_distance_to_source': float(self.min_distance),
            'success_at_1m': success_1m,
            'success_at_2m': success_2m,
            'elapsed_sec': float(elapsed),
            'path_length': float(path_length),
            'n_positions': len(self.positions),
            'timed_out': timed_out,
            'error': error or '',
            'dataset': 'VGR_House01',
            'notes': 'official_baseline_via_GSL_action_server',
        }

        # Append to CSV
        file_exists = os.path.exists(self.output_csv)
        with open(self.output_csv, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=sorted(result.keys()))
            if not file_exists:
                writer.writeheader()
            writer.writerow(result)

        self.get_logger().info(f'Result saved: min_dist={self.min_distance:.3f}m, '
                               f'success_1m={success_1m}, success_2m={success_2m}')


def main(args=None):
    rclpy.init(args=args)
    node = GSLBenchmarkRunner()
    rclpy.spin(node)


if __name__ == '__main__':
    main()
