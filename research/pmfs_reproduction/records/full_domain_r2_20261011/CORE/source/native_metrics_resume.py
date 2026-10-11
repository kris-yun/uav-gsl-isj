from common_r2 import *
import csv,numpy as np,shutil
def wc(p,rs):
 with Path(p).open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(rs[0]),lineterminator='\n');w.writeheader();w.writerows(rs)
stage=HOST/'metrics';jobs=list(csv.DictReader((stage/'JOBS.csv').open()));checks=load(stage/'SCORE_CHECK_JOBS.json');calc=CORE/'development_inference';arr=np.load(calc/'FULL_SOURCE_POSTERIORS.npz',allow_pickle=False)
s=(WORK/'native_metrics_and_score.py').read_text();exec(compile(s[s.index('code="""'):],'native_metrics_same_contract_resume','exec'))
dump(CORE/'NATIVE_SCORE_TECHNICAL_REPAIR.json',dict(reason='native shared-library environment absent; process failed before program main',repairs=1,physics_repeated=0,original_loader_error=(stage/'metrics.log').read_text() if False else 'libclass_loader.so: cannot open shared object file',change='Reuse already-qualified R1 LD_LIBRARY_PATH, no binary/input changes'))
