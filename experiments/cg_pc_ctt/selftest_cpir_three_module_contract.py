#!/usr/bin/env python3
"""Bank-free formula/source/launch audit for the frozen CPIR three modules."""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

import numpy as np

from cpir_three_module_shadow import (
    ALPHA,
    MEMBER_COUNT,
    STOP_SAMPLES,
    carrier_scores,
    projection,
    raw_events,
    stateful_events_members,
)


ROOT = Path(__file__).resolve().parents[2]


def launch_default(text: str, name: str) -> str:
    pattern = rf"DeclareLaunchArgument\('{re.escape(name)}', default_value='([^']+)'\)"
    match = re.search(pattern, text)
    if not match:
        raise AssertionError(f"missing launch default: {name}")
    return match.group(1)


def main() -> int:
    contract_path = ROOT / "docs" / "CPIR_THREE_MODULE_FORMULA_CONTRACT_20260831.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    modules = contract["paper_modules"]
    assert list(modules) == ["M1", "M2", "M3"]
    assert modules["M1"]["member_count_runtime"] == MEMBER_COUNT == 8
    assert modules["M1"]["member_semantics"] == "joint_source_placement_height_transport_nuisance_atom"
    assert math.isclose(modules["M2"]["alpha"], ALPHA, rel_tol=0.0, abs_tol=1e-15)
    assert modules["M2"]["stop_samples"] == STOP_SAMPLES == 80
    assert modules["M3"]["joint_claim"] == "composite_likelihood_not_exact_joint_transport_probability"

    # Pure synthetic M1/M2/M3 isolation. No bank metadata or payload is opened.
    physical = np.zeros((MEMBER_COUNT, 170), dtype=np.float64)
    physical[:, 2:6] = 1.0
    stops = [np.arange(0, 80), np.arange(80, 160)]
    assert raw_events(physical[:1], stops).tolist() == [True, False]
    stateful = stateful_events_members(physical, stops)
    assert stateful.shape == (MEMBER_COUNT, 2)
    q = (stateful.sum(axis=0, keepdims=True) + 0.5) / (MEMBER_COUNT + 1.0)
    q = np.vstack([q, q[:, ::-1]])
    q0 = np.asarray([0.5, 0.5])
    observed = np.asarray([True, False])
    count_score, _ = carrier_scores(q0, q, observed, np.asarray([0, 1]), "count_only")
    stop_score, posterior = carrier_scores(q0, q, observed, np.asarray([0, 1]), "stop_resolved")
    assert not np.allclose(count_score, stop_score)
    assert math.isclose(float(posterior.sum()), 1.0, rel_tol=0.0, abs_tol=1e-12)
    mapping = np.asarray([0, 0, 1, 1, 1])
    lifted = projection(posterior, mapping, np.asarray([2, 3]))
    assert np.allclose(np.bincount(mapping, weights=lifted), posterior)

    cpp = (ROOT / "ros2_package" / "src" / "gsl_server" / "algorithms" /
           "PMFS" / "CPIR.cpp").read_text(encoding="utf-8")
    for marker in (
        'pfdiMode == "cpir_a1"',
        'pfdiMode == "cpir_a3"',
        'CPIR_CELL_MANIFEST_MISSING_FREE_CELL',
        'cpirCarrierReferenceMass[source] *',
        'std::log1p(-qsb)',
        'cpirCellCache.clear()',
    ):
        assert marker in cpp, marker

    launch = (ROOT / "closed_loop" / "cpir" /
              "vgr_gsl_pmfs_cpir.launch.py").read_text(encoding="utf-8")
    assert launch_default(launch, "flight_height") == "0.3"
    assert launch_default(launch, "maxUpdatesPerStop") == "8"
    assert launch_default(launch, "measurement_block_samples") == "10"
    assert launch_default(launch, "measurement_settle_samples") == "0"
    assert launch_default(launch, "deltaTime") == "0.2"
    assert launch_default(launch, "pfdi_mode") == "UNSET"
    assert launch_default(launch, "algorithm") == "PMFS"
    assert launch_default(launch, "ablation_id") == "UNSET"
    declared = re.findall(r"DeclareLaunchArgument\('([^']+)'", launch)
    assert len(declared) == len(set(declared)), "duplicate launch argument"
    assert "CPIR_STOP_MUST_BE_EXACTLY_80_SAMPLES_WITH_ZERO_SETTLE" in launch
    assert "CPIR_ABLATION_MODE_MISMATCH" in launch

    print("CPIR_THREE_MODULE_BANK_FREE_CONTRACT_SELFTEST=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
