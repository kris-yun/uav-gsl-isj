"""Read-only package integrity and bounded M1 component regressions."""
import gzip,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PACK=ROOT/'evidence/m1_review_upload_20260912'
def main():
    manifest=json.loads((PACK/'manifest.json').read_text())
    checked=0
    for item in manifest['files']:
        p=ROOT/item['stored'];raw=p.read_bytes()
        assert hashlib.sha256(raw).hexdigest()==item['stored_sha256'],p
        if item['encoding']=='gzip':raw=gzip.decompress(raw)
        assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256'],p
        checked+=1
    tests=[]
    names=['causal_counterfactual_likelihood','causal_temporal_transport','estimated_wind_history',
           'evidence_bounds_v3','filament_geometry','filament_observation','filament_transport','occupancy3d']
    for name in names:
        p=ROOT/f'experiments/ctpi_cstar/selftest_m1_{name}.py'
        run=subprocess.run([sys.executable,'-X','utf8',str(p)],cwd=ROOT,capture_output=True,text=True,timeout=120)
        tests.append({'test':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'exit':run.returncode,'stdout':run.stdout,'stderr':run.stderr})
    result={'integrity_files_checked':checked,'tests':tests,'all_component_tests_pass':all(t['exit']==0 for t in tests),
            'scope':'package integrity and component tests only; NOT innovation or closed-loop utility'}
    with (PACK/'verification.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if not result['all_component_tests_pass']:sys.exit(1)
if __name__=='__main__':main()
