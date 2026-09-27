#!/usr/bin/env python3
"""Isolated adapter port: recorded physical times; PMFS estimate, not robot pose."""
import argparse,hashlib,json,shutil
from pathlib import Path

def once(text,old,new):
    if text.count(old)!=1:raise ValueError(f'exact anchor mismatch: {old[:80]}')
    return text.replace(old,new,1)

def main():
    a=argparse.ArgumentParser();a.add_argument('--original',required=True);a.add_argument('--out',required=True);args=a.parse_args()
    src=Path(args.original);out=Path(args.out)
    shutil.copytree(src,out,ignore=shutil.ignore_patterns('__pycache__','*.pyc','*.py.'),dirs_exist_ok=False)
    paths=[out/'vgr_bridge/vgr_sim_node.py',out/'vgr_bridge/gsl_benchmark_runner.py'];old={p.name:p.read_bytes() for p in paths}
    p=paths[0];s=p.read_text()
    s=once(s,"        self.declare_parameter('gaden_iteration_mode', 'seeded_time_replay')", """        self.declare_parameter('gaden_iteration_mode', 'seeded_time_replay')
        self.declare_parameter('recorded_snapshot_time_map', '')""")
    s=once(s,'        self._load_gaden()','''        self._load_gaden()
        self._recorded_snapshot_ids = self._recorded_snapshot_times = None
        schedule_path = str(self.get_parameter('recorded_snapshot_time_map').value)
        if str(self.get_parameter('gaden_iteration_mode').value) == 'recorded_snapshot_time_replay':
            import csv
            with open(schedule_path) as schedule_file:
                rows = list(csv.DictReader(schedule_file, delimiter='\\t'))
            self._recorded_snapshot_times = np.array([float(r['physical_sim_time_s']) for r in rows])
            self._recorded_snapshot_ids = np.array([int(r['save_record_id']) for r in rows])
            if not len(rows) or not np.isfinite(self._recorded_snapshot_times).all() or np.any(np.diff(self._recorded_snapshot_times) <= 0):
                raise RuntimeError('invalid recorded snapshot schedule')
            if self._recorded_snapshot_times[0] != 0 or self._recorded_snapshot_times[-1] < 300:
                raise RuntimeError('recorded replay does not cover full 300 s budget')
            if np.any(self._recorded_snapshot_ids < 0) or np.any(self._recorded_snapshot_ids > self.max_iteration):
                raise RuntimeError('recorded file IDs outside existing plume')
            for file_id in self._recorded_snapshot_ids:
                if not os.path.isfile(os.path.join(self.selected_gas_realization_path, f'iteration_{file_id}')):
                    raise RuntimeError(f'missing recorded snapshot {file_id}')''')
    s=once(s,"        return self.timebase.replay_iteration(self.max_iteration, self.seed, mode)",'''        if mode == 'recorded_snapshot_time_replay':
            # Causal zero-order hold on actual writer times. No future frame,
            # guessed 0.5 s interval, seed offset, interpolation or cyclic replay.
            index = np.searchsorted(self._recorded_snapshot_times, self.timebase.time_s, side='right') - 1
            return int(self._recorded_snapshot_ids[max(0, index)])
        return self.timebase.replay_iteration(self.max_iteration, self.seed, mode)''')
    s=once(s,'        publish_observation = (not advancing) or within_evidence_horizon','''        publish_observation = (not advancing) or within_evidence_horizon
        if str(self.get_parameter('gaden_iteration_mode').value) == 'recorded_snapshot_time_replay':
            publish_observation = advancing and within_evidence_horizon''')
    p.write_text(s)
    p=paths[1];s=p.read_text()
    s=once(s,'        self.declare_parameter("official_pf_result_file", "")','''        self.declare_parameter("official_pf_result_file", "")
        self.declare_parameter("official_pmfs_belief_file", "")''')
    s=once(s,'        self.method = self._param_str("method")','''        self.official_pmfs_belief_file = self._param_str("official_pmfs_belief_file")
        self._action_start_ros_s = None
        self.method = self._param_str("method")''')
    # Keep benchmark's actual action client; only align its elapsed clock.
    anchor='        elapsed = 0.0 if self.start_wall is None else time.time() - self.start_wall'
    assert s.count(anchor)==2
    s=s.replace(anchor,'        elapsed = 0.0 if self._action_start_ros_s is None else self.get_clock().now().nanoseconds / 1e9 - self._action_start_ros_s')
    s=once(s,'        return any(token in lowered for token in ["success", "source_found", "found", "1"])',
        '        return lowered in {"true", "1", "success", "source_found", "found"}')
    s=once(s,'        self.create_timer(2.0, self._run_once)', '''        from rclpy.clock import Clock, ClockType
        self.create_timer(2.0, self._run_once, clock=Clock(clock_type=ClockType.STEADY_TIME))''')
    s=once(s,'        contract = CANONICAL[self.method]','''        contract = CANONICAL[self.method]
        if self.method == "B4_PMFS_official" and self.official_pmfs_belief_file:
            with open(self.official_pmfs_belief_file) as belief_file:
                rows = [json.loads(line) for line in belief_file if line.strip()]
            rows = [r for r in rows if r['search_time_s'] <= self.time_budget_s]
            if not rows:
                raise RuntimeError('no PMFS source estimate within budget; robot-pose fallback prohibited')
            r = rows[-1]
            x, y = map(float, r['estimate_xy'])
            if not np.isfinite([x, y]).all():
                raise RuntimeError('nonfinite PMFS estimate')
            return x, y, 'native_top5pct_probability_weighted_source_estimate', {}''')
    # Locate the existing wall-start assignment exactly; inspect rather than guess.
    anchor='        self.start_wall = time.time()'
    s=once(s,anchor,anchor+'\n        self._action_start_ros_s = self.get_clock().now().nanoseconds / 1e9')
    p.write_text(s)
    report={'original_root':str(src),'new_root':str(out),'ports':['recorded physical-time causal snapshot lookup','PMFS belief estimate replaces terminal-pose fallback','action elapsed uses ROS clock'],
        'before':{k:hashlib.sha256(v).hexdigest() for k,v in old.items()},'after':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    (out/'BRG_ADAPTER_PORT.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
