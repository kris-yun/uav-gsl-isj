import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,hashlib,subprocess,os
root=Path(__file__).resolve().parent
m=json.loads((root/'SHA256_MANIFEST.json').read_text(encoding='utf-8'))
actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p!=root/'SHA256_MANIFEST.json'}
assert actual==set(m),('unlisted/missing',actual^set(m))
for n,h in m.items():assert hashlib.sha256((root/n).read_bytes()).hexdigest()==h,('SHA256',n)
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1')
results={}
for name,args in [('M2',[root/'M2_FROZEN/verify_m2.py']),('M3',[root/'M3_NEW/verify_m3.py','--m2',root/'M2_FROZEN'])]:
    r=subprocess.run([sys.executable,'-B','-X','utf8',*map(str,args)],capture_output=True,text=True,encoding='utf-8',env=env)
    assert r.returncode==0,(name,r.stdout[-6000:],r.stderr[-6000:])
    results[name]=json.loads(r.stdout)
print(json.dumps(dict(status='PASS_COMBINED_FROZEN_M2_AND_NEW_M3',SHA256_members_passed=len(m),new_experiments_executed=0,results=results),ensure_ascii=False,indent=2))
