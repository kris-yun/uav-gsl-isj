#!/usr/bin/env python3
"""Copy-only raw archives, validated against VM metadata; no gas decoding."""
import hashlib,json,zipfile
from pathlib import Path
ROOT=Path(r'C:\Users\50176\Downloads\AOD_F1_AMENDED_RAW_ARCHIVE_20260927')
SHARED=Path(r'D:\ZYC\A-gas\workspace\_staging\AOD_F1_AMENDED_TARGETS_20260927')
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
ROOT.mkdir(exist_ok=True)
for meta in sorted((ROOT/'metadata').glob('*.json')):
    rec=json.loads(meta.read_text());name=meta.stem
    registry=ROOT/(name+'.archive.json')
    if registry.exists():continue
    src=ROOT/'source_0_replica_0' if rec['first_reused'] else SHARED/name
    archive=ROOT/(name+'.zip')
    assert not archive.exists(),f'Preserve incomplete archive: {archive}'
    for n,h in rec['files_sha256'].items():assert sha(src/n)==h,(name,n)
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as z:
        for n in sorted(rec['files_sha256']):z.write(src/n,n)
        z.writestr('RAW_FILES_SHA256.json',json.dumps(rec['files_sha256'],indent=2,sort_keys=True)+'\n')
        z.writestr('RUN_METADATA.json',json.dumps(rec,indent=2,sort_keys=True)+'\n')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for n,h in rec['files_sha256'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h,(name,n)
    registry.write_text(json.dumps(dict(archive_path=str(archive),bytes=archive.stat().st_size,
        sha256=sha(archive),run_id=name,files=len(rec['files_sha256']),verified=True,
        original_preserved=True,concentration_values_decoded=False),indent=2)+'\n')
    print('RAW_ARCHIVED_VERIFIED',name,archive.stat().st_size,flush=True)
