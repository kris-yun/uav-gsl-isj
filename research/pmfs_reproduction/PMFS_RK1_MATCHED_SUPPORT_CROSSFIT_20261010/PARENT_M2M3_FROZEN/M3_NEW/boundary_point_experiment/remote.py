import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,subprocess
WORK=Path(__file__).resolve().parent
REMOTE='/home/zyc/pmfs_m3_root_discrimination_20261010/boundary_point_experiment'
def run(code,tag,timeout=45):
    compile(code,'remote_'+tag,'exec')
    c=json.loads(Path('D:/ZYC/FSR_S2_FIRST_USABLE_SCENARIO_V1_20261009T043938Z/production/finite_chain/S2_FIRST_ACTIVE_ROOT.json').read_text(encoding='utf-8'))
    args=['ssh','-T','-i',c['key'],'-o','BatchMode=yes','-o','IdentitiesOnly=yes','-o','ConnectTimeout=6','-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile='+c['known_hosts'],c['target'],'python3 -']
    p=subprocess.run(args,input=code.encode('utf-8'),capture_output=True,timeout=timeout)
    for suffix,b in [('stdout',p.stdout),('stderr',p.stderr)]:
        f=WORK/(tag+'.'+suffix);assert not f.exists();f.write_bytes(b)
    if p.returncode:raise RuntimeError(p.stderr.decode(errors='replace')[-4000:])
    return p.stdout.decode('utf-8')
