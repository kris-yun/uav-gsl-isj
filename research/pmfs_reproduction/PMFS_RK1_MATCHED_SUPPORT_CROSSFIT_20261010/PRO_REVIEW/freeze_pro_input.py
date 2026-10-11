"""Freeze provided PRO ZIP into this new review directory; no research inputs changed."""
import hashlib,json,zipfile
from pathlib import Path,PurePosixPath
W=Path(__file__).resolve().parent
p=Path('C:/Users/50176/Downloads/PRO_M2M3_独立复核与跨领域机制候选_20261010.zip')
sha=lambda b:hashlib.sha256(b).hexdigest()
b=p.read_bytes();digest=sha(b)
assert digest=='d5ab72cc9d3aef5e10cf5a2d05458f101c7b52bb2faa36c6db8e15e65ebc456d'
dest=W/'handoff';assert not dest.exists();dest.mkdir(parents=True)
with zipfile.ZipFile(p) as z:
    assert z.testzip() is None
    declared=json.loads(z.read('SHA256_MANIFEST.json'));contents=[]
    for info in z.infolist():
        name=PurePosixPath(info.filename)
        assert not name.is_absolute() and '..' not in name.parts and ':' not in name.parts[0]
        if info.is_dir():continue
        data=z.read(info.filename)
        if info.filename in declared:assert sha(data)==declared[info.filename]
        target=dest.joinpath(*name.parts);assert target.resolve().is_relative_to(dest.resolve())
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        contents.append(dict(path=info.filename,bytes=len(data),SHA256=sha(data),declared_hash_pass=info.filename in declared))
assert len(contents)==22 and len(declared)==21
(W/'PRO_PACKAGE_FREEZE.json').write_text(json.dumps(dict(original_path=str(p),ZIP_bytes=len(b),ZIP_SHA256=digest,ZIP_CRC_pass=True,declared_hashes_passed=21,total_members=22,contents=contents),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(W/'ORIGINAL_PRO_PACKAGE.zip').write_bytes(b)
print(json.dumps(dict(ZIP_SHA256=digest,declared_hashes_passed=21,total_members=22),indent=2))
