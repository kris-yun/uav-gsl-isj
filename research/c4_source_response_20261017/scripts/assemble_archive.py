"""Reassemble research evidence from checked GitHub parts. Never overwrites an existing file."""
from pathlib import Path
import json,hashlib,shutil
B=Path(__file__).resolve().parent;manifest=json.loads((B/'evidence/ARCHIVE_PARTS.json').read_text())
out=B/manifest['filename'];assert not out.exists(),out
for part in manifest['parts']:
 p=B/part['path'];assert p.stat().st_size==part['bytes']
 with p.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==part['sha256'],p
with out.open('xb') as dest:
 for part in manifest['parts']:
  with (B/part['path']).open('rb') as src:shutil.copyfileobj(src,dest)
with out.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==manifest['whole_sha256']
print('PASS all parts and reconstructed archive SHA-256:',out)
