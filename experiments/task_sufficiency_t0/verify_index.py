"""Ensure staged Git bytes equal the evidence manifest before commit."""
import hashlib,subprocess
from pathlib import Path
import pandas as pd
root=Path(__file__).resolve().parents[2]
m=pd.read_csv(root/'evidence/task_sufficiency_t0_20261003/MANIFEST.csv')
result=subprocess.run(['git','cat-file','--batch'],cwd=root,input=''.join(':'+n+'\n' for n in m.path).encode(),capture_output=True,check=True)
data=result.stdout;position=0
for row in m.to_dict('records'):
 end=data.index(b'\n',position);header=data[position:end].split();size=int(header[2]);blob=data[end+1:end+1+size];position=end+size+2
 assert hashlib.sha256(blob).hexdigest()==row['sha256'],row['path']
changed=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=root,text=True).splitlines()
assert len(changed)==len(m)+1
assert all(n.startswith(('experiments/task_sufficiency_t0/','evidence/task_sufficiency_t0_20261003/')) for n in changed)
print(f'PASS: {len(m)} staged artifact hashes; {len(changed)} changes confined to new T0 directories; frozen previous evidence untouched')
