#!/usr/bin/env python3
"""Pre-build handoff integrity checker for the frozen CTPI M3 fast-track.

Run this in a clean isolated checkout before materializing the generated CTPI
launch/runner or applying the runtime patch.  It verifies only pre-outcome
artifacts and never reads localization truth or experiment results.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ANCHOR_COMMIT = "44a20c9c92bb2643c17c5c73c68249197b8d163d"
EXPECTED_SHA256 = {
    "experiments/cg_pc_ctt/ctpi_m2_tsdc_frozen_v0.py": "854a2fc8513201cdb2ae497a62c0cd3c5fa09fdae2f1bc309ad594a8b1aaacf7",
    "experiments/cg_pc_ctt/ctpi_m3_pip_frozen_v0.py": "bcf065903ec8cd88533ff0ac0dbd453131a9aeaf0d075fbf71ec92dc00fc2706",
    "ros2_package/src/gsl_server/algorithms/PMFS/CTPI.cpp": "e5ce97b3f6ed5d1c7d17636933130a3b7207be9286b6173255d9ffca65fb8675",
    "ros2_package/src/gsl_server/algorithms/PMFS/PMFS.hpp": "7fe197312c6ea93cd8edf4876dd5d8c60328a64aa017b236f97848c24a00339e",
    "patches/CTPI_M3_FASTTRACK_RUNTIME_INTEGRATION_20260903.patch": "96e1e425a7c4e6e97ad123c1d46e67120dc86574b3d3927a370e5b99d1020743",
    "patches/CTPI_M3_FASTTRACK_LAUNCH_20260903.patch": "d4d9d992d78285ab87721e5249c7641f39181d9f9fb56057307d2ba2c9574c55",
    "patches/CTPI_M3_FASTTRACK_RUNNER_20260903.patch": "e4d6a3137dadca6997cd34d9177becc83861c16493c0057b80e4ca5acfd34ea0",
}
REQUIRED = (
    "tools/materialize_ctpi_m3_fasttrack_vm_files.py",
    "tools/apply_ctpi_m3_fasttrack_runtime_patch.py",
    "tools/ctpi_m3_fasttrack_preflight.py",
    "tools/ctpi_m3_static_parity.py",
    "tools/ctpi_m3_action_sanity.py",
    "tools/ctpi_true_closed_loop_check.py",
    "tools/ctpi_fasttrack_terminal_guard.py",
    "tools/ctpi_fasttrack_performance.py",
    "tools/ctpi_fasttrack_screen_gate.py",
    "tools/ctpi_crosshouse_performance.py",
    "closed_loop/ctpi/prepare_ctpi_m3_fasttrack_vm_20260903.sh",
    "closed_loop/ctpi/verify_ctpi_fasttrack_banks_vm_20260903.sh",
    "closed_loop/ctpi/run_ctpi_h01_seed0_smoke_20260903.sh",
    "closed_loop/ctpi/run_ctpi_h01_3seed_screen_20260903.sh",
    "closed_loop/ctpi/run_ctpi_crosshouse_36run_confirm_20260903.sh",
    "docs/CTPI_M3_FASTTRACK_FREEZE_20260903.md",
    "docs/CTPI_M3_FASTTRACK_PREREG_20260903.json",
)
GENERATED_MUST_BE_ABSENT = (
    "closed_loop/ctpi/vgr_gsl_pmfs_ctpi_fasttrack.launch.py",
    "closed_loop/ctpi/run_ctpi_fasttrack_case_safe_20260903.sh",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, required=True)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    root = args.repo_root.resolve()
    checks: dict[str, bool] = {}

    checks["git_worktree"] = (root / ".git").exists()
    if checks["git_worktree"]:
        ancestor = subprocess.run(
            ["git", "-C", str(root), "merge-base", "--is-ancestor", ANCHOR_COMMIT, "HEAD"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        checks["anchor_is_ancestor"] = ancestor.returncode == 0
        status = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        checks["clean_worktree"] = status == ""
    else:
        checks["anchor_is_ancestor"] = False
        checks["clean_worktree"] = False

    for rel, expected in EXPECTED_SHA256.items():
        path = root / rel
        checks[f"sha256:{rel}"] = path.is_file() and sha256(path) == expected
    for rel in REQUIRED:
        checks[f"required:{rel}"] = (root / rel).is_file()
    for rel in GENERATED_MUST_BE_ABSENT:
        checks[f"pre_materialize_absent:{rel}"] = not (root / rel).exists()

    prereg_path = root / "docs/CTPI_M3_FASTTRACK_PREREG_20260903.json"
    prereg = json.loads(prereg_path.read_text(encoding="utf-8")) if prereg_path.is_file() else {}
    cadence = prereg.get("runtime_cadence", {})
    checks["prereg_status"] = prereg.get("status") == "PREREGISTERED_BEFORE_TRUE_CLOSED_LOOP_OUTCOME"
    checks["cadence_3_3_1"] = (
        cadence.get("stepsSourceUpdate") == 3
        and cadence.get("maxWarmupIterations") == 3
        and cadence.get("minWarmupIterations") == 1
        and cadence.get("same_for_all_arms") is True
    )
    confirm = prereg.get("confirmatory_36run", {})
    checks["formal_seeds_3_4_5"] = confirm.get("seeds") == [3, 4, 5] and confirm.get("run_count") == 36

    for rel in (
        "closed_loop/ctpi/run_ctpi_h01_seed0_smoke_20260903.sh",
        "closed_loop/ctpi/run_ctpi_h01_3seed_screen_20260903.sh",
        "closed_loop/ctpi/run_ctpi_crosshouse_36run_confirm_20260903.sh",
    ):
        text = (root / rel).read_text(encoding="utf-8") if (root / rel).is_file() else ""
        checks[f"runner_cadence:{rel}"] = all(
            token in text
            for token in (
                'STEPS_SOURCE_UPDATE="${STEPS_SOURCE_UPDATE:-3}"',
                'MAX_WARMUP_ITERATIONS="${MAX_WARMUP_ITERATIONS:-3}"',
                'MIN_WARMUP_ITERATIONS="${MIN_WARMUP_ITERATIONS:-1}"',
            )
        )
        checks[f"runner_terminal_guard:{rel}"] = "ctpi_fasttrack_terminal_guard.py" in text

    passed = all(checks.values())
    report = {
        "contract": "CTPI_M3_FASTTRACK_CODEX_HANDOFF_CHECK_V0",
        "anchor_commit": ANCHOR_COMMIT,
        "checks": checks,
        "pass": passed,
        "verdict": "CTPI_M3_FASTTRACK_CODEX_HANDOFF=PASS" if passed else "CTPI_M3_FASTTRACK_CODEX_HANDOFF=FAIL",
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(report["verdict"])
    if not passed:
        for key, value in checks.items():
            if not value:
                print("FAILED=" + key)
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
