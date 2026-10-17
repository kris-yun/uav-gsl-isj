"""Verify or replay this self-contained OFFLINE source-time diagnostic."""
from pathlib import Path
import argparse,csv,hashlib,json,os,shutil,subprocess,sys
R=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--verify-only',action='store_true');p.add_argument('--analysis-out',type=Path);p.add_argument('--full-forward-out',type=Path);a=p.parse_args()
manifest=json.loads((R/'MANIFEST_SHA256.json').read_text(encoding='utf-8'))
for name,v in manifest.items():
    h=hashlib.sha256()
    with (R/name).open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    got=h.hexdigest()
    assert got==v['sha256'] and (R/name).stat().st_size==v['bytes'],name
print('PASS_MANIFEST_SHA256',len(manifest),flush=True)
if a.verify_only:raise SystemExit(0)
assert bool(a.analysis_out)!=bool(a.full_forward_out),'Choose --analysis-out NEW or --full-forward-out NEW'
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
if a.full_forward_out:
    assert os.name=='posix','Forward build needs Linux, CMake, C++20, OpenCV core/imgproc and zlib'
    W=a.full_forward_out.resolve();assert not W.exists();W.mkdir(parents=True)
    for name in ['code','scripts','inputs']:shutil.copytree(R/name,W/name)
    for name in ['diagnostic.cpp','FROZEN_PLAN.json','INPUT_MANIFEST_SHA256.json']:shutil.copy2(R/name,W/name)
    for name in ['logs','lineage','results']:(W/name).mkdir()
    subprocess.run([sys.executable,str(W/'scripts/run.py'),'--build',str(W/'build')],env=env,check=True)
    subprocess.run([sys.executable,str(W/'scripts/analyze.py')],env=env,check=True)
    print('PASS_FRESH_FULL_FROZEN_OFFLINE_RUN',flush=True)
else:
    O=a.analysis_out.resolve();assert not O.exists()
    subprocess.run([sys.executable,str(R/'scripts/analyze.py')],env=dict(env,C4H17_ANALYSIS_OUTPUT=str(O)),check=True)
    numeric_checks=0
    for q in (R/'analysis').glob('*.csv'):
        if not (O/q.name).exists():continue  # Additional report-only audit tables.
        with q.open(encoding='utf-8',newline='') as f:old=list(csv.DictReader(f))
        with (O/q.name).open(encoding='utf-8',newline='') as f:new=list(csv.DictReader(f))
        assert len(old)==len(new),q.name
        for x,y in zip(old,new):
            assert list(x)==list(y)
            for k in x:
                if x[k]==y[k]:continue
                try:
                    v,w=float(x[k]),float(y[k]);assert abs(v-w)<=1e-12*max(1,abs(v),abs(w))
                    numeric_checks+=1
                except ValueError:raise AssertionError((q.name,k,x[k],y[k]))
    result=dict(status='PASS_FRESH_STORED_TRACE_MAP_ANALYSIS',forward_calls=0,numeric_tolerance=1e-12,nonidentical_but_within_tolerance_fields=numeric_checks)
    (O/'REPRODUCTION_PASS.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
