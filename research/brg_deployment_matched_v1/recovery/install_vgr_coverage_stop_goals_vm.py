"""Opt-in source-blind goal sequence with normal VGR navigate-then-sample flow."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

TARGET = Path('/home/zyc/brg_closedloop_20260927/vgr_execution_v2/vgr_bridge/vgr_sim_node.py')
EXPECTED = 'd0b87e0907f4ffd7dae55ad09effb9e26c970566b96de2f2458fa5396a95e95e'
BACKUP = TARGET.with_name(TARGET.name + '.pre_brg_v1_stop_goals_20260928')
FREEZE = Path('/home/zyc/brg_v1_recovery_20260928/coverage_routes/COVERAGE_STOP_GOALS_FREEZE_V3.json')
FREEZE_SHA = '645df8e8f2b8527eb17d4daa65a055bfdaa18e8042fbf6d31b55b2b60bbc2261'


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def replace_once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError('VGR opt-in patch anchor changed')
    return text.replace(old, new)


def main() -> None:
    original = TARGET.read_bytes()
    if sha(original) != EXPECTED or sha(FREEZE.read_bytes()) != FREEZE_SHA:
        raise RuntimeError('VGR source or source-blind goal freeze changed')
    freeze = json.loads(FREEZE.read_text())
    if (freeze['status'] != 'SOURCE_BLIND_STOP_AND_SAMPLE_GOALS_FROZEN_V3' or
            freeze['goal_count_per_environment'] != 12):
        raise RuntimeError('V3 stop-goal freeze invalid')
    if BACKUP.exists():
        if sha(BACKUP.read_bytes()) != EXPECTED:
            raise RuntimeError('existing pre-patch VGR backup changed')
    else:
        BACKUP.write_bytes(original)
    text = original.decode('utf-8')
    text = replace_once(text, 'import json\nimport subprocess\n',
                        'import json\nimport hashlib\nimport subprocess\n')
    text = replace_once(text, "        self.declare_parameter('open_loop_profile', '')\n",
                        "        self.declare_parameter('open_loop_profile', '')\n"
                        "        self.declare_parameter('coverage_goal_file', '')\n"
                        "        self.declare_parameter('coverage_environment_index', -1)\n")
    text = replace_once(text,
        '        self.open_loop_profile = self._prepare_open_loop_profile()\n'
        '        self._initialize_trace_files()\n',
        '''        self.open_loop_profile = self._prepare_open_loop_profile()
        self._coverage_goals = []
        self._coverage_goal_index = 0
        self._coverage_goal_trace_file = None
        goal_file = str(self.get_parameter('coverage_goal_file').value)
        if goal_file:
            goal_path = Path(goal_file).resolve()
            allowed = Path('/home/zyc/brg_v1_recovery_20260928/coverage_routes').resolve()
            if (goal_path.parent != allowed or
                    goal_path.name != 'COVERAGE_STOP_GOALS_FREEZE_V3.json' or
                    self.open_loop_profile is not None):
                raise ValueError('coverage goals require the frozen V3 file and normal navigation')
            if (hashlib.sha256(goal_path.read_bytes()).hexdigest() !=
                    '645df8e8f2b8527eb17d4daa65a055bfdaa18e8042fbf6d31b55b2b60bbc2261'):
                raise ValueError('frozen V3 coverage goal SHA mismatch')
            frozen = json.loads(goal_path.read_text())
            env_index = int(self.get_parameter('coverage_environment_index').value)
            expected_wind = {0: '1,3-2,4_fast', 1: '3,5-1_slow', 2: '4,5-3_slow'}
            if env_index not in expected_wind or self.config_id != expected_wind[env_index]:
                raise ValueError('V3 coverage environment/wind binding mismatch')
            selected = [r for r in frozen['records'] if r['environment_index'] == env_index]
            if len(selected) != 1 or len(selected[0]['goal_xy_m']) != 12:
                raise ValueError('frozen V3 coverage goal record missing')
            route = allowed / f'env_{env_index}_coverage.npz'
            if hashlib.sha256(route.read_bytes()).hexdigest() != selected[0]['route_file_sha256']:
                raise ValueError('V2 parent coverage route SHA mismatch')
            self._coverage_goals = [np.asarray(xy, dtype=float)
                                    for xy in selected[0]['goal_xy_m']]
            self._coverage_goal_trace_file = str(
                Path(self._sensor_trace_file).with_name('coverage_goal_trace.csv'))
            with open(self._coverage_goal_trace_file, 'w') as trace:
                trace.write('goal_index,request_x,request_y,actual_x,actual_y,t_sim_s\\n')
        self._initialize_trace_files()
''')
    text = replace_once(text,
        '        target_pos = np.array([target.x, target.y, self.flight_height], dtype=float)\n'
        '        if not self._is_position_free(target.x, target.y):\n'
        "            self.get_logger().warn(f'Rejecting obstacle navigation target ({target.x:.2f}, {target.y:.2f})')\n"
        '            return GoalResponse.REJECT\n'
        '        waypoints = self._navigation_waypoints(target_pos)\n'
        '        if not waypoints:\n'
        "            self.get_logger().warn(f'No collision-free path to navigation target ({target.x:.2f}, {target.y:.2f})')\n"
        '            return GoalResponse.REJECT\n',
        '''        if self._coverage_goals:
            target_xy = self._coverage_goals[self._coverage_goal_index % len(self._coverage_goals)]
            target_pos = np.array([target_xy[0], target_xy[1], self.flight_height], dtype=float)
        else:
            target_pos = np.array([target.x, target.y, self.flight_height], dtype=float)
        if not self._is_position_free(float(target_pos[0]), float(target_pos[1])):
            self.get_logger().warn(f'Rejecting obstacle navigation target ({target_pos[0]:.2f}, {target_pos[1]:.2f})')
            return GoalResponse.REJECT
        waypoints = self._navigation_waypoints(target_pos)
        if not waypoints:
            self.get_logger().warn(f'No collision-free path to navigation target ({target_pos[0]:.2f}, {target_pos[1]:.2f})')
            return GoalResponse.REJECT
        if self._coverage_goals:
            with open(self._coverage_goal_trace_file, 'a') as trace:
                trace.write(f'{self._coverage_goal_index},{target.x:.9f},{target.y:.9f},'
                            f'{target_pos[0]:.9f},{target_pos[1]:.9f},{self.t_sim_s:.6f}\\n')
            self._coverage_goal_index += 1
''')
    text = replace_once(text,
        "            f'Prepared {1 + len(self._nav_waypoints)} collision-free navigation waypoints to ({target.x:.2f}, {target.y:.2f})'\n",
        "            f'Prepared {1 + len(self._nav_waypoints)} collision-free navigation waypoints to ({target_pos[0]:.2f}, {target_pos[1]:.2f})'\n")
    compile(text, str(TARGET), 'exec')
    TARGET.write_text(text, encoding='utf-8')
    result = {'status': 'VGR_OPT_IN_SOURCE_BLIND_STOP_GOALS_INSTALLED',
              'target': str(TARGET), 'backup': str(BACKUP),
              'original_sha256': EXPECTED, 'patched_sha256': sha(TARGET.read_bytes()),
              'v3_freeze_sha256': FREEZE_SHA,
              'default_native_motion_or_sensor_branch_changed': False}
    output = Path('/home/zyc/brg_v1_recovery_20260928/VGR_COVERAGE_STOP_GOALS_PATCH.json')
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
