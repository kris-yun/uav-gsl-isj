#!/usr/bin/env python3
"""HGFS has no symlinks: add a verified occupancy copy, no gas decoding."""
import json,shutil,subprocess
from pathlib import Path
from resume_amended_f1_vm import R,O,FIRST,EX,sha,write,check_freeze

check_freeze()
f=json.loads((O/'ALL96_METADATA_FREEZE.json').read_text());assert f['passed']
cfg=json.loads((FIRST/'RUN_CONFIGURATION.json').read_text())
occ=Path(cfg['options']['occupancy3D_data'])
assert sha(occ)=='ac8c9e69e762c8941dab46cd7e804684c2aa50dc6f0912806d19b070c135c4af'
copies=[]
for r in f['runs']:
    dest=Path(r['run_directory'])/'realization/OccupancyGrid3D.csv'
    if not dest.exists():shutil.copyfile(occ,dest)
    assert sha(dest)==sha(occ)
    copies.append(str(dest))
linkage=subprocess.check_output(['ldd',str(EX)],text=True)
assert 'not found' not in linkage
expected='/home/zyc/hcmc_gaden_seed_build_20260922/install/gaden_common/lib/libgaden.so'
line=next(x for x in linkage.splitlines() if 'libgaden.so =>' in x)
assert line.split('=>',1)[1].strip().split()[0]==expected
p=json.loads((R/'timebase_logger/LOGGER_BUILD_PROVENANCE.json').read_text())
assert sha(expected)==p['seeded_numerical_library_sha256']
write(O/'EXTRACTION_INFRASTRUCTURE.json',dict(passed=True,copies=copies,occupancy_sha256=sha(occ),
      extractor_sha256=sha(EX),runtime_linkage=linkage,concentration_values_read=False,
      reason='HGFS rejects symlinks; copied unchanged occupancy bytes. No generator or reader changes.'))
