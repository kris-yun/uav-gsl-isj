"""Create a source/results SHA256 manifest. Run after tests, before handoff."""
from pathlib import Path
import hashlib,json,sys
root=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
out=root/'ARTIFACT_MANIFEST.json'
skip={'__pycache__','.pytest_cache','.git','.venv','node_modules'}
files=[]
for p in sorted(root.rglob('*')):
    if p.is_file() and p!=out and not any(part in skip for part in p.relative_to(root).parts):
        files.append({'path':str(p.relative_to(root)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
out.write_text(json.dumps({'schema':1,'scope':'engineering artifacts, not scientific success certificate','files':files},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'manifest':str(out),'files':len(files)}))
