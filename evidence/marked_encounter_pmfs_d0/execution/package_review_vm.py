#!/usr/bin/env python3
import hashlib,json,zipfile
from pathlib import Path
R=Path('/home/zyc/marked_encounter_pmfs_d0_20260927')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert json.loads((R/'BANK_REPEAT.json').read_text())['pass']
assert json.loads((R/'EVALUATION_REPEAT.json').read_text())['pass']
files=[]
for folder in ('protocol','execution','kernel','inputs','evaluation','evaluation_repeat','parity_off','parity_on','forward','forward_repeat'):
    files.extend(p for p in (R/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
files.extend(R/n for n in ['NATIVE_PARITY.json','BANK_REPEAT.json','EVALUATION_REPEAT.json','CANDIDATE_FREEZE.json','candidate_freeze_commit.txt','build_provenance.json','initial_export_hashes.txt','build.log','parity_off.log','parity_on.log','EXECUTION_PROVENANCE.json'])
files=sorted(files)
inventory=''.join(sha(p)+'  '+str(p.relative_to(R))+'\n' for p in files)
(R/'SHA256SUMS').write_text(inventory)
target=R/'MARKED_ENCOUNTER_PMFS_D0_REVIEW_20260927.zip'
assert not target.exists(),'refuse overwrite'
with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in [*files,R/'SHA256SUMS']:
        info=zipfile.ZipInfo(str(p.relative_to(R)),date_time=(2026,9,27,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
        z.writestr(info,p.read_bytes())
with zipfile.ZipFile(target) as z:
    for line in inventory.splitlines():
        h,name=line.split('  ',1);assert hashlib.sha256(z.read(name)).hexdigest()==h,name
meta={'path':str(target),'bytes':target.stat().st_size,'sha256':sha(target),'inventory_file_count':len(files),'internal_inventory_verified':True}
(R/'REVIEW_PACKAGE.json').write_text(json.dumps(meta,indent=2,sort_keys=True)+'\n')
print(json.dumps(meta,indent=2))
