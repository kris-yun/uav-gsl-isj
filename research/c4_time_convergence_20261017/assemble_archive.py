"""Reassemble bounded GitHub evidence parts; verify every SHA-256."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parent
m=json.loads((R/'evidence/ARCHIVE_PARTS.json').read_text(encoding='utf-8'))
dest=R/m['filename']
if dest.exists():
    assert hashlib.sha256(dest.read_bytes()).hexdigest()==m['whole_sha256']
    print('PASS_EXISTING_ARCHIVE',dest);raise SystemExit(0)
h=hashlib.sha256()
with dest.open('xb') as out:
    for a in m['parts']:
        p=R/a['path'];block=p.read_bytes()
        assert len(block)==a['bytes'] and hashlib.sha256(block).hexdigest()==a['sha256'],p
        h.update(block);out.write(block)
assert dest.stat().st_size==m['total_bytes'] and h.hexdigest()==m['whole_sha256']
print('PASS_REASSEMBLED_ARCHIVE',dest)
