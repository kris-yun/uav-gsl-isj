#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=/mnt/hgfs/workspace/_vm_worktrees/pmfs3d-o0-20261001
WORK_ROOT=/mnt/hgfs/workspace/PMFS3D_O0_PROJECTED2D_20261001
export ROOT WORK_ROOT O0_PRESERVE_WORK_ROOT="$WORK_ROOT"
mkdir -p "$WORK_ROOT/runtime/bin"
cp "$ROOT/research/pmfs3d_o0/runtime_preservation/sitecustomize.py" "$WORK_ROOT/runtime/"
printf '#!/bin/sh\nexec /usr/bin/python3 "$@"\n' > "$WORK_ROOT/runtime/bin/python"
printf '#!/bin/sh\nexec /usr/bin/git -c core.fileMode=false "$@"\n' > "$WORK_ROOT/runtime/bin/git"
chmod +x "$WORK_ROOT/runtime/bin/python" "$WORK_ROOT/runtime/bin/git"
export PATH="$WORK_ROOT/runtime/bin:$PATH"
export PYTHONPATH="$WORK_ROOT/runtime${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONUNBUFFERED=1
set +u
source /opt/ros/humble/setup.bash
source /home/zyc/hcmc_gaden_seed_build_20260922/install/setup.bash
set -u
export LD_LIBRARY_PATH="/home/zyc/hcmc_gaden_seed_build_20260922/build/gaden_common/third_party/gaden_core/third_party/libbsc:/home/zyc/hcmc_gaden_seed_build_20260922/install/gaden_common/lib:${LD_LIBRARY_PATH:-}"
cd "$ROOT"
python - <<'PY'
import hashlib,json,os,shutil,subprocess
from pathlib import Path
import numpy as np
root=Path(os.environ['ROOT']); work=Path(os.environ['WORK_ROOT'])
bank=root/'evidence/causal_compositional_plume_world_model_v1/c0_5_real_gaden_bank'
summary=json.loads((bank/'spatial_summary.json').read_text())
records=[]
for sid in ('S1','S2'):
    for rep in ('A','B'):
        name=f'{sid}_W1_{rep}'; file=bank/'realizations'/name/'concentration.npy'
        digest=hashlib.sha256(file.read_bytes()).hexdigest()
        assert digest==summary['cells'][name]['sha256'], name
        array=np.load(file,allow_pickle=False)
        assert array.shape==(10,83,119) and np.isfinite(array).all() and (array>=0).all()
        records.append({'run':name,'path':str(file),'sha256':digest,'shape':list(array.shape)})
assert shutil.disk_usage(work).free > 1024**3
cached=[]
if (work/'projected2d_runs').exists():
    for run in sorted((work/'projected2d_runs').iterdir()):
        assert run.name in ('S1_A','S1_B','S2_A','S2_B')
        metadata=json.loads((run/'run_metadata.json').read_text())
        assert hashlib.sha256((run/'concentration.npy').read_bytes()).hexdigest()==metadata['cube_sha256']
        assert (run/'RAW_PRESERVATION.json').is_file()
        cached.append(run.name)
out=root/'evidence/pmfs3d_o0_projected2d_20261001'; out.mkdir(parents=True,exist_ok=True)
record={'frozen_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'reference_cubes':records,'work_root':str(work),'available_bytes':shutil.disk_usage(work).free,
        'python':'/usr/bin/python3','OMP_NUM_THREADS':os.environ.get('OMP_NUM_THREADS'),
        'storage_change':'retain new filament directories rather than deleting unique raw data',
        'completed_runs_reused_without_simulation':cached,'scientific_parameters_changed':False}
name='PRE_RESUME_ASSET_AUDIT.json' if (out/'PRE_RUN_ASSET_AUDIT.json').exists() else 'PRE_RUN_ASSET_AUDIT.json'
(out/name).write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
print('PRE_RUN_ASSET_AUDIT_PASS')
PY
bash research/pmfs3d_o0/run_pmfs3d_o0_remote.sh
