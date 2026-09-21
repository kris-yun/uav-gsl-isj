"""Create an isolated, hash-bound lifecycle overlay; no scientific computation edits."""
import hashlib,json,pathlib,shutil,sys
here=pathlib.Path(__file__).resolve().parent
source=pathlib.Path('/dev/shm/house1_vgr_bridge/vgr_bridge')
target=pathlib.Path(sys.argv[1]); assert not target.exists()
hashes=json.loads((here/'external_runtime_hashes.json').read_text())
for name,digest in hashes.items():
    assert hashlib.sha256((source/name).read_bytes()).hexdigest()==digest,name
shutil.copytree(source,target/'vgr_bridge',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
node=target/'vgr_bridge/vgr_sim_node.py'; s=node.read_text()
anchor='    def _simulation_tick(self):\n'
assert s.count(anchor)==1
s=s.replace(anchor,anchor+'''        # Hard freeze: no measurement, FOPDT, navigation, or clock advancement.
        # Only ROS service/action cleanup remains live after the last 300 s tick.
        if self.sim_stop_at_s >= 0.0 and self.t_sim_s >= self.sim_stop_at_s:
            if not getattr(self, '_terminal_horizon_logged', False):
                self.get_logger().info(f'SCIENTIFIC_STATE_FROZEN t_sim={self.t_sim_s:.9f} step={self.step_count}')
                self._terminal_horizon_logged = True
            return
''')
node.write_text(s)
bench=target/'vgr_bridge/gsl_benchmark_runner.py'; s=bench.read_text()
old='self.create_timer(self.time_budget_s + 0.5, self._timeout_callback)'
assert s.count(old)==1
s=s.replace(old,'self.create_timer(900.0, self._timeout_callback) # infrastructure watchdog; simulator enforces scientific budget')
bench.write_text(s)
(target/'runtime_provenance.json').write_text(json.dumps({'baseline_sha256':hashes,'patched_sha256':{n:hashlib.sha256((target/'vgr_bridge'/n).read_bytes()).hexdigest() for n in hashes}},indent=2)+'\n')
print(target)
