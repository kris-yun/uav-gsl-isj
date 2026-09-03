#!/usr/bin/env python3
"""Static/runtime-source preflight before any CTPI fast-track VM build."""
from __future__ import annotations
import argparse, hashlib, json, subprocess, sys
from pathlib import Path

EXPECTED={
 'experiments/cg_pc_ctt/ctpi_m2_tsdc_frozen_v0.py':'854a2fc8513201cdb2ae497a62c0cd3c5fa09fdae2f1bc309ad594a8b1aaacf7',
 'experiments/cg_pc_ctt/ctpi_m3_pip_frozen_v0.py':'bcf065903ec8cd88533ff0ac0dbd453131a9aeaf0d075fbf71ec92dc00fc2706',
 'ros2_package/src/gsl_server/algorithms/PMFS/CTPI.cpp':'e5ce97b3f6ed5d1c7d17636933130a3b7207be9286b6173255d9ffca65fb8675',
 'ros2_package/src/gsl_server/algorithms/PMFS/PMFS.hpp':'7fe197312c6ea93cd8edf4876dd5d8c60328a64aa017b236f97848c24a00339e',
 'closed_loop/ctpi/vgr_gsl_pmfs_ctpi_fasttrack.launch.py':'8559d930df9436917ea2d961fb4cdfd6ea23ac5cd5597c83ef23960be2cd648b',
 'closed_loop/ctpi/run_ctpi_fasttrack_case_safe_20260903.sh':'7a1e8aa8747cb942f7c49edb53efdd65b8064e42d910b3dd73748e33dac32138',
 'patches/CTPI_M3_FASTTRACK_RUNTIME_INTEGRATION_20260903.patch':'96e1e425a7c4e6e97ad123c1d46e67120dc86574b3d3927a370e5b99d1020743',
}
POST={
 'ros2_package/src/gsl_server/algorithms/PMFS/PMFS.cpp':'cb967ec57c52abfb126635075e9c2c7a98c5949327ea16d4a6b8448ba503ba1f',
 'ros2_package/src/gsl_server/algorithms/PMFS/MovingStatePMFS.cpp':'008844892652c576a88ff35129f73482e683f25cb43140535ee815c41d49ae60',
 'ros2_package/src/gsl_server/algorithms/PMFS/CPIR.cpp':'481238de71adda0d5efb3180014aa1e1b86b7c306273ee7a9274642b24cd6f90',
}

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args(); root=a.repo_root.resolve()
    checks={}
    for rel,exp in EXPECTED.items():
        p=root/rel; checks['hash:'+rel]=p.is_file() and sha(p)==exp
    for rel,exp in POST.items():
        p=root/rel; checks['postpatch:'+rel]=p.is_file() and sha(p)==exp
    ctpi=(root/'ros2_package/src/gsl_server/algorithms/PMFS/CTPI.cpp').read_text(encoding='utf-8')
    forbidden=('source_x','source_y','true_source','localization_error','groundTruthSource')
    checks['planner_truth_blind_static']=not any(x in ctpi for x in forbidden)
    checks['ctpi_modes_present']=all(x in (root/'ros2_package/src/gsl_server/algorithms/PMFS/PMFS.cpp').read_text(encoding='utf-8') for x in ('ctpi_f00','ctpi_f10','ctpi_f11'))
    cmds=[
      [sys.executable,str(root/'experiments/cg_pc_ctt/ctpi_m2_tsdc_frozen_v0.py')],
      [sys.executable,str(root/'experiments/cg_pc_ctt/ctpi_m3_pip_frozen_v0.py'),'--selftest'],
      [sys.executable,str(root/'tools/ctpi_m3_static_parity.py'),'--cpp',str(root/'ros2_package/src/gsl_server/algorithms/PMFS/CTPI.cpp'),'--tsdc',str(root/'experiments/cg_pc_ctt/ctpi_m2_tsdc_frozen_v0.py')],
    ]
    for i,cmd in enumerate(cmds): checks[f'selftest_{i}']=subprocess.run(cmd,cwd=root).returncode==0
    passed=all(checks.values()); out={'contract':'CTPI_M3_FASTTRACK_RUNTIME_PREFLIGHT_V0','checks':checks,'pass':passed,'verdict':'CTPI_M3_FASTTRACK_RUNTIME_PREFLIGHT=PASS' if passed else 'CTPI_M3_FASTTRACK_RUNTIME_PREFLIGHT=FAIL'}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(out['verdict']); return 0 if passed else 2
if __name__=='__main__': raise SystemExit(main())
