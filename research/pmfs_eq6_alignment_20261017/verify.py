from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parent
m=json.loads((R/'MANIFEST_SHA256.json').read_text(encoding='utf-8'))
for r in m['files']:
 p=R/r['path'];assert p.stat().st_size==r['bytes'],r['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'],r['path']
print(json.dumps(dict(status='PASS',files=len(m['files']))))
