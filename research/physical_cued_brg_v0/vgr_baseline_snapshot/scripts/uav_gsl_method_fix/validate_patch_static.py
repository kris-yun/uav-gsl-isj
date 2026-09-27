#!/usr/bin/env python3
"""Static checks for the UAV-GSL method patch.

Works in two layouts:
1. Patch package layout: uav_gsl_method_fix/code/...
2. Installed ROS layout: vgr_bridge/scripts/uav_gsl_method_fix plus GSL_SERVER_ROOT.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Dict


def fail(msg: str) -> None:
    print(f"[FAIL] {msg}")
    raise SystemExit(1)


def discover_files() -> Dict[str, Path]:
    script = Path(__file__).resolve()
    pkg_root = script.parents[2]
    package_pmfs = pkg_root / "code/src/PMFS.cpp"
    if package_pmfs.exists():
        return {
            "PMFS.cpp": pkg_root / "code/src/PMFS.cpp",
            "PMFS_utils.cpp": pkg_root / "code/src/PMFS_utils.cpp",
            "PMFS.hpp": pkg_root / "code/src/PMFS.hpp",
            "Settings.hpp": pkg_root / "code/include/Settings.hpp",
            "PwcCorrector.hpp": pkg_root / "code/include/gsl_server/pwc/PwcCorrector.hpp",
            "launch": pkg_root / "code/launch/vgr_gsl_unified_ablation.launch.py",
            "collect": pkg_root / "code/scripts/collect_results.py",
        }

    gsl_root = Path(os.environ.get("GSL_SERVER_ROOT", str(Path.home() / "ros2_ws/src/GSL/gsl_server"))).expanduser()
    vgr_root = Path(os.environ.get("VGR_BRIDGE_ROOT", str(Path.home() / "ros2_ws/src/vgr_bridge"))).expanduser()
    return {
        "PMFS.cpp": gsl_root / "src/algorithms/PMFS/PMFS.cpp",
        "PMFS_utils.cpp": gsl_root / "src/algorithms/PMFS/PMFS_utils.cpp",
        "PMFS.hpp": gsl_root / "include/gsl_server/algorithms/PMFS/PMFS.hpp",
        "Settings.hpp": gsl_root / "include/gsl_server/algorithms/PMFS/internal/Settings.hpp",
        "PwcCorrector.hpp": gsl_root / "include/gsl_server/pwc/PwcCorrector.hpp",
        "launch": vgr_root / "launch/vgr_gsl_unified_ablation.launch.py",
        "collect": script.with_name("collect_results.py"),
    }


def main() -> int:
    files = discover_files()
    for name, path in files.items():
        if not path.exists():
            fail(f"missing required file {name}: {path}")

    text_all = "\n".join(p.read_text(errors="ignore") for p in files.values() if p.suffix in {".cpp", ".hpp", ".py"})
    forbidden = [
        "d_est = std::max(0.5, std::min(d_est, 6.0))",
        "cut -d_ -f2",
        "err:",
        "SDR] replace if better",
    ]
    for needle in forbidden:
        if needle in text_all:
            fail(f"forbidden legacy pattern found: {needle}")

    pmfs = files["PMFS.cpp"].read_text(errors="ignore")
    if "static double bwe_ema" in pmfs or "static int number_of_updates" in pmfs:
        fail("BWE/measurement static state still present")
    if "settings.method.bwe_enabled" not in pmfs:
        fail("BWE flag is not used")
    if "settings.method.psde_online_enabled" not in pmfs:
        fail("PSDE online/final split missing")

    utils = files["PMFS_utils.cpp"].read_text(errors="ignore")
    for idx, line in enumerate(utils.splitlines(), start=1):
        if "sourcePositionGT" not in line:
            continue
        # Allowed: navigationTime metric before decisions; final error/audit after final estimate is fixed.
        if 190 <= idx <= 220:
            continue
        if idx >= 455:
            continue
        fail(f"unexpected GT use inside estimator decision section: line {idx}: {line.strip()}")

    collect = files["collect"].read_text(errors="ignore")
    if "rsplit(marker, 1)" not in collect:
        fail("collect_results.py does not contain safe suffix-based condition parsing")

    print("[OK] static patch checks passed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
