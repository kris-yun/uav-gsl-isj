#!/usr/bin/env python3
"""Static fail-closed audit for the House-aware CPIR formal runner."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "closed_loop" / "cpir" / "run_cpir_formal_case_20260901.sh"
LAUNCH = ROOT / "closed_loop" / "cpir" / "vgr_gsl_pmfs_cpir.launch.py"


def require(text: str, *markers: str) -> None:
    for marker in markers:
        assert marker in text, marker


def main() -> int:
    runner = RUNNER.read_text(encoding="utf-8")
    launch = LAUNCH.read_text(encoding="utf-8")

    # Formal cadence must be explicit, never inferred from development tapes.
    require(
        runner,
        'STEPS_SOURCE_UPDATE="${STEPS_SOURCE_UPDATE:?',
        'MAX_WARMUP_ITERATIONS="${MAX_WARMUP_ITERATIONS:?',
        'MIN_WARMUP_ITERATIONS="${MIN_WARMUP_ITERATIONS:?',
        '--steps-source-update "${STEPS_SOURCE_UPDATE}"',
        '--max-warmup-iterations "${MAX_WARMUP_ITERATIONS}"',
        '--min-warmup-iterations "${MIN_WARMUP_ITERATIONS}"',
    )

    # Exact frozen House scenario contract recovered from the prior paired runner.
    require(
        runner,
        'START_X="-3.17"; START_Y="-1.75"',
        'START_X="-0.50"; START_Y="-2.50"',
        'START_X="2.00"; START_Y="0.00"',
        'CONFIG_ID="2,4-1_fast"',
        'CONFIG_ID="3,5-1_fast"',
        'CONFIG_ID="1-2,5_fast"',
        'GAS_BACKEND="raw_house1_snapshot"',
        'GAS_BACKEND="gaden_player"',
        'CPIR_FORMAL_FRAME_QUERY_TIMEOUT_SEC',
        'wind_value_server.py',
    )

    # The same wrapper owns A0/A1/A2/A3 and always hashes/preflights the bank.
    require(
        runner,
        'A0) PFDI_MODE="off"',
        'A1) PFDI_MODE="cpir_a1"',
        'A2) PFDI_MODE="cpir_a2"',
        'A3) PFDI_MODE="cpir_a3"',
        'cpir_expected_bank_summary_sha256:=${BANK_SUMMARY_SHA}',
        'cpir_expected_cell_manifest_sha256:=${CELL_MANIFEST_SHA}',
        'measurement_deduplicate_sim_timestamps:=true',
        'sensor_config:=fopdt_tau1p2_dead0p4_noise0',
        'th_gas_present:=0.1',
    )

    # Launch-side guards and seed propagation must still be present.
    require(
        launch,
        'CPIR_STEPS_SOURCE_UPDATE_EXPECTED_MISMATCH',
        'CPIR_MAX_WARMUP_EXPECTED_MISMATCH',
        'CPIR_MIN_WARMUP_EXPECTED_MISMATCH',
        'CPIR_BANK_SUMMARY_SHA_MISMATCH',
        "'seed': _int('seed')",
        "'posterior_guidance_weight': 0.0",
    )

    print("CPIR_FORMAL_RUNNER_STATIC_SELFTEST=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
