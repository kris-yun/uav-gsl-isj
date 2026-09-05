#!/usr/bin/env python3
"""Static contract checks for the M1+M2-only F01 closed-loop arm."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def require(text: str, token: str) -> None:
    if token not in text:
        raise AssertionError(f"CTPI_G2_M12_CONTRACT_MISSING:{token}")


def main() -> int:
    pmfs = (ROOT / "ros2_package/src/gsl_server/algorithms/PMFS/PMFS.cpp").read_text()
    launch = (ROOT / "closed_loop/ctpi/vgr_gsl_pmfs_ctpi_fasttrack.launch.py").read_text()
    runner = (ROOT / "closed_loop/ctpi/run_ctpi_fasttrack_case_safe_20260903.sh").read_text()
    crosshouse = (ROOT / "closed_loop/ctpi/run_ctpi_g2_m12_seed12_crosshouse_20260905.sh").read_text()
    bridge_prep = (ROOT / "tools/prepare_ctpi_g2_m12_vgr_bridge_overlay.py").read_text()
    simulations = (ROOT / "ros2_package/src/gsl_server/algorithms/PMFS/internal/Simulations.cpp").read_text()
    cpir = (ROOT / "ros2_package/src/gsl_server/algorithms/PMFS/CPIR.cpp").read_text()

    require(pmfs, 'ctpiPlannerEnabled = pfdiMode == "ctpi_f10" || pfdiMode == "ctpi_f11";')
    require(pmfs, 'ctpiTSDCEnabled = pfdiMode == "ctpi_f01" || pfdiMode == "ctpi_f11";')
    require(pmfs, 'pfdiMode == "ctpi_f00" || pfdiMode == "ctpi_f01" || pfdiMode == "ctpi_f10"')
    require(launch, "('CTPI_G2_M1_M2', 'ctpi_two_module')")
    require(launch, "allowed = {'off', 'ctpi_f00', 'ctpi_f01'}")
    require(launch, "'ctpi_f01': 'F01'")
    require(runner, 'F01) PFDI_MODE="ctpi_f01" ;;')
    require(runner, '"method:=${METHOD}" "method_family:=${METHOD_FAMILY}"')
    require(runner, 'VGR_BRIDGE_SOURCE_ROOT="${VGR_BRIDGE_SOURCE_ROOT:?')
    require(runner, 'CTPI_G2_M12_VGR_BRIDGE_PREFLIGHT_PASS')
    require(runner, '"vgr_bridge_contract_sha256": "${VGR_BRIDGE_CONTRACT_SHA256}"')
    require(crosshouse, 'VGR_BRIDGE_SOURCE_ROOT="${VGR_BRIDGE_SOURCE_ROOT:?')
    require(crosshouse, 'VGR_BRIDGE_SOURCE_ROOT="${VGR_BRIDGE_SOURCE_ROOT}"')
    require(bridge_prep, '"CTPI_G2_M1_M2": {"algorithm": "PMFS", "type": "proposed", "use_sepf": 0},')
    require(simulations, "if (weight == 0.0)")
    require(simulations, "if (statistics.weight_sum > 0.0)")
    require(simulations, "varianceOfHitProb[cellI] = 0.0;")
    require(simulations, 'GSL_INFO("[CTPI-DIAG] planner variance zero-mass cells={}"')
    require(cpir, "void stripTrailingCarriageReturn(std::string& line)")
    require(cpir, "stripTrailingCarriageReturn(line);")
    print("CTPI_G2_M12_F01_STATIC_CONTRACT=PASS")
    print("CTPI_G2_M12_M3_DISABLED_IN_F01=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
