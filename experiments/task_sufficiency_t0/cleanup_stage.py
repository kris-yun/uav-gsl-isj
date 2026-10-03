"""Remove only copied native inputs inside this experiment staging directory."""
from pathlib import Path
import shutil
root=Path('/home/zyc/task_sufficiency_t0_20261003').resolve()
assert str(root)=='/home/zyc/task_sufficiency_t0_20261003'
for p in root.glob('ocb_r2_*'):
 assert p.resolve().parent==root and p.is_dir()
 shutil.rmtree(p)
