#!/usr/bin/env python3
import argparse, hashlib, json, platform, shutil, zipfile
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument('--final-commit',required=True)
a=ap.parse_args()
base=Path('/home/zyc/wind_contract_identity_audit_20260926')
stage=Path('/home/zyc/WIND_CONTRACT_IDENTITY_AUDIT_REVIEW_20260926')
archive=stage.with_suffix('.zip')
assert not stage.exists() and not archive.exists(), 'refuse package overwrite'
stage.mkdir()
shutil.copytree(base/'code',stage/'execution_code')
shutil.copytree(base/'evidence',stage/'evidence')
metadata={'branch':'research/wind-contract-identity-audit-v0-20260926',
          'base_commit':'583204fc06925dcb8725c4046cca29c48bf2abbf','final_commit':a.final_commit,
          'python':platform.python_version(),'platform':platform.platform(),
          'decision':'HOLD_Z_OR_TIME_SEMANTICS_UNRESOLVED',
          'supplied_analyzer_modified':False,'new_simulations':0,'localization_scores_computed':False}
(stage/'PACKAGE_PROVENANCE.json').write_text(json.dumps(metadata,indent=2,sort_keys=True)+'\n')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=sorted(p for p in stage.rglob('*') if p.is_file())
(stage/'SHA256SUMS.txt').write_text(''.join(f'{sha(p)}  {p.relative_to(stage).as_posix()}\n' for p in files))
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in sorted(stage.rglob('*')):
        if p.is_file():z.write(p,p.relative_to(stage).as_posix())
with zipfile.ZipFile(archive) as z: assert z.testzip() is None
print(f'archive={archive}\nbytes={archive.stat().st_size}\nsha256={sha(archive)}')
