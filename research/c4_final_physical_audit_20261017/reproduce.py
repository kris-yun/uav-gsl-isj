"""Read-only integrity and saved-data replay entry point. No new transport/ROS."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys,os,csv
R=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--verify-only',action='store_true');p.add_argument('--event-audit-out',type=Path);p.add_argument('--analysis-out',type=Path);a=p.parse_args()
manifest=json.loads((R/'MANIFEST_SHA256.json').read_text(encoding='utf8'))
for name,v in manifest.items():
    q=R/name;assert q.stat().st_size==v['bytes'] and hashlib.sha256(q.read_bytes()).hexdigest()==v['sha256'],name
print('PASS_MANIFEST',len(manifest),flush=True)
if a.verify_only:raise SystemExit(0)
assert bool(a.event_audit_out)!=bool(a.analysis_out),'Choose one NEW output directory'
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
if a.event_audit_out:
    subprocess.run([sys.executable,str(R/'scripts/portable_events.py'),str(a.event_audit_out.resolve())],env=env,check=True)
else:
    out=a.analysis_out.resolve();assert not out.exists()
    subprocess.run([sys.executable,str(R/'scripts/analyze.py')],env=dict(env,C4_CLOSE_ANALYSIS_OUT=str(out)),stdout=subprocess.DEVNULL,check=True)
    compared=0
    for old in (R/'analysis').glob('*.csv'):
        new=out/old.name
        if not new.exists():continue
        before=list(csv.DictReader(old.open(encoding='utf8')));after=list(csv.DictReader(new.open(encoding='utf8')))
        assert before==after,old.name;compared+=1
    assert json.loads((out/'AUDIT_CHECKS.json').read_text())==json.loads((R/'analysis/AUDIT_CHECKS.json').read_text())
    (out/'REPLAY_PASS.json').write_text(json.dumps(dict(status='PASS_STORED_MAP_TRACE_AND_EVENT_ANALYSIS',exact_csv_tables=compared,new_transport_calls=0),indent=2))
    print('PASS_EXACT_ANALYSIS_TABLES',compared)
