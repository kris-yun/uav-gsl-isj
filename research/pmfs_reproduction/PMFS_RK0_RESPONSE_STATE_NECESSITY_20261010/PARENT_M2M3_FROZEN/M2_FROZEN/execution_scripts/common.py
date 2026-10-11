"""Isolated M2 task helpers; reuse original VM and never write old banks."""
import sys
sys.dont_write_bytecode=True
import base64,json,subprocess
from pathlib import Path
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
OUT=ROOT/'outputs/PMFS_M2_PROCESS_OBSERVATION_DISCRIMINATION_20261010'
OUT.mkdir(exist_ok=True)
REMOTE='/home/zyc/pmfs_m2_process_observation_20261010'
CONNECTION=Path('D:/ZYC/FSR_S2_FIRST_USABLE_SCENARIO_V1_20261009T043938Z/production/finite_chain/S2_FIRST_ACTIVE_ROOT.json')
def run(code,tag,timeout=45):
    c=json.loads(CONNECTION.read_text(encoding='utf-8'))
    args=['ssh','-T','-i',c['key'],'-o','BatchMode=yes','-o','IdentitiesOnly=yes','-o','ConnectTimeout=6',
          '-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile='+c['known_hosts'],c['target'],'python3 -']
    compile(code,'remote_'+tag,'exec')
    p=subprocess.run(args,input=code.encode(),capture_output=True,timeout=timeout)
    for suffix,data in [('stdout',p.stdout),('stderr',p.stderr)]:
        dest=W/(tag+'.'+suffix);assert not dest.exists();dest.write_bytes(data)
    if p.returncode:raise RuntimeError(p.stderr.decode(errors='replace')[-3500:])
    return p.stdout.decode()
def upload(files,code,tag,timeout=45):
    data={name:base64.b64encode(b).decode() for name,b in files.items()}
    prefix='from pathlib import Path\nimport base64,json\nt=Path('+repr(REMOTE)+')\nt.mkdir(exist_ok=True)\n'
    prefix+='for n,b in '+repr(data)+'.items():\n p=t/n;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists();p.write_bytes(base64.b64decode(b))\n'
    return run(prefix+code,tag,timeout)
