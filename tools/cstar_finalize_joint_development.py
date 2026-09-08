"""Record a partial implementation honestly; never synthesize a utility PASS."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'evidence/cstar_joint_development_20260908'


def main():
    target = OUT / 'IMPLEMENTATION_STATUS.json'
    if target.exists():
        raise FileExistsError(target)
    test = subprocess.run([sys.executable, str(ROOT / 'experiments/ctpi_cstar/selftest_sequential_joint.py')],
                          cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (OUT / 'joint_tests_v2.log').write_text(test.stdout)
    if test.returncode:
        raise RuntimeError(test.stdout)
    files = ['experiments/ctpi_cstar/m1_picr/sequential_joint.py',
             'experiments/ctpi_cstar/m2_cpo/physical_prior.py',
             'experiments/ctpi_cstar/selftest_sequential_joint.py',
             'closed_loop/ctpi/cstar_joint_source_online.py',
             'closed_loop/ctpi/cstar_launch_binding.py',
             'closed_loop/ctpi/vgr_gsl_pmfs_ctpi_fasttrack.launch.py',
             'tools/cstar_verify_joint_launch_vm.py', 'tools/cstar_finalize_joint_development.py',
             'tools/cstar_verify_reusable_live.py']
    baseline = Path('/home/zyc/ros2_ws/install/gsl_server/lib/gsl_server/gsl_actionserver_node')
    report = dict(status='PARTIAL_IMPLEMENTATION_NOT_CLOSED_LOOP',
                  joint_regression_tests=7, joint_regression_returncode=test.returncode,
                  source_sha256={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in files},
                  baseline_executable=dict(path=str(baseline), exists=baseline.exists(),
                       is_symlink=baseline.is_symlink(), resolved_path=str(baseline.resolve())),
                  closed_loop_ran=False, causal_identifiability_proved=False,
                  m1_utility_proved=False, m2_utility_proved=False,
                  remaining=['Bind joint posterior to actual PMFS grid and source-update consumer.',
                             'Establish a matched native-law M1 arm; existing wrapper uses the physical M2 prior.',
                             'Remove full-prefix replay cost before full-grid online deployment.',
                             'Recover and hash a current-source PMFS executable; do not substitute an old binary.',
                             'Audit live GMRF and planner geometry, then run House123 seed12 240s development arms.'])
    for name in ['LAUNCH_BINDING.json', 'INDEPENDENT_LIVE_VERIFICATION.json']:
        path = OUT / name
        if not path.is_file():
            raise FileNotFoundError(path)
        report[name] = {'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    target.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
