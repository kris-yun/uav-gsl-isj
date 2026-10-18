from pathlib import Path
import json,hashlib,argparse,subprocess,sys,csv,os
R=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--verify-only',action='store_true');p.add_argument('--analysis-out',type=Path);a=p.parse_args()
manifest=json.loads((R/'MANIFEST_SHA256.json').read_text(encoding='utf8'))
for n,v in manifest.items():
    q=R/n;assert q.stat().st_size==v['bytes'] and hashlib.sha256(q.read_bytes()).hexdigest()==v['sha256'],n
print('PASS_MANIFEST',len(manifest),flush=True)
if a.verify_only:raise SystemExit(0)
assert a.analysis_out and not a.analysis_out.exists(),'Choose a new output directory'
env=dict(os.environ,AIMMD_ANALYSIS_OUT=str(a.analysis_out.resolve()),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
subprocess.run([sys.executable,str(R/'analyze.py')],env=env,stdout=subprocess.DEVNULL,check=True)
count=0
for old in (R/'analysis').glob('*.csv'):
    new=a.analysis_out/old.name;assert list(csv.DictReader(old.open(encoding='utf8')))==list(csv.DictReader(new.open(encoding='utf8'))),old.name;count+=1
for n in ['CHECKS.json','DECISION.json']:
    assert json.loads((R/'analysis'/n).read_text(encoding='utf8'))==json.loads((a.analysis_out/n).read_text(encoding='utf8'))
(a.analysis_out/'REPLAY_PASS.json').write_text(json.dumps(dict(status='PASS_EXACT_FRESH_STORED_RESULT_ANALYSIS',CSV_tables=count,new_forward_calls=0),indent=2))
print('PASS_EXACT_STORED_RESULT_ANALYSIS',count)
