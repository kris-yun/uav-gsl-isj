"""Run declared analytic certificates; never launches native/ROS experiments."""
from pathlib import Path
import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import sys
from time import perf_counter

ROOT=Path(__file__).resolve().parent


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--include-v58',action='store_true',
                        help='Also rerun preserved V58 fixtures (private delivery only).')
    args=parser.parse_args()
    logs=ROOT/'run_logs'; logs.mkdir(exist_ok=True)
    evidence=ROOT/'evidence';evidence.mkdir(exist_ok=True)
    tasks=[('src/adaptive_source_design.py','src/results/adaptive_source_design.json'),
           ('src/prediction_budget.py','src/results/prediction_budget.json'),
           ('src/body_history_adapter.py','src/results/body_history_adapter.json'),
           ('checks/finite_certificates.py','checks/finite_certificates_results.json'),
           ('checks/local_curvature_certificate.py','checks/local_curvature_results.json'),
           ('checks/raed_aliasing_toy.py','checks/raed_aliasing_toy.json')]
    rows=[]
    for script,result in tasks:
        started=perf_counter()
        with (logs/(Path(script).stem+'.log')).open('w',encoding='utf-8') as output:
            p=subprocess.run([sys.executable,str(ROOT/script)],cwd=ROOT,stdout=output,
                             stderr=subprocess.STDOUT,timeout=120,check=False)
        row={'script':script,'exit_code':p.returncode,'seconds':perf_counter()-started,
             'source_sha256':hashlib.sha256((ROOT/script).read_bytes()).hexdigest()}
        rows.append(row)
        if p.returncode:
            raise RuntimeError(f'Certificate failed: {script}; see run_logs')
        src=ROOT/result
        if not src.is_file():
            raise RuntimeError(f'Missing result: {result}')
        json.loads(src.read_text())
        shutil.copy2(src,evidence/src.name)
        print('PASS '+script,flush=True)
    if args.include_v58:
        runner=ROOT/'prior_v58/run_all.py'
        if not runner.is_file():
            raise RuntimeError('V58 private fixture package is absent; it cannot be synthesized')
        with (logs/'prior_v58.log').open('w',encoding='utf-8') as output:
            subprocess.run([sys.executable,str(runner)],cwd=runner.parent,stdout=output,
                           stderr=subprocess.STDOUT,timeout=120,check=True)
        print('PASS prior_v58/run_all.py',flush=True)
    import numpy, scipy
    receipt={'status':'PASS','scope':'analytic and accounting certificates only; no native localization run',
             'python':platform.python_version(),'numpy':numpy.__version__,'scipy':scipy.__version__,
             'tasks':rows,'prior_v58_run':args.include_v58}
    (evidence/'RUN_RECEIPT.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print('Completed. Native source-localization superiority remains untested.')


if __name__=='__main__':
    main()
