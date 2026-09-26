from pathlib import Path
import hashlib
import json
import sys
root=Path(__file__).resolve().parent
entries=json.loads((root/'MANIFEST.json').read_text(encoding='utf8'))
bad=[]
for entry in entries:
    p=root/entry['path']
    if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=entry['sha256']:
        bad.append(entry['path'])
print(f"Checked {len(entries)} files; mismatches: {bad}")
sys.exit(bool(bad))
