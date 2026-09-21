"""Create or verify the output-file SHA256 manifest without reading file semantics."""
import hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[2])
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
if sys.argv[1]=='create':
    payload={p.relative_to(root).as_posix():sha(p) for p in sorted(root.rglob('*')) if p.is_file() and p.name!='SHA256SUMS.json'}
    (root/'SHA256SUMS.json').write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
else:payload=json.loads((root/'SHA256SUMS.json').read_text())
assert set(payload)=={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p.name!='SHA256SUMS.json'}
assert all(sha(root/p)==h for p,h in payload.items())
print('SHA256_PASS',len(payload))
