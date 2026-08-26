#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import argparse
import hashlib
import subprocess
import tempfile


def sha(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args()
    root = args.root.resolve()
    cpp = root / "ros2_package/src/gsl_server/algorithms/PMFS/internal/Simulations.cpp"
    hpp = root / "ros2_package/src/gsl_server/algorithms/PMFS/internal/Simulations.hpp"
    core = root / "ros2_package/src/gsl_server/algorithms/PMFS/internal/RCECV13.hpp"
    test = root / "ros2_package/test/test_rcec_v13_core.cpp"
    text = cpp.read_text()
    htext = hpp.read_text()

    required = [
        "RCEC_V13_FROZEN_CANDIDATE_20260826",
        "RCEC_V13_NATIVE_ABSOLUTE_V2_20260826",
        'std::getenv("RCEC_V13_ARM")',
        '"v11_stouffer"',
        '"crei_latest"',
        '"rcec_full"',
        "rcec_v13::normalRanks",
        "rcec_v13::normalRanks(rcecNativeMass, rcecCandidateIds)",
        "rcec_v13::conjunctiveConsensus",
        "rcec_v13::temporalMedian",
        "rcecV13CandidateIds.clear();",
        "rcecV13ConsensusHistory.clear();",
        "rcec_v13_scores_update_",
        "native_absolute_mass,native_normal_rank",
        "rcec_v13_acit_crei_native_absolute_tmem_v2",
        "meAciEvidenceReservoir = pcAciActiveEvents;",
        "candidatePrior[s] += std::max(pcAciDesignPriorGrid[cell], 0.0L);",
    ]
    for item in required:
        assert item in text + htext, f"missing required source contract: {item}"

    # The V11 pre-native snapshot may remain as legacy infrastructure, but the
    # corrected RCEC M2 block must not use it. Its native view is the current
    # post-native/pre-RCEC PMFS candidate ordering only.
    apply_start = text.index("bool Simulations::applyMEAci")
    rcec_start = text.index("RCEC_V13_NATIVE_ABSOLUTE_V2_20260826", apply_start)
    rcec_end = text.index("const double simulationWallSeconds", rcec_start)
    rcec_block = text[rcec_start:rcec_end]
    for item in [
        "pcAciIncomingNativePriorSnapshot",
        "rcecNativeBeforeMass",
        "rcecNativeAfterMass",
        "rcecNativeIncrement",
        "native_log_increment",
    ]:
        assert item not in rcec_block, f"feedback-coupled native view remains in RCEC block: {item}"

    forbidden = [
        "rcec_alpha",
        "rcec_temperature",
        "truth_distance",
        "source_error_gate",
        "house_specific",
    ]
    combined = (text + htext + core.read_text()).lower()
    for item in forbidden:
        assert item not in combined, f"forbidden adaptive/truth pattern: {item}"

    for item in [
        "spreads{0.25, 0.5, 1.0}",
        "decays{4.0, 8.0, 16.0}",
        "upstreamPenalties{1.0, 2.0}",
        "slopes{0.5, 1.0, 2.0}",
    ]:
        assert item in text, f"frozen ACIT family changed/missing: {item}"

    with tempfile.TemporaryDirectory() as td:
        exe = Path(td) / "test_rcec_v13_core"
        subprocess.run([
            "g++", "-std=c++20", "-O2", "-I" + str(root / "ros2_package/src"),
            str(test), "-o", str(exe)
        ], check=True)
        subprocess.run([str(exe)], check=True)

    print("RCEC_V13_SOURCE_CONTRACT=PASS")
    print("RCEC_V13_NATIVE_VIEW=ABSOLUTE_CURRENT_NATIVE_RANK")
    print("RCEC_V13_PREVIOUS_INJECTED_STATE_IN_CREI=false")
    print(f"Simulations.cpp_sha256={sha(cpp)}")
    print(f"Simulations.hpp_sha256={sha(hpp)}")
    print(f"RCECV13.hpp_sha256={sha(core)}")


if __name__ == "__main__":
    main()
