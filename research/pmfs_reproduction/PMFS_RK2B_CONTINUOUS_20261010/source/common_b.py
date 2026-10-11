"""Current-task local/remote helpers. Never modify prior banks or source trees."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import subprocess,json,hashlib,base64,time,os
WORK=Path(__file__).resolve().parent;BASE=WORK.parents[1]
CORE=BASE/'outputs/PMFS_RK2B_CONTINUOUS_20261010_CORE'
RAW=BASE/'outputs/PMFS_RK2B_RAW_SUPPORT_20261010'
PARENT=BASE/'outputs/PMFS_RK2_PROTOTYPE_REVIEW_BUNDLE_20261010'
RK1=BASE/'outputs/PMFS_RK1_PRO_REVIEW_BUNDLE_20261010'
REMOTE='/home/zyc/ros2_ws/pmfs_rk2b_continuous_20261010'
DATA='/mnt/hgfs/workspace/PMFS_RK2B_DATA_20261010'
SSH=['ssh','-T','-i','C:/Users/50176/.ssh/id_ed25519_vm','-o','BatchMode=yes','-o','IdentitiesOnly=yes','-o','ConnectTimeout=6','-o','StrictHostKeyChecking=yes','zyc@192.168.111.128']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def run_remote(code,tag,timeout=60):
    compile(code,'remote_'+tag,'exec');started=time.perf_counter()
    p=subprocess.run(SSH+['python3 -'],input=code.encode(),capture_output=True,timeout=timeout)
    for ext,data in [('stdout',p.stdout),('stderr',p.stderr)]:
        q=WORK/(tag+'.'+ext);assert not q.exists();q.write_bytes(data)
    if p.returncode:raise RuntimeError(p.stderr.decode(errors='replace')[-3000:])
    return p.stdout.decode()
def upload(files,tail,tag,timeout=60):
    content={n:base64.b64encode(b).decode() for n,b in files.items()}
    code='from pathlib import Path\nimport json,base64\nt=Path('+repr(REMOTE)+')\nt.mkdir(parents=True,exist_ok=True)\n'
    code+='for n,b in '+repr(content)+'.items():\n p=t/n;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists();p.write_bytes(base64.b64decode(b))\n'
    return run_remote(code+tail,tag,timeout)
