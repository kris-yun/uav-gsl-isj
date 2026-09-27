"""Reproduce ALL posthoc diagnostics from the supplied review ZIP.

No new forward run, no optimization, no randomization, no private/sealed asset.
This reads historically OPEN targets: outputs are NOT fresh confirmation.
"""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,tempfile,zipfile
EXPECTED='7a3e436900ab2696c2d7148215cd58b6632a017e447583f77c9c864b56f9c56c'
def main():
    p=argparse.ArgumentParser();p.add_argument('--review-zip',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    zhash=hashlib.sha256(a.review_zip.read_bytes()).hexdigest()
    if zhash!=EXPECTED:raise ValueError('Input differs from the reviewed frozen package')
    a.out.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='me_readout_') as tmp:
        root=Path(tmp)
        with zipfile.ZipFile(a.review_zip) as z:
            for info in z.infolist():
                dest=(root/info.filename).resolve()
                if not dest.is_relative_to(root.resolve()):raise ValueError('Unsafe ZIP path')
                if info.is_dir():continue
                dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(info))
        entries=[]
        for line in (root/'SHA256SUMS').read_text().splitlines():
            if not line.strip():continue
            expected,name=line.split(None,1);name=name.lstrip('* ').strip()
            if hashlib.sha256((root/name).read_bytes()).hexdigest()!=expected:raise ValueError(name)
            entries.append(name)
        env=dict(os.environ,ME_REVIEW_ROOT=str(root),ME_AUDIT_OUT=str(a.out.resolve()),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
        here=Path(__file__).resolve().parent
        for name in ['me_current_audit.py','me_supplement.py','me_footprint_diagnostic.py','me_readout_factorial.py']:
            proc=subprocess.run([sys.executable,str(here/name)],env=env,capture_output=True,text=True)
            (a.out/(name+'.log')).write_text(proc.stdout+proc.stderr)
            if proc.returncode:raise RuntimeError(f'{name} failed; inspect its log')
        (a.out/'REPLAY_PROVENANCE.json').write_text(json.dumps(dict(input_sha256=zhash,verified_entries=len(entries),new_forward_runs=0,new_random_draws=0,new_training_runs=0,analysis_role='posthoc OPEN development diagnostics; no frozen decision changed'),indent=2))
    print('Completed all fixed diagnostics. These are NOT confirmation results.')
if __name__=='__main__':main()
