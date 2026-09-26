#!/usr/bin/env python3
import csv, hashlib, json, shutil
from pathlib import Path
from score_frozen_r1_maps import EXPECTED

historical=Path('/home/zyc/native_pmfs_recovery_v1/runs/R1_R2_SOURCE_CORRECTED_House01_S0_20260923')
dest=Path('/home/zyc/pmfs_evidence_pseudoreplication_20260926/inputs')
assert not dest.exists(), 'refuse input overwrite'
manifest=json.loads((historical/'r1_scores_frozen_manifest.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sources={'measurement_events.csv':historical/'measurement_events.csv',
         'measured_map_at_update.csv':historical/'measured_map_at_update.csv',
         'C_candidate_scores.csv':historical/'R1_arm_C/candidate_scores.csv'}
for name,p in sources.items():
    assert sha(p)==EXPECTED[name], 'input hash mismatch: '+name
    historical_sha=(manifest['arms']['C']['scores_sha256'] if name=='C_candidate_scores.csv'
                    else manifest['source_blind_inputs'][name])
    assert sha(p)==historical_sha, 'manifest hash mismatch: '+name
with sources['C_candidate_scores.csv'].open(newline='') as f:
    candidates=list(csv.DictReader(f))
assert len(candidates)==87
for c in candidates:
    p=historical/'R1_arm_C'/c['map_file']
    assert sha(p)==manifest['arms']['C']['candidate_map_sha256'][c['candidate_id']], c['candidate_id']
dest.mkdir(parents=True)
(dest/'maps').mkdir()
for name,p in sources.items(): shutil.copyfile(p,dest/name)
shutil.copyfile(historical/'r1_scores_frozen_manifest.json',dest/'r1_scores_frozen_manifest.json')
for c in candidates:
    shutil.copyfile(historical/'R1_arm_C'/c['map_file'],dest/'maps'/Path(c['map_file']).name)
files=sorted(p for p in dest.rglob('*') if p.is_file())
(dest/'INPUT_SHA256SUMS.txt').write_text(''.join(f'{sha(p)}  {p.relative_to(dest).as_posix()}\n' for p in files))
print('FROZEN_INPUT_HASH_PASS C_MAPS=87 NO_TRUTH_INPUT')
