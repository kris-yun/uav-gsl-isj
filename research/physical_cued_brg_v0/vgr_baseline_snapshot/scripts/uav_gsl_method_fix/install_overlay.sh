#!/usr/bin/env bash
set -euo pipefail

# Overlay this method patch onto a fresh official GSL/vgr_bridge checkout.
# Usage:
#   GSL_SERVER_ROOT=~/ros2_ws/src/GSL/gsl_server \
#   VGR_BRIDGE_ROOT=~/ros2_ws/src/vgr_bridge \
#   bash install_overlay.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
GSL_SERVER_ROOT="${GSL_SERVER_ROOT:-$HOME/ros2_ws/src/GSL/gsl_server}"
VGR_BRIDGE_ROOT="${VGR_BRIDGE_ROOT:-$HOME/ros2_ws/src/vgr_bridge}"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_ROOT="${BACKUP_ROOT:-$HOME/uav_gsl_method_backup_$STAMP}"

backup_and_copy() {
    local src="$1"
    local dst="$2"
    mkdir -p "$(dirname "$dst")"
    mkdir -p "$BACKUP_ROOT/$(dirname "$dst")"
    if [[ -f "$dst" ]]; then
        cp -a "$dst" "$BACKUP_ROOT/$dst"
    fi
    cp -a "$src" "$dst"
    echo "[COPY] $src -> $dst"
}

[[ -d "$GSL_SERVER_ROOT" ]] || { echo "[ERR] GSL_SERVER_ROOT not found: $GSL_SERVER_ROOT" >&2; exit 1; }
[[ -d "$VGR_BRIDGE_ROOT" ]] || { echo "[ERR] VGR_BRIDGE_ROOT not found: $VGR_BRIDGE_ROOT" >&2; exit 1; }

backup_and_copy "$PKG_ROOT/code/src/PMFS.cpp" "$GSL_SERVER_ROOT/src/algorithms/PMFS/PMFS.cpp"
backup_and_copy "$PKG_ROOT/code/src/PMFS_utils.cpp" "$GSL_SERVER_ROOT/src/algorithms/PMFS/PMFS_utils.cpp"
backup_and_copy "$PKG_ROOT/code/src/PMFS.hpp" "$GSL_SERVER_ROOT/include/gsl_server/algorithms/PMFS/PMFS.hpp"
backup_and_copy "$PKG_ROOT/code/include/Settings.hpp" "$GSL_SERVER_ROOT/include/gsl_server/algorithms/PMFS/internal/Settings.hpp"
backup_and_copy "$PKG_ROOT/code/include/gsl_server/pwc/PwcCorrector.hpp" "$GSL_SERVER_ROOT/include/gsl_server/pwc/PwcCorrector.hpp"
backup_and_copy "$PKG_ROOT/code/launch/vgr_gsl_unified_ablation.launch.py" "$VGR_BRIDGE_ROOT/launch/vgr_gsl_unified_ablation.launch.py"

mkdir -p "$VGR_BRIDGE_ROOT/scripts/uav_gsl_method_fix"
cp -a "$PKG_ROOT/code/scripts/"*.sh "$VGR_BRIDGE_ROOT/scripts/uav_gsl_method_fix/" 2>/dev/null || true
cp -a "$PKG_ROOT/code/scripts/"*.py "$VGR_BRIDGE_ROOT/scripts/uav_gsl_method_fix/" 2>/dev/null || true
chmod +x "$VGR_BRIDGE_ROOT/scripts/uav_gsl_method_fix/"*.sh 2>/dev/null || true

echo "[OK] Overlay installed. Backup root: $BACKUP_ROOT"
echo "[NEXT] Rebuild: cd ~/ros2_ws && colcon build --symlink-install --packages-select gsl_server vgr_bridge"
