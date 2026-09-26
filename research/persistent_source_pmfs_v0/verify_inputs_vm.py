#!/usr/bin/env python3
import hashlib, json, shutil
from pathlib import Path
old = Path('/home/zyc/native_pmfs_recovery_v1/runs/R1_R2_SOURCE_CORRECTED_House01_S0_20260923')
new = Path('/home/zyc/persistent_source_r1_source_blind_20260926')
manifest = json.loads((old/'r1_scores_frozen_manifest.json').read_text())
assert manifest['truth_inputs_read'] is False
names = ('measurement_events.csv','measured_map_at_update.csv',
         'frozen_candidate_geometry.csv','wind_source_update.csv')
new.mkdir(exist_ok=False)
verified={}
for name in names:
    raw=(old/name).read_bytes()
    actual=hashlib.sha256(raw).hexdigest()
    assert actual==manifest['source_blind_inputs'][name],name
    (new/name).write_bytes(raw)
    verified[name]=actual
(new/'INPUT_SHA256.json').write_text(json.dumps(verified,indent=2)+'\n')
print('R1_SOURCE_BLIND_INPUT_HASHES_PASS',json.dumps(verified))
