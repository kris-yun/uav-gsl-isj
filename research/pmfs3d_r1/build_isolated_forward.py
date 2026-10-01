"""Compile one new offline executable, reusing frozen library objects read-only."""
import argparse
import hashlib
import json
import re
import shlex
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
parser.add_argument('--reference', type=Path, default=Path('/home/zyc/native_pmfs_recovery_v1/r2_reference_build'))
args = parser.parse_args()
build = args.reference / 'build/gsl_server'
source_root = args.reference / 'src/gsl_server/src/gsl_server/algorithms/PMFS'
expected = {
    source_root / 'PMFSLib.cpp': '2e55858ca3f71cc1c6c00f9642ae3c7c3498fcbb2154ae1d88a07cc44b3213b8',
    source_root / 'internal/Simulations.cpp': 'd8b7c3d8a3799192719cbbf3abbcc1d421d0acfe3b23f3e8822f5cd3474c30ed',
    source_root / 'internal/EventKeyedRng.hpp': '26824c31c6b2fea2d801b0d248217077bdd9c65877c52f2389fa4652b1b4c1a2',
}
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
for path, wanted in expected.items():
    assert sha(path) == wanted, str(path)
protected = [build / 'libPMFS.a', build / 'libGSL_common.a'] + list(expected)
before = {str(path): sha(path) for path in protected}
target = build / 'CMakeFiles/native_pmfs_r1_r2_forward_replay.dir'
flags = dict(re.findall(r'^(CXX_\w+) = (.*)$', (target / 'flags.make').read_text(), re.M))
args.out.mkdir(parents=True, exist_ok=True)
obj = (args.out / 'oracle_forward.o').resolve()
binary = (args.out / 'oracle_forward').resolve()
compile_cmd = ['/usr/bin/c++']
for name in ('CXX_DEFINES', 'CXX_INCLUDES', 'CXX_FLAGS'):
    compile_cmd += shlex.split(flags[name])
compile_cmd += ['-c', str(args.source.resolve()), '-o', str(obj)]
subprocess.run(compile_cmd, check=True, cwd=build)
link_cmd = shlex.split((target / 'link.txt').read_text())
for i, token in enumerate(link_cmd):
    if token.endswith('native_pmfs_r1_r2_forward_replay.cpp.o'):
        link_cmd[i] = str(obj)
link_cmd[link_cmd.index('-o') + 1] = str(binary)
subprocess.run(link_cmd, check=True, cwd=build)
after = {str(path): sha(path) for path in protected}
assert before == after, 'reference libraries/source changed'
report = dict(source_sha256=sha(args.source), binary_sha256=sha(binary),
              reference_hashes=before, protected_unchanged=True,
              compile_command=compile_cmd, link_command=link_cmd,
              no_ros_workspace_rebuild=True, no_scientific_forward_executed=True)
(args.out / 'BUILD_AUDIT.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
print(json.dumps({k: report[k] for k in ('source_sha256', 'binary_sha256', 'protected_unchanged')}))
