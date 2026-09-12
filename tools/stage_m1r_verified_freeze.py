#!/usr/bin/env python3
"""Archive an already-pushed freeze on the authenticated host, without credentials."""
import argparse
import datetime
import hashlib
import json
import subprocess
import tarfile
from pathlib import Path

SCOPES = ['ros2_package','closed_loop/ctpi','tools','experiments/ctpi_cstar',
          'docs','evidence/m1r_crossdomain_20260912']

def git(*args):
    return subprocess.check_output(['git',*args],text=True).strip()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir',type=Path,required=True)
    args=p.parse_args()
    commit=git('rev-parse','HEAD')
    branch=git('branch','--show-current')
    ref='refs/heads/'+branch
    url=git('remote','get-url','origin')
    if git('status','--porcelain'):
        raise SystemExit('FREEZE_WORKTREE_MUST_BE_CLEAN')
    args.output_dir.mkdir(parents=True,exist_ok=True)
    archive=args.output_dir/f'freeze_{commit}.tar.gz'
    receipt=args.output_dir/'REMOTE_RECEIPT.json'
    if archive.exists() or receipt.exists():
        raise SystemExit('REFUSE_OVERWRITE_STAGED_FREEZE')
    subprocess.run(['git','archive','--format=tar.gz',f'--output={archive}',commit,*SCOPES],check=True)
    with tarfile.open(archive,'r:gz') as tar:
        if tar.pax_headers.get('comment') != commit:
            raise SystemExit('ARCHIVE_COMMIT_HEADER_MISMATCH')
    resolved=git('ls-remote','--exit-code','origin',ref).split()[0]
    if resolved!=commit:
        raise SystemExit('REMOTE_COMMIT_DIFFERS_FROM_ARCHIVE')
    record={'schema':'M1R_AUTHENTICATED_HOST_REMOTE_RECEIPT_V1',
            'verification_origin':'authenticated_host','remote_url':url,'remote_ref':ref,
            'resolved_commit':resolved,
            'verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'source_archive':archive.name,'source_archive_bytes':archive.stat().st_size,
            'source_archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
            'verification_method':'actual host git ls-remote exact equality after git archive',
            'limitation':'VM verifies host receipt and exact source archive, not an independent authenticated GitHub session'}
    receipt.write_bytes((json.dumps(record,indent=2)+'\n').encode('utf-8'))
    print(json.dumps(record,indent=2))

if __name__=='__main__':
    main()
