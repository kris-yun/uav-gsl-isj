"""Preserve failed pre-clock adapter attempt, without deleting or modifying inputs."""
from pathlib import Path
import json
root=Path('/home/zyc/d1a_common_replay_20260930').resolve()
path=root/'runs/ocb_r2_cfg00_r01/on'
assert path.resolve().is_relative_to(root)
assert not (path/'clock_start.log').exists()
assert not (path/'beliefs.jsonl').exists(),'do not relaunch an exposed scientific target'
(path/'execution_status.json').write_text(json.dumps(dict(status='PRE_CLOCK_INFRASTRUCTURE_FAILURE',reason='VGR requires tab-separated timeline; no clock start or Native belief',target_executions=0),indent=2)+'\n')
for kind in ['runs','views']:
    p=root/kind/'ocb_r2_cfg00_r01/on'
    dest=p.with_name('preclock_time_delimiter_failure')
    assert p.resolve().is_relative_to(root) and not dest.exists()
    p.rename(dest)
