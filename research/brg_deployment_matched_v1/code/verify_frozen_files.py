from pathlib import Path
import subprocess,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
repo=ROOT.parents[1]
original=0
for line in (ROOT/'SHA256SUMS').read_text().splitlines():
    expected,name=line.split(maxsplit=1);name=name.lstrip('*')
    if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=expected:
        raise RuntimeError('original package file changed: '+name)
    original+=1
manifest=json.loads((ROOT/'evidence/INSTALL_FILE_HASHES.json').read_text())
for name,expected in manifest.items():
    if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=expected:raise RuntimeError('working file hash mismatch: '+name)
    path=(ROOT/name).relative_to(repo).as_posix()
    staged=subprocess.check_output(['git','show',':'+path],cwd=repo)
    if hashlib.sha256(staged).hexdigest()!=expected:raise RuntimeError('Git staged bytes differ: '+name)
print(json.dumps({'original_frozen_files_passed':original,'staged_byte_hashes_passed':len(manifest)}))
