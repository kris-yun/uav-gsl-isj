"""Isolated post-export truth writer. Never imported by anchor or query code."""
import json, sys
from pathlib import Path

out=Path(sys.argv[1])
assert json.loads((out/'integrity_audit.json').read_text())['status']=='PASS'
assert not (out/'truth_eval.json').exists()
root=Path('/home/zyc/ros2_ws/tnqc_r2_six_offline_20260921_authoritative')
frozen=json.loads((root/'freeze/preregistration.json').read_text())
truth={}
for case in frozen['resolved_cases']:
    a=case['launch_arguments'];key=f"{case['house']}_seed{case['seed']}"
    truth[key]=dict(source_xyz_m=[float(a['source_'+axis]) for axis in ('x','y','z')],
        scenario_id=a['scenario_id'],environment_id=a['environment_id'])
(out/'truth_eval.json').write_text(json.dumps(dict(policy='Evaluation only; written after raw export and integrity freeze; never read by export scripts.',cases=truth),indent=2)+'\n')
print('TRUTH_SIDECAR_WRITTEN')
