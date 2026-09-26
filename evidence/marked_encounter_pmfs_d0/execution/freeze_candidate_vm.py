#!/usr/bin/env python3
import hashlib,json
from pathlib import Path
R=Path('/home/zyc/marked_encounter_pmfs_d0_20260927')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert json.loads((R/'NATIVE_PARITY.json').read_text())['pass']
assert json.loads((R/'BANK_REPEAT.json').read_text())['pass']
assert json.loads((R/'forward/FORWARD_MANIFEST.json').read_text())['forward_count']==1584
assert not (R/'evaluation').exists()
paths=[]
for folder in ('execution','protocol','inputs','kernel'):
    paths.extend(p for p in (R/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
paths.extend(R/p for p in ['NATIVE_PARITY.json','BANK_REPEAT.json','build_provenance.json','forward/candidate_mark_bank.csv','forward/FORWARD_MANIFEST.json'])
result={'base_commit':'d3afac6488a9ee797f7e8d3289b485729fc5da31','definition_commit':'cf4f14dc47af028446fec9163419217258fe12f3','target_rank_read_before_freeze':False,'U_amendment_authorized_by_user':True,'files':{str(p.relative_to(R)):sha(p) for p in sorted(paths)}}
(R/'CANDIDATE_FREEZE.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print('CANDIDATE_BANK_FROZEN',len(paths),sha(R/'CANDIDATE_FREEZE.json'))
