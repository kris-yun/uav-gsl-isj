#!/usr/bin/env python3
"""Materialize the frozen CTPI launch/runner from authoritative CPIR files.

The source CPIR files remain unchanged. GNU patch writes exact CTPI outputs to
new paths, then SHA-256 checks them against the clean-room validated targets.
"""
from __future__ import annotations
import argparse,hashlib,subprocess
from pathlib import Path

LAUNCH_PATCH_SHA='d4d9d992d78285ab87721e5249c7641f39181d9f9fb56057307d2ba2c9574c55'
RUNNER_PATCH_SHA='e4d6a3137dadca6997cd34d9177becc83861c16493c0057b80e4ca5acfd34ea0'
LAUNCH_OUT_SHA='8559d930df9436917ea2d961fb4cdfd6ea23ac5cd5597c83ef23960be2cd648b'
RUNNER_OUT_SHA='7a1e8aa8747cb942f7c49edb53efdd65b8064e42d910b3dd73748e33dac32138'

def sha(p:Path): return hashlib.sha256(p.read_bytes()).hexdigest()
def check(p:Path,e:str,label:str):
    if not p.is_file() or sha(p)!=e: raise RuntimeError(f'{label}_SHA:{sha(p) if p.is_file() else "MISSING"}:{e}')

def materialize(source:Path,patch:Path,target:Path,patch_sha:str,out_sha:str):
    check(patch,patch_sha,'PATCH')
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():
        if sha(target)==out_sha:return
        raise RuntimeError(f'REFUSE_EXISTING_TARGET:{target}')
    with patch.open('rb') as inp:
        subprocess.run(['patch','--batch','--fuzz=0','-o',str(target),str(source)],stdin=inp,check=True)
    check(target,out_sha,'OUTPUT')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo-root',type=Path,required=True);a=ap.parse_args();r=a.repo_root.resolve()
    materialize(r/'closed_loop/cpir/vgr_gsl_pmfs_cpir.launch.py',r/'patches/CTPI_M3_FASTTRACK_LAUNCH_20260903.patch',r/'closed_loop/ctpi/vgr_gsl_pmfs_ctpi_fasttrack.launch.py',LAUNCH_PATCH_SHA,LAUNCH_OUT_SHA)
    materialize(r/'closed_loop/cpir/run_cpir_formal_case_20260901.sh',r/'patches/CTPI_M3_FASTTRACK_RUNNER_20260903.patch',r/'closed_loop/ctpi/run_ctpi_fasttrack_case_safe_20260903.sh',RUNNER_PATCH_SHA,RUNNER_OUT_SHA)
    print('CTPI_M3_FASTTRACK_VM_FILES_MATERIALIZED=PASS')
if __name__=='__main__':raise SystemExit(main())
