from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parent
m=json.loads((R/'FINAL_MANIFEST_SHA256.json').read_text(encoding='utf-8'))
for x in m['files']:
 p=R/x['path'];assert p.stat().st_size==x['bytes'];assert hashlib.sha256(p.read_bytes()).hexdigest()==x['sha256'],x['path']
print(json.dumps(dict(status='PASS_FINAL_MANIFEST',files=len(m['files']))))
