"""R2 isolated helpers; immutable R1 is referenced, never mutated."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,time,hashlib,subprocess,base64,os
WORK=Path(__file__).resolve().parent;BASE=WORK.parents[1]
CORE=BASE/'outputs/PMFS_FULL_DOMAIN_R2_20261011_CORE';RAW=BASE/'outputs/PMFS_FULL_DOMAIN_R2_20261011_RAW'
R1=BASE/'outputs/PMFS_NATIVE_MECHANISM_CLOSURE_R1_20261011_CORE'
R1RAW=BASE/'outputs/PMFS_NATIVE_MECHANISM_CLOSURE_R1_20261011_RAW'
REMOTE='/home/zyc/ros2_ws/pmfs_full_domain_r2_20261011'
DATA='/mnt/hgfs/workspace/PMFS_FULL_DOMAIN_R2_DATA_20261011'
HOST=Path('D:/ZYC/A-gas/workspace/PMFS_FULL_DOMAIN_R2_DATA_20261011')
SSH=['ssh','-T','-i','C:/Users/50176/.ssh/id_ed25519_vm','-o','BatchMode=yes','-o','IdentitiesOnly=yes','-o','ConnectTimeout=6','-o','StrictHostKeyChecking=yes','zyc@192.168.111.128']
def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def remote(code,tag,timeout=60):
 assert time.time()-load(WORK/'ENTRY_TIME.json')['start_unix']<14400,'R2_TOTAL_BUDGET'
 compile(code,tag,'exec');assert not (WORK/(tag+'.stdout')).exists()
 p=subprocess.run(SSH+['python3 -'],input=code.encode(),capture_output=True,timeout=timeout)
 for suffix,value in [('stdout',p.stdout),('stderr',p.stderr)]:(WORK/(tag+'.'+suffix)).write_bytes(value)
 assert p.returncode==0,dict(tag=tag,exitcode=p.returncode,stderr=p.stderr.decode(errors='replace')[-4000:])
 return p.stdout.decode()
def upload(files,code,tag,timeout=60):
 data={k:base64.b64encode(v).decode() for k,v in files.items()}
 pre='from pathlib import Path\nimport json,base64\nt=Path('+repr(REMOTE)+');t.mkdir(parents=True,exist_ok=True)\n'
 pre+='for n,b in '+repr(data)+'.items():\n p=t/n;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists();p.write_bytes(base64.b64decode(b))\n'
 return remote(pre+code,tag,timeout)
