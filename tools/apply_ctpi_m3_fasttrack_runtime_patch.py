#!/usr/bin/env python3
"""Fail-closed application of the frozen CTPI M3 runtime integration patch."""
from __future__ import annotations
import argparse, hashlib, subprocess, sys, tempfile
from pathlib import Path

PATCH_SOURCE_SHA='a054a28c593f095956469e87713350e89baf3f30c94a9d23e8708b63379f4713'
BASE={
 'ros2_package/src/gsl_server/algorithms/PMFS/PMFS.cpp':'183f667fd5b04804b7e4cf06d2bdc8b299abe13d936533ce1eef56116b04b743',
 'ros2_package/src/gsl_server/algorithms/PMFS/MovingStatePMFS.cpp':'2d13ce664330bf5073655b7477b3967967a2e704ae8c3d3b67e90244daa24330',
 'ros2_package/src/gsl_server/algorithms/PMFS/CPIR.cpp':'e24c7567b7d3bcb5d5f32d1e36fb92092515d454bf5445cab1e4b6afb620b7c1',
}
POST={
 'ros2_package/src/gsl_server/algorithms/PMFS/PMFS.cpp':'cb967ec57c52abfb126635075e9c2c7a98c5949327ea16d4a6b8448ba503ba1f',
 'ros2_package/src/gsl_server/algorithms/PMFS/MovingStatePMFS.cpp':'008844892652c576a88ff35129f73482e683f25cb43140535ee815c41d49ae60',
 'ros2_package/src/gsl_server/algorithms/PMFS/CPIR.cpp':'481238de71adda0d5efb3180014aa1e1b86b7c306273ee7a9274642b24cd6f90',
}
HEADER=('ros2_package/src/gsl_server/algorithms/PMFS/PMFS.hpp','7fe197312c6ea93cd8edf4876dd5d8c60328a64aa017b236f97848c24a00339e')
CTPI=('ros2_package/src/gsl_server/algorithms/PMFS/CTPI.cpp','e5ce97b3f6ed5d1c7d17636933130a3b7207be9286b6173255d9ffca65fb8675')

def sha(p:Path): return hashlib.sha256(p.read_bytes()).hexdigest()
def req(root:Path, rel:str, expected:str):
    p=root/rel
    if not p.is_file(): raise RuntimeError(f'MISSING:{rel}')
    got=sha(p)
    if got!=expected: raise RuntimeError(f'HASH:{rel}:{got}:{expected}')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',type=Path,required=True); ap.add_argument('--patch',type=Path); a=ap.parse_args()
    root=a.repo_root.resolve(); patch=(a.patch or (root/'patches/CTPI_M3_FASTTRACK_RUNTIME_INTEGRATION_20260903.patch')).resolve()
    if sha(patch)!=PATCH_SOURCE_SHA: raise RuntimeError(f'PATCH_SOURCE_SHA:{sha(patch)}:{PATCH_SOURCE_SHA}')
    req(root,*HEADER); req(root,*CTPI)
    current={rel:sha(root/rel) for rel in BASE}
    if current==POST:
        print('CTPI_M3_RUNTIME_PATCH=ALREADY_APPLIED'); return 0
    if current!=BASE: raise RuntimeError(f'BASE_HASH_SET:{current}')
    helper=root/'tools/ctpi_m3_runtime_patch_materializer.py'
    if not helper.is_file(): raise RuntimeError('CTPI_M3_PATCH_MATERIALIZER_MISSING')
    with tempfile.TemporaryDirectory(prefix='ctpi_m3_patch_') as td:
        complete=Path(td)/'CTPI_M3_RUNTIME_COMPLETE.patch'
        subprocess.run([sys.executable,str(helper),'--source',str(patch),'--output',str(complete)],check=True)
        subprocess.run(['git','-C',str(root),'apply','--check',str(complete)],check=True)
        subprocess.run(['git','-C',str(root),'apply',str(complete)],check=True)
    for rel,expected in POST.items(): req(root,rel,expected)
    print('CTPI_M3_RUNTIME_PATCH=PASS')
    return 0
if __name__=='__main__': raise SystemExit(main())
