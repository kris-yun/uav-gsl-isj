"""Fresh-directory table reproduction; never starts a physical forward or ROS."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys
from analyze import O, put


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    suffix = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    target = O.parent / ('E3_CAUSAL_PAIR_PORTABLE_QA_' + suffix)
    assert not target.exists()
    shutil.copytree(O, target, ignore=shutil.ignore_patterns('__pycache__'))
    environment = dict(os.environ, E3_PAIR_OUTPUT=str(target),
                       E3_PARENT_OUTPUT=str(target / 'parent_audit'),
                       PMFS_AUDIT_OUTPUT=str(target / 'parent_audit'),
                       OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1')
    runs = []
    for script in ['analyze.py', 'diagnostics.py', 'age_audit.py', 'verify.py']:
        result = subprocess.run([sys.executable, '-X', 'utf8',
                                 str(target / 'code' / script)],
                                cwd=target, env=environment, capture_output=True,
                                encoding='utf8', timeout=90)
        (target / ('PORTABLE_' + script + '.stdout')).write_text(result.stdout,
                                                                encoding='utf8')
        (target / ('PORTABLE_' + script + '.stderr')).write_text(result.stderr,
                                                                encoding='utf8')
        assert result.returncode == 0, (script, result.stderr)
        runs.append(dict(script=script, returncode=result.returncode))
    compared = []
    for path in sorted(O.glob('*.csv')):
        other = target / path.name
        assert sha(path) == sha(other), ('TABLE_REPRODUCTION_MISMATCH', path.name)
        compared.append(dict(path=path.name, sha256=sha(path), exact=True))
    for name in ['ANALYSIS_SUMMARY.json', 'AGE_INFERENCE_QA.json',
                 'ORDINARY_RESPONSE_RELIABILITY_GATE.json',
                 'MASS_WEIGHT_ACCOUNTING.json', 'PHYSICAL_FRAME_SHA256.json']:
        assert sha(O / name) == sha(target / name), name
        compared.append(dict(path=name, sha256=sha(O / name), exact=True))
    put(O / 'PORTABLE_RECOMPUTATION_QA.json',
        dict(status='PASS_FRESH_DIRECTORY_BYTE_EXACT_RECOMPUTATION',
             directory=str(target), runs=runs, compared=compared,
             new_physical_calls=0, new_ROS=0,
             original_result_tables_modified=False))
    print(json.dumps(dict(status='PASS_PORTABLE', compared=len(compared),
                          directory=str(target))))


if __name__ == '__main__':
    main()
