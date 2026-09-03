#!/usr/bin/env bash
set -Eeo pipefail

REPO_ROOT="${REPO_ROOT:?set REPO_ROOT to the exact CTPI checkout}"
DEP_ROOT="${CTPI_DEP_OVERLAY_ROOT:?set CTPI_DEP_OVERLAY_ROOT to a fresh isolated dependency workspace}"
OLFACTION_SOURCE="${CTPI_OLFACTION_MSGS_SOURCE:-/home/zyc/ros2_ws/src/olfaction_msgs}"
GSL_ACTIONS_SOURCE="${CTPI_GSL_ACTIONS_SOURCE:-/home/zyc/ros2_ws/src/GSL/gsl_actions}"

[[ "$(git -C "${REPO_ROOT}" rev-parse HEAD)" != "" ]]
[[ ! -e "${DEP_ROOT}" ]] || { echo "CTPI_DEP_REFUSE_EXISTING_ROOT=${DEP_ROOT}" >&2; exit 71; }
[[ -f "${OLFACTION_SOURCE}/package.xml" && -f "${OLFACTION_SOURCE}/CMakeLists.txt" ]] || {
  echo "CTPI_DEP_OLFACTION_SOURCE_INVALID=${OLFACTION_SOURCE}" >&2; exit 72; }
[[ -f "${GSL_ACTIONS_SOURCE}/package.xml" && -f "${GSL_ACTIONS_SOURCE}/CMakeLists.txt" ]] || {
  echo "CTPI_DEP_GSL_ACTIONS_SOURCE_INVALID=${GSL_ACTIONS_SOURCE}" >&2; exit 72; }

mkdir -p "${DEP_ROOT}/src"
cp -a "${OLFACTION_SOURCE}" "${DEP_ROOT}/src/olfaction_msgs"
cp -a "${GSL_ACTIONS_SOURCE}" "${DEP_ROOT}/src/gsl_actions"

source /opt/ros/humble/setup.bash
export COLCON_LOG_PATH="${DEP_ROOT}/log"
(
  cd "${DEP_ROOT}"
  colcon build \
    --packages-select olfaction_msgs gsl_actions \
    --cmake-args -DCMAKE_BUILD_TYPE=Release \
    2>&1 | tee "${DEP_ROOT}/DEPENDENCY_BUILD.log"
)

OLFACTION_CONFIG="${DEP_ROOT}/install/olfaction_msgs/share/olfaction_msgs/cmake/olfaction_msgsConfig.cmake"
GSL_ACTIONS_CONFIG="${DEP_ROOT}/install/gsl_actions/share/gsl_actions/cmake/gsl_actionsConfig.cmake"
[[ -f "${OLFACTION_CONFIG}" ]] || { echo "CTPI_DEP_OLFACTION_CONFIG_MISSING=${OLFACTION_CONFIG}" >&2; exit 73; }
[[ -f "${GSL_ACTIONS_CONFIG}" ]] || { echo "CTPI_DEP_GSL_ACTIONS_CONFIG_MISSING=${GSL_ACTIONS_CONFIG}" >&2; exit 73; }

source "${DEP_ROOT}/install/setup.bash"
[[ "$(ros2 pkg prefix olfaction_msgs)" == "${DEP_ROOT}/install/olfaction_msgs" ]]
[[ "$(ros2 pkg prefix gsl_actions)" == "${DEP_ROOT}/install/gsl_actions" ]]

python3 - "${DEP_ROOT}" "${REPO_ROOT}" "${OLFACTION_SOURCE}" "${GSL_ACTIONS_SOURCE}" <<'PY'
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

dep_root, repo_root, olf_source, gsl_source = map(Path, sys.argv[1:])

def file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def tree_sha(root: Path, exclude_git: bool = False) -> tuple[str, int, int]:
    h = hashlib.sha256(); files = 0; links = 0
    for path in sorted(root.rglob('*'), key=lambda p: p.as_posix()):
        rel = path.relative_to(root).as_posix()
        if exclude_git and (rel == '.git' or rel.startswith('.git/')):
            continue
        if path.is_symlink():
            links += 1; payload = f'L\t{rel}\t{os.readlink(path)}\n'.encode()
        elif path.is_file():
            files += 1; payload = f'F\t{rel}\t{file_sha(path)}\n'.encode()
        elif path.is_dir():
            payload = f'D\t{rel}\n'.encode()
        else:
            payload = f'O\t{rel}\n'.encode()
        h.update(payload)
    return h.hexdigest(), files, links

sources = {}
for name, path in [('olfaction_msgs', olf_source), ('gsl_actions', gsl_source)]:
    sha, files, links = tree_sha(path, exclude_git=True)
    sources[name] = {
        'path': str(path.resolve()),
        'tree_sha256_excluding_git': sha,
        'files_excluding_git': files,
        'symlinks_excluding_git': links,
        'package_xml_sha256': file_sha(path/'package.xml'),
        'cmakelists_sha256': file_sha(path/'CMakeLists.txt'),
    }

install_sha, install_files, install_links = tree_sha(dep_root/'install')
versions = {}
for package in ('libspdlog-dev', 'libfmt-dev'):
    proc = subprocess.run(['dpkg-query', '-W', '-f=${Version}', package], capture_output=True, text=True)
    versions[package] = proc.stdout.strip() if proc.returncode == 0 else f'UNAVAILABLE:{proc.stderr.strip()}'

report = {
    'contract': 'CTPI_M3_FASTTRACK_DEPENDENCY_OVERLAY_V1',
    'repo_head': subprocess.check_output(['git', '-C', str(repo_root), 'rev-parse', 'HEAD'], text=True).strip(),
    'dependency_root': str(dep_root.resolve()),
    'sources': sources,
    'install_tree_sha256': install_sha,
    'install_files': install_files,
    'install_symlinks': install_links,
    'critical_outputs': {
        'olfaction_msgs_config_sha256': file_sha(dep_root/'install/olfaction_msgs/share/olfaction_msgs/cmake/olfaction_msgsConfig.cmake'),
        'gsl_actions_config_sha256': file_sha(dep_root/'install/gsl_actions/share/gsl_actions/cmake/gsl_actionsConfig.cmake'),
    },
    'system_packages': versions,
    'status': 'CTPI_MESSAGE_DEPENDENCY_OVERLAY=PASS',
}
(dep_root/'DEPENDENCY_OVERLAY_MANIFEST.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n', encoding='utf-8')
PY

echo CTPI_MESSAGE_DEPENDENCY_OVERLAY=PASS
echo "CTPI_CUSTOM_MSG_OVERLAY_ROOT=${DEP_ROOT}/install"
