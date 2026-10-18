from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parent
m=json.loads((r/'MANIFEST_SHA256.json').read_text(encoding='utf-8'))
for a in m['files']:
 p=r/a['path'];assert p.is_file()and hashlib.sha256(p.read_bytes()).hexdigest()==a['sha256'],a['path']
print(json.dumps(dict(status='PASS_ALL_PAYLOAD_SHA256',files=len(m['files']))))
