"""Run the two inspected provided scripts into a new audit directory only."""
import sys
sys.dont_write_bytecode=True
import hashlib,json,os,subprocess,time
from pathlib import Path
W=Path(__file__).resolve().parent;ROOT=W.parents[2]
COMBINED=ROOT/'outputs/PMFS_M2_M3_COMBINED_ROOT_CAUSE_20261010'
M2ZIP=ROOT/'outputs/PMFS_M2_PROCESS_OBSERVATION_DISCRIMINATION_20261010_REVIEW.zip'
OUT=W/'pro_script_recompute';assert not OUT.exists()
ledger=[]
for script,extra in [('independent_readout_audit.py',['--m2-zip',str(M2ZIP)]),('same_bank_readout_contrast.py',[])]:
    src=W/'handoff/scripts'/script
    cmd=[sys.executable,'-B','-X','utf8',str(src),'--combined-root',str(COMBINED),'--out',str(OUT),*extra]
    start=time.perf_counter();r=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1'),timeout=120)
    (W/(script+'.stdout')).write_text(r.stdout,encoding='utf-8');(W/(script+'.stderr')).write_text(r.stderr,encoding='utf-8')
    ledger.append(dict(script=script,script_SHA256=hashlib.sha256(src.read_bytes()).hexdigest(),arguments=cmd[4:],returncode=r.returncode,wall_s=time.perf_counter()-start,new_forward_calls=0,new_gas=0))
    (W/'PRO_SCRIPT_EXECUTION_LEDGER.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if r.returncode:raise RuntimeError(script+' failed: '+r.stderr[-2000:])
    print(r.stdout)
