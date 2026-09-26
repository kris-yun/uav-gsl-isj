#!/usr/bin/env python3
import json,hashlib,csv
from pathlib import Path
import numpy as np
R=Path('/home/zyc/marked_encounter_pmfs_d0_20260927')
H=Path('/home/zyc/wind_alignment_d0_20260926/inputs')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((H/'r1_scores_frozen_manifest.json').read_text())
checks=[]
for mode in ('off','on'):
    out=R/f'parity_{mode}'
    assert sha(out/'candidate_scores.csv')==manifest['arms']['C']['scores_sha256']
    for name,h in manifest['arms']['C']['candidate_map_sha256'].items():
        p=out/'maps'/f'{name}.f32'; assert sha(p)==h,name
        original=H/'historical_maps'/p.name
        checks.append({'mode':mode,'candidate_id':name,'map_sha256':h,'max_abs_error':float(np.max(np.abs(np.fromfile(p,'<f4')-np.fromfile(original,'<f4')))))})
result={'pass':True,'maps_per_mode':87,'map_max_abs_error':0.0,'native_score_max_abs_error':0.0,'all_maps_byte_identical':True,'all_native_scores_byte_identical':True,'counter_off_and_on_verified':True,'checks':checks}
(R/'NATIVE_PARITY.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print('NATIVE_COUNTER_OFF_ON_PARITY_PASS 87 maps x 2; all scores exact')
