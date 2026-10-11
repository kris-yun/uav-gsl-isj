"""Current isolated campaign helpers. No writes to historical evidence."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import subprocess,json,hashlib,time,base64,os
WORK=Path(__file__).resolve().parent
BASE=WORK.parents[1]
CORE=BASE/'outputs/PMFS_NATIVE_MECHANISM_CLOSURE_R1_20261011_CORE'
RAW=BASE/'outputs/PMFS_NATIVE_MECHANISM_CLOSURE_R1_20261011_RAW'
REMOTE='/home/zyc/ros2_ws/pmfs_native_mechanism_closure_r1_20261011'
DATA='/mnt/hgfs/workspace/PMFS_NATIVE_MECHANISM_CLOSURE_R1_DATA_20261011'
SSH=['ssh','-T','-i','C:/Users/50176/.ssh/id_ed25519_vm','-o','BatchMode=yes','-o','IdentitiesOnly=yes',
     '-o','ConnectTimeout=6','-o','StrictHostKeyChecking=yes','zyc@192.168.111.128']
def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    return h.hexdigest()
def run_remote(code,tag,timeout=60):
    assert time.time()-load(WORK/'ENTRY_TIME.json')['start_unix']<9000,'TOTAL_TASK_BUDGET_EXHAUSTED'
    compile(code,tag,'exec');start=time.perf_counter()
    p=subprocess.run(SSH+['python3 -'],input=code.encode(),capture_output=True,timeout=timeout)
    for suffix,data in [('stdout',p.stdout),('stderr',p.stderr)]:
        dest=WORK/(tag+'.'+suffix);assert not dest.exists();dest.write_bytes(data)
    if p.returncode:raise RuntimeError(dict(tag=tag,exitcode=p.returncode,stderr=p.stderr.decode(errors='replace')[-4000:]))
    return p.stdout.decode()
def upload(files,code,tag,timeout=60):
    blob={n:base64.b64encode(b).decode() for n,b in files.items()}
    prefix='from pathlib import Path\nimport base64,json\nt=Path('+repr(REMOTE)+')\nt.mkdir(parents=True,exist_ok=True)\n'
    prefix+='for n,b in '+repr(blob)+'.items():\n p=t/n;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists();p.write_bytes(base64.b64decode(b))\n'
    return run_remote(prefix+code,tag,timeout)

