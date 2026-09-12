#!/usr/bin/env bash
# Deliberately separate build from experiment execution. No mode runs implicitly.
set -Ee -o pipefail
MODE=${1:?usage: bash m1r_h03_build_and_pair.sh build|run-pair}
[[ "$MODE" == build || "$MODE" == run-pair ]] || { echo INVALID_MODE >&2; exit 2; }
: "${FREEZE_COMMIT:?provide the full already-pushed commit SHA}"
: "${RUN_TAG:?provide a fresh alphanumeric or underscore tag}"
[[ "$FREEZE_COMMIT" =~ ^[0-9a-f]{40}$ ]] || { echo FULL_FREEZE_SHA_REQUIRED >&2; exit 2; }
[[ "$RUN_TAG" =~ ^[A-Za-z0-9_]+$ ]] || { echo INVALID_RUN_TAG >&2; exit 2; }
REMOTE_URL=${REMOTE_URL:-https://github.com/kris-yun/uav-gsl-isj.git}
REMOTE_REF=${REMOTE_REF:-refs/heads/codex/m1r-causal-repair-20260912}
[[ "$REMOTE_REF" == refs/heads/* ]] || { echo FULL_BRANCH_REF_REQUIRED >&2; exit 2; }
BUILD_ROOT=/dev/shm/m1r_h03_${FREEZE_COMMIT:0:12}_${RUN_TAG}
RESULT_ROOT=/mnt/hgfs/workspace/M1R_H03_SEED12_PAIR_20260912_${RUN_TAG}
OLD_BUILD=/dev/shm/m1r_v41_build_20260912
OLD_REPO=/dev/shm/cstar_joint_development_20260908
OLD_PREFLIGHT=/dev/shm/m1r_v41_derived_preflight.json
OLD_BINARY=$OLD_BUILD/install/gsl_server/lib/gsl_server/gsl_actionserver_node
OLD_BINARY_SHA=006fd79a950f48bb76308174573048b26e37c3815466cf69ba22bcbddf1e2a52
FREEZE_REPO=$BUILD_ROOT/freeze_repo
NEW_BINARY=$BUILD_ROOT/install/gsl_server/lib/gsl_server/gsl_actionserver_node
export FREEZE_COMMIT RUN_TAG REMOTE_URL REMOTE_REF BUILD_ROOT RESULT_ROOT OLD_BUILD OLD_REPO
export OLD_PREFLIGHT OLD_BINARY OLD_BINARY_SHA FREEZE_REPO NEW_BINARY
export PYTHONDONTWRITEBYTECODE=1 GIT_TERMINAL_PROMPT=0 GIT_LFS_SKIP_SMUDGE=1

verify_remote() {
  local resolved
  resolved=$(git ls-remote --exit-code "$REMOTE_URL" "$REMOTE_REF" | awk 'NR==1 {print $1}')
  [[ "$resolved" == "$FREEZE_COMMIT" ]] || {
    echo "PUSHED_FREEZE_MISMATCH expected=$FREEZE_COMMIT actual=$resolved" >&2; exit 3;
  }
}
check_idle() {
  python3 - <<'PY'
import os,pathlib
found=[]
for p in pathlib.Path('/proc').iterdir():
    if not p.name.isdigit(): continue
    try:
        if p.stat().st_uid != os.getuid(): continue
        args=p.joinpath('cmdline').read_bytes().decode(errors='replace').split('\0')
        names=[pathlib.Path(x).name for x in args[:3] if x]
        if any(x in {'gsl_actionserver_node','vgr_sim_node','gmrf_wind_mapping_node','wind_value_server.py'} for x in names):
            found.append((p.name,names))
        elif any('/gaden_player/' in x and x.endswith('/player') for x in args[:2]):
            found.append((p.name,names))
        elif any(x.startswith('run_ctpi') and x.endswith('.sh') for x in names):
            found.append((p.name,names))
    except (FileNotFoundError,PermissionError): pass
if found: raise SystemExit('EXPERIMENT_ALREADY_RUNNING:'+repr(found))
PY
}
verify_remote
check_idle
[[ $(sha256sum "$OLD_BINARY" | awk '{print $1}') == "$OLD_BINARY_SHA" ]] || {
  echo OLD_BASELINE_BINARY_CHANGED >&2; exit 4;
}

if [[ "$MODE" == build ]]; then
  [[ ! -e "$BUILD_ROOT" && ! -e "$RESULT_ROOT" ]] || { echo REFUSE_EXISTING_BUILD_OR_RESULT >&2; exit 5; }
  # Old package is ~53 MiB including dependencies. Leave room for clone, compiler
  # scratch, new objects, and persisted build/source provenance, without rootfs writes.
  python3 - <<'PY'
import shutil
for p,n in [('/dev/shm',512*1024**2),('/mnt/hgfs/workspace',256*1024**2)]:
    if shutil.disk_usage(p).free<n: raise SystemExit('INSUFFICIENT_FREE_BYTES:'+p)
PY
  mkdir -p "$BUILD_ROOT/tmp" "$BUILD_ROOT/deps" "$RESULT_ROOT/provenance"
  export TMPDIR=$BUILD_ROOT/tmp
  git -c core.autocrlf=false -c core.eol=lf clone --filter=blob:none --no-checkout --single-branch --depth=1 \
    --branch "${REMOTE_REF#refs/heads/}" "$REMOTE_URL" "$FREEZE_REPO" \
    >"$RESULT_ROOT/provenance/clone.log" 2>&1
  [[ $(git -C "$FREEZE_REPO" rev-parse HEAD) == "$FREEZE_COMMIT" ]] || { echo CLONE_FREEZE_MISMATCH >&2; exit 6; }
  git -C "$FREEZE_REPO" config core.autocrlf false
  git -C "$FREEZE_REPO" config core.eol lf
  git -C "$FREEZE_REPO" sparse-checkout init --cone
  git -C "$FREEZE_REPO" sparse-checkout set ros2_package closed_loop/ctpi tools \
    experiments/ctpi_cstar docs evidence/m1r_crossdomain_20260912
  git -C "$FREEZE_REPO" checkout --detach "$FREEZE_COMMIT"
  [[ -z $(git -C "$FREEZE_REPO" status --porcelain) ]] || { echo DIRTY_FROZEN_SOURCE >&2; exit 6; }
  # This script must itself come from that exact published freeze, not an ad-hoc wrapper.
  cmp -- "${BASH_SOURCE[0]}" "$FREEZE_REPO/tools/m1r_h03_build_and_pair.sh"
  test -s "$FREEZE_REPO/evidence/m1r_crossdomain_20260912/GEOSCIENCE_2026.md"
  grep -q m1r_source_quadrature_enabled "$FREEZE_REPO/closed_loop/ctpi/vgr_gsl_pmfs_ctpi_fasttrack.launch.py"
  grep -q M1R_SOURCE_QUADRATURE_ENABLED "$FREEZE_REPO/closed_loop/ctpi/run_ctpi_fasttrack_case_safe_20260903.sh"
  python3 - <<'PY'
import hashlib,json,os,pathlib,datetime
e=os.environ; repo=pathlib.Path(e['FREEZE_REPO']); out=pathlib.Path(e['RESULT_ROOT'])/'provenance'
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
old=json.loads(pathlib.Path(e['OLD_PREFLIGHT']).read_text())
rel='experiments/ctpi_cstar/environment_runtime.py'
old_runtime=pathlib.Path(e['OLD_REPO'])/rel; new_runtime=repo/rel
if sha(old_runtime)!=sha(new_runtime): raise SystemExit('ENVIRONMENT_RUNTIME_CHANGE_REQUIRES_SEPARATE_REVIEW')
for p in list((repo/'ros2_package').rglob('*.cpp'))+list((repo/'ros2_package').rglob('*.hpp')):
    if p.read_bytes().startswith(b'version https://git-lfs.github.com/spec/v1'):
        raise SystemExit('SOURCE_IS_LFS_POINTER:'+str(p))
# Only add a content-identical module at its new absolute path. Physical input
# bindings, geometry, helper, sensor clock and all old bindings remain unchanged.
old['bindings'].append({'path':str(new_runtime.resolve()),'sha256':sha(new_runtime)})
old['h03_pair_relocation']={'freeze_commit':e['FREEZE_COMMIT'],'old_preflight_sha256':sha(e['OLD_PREFLIGHT']),
    'new_binding':str(new_runtime.resolve()),'scope':'identical environment-runtime module relocation only'}
derived=pathlib.Path(e['BUILD_ROOT'])/'environment_preflight.json'
derived.write_text(json.dumps(old,indent=2)+'\n')
(out/'environment_preflight.json').write_bytes(derived.read_bytes())
files={str(p.relative_to(repo)):sha(p) for p in repo.rglob('*')
       if p.is_file() and '.git' not in p.relative_to(repo).parts}
m={'schema':'M1R_H03_PUSHED_FREEZE_V1','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
   'freeze_commit':e['FREEZE_COMMIT'],'remote_url':e['REMOTE_URL'],'remote_ref':e['REMOTE_REF'],
   'scope':{'house':'H03','algorithm_seed':12,'sensor_seed':12,'arms':['BASELINE','FIXED_SOURCE'],'horizon_s_each':240},
   'old_binary':e['OLD_BINARY'],'old_binary_sha256':sha(e['OLD_BINARY']),
   'source_files_sha256':files,'derived_preflight_sha256':sha(derived)}
(out/'FREEZE_MANIFEST.json').write_text(json.dumps(m,indent=2)+'\n')
PY
  # Preserve the exact checked-out code/theory/scripts before any build or run.
  tar -czf "$RESULT_ROOT/provenance/FROZEN_SOURCE_AND_THEORY.tar.gz" -C "$FREEZE_REPO" \
    ros2_package closed_loop/ctpi tools experiments/ctpi_cstar docs evidence/m1r_crossdomain_20260912
  sha256sum "$RESULT_ROOT/provenance/FROZEN_SOURCE_AND_THEORY.tar.gz" \
    >"$RESULT_ROOT/provenance/FROZEN_SOURCE_AND_THEORY.sha256"
  cp -- "$OLD_BINARY" "$RESULT_ROOT/provenance/HISTORICAL_INSTRUMENTED_BASELINE.bin"
  # Reuse installed message dependencies read-only. Never relocate old CMakeCache
  # or overwrite its source, objects, installation, or binary.
  ln -s "$OLD_BUILD/deps/install" "$BUILD_ROOT/deps/install"
  source /opt/ros/humble/setup.bash
  source /home/zyc/PF_DEI_FORWARD_CLOSURE_20260828/gaden_install/local_setup.bash
  source "$OLD_BUILD/deps/install/local_setup.bash"
  GADEN_PREFIX=$(find /home/zyc/PF_DEI_FORWARD_CLOSURE_20260828/gaden_install -mindepth 1 -maxdepth 1 -type d | sort | paste -sd:)
  export CMAKE_PREFIX_PATH="$GADEN_PREFIX:${CMAKE_PREFIX_PATH:-}"
  export AMENT_PREFIX_PATH="$GADEN_PREFIX:${AMENT_PREFIX_PATH:-}"
  export MAKEFLAGS=-j1 CMAKE_BUILD_PARALLEL_LEVEL=1
  cmake -S "$FREEZE_REPO/ros2_package" -B "$BUILD_ROOT/build/gsl_server" \
    -DCMAKE_INSTALL_PREFIX="$BUILD_ROOT/install/gsl_server" -DCMAKE_BUILD_TYPE=Release \
    -DPFDI_LOW_MEMORY_BUILD=ON -DBUILD_TESTING=OFF \
    >"$RESULT_ROOT/provenance/configure.log" 2>&1
  cmake --build "$BUILD_ROOT/build/gsl_server" --target gsl_actionserver_node gsl_actionserver_call send_pose \
    --parallel 1 >"$RESULT_ROOT/provenance/build.log" 2>&1
  cmake --install "$BUILD_ROOT/build/gsl_server" >"$RESULT_ROOT/provenance/install.log" 2>&1
  test -x "$NEW_BINARY"
  [[ $(sha256sum "$OLD_BINARY" | awk '{print $1}') == "$OLD_BINARY_SHA" ]] || { echo OLD_BINARY_MUTATED >&2; exit 7; }
  cp -- "$NEW_BINARY" "$RESULT_ROOT/provenance/NEW_PAIRED_ALGORITHM.bin"
  cp -- "$BUILD_ROOT/build/gsl_server/CMakeCache.txt" "$RESULT_ROOT/provenance/CMakeCache.txt"
  python3 - <<'PY'
import hashlib,json,os,pathlib
e=os.environ; out=pathlib.Path(e['RESULT_ROOT'])/'provenance'; sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
m={'schema':'M1R_H03_ISOLATED_BUILD_V1','freeze_commit':e['FREEZE_COMMIT'],'build_root':e['BUILD_ROOT'],
 'result_root':e['RESULT_ROOT'],'new_binary':e['NEW_BINARY'],'new_binary_sha256':sha(e['NEW_BINARY']),
 'old_binary_sha256':sha(e['OLD_BINARY']),'freeze_manifest_sha256':sha(out/'FREEZE_MANIFEST.json'),
 'build_strategy':'fresh target-only Release build; read-only reuse of old installed messages; no replay target',
 'cmake_cache_sha256':sha(out/'CMakeCache.txt'),'run_started':False}
(out/'BUILD_MANIFEST.json').write_text(json.dumps(m,indent=2)+'\n')
PY
  printf 'M1R_H03_BUILD_READY=%s\nNO_EXPERIMENT_STARTED\n' "$RESULT_ROOT/provenance/BUILD_MANIFEST.json"
  exit 0
fi

# run-pair only: requires the previous build artifacts, with remote freeze still exact.
export TMPDIR=$BUILD_ROOT/tmp
test -s "$RESULT_ROOT/provenance/BUILD_MANIFEST.json"
exec 9>"$BUILD_ROOT/pair.lock"
flock -n 9 || { echo PAIR_ALREADY_LOCKED >&2; exit 8; }
[[ ! -e "$RESULT_ROOT/BASELINE" && ! -e "$RESULT_ROOT/FIXED_SOURCE" ]] || { echo REFUSE_PARTIAL_OR_EXISTING_PAIR >&2; exit 8; }
python3 - <<'PY'
import hashlib,json,os,pathlib,datetime
e=os.environ; out=pathlib.Path(e['RESULT_ROOT'])/'provenance'; repo=pathlib.Path(e['FREEZE_REPO'])
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
b=json.loads((out/'BUILD_MANIFEST.json').read_text()); f=json.loads((out/'FREEZE_MANIFEST.json').read_text())
if b['freeze_commit']!=e['FREEZE_COMMIT'] or f['freeze_commit']!=e['FREEZE_COMMIT']: raise SystemExit('MANIFEST_FREEZE_MISMATCH')
if sha(out/'FREEZE_MANIFEST.json')!=b['freeze_manifest_sha256']: raise SystemExit('FREEZE_MANIFEST_BYTES_CHANGED')
if sha(e['NEW_BINARY'])!=b['new_binary_sha256']: raise SystemExit('NEW_BINARY_BYTES_CHANGED')
for rel,digest in f['source_files_sha256'].items():
    if sha(repo/rel)!=digest: raise SystemExit('FROZEN_SOURCE_BYTES_CHANGED:'+rel)
if sha(pathlib.Path(e['BUILD_ROOT'])/'environment_preflight.json')!=f['derived_preflight_sha256']:
    raise SystemExit('DERIVED_PREFLIGHT_CHANGED')
pre={'schema':'M1R_H03_TWO_ARM_PRERUN_V1','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'freeze_commit':e['FREEZE_COMMIT'],'algorithm_sha256':b['new_binary_sha256'],'house':'H03','seed':12,'sensor_seed':12,
 'horizon_s_each':240,'allowed_arms':{'BASELINE':False,'FIXED_SOURCE':True},
 'only_changed_scientific_parameter':'m1r_source_quadrature_enabled','historical_exact_replay':False}
(out/'PRE_RUN_MANIFEST.json').write_text(json.dumps(pre,indent=2)+'\n')
PY
export HOUSE=H03 ARM=M1R SEED=12 SENSOR_SEED=12 TIMEOUT_SEC=240.0 REALTIME_FACTOR=1.0
export METHOD=CTPI_G2_M1_M2 METHOD_FAMILY=ctpi_two_module
export STEPS_SOURCE_UPDATE=3 MAX_WARMUP_ITERATIONS=3 MIN_WARMUP_ITERATIONS=1
export M1R_V41_HISTORICAL_ROLLING_PERSISTENCE=true
export CONTEXT_BANK_EXPORT_ENABLED=true M1R_V41_LIGHTWEIGHT_AUDIT=true
export REPO_ROOT=$FREEZE_REPO PFDI_INSTALL_ROOT=$BUILD_ROOT GIT_COMMIT=$FREEZE_COMMIT
export CTPI_LAUNCH_FILE=$FREEZE_REPO/closed_loop/ctpi/vgr_gsl_pmfs_ctpi_fasttrack.launch.py
export VGR_BRIDGE_SOURCE_ROOT=/home/zyc/CTPI_G2_M12_SEED12_20260905/vgr_bridge_overlay_c8454d5
export ENV_PREFLIGHT=$BUILD_ROOT/environment_preflight.json INTEGRITY_REPORT=$BUILD_ROOT/environment_preflight.json
export GEOMETRY_MANIFEST=$OLD_REPO/evidence/cstar_environment_20260906/maps_v1/geometry_manifest.json
export QUALIFIED_HELPER=/home/zyc/CSTAR_CONTROLLED_ASSETS_20260907/tools/cstar_numeric_wind_raw_query
export DOMAIN_ID=226 OUTER_DEADLINE_SEC=1200 NAV_COMMAND_QUANTUM_S=2.0
export GMRF_UPDATE_ON_NEW_OBSERVATION_ONLY=false
unset RUN_ID CONTEXT_BANK_EXPORT_DIRECTORY
export PAIR_WALL_START_EPOCH=$(date +%s.%N)
record_pair_walltime() {
  export PAIR_EXIT_STATUS=$? PAIR_WALL_END_EPOCH=$(date +%s.%N)
  python3 - <<'PY'
import datetime,json,os,pathlib
e=os.environ; start=float(e['PAIR_WALL_START_EPOCH']); end=float(e['PAIR_WALL_END_EPOCH'])
utc=lambda t:datetime.datetime.fromtimestamp(t,datetime.timezone.utc).isoformat()
m={'scope':'paired runner execution excluding build and initial preflight','wall_start_utc':utc(start),
   'wall_end_utc':utc(end),'elapsed_s':end-start,'exit_status':int(e['PAIR_EXIT_STATUS'])}
(pathlib.Path(e['RESULT_ROOT'])/'provenance'/'PAIR_WALLTIME.json').write_text(json.dumps(m,indent=2)+'\n')
PY
}
trap record_pair_walltime EXIT
for PAIR_LABEL in BASELINE FIXED_SOURCE; do
  check_idle
  export RUN_ROOT=$RESULT_ROOT/$PAIR_LABEL
  if [[ "$PAIR_LABEL" == BASELINE ]]; then export M1R_SOURCE_QUADRATURE_ENABLED=false
  else export M1R_SOURCE_QUADRATURE_ENABLED=true; fi
  export PAIR_LABEL
  export ARM_WALL_START_EPOCH=$(date +%s.%N)
  set +e
  bash "$FREEZE_REPO/closed_loop/ctpi/run_ctpi_fasttrack_case_safe_20260903.sh" \
    >"$RESULT_ROOT/${PAIR_LABEL}_runner.log" 2>&1
  ARM_RUN_EXIT_STATUS=$?
  set -e
  export ARM_RUN_EXIT_STATUS ARM_WALL_END_EPOCH=$(date +%s.%N)
  python3 - <<'PY'
import datetime,json,os,pathlib
e=os.environ; start=float(e['ARM_WALL_START_EPOCH']); end=float(e['ARM_WALL_END_EPOCH'])
utc=lambda t:datetime.datetime.fromtimestamp(t,datetime.timezone.utc).isoformat()
m={'pair_label':e['PAIR_LABEL'],'scope':'safe runner including startup and cleanup',
   'wall_start_utc':utc(start),'wall_end_utc':utc(end),'elapsed_s':end-start,
   'exit_status':int(e['ARM_RUN_EXIT_STATUS']),'horizon_s':240}
(pathlib.Path(e['RESULT_ROOT'])/'provenance'/(e['PAIR_LABEL']+'_WALLTIME.json')).write_text(json.dumps(m,indent=2)+'\n')
PY
  [[ "$ARM_RUN_EXIT_STATUS" == 0 ]] || { echo "ARM_RUNNER_FAILED=$PAIR_LABEL" >&2; exit "$ARM_RUN_EXIT_STATUS"; }
  python3 - <<'PY'
import hashlib,json,os,pathlib,re
e=os.environ; run=pathlib.Path(e['RUN_ROOT'])/'H03_seed12_M1R'; prov=pathlib.Path(e['RESULT_ROOT'])/'provenance'
b=json.loads((prov/'BUILD_MANIFEST.json').read_text()); m=json.loads((run/'formal_runtime_manifest.json').read_text())
if (m['house'],m['seed'],m['sensor_seed'],m['timeout_sec'],m['algorithm_sha256'],m['git_commit']) != ('H03',12,12,240.0,b['new_binary_sha256'],e['FREEZE_COMMIT']):
    raise SystemExit('PAIRED_RUNTIME_MANIFEST_MISMATCH')
if hashlib.sha256(pathlib.Path(e['NEW_BINARY']).read_bytes()).hexdigest()!=b['new_binary_sha256']: raise SystemExit('BINARY_CHANGED_DURING_PAIR')
if m.get('pfdi_mode')!='cer_ratio_m1' or m.get('m1r_historical_rolling_persistence') is not True:
    raise SystemExit('HISTORICAL_ROLLING_MODE_NOT_BOUND')
if m.get('m1r_source_quadrature_enabled') is not (e['M1R_SOURCE_QUADRATURE_ENABLED']=='true'):
    raise SystemExit('MANIFEST_QUADRATURE_FLAG_MISMATCH')
flags=[]
for p in (run/'tmp').glob('launch_params_*'):
    flags+=re.findall(r'^\s+m1r_source_quadrature_enabled:\s*(true|false)\s*$',p.read_text(),re.M)
if flags!=[e['M1R_SOURCE_QUADRATURE_ENABLED']]: raise SystemExit('ACTUAL_LAUNCH_QUADRATURE_FLAG_MISMATCH:'+repr(flags))
status=json.loads((run/'run_status.json').read_text())
if status.get('status')!='time_budget_timeout': raise SystemExit('EXPECTED_FIXED_BUDGET_NOT_REACHED:'+repr(status))
print('H03_ARM_RUNTIME_BOUND='+e['PAIR_LABEL'])
PY
done
printf 'M1R_H03_TWO_ARM_COMPLETE=%s\n' "$RESULT_ROOT"
