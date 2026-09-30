#!/usr/bin/env python3
"""Collect supplied instruction and official PMFS code without extracting the archive."""
import hashlib,json,zipfile
from pathlib import Path
REPO=Path(__file__).resolve().parents[2]
OUT=REPO/'evidence/pmfs_3d_author_limitation_d0'
ARCHIVE=Path('D:/ZYC/A-gas/ASCi/GasSourceLocalization-humble.zip')
REQUEST=Path('D:/ZYC/UAV/.codex/attachments/7bb4c4f5-db93-4957-b599-33ad087b7fae/已粘贴的文本.txt')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'USER_REQUEST.txt').write_bytes(REQUEST.read_bytes())
names=['PMFS.hpp','PMFSLib.cpp','PMFSLib.hpp','internal/Simulations.cpp','internal/Simulations.hpp','internal/Settings.hpp','internal/HitProbability.hpp']
source=[]
with zipfile.ZipFile(ARCHIVE) as z:
 for name in names:
  matches=[f for f in z.namelist() if f.endswith('/algorithms/PMFS/'+name)];assert len(matches)==1,(name,matches)
  payload=z.read(matches[0]);out=OUT/'official_source'/name;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(payload)
  source.append(dict(archive_member=matches[0],file=name,sha256=sha(out),bytes=len(payload)))
obj=dict(archive_path=str(ARCHIVE),archive_sha256=sha(ARCHIVE),request_sha256=sha(REQUEST),files=source,
         untouched_official_archive=True,production_source_modified=False)
(OUT/'SOURCE_SNAPSHOT.json').write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
print(json.dumps(dict(official_source_files=len(source),archive_sha256=obj['archive_sha256'])))
