import sys
sys.dont_write_bytecode=True
from pathlib import Path
import shutil
W=Path(__file__).resolve().parent
O=W.parents[1]/'outputs/PMFS_M2_PROCESS_OBSERVATION_DISCRIMINATION_20261010'
w=W/'independent_final_review'
dst=O/'independent_final_review'
if not dst.exists():shutil.copytree(w,dst)
s=(w/'independent_qa.py').read_text(encoding='utf-8')
s=s.replace("ROOT=BASE/'outputs/PMFS_M2_PROCESS_OBSERVATION_DISCRIMINATION_20261010'","ROOT=Path(__file__).resolve().parent")
start=s.index("local=BASE/'work/");end=s.index('result=dict(verdict=',start)
s=s[:start]+'coverage=[]\n'+s[end:]
s=s.replace("(HERE/'INDEPENDENT_FINAL_QA.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')",'')
(O/'verify_independent_scalar.py').write_text(s,encoding='utf-8',newline='\n')
print('Portable QA prepared; original reviewer source unchanged.')
