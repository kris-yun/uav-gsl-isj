#!/usr/bin/env python3
import hashlib,json
from pathlib import Path
ROOT=Path('/home/zyc/qa_pmfs_crossenv_f1_20260926')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not (ROOT/'result').exists() and not (ROOT/'repeat').exists()
assert sha(ROOT/'execution/G7_PRE_TARGET_AMENDMENT.md')=='7d5d865050afc4eb0e851a339a076873574fea70b9d92beda493a4438ee1d007'
for line in (ROOT/'protocol/SHA256SUMS.txt').read_text().splitlines():
    expected,name=line.split('  ',1);assert sha(ROOT/'protocol'/name)==expected
model=json.loads((ROOT/'reference_freeze/PRE_TARGET_MODEL_LOCK.json').read_text())
assert model['reference_only'] and not model['target_files_opened']
items=[p for d in ('execution','protocol','reference_freeze','audit','g7_amendment') for p in sorted((ROOT/d).rglob('*')) if p.is_file() and '__pycache__' not in p.parts]
record={'asset_audit_commit':(ROOT/'asset_audit_commit.txt').read_text().strip(),'G7_amendment_sha256':sha(ROOT/'execution/G7_PRE_TARGET_AMENDMENT.md'),'G7_zip_sha256':'c2c0f75b5c0a37b832463c86f6a8f0f4d5945318ccf283e27e840182f5e415e4','main_package_sha256':'ab8287c467887b6e843f8ef63262ae0dbd3ad079520bb5fc4e33b1f10daaf9c3','fresh_targets_read':False,'selected_models':model['models'],'frozen_hashes':{str(p.relative_to(ROOT)):sha(p) for p in items}}
(ROOT/'PRE_TARGET_FREEZE.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
print('QA_F1_PRE_TARGET_FREEZE_COMPLETE',record['G7_amendment_sha256'])
