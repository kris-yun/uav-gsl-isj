#!/usr/bin/env python3
"""Re-run theory/implementation certificates; these are not localization experiments."""
from pathlib import Path
import subprocess,sys,json,time
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'verification'/'certificate_logs';OUT.mkdir(parents=True,exist_ok=True)
scripts=['proof_checks/m1/test_certificates.py','proof_checks/m1/green_3d_certificate.py','proof_checks/support/support_certificates.py','proof_checks/support/independent_m1_review.py','proof_checks/support/green_support_review.py','proof_checks/history/run_verification.py','proof_checks/support/green_information_audit.py','proof_checks/support/adaptive_information_audit.py','tests/test_chain.py','run_reference.py']
report=[]
for path in scripts:
    cmd=[sys.executable,str(ROOT/path)]
    if path.endswith('run_verification.py') and '--closed-loop' in sys.argv:cmd.append('--closed-loop')
    if path.endswith('run_reference.py'):cmd.extend(['--output',str(ROOT/'verification'/'reference_run.json')])
    start=time.monotonic()
    proc=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=180)
    log=OUT/(Path(path).stem+'.log');log.write_text(proc.stdout+proc.stderr)
    report.append({'script':path,'exit_code':proc.returncode,'elapsed_seconds':round(time.monotonic()-start,3),'log':str(log.relative_to(ROOT))})
    print(path, 'PASS' if proc.returncode==0 else 'FAIL',flush=True)
    if proc.returncode:
        (ROOT/'verification/CERTIFICATES_RUN.json').write_text(json.dumps(report,indent=2))
        raise SystemExit('Certificate failed; inspect '+str(log))
(ROOT/'verification/CERTIFICATES_RUN.json').write_text(json.dumps({'scope':'Mathematical and historical diagnostics only; not native localization performance.','checks':report},indent=2))
