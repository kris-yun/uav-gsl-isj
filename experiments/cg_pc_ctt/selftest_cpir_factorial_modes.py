#!/usr/bin/env python3
"""Bank-free contract test for the frozen CPIR 2x2 factorial modes."""
from __future__ import annotations

from pathlib import Path

import numpy as np

from cpir_three_module_shadow import (
    MEMBER_COUNT,
    carrier_scores,
    raw_events,
    stateful_events_members,
)


ROOT = Path(__file__).resolve().parents[2]

FACTORS = {
    "F00": {"runtime": "cpir_a1", "sensor": "raw", "score": "count_only"},
    "F01": {"runtime": "cpir_m1_m3", "sensor": "raw", "score": "stop_resolved"},
    "F10": {"runtime": "cpir_a2", "sensor": "stateful", "score": "count_only"},
    "F11": {"runtime": "cpir_a3", "sensor": "stateful", "score": "stop_resolved"},
}


def differing_factors(left: str, right: str) -> set[str]:
    return {
        key for key in ("sensor", "score")
        if FACTORS[left][key] != FACTORS[right][key]
    }


def main() -> int:
    assert differing_factors("F00", "F01") == {"score"}
    assert differing_factors("F01", "F11") == {"sensor"}
    assert differing_factors("F00", "F10") == {"sensor"}
    assert differing_factors("F10", "F11") == {"score"}
    assert len({item["runtime"] for item in FACTORS.values()}) == 4

    # Formula-level isolation: an arm pair sharing a sensor factor must receive
    # the exact same event matrix, while its score factor alone may differ.
    physical = np.zeros((MEMBER_COUNT, 170), dtype=np.float64)
    physical[:4, 2:6] = 1.0
    physical[4:, 82:86] = 1.0
    stops = [np.arange(0, 80), np.arange(80, 160)]
    raw = np.stack([raw_events(physical[m:m + 1], stops) for m in range(MEMBER_COUNT)])
    stateful = stateful_events_members(physical, stops)
    assert raw.shape == stateful.shape == (MEMBER_COUNT, 2)
    # Use heterogeneous candidate probabilities so stop identity is
    # load-bearing. The event arrays above separately exercise both sensor
    # operators without coupling this test to a specially tuned tape.
    q_raw = np.asarray([[7.5 / 9.0, 1.5 / 9.0],
                        [2.5 / 9.0, 6.5 / 9.0]])
    q_state = np.asarray([[6.5 / 9.0, 2.5 / 9.0],
                          [1.5 / 9.0, 7.5 / 9.0]])
    q0 = np.asarray([0.5, 0.5])
    observed = np.asarray([True, False])
    visible = np.asarray([0, 1])
    scores = {}
    for factorial_id, factor in FACTORS.items():
        q = q_raw if factor["sensor"] == "raw" else q_state
        scores[factorial_id], _ = carrier_scores(
            q0, q, observed, visible, factor["score"]
        )
    assert not np.allclose(scores["F00"], scores["F01"])
    assert not np.allclose(scores["F10"], scores["F11"])

    cpp = (ROOT / "ros2_package" / "src" / "gsl_server" / "algorithms" /
           "PMFS" / "CPIR.cpp").read_text(encoding="utf-8")
    pmfs = (ROOT / "ros2_package" / "src" / "gsl_server" / "algorithms" /
            "PMFS" / "PMFS.cpp").read_text(encoding="utf-8")
    launch = (ROOT / "closed_loop" / "cpir" /
              "vgr_gsl_pmfs_cpir.launch.py").read_text(encoding="utf-8")
    runner = (ROOT / "closed_loop" / "cpir" /
              "run_cpir_formal_case_20260901.sh").read_text(encoding="utf-8")

    # Source wiring must implement the same two independent switches as the
    # declared matrix. No mode-specific formula or scientific constant exists.
    assert 'pfdiMode == "cpir_a1" || pfdiMode == "cpir_m1_m3"' in cpp
    assert 'pfdiMode == "cpir_a3" || pfdiMode == "cpir_m1_m3"' in cpp
    assert 'pfdiMode != "cpir_m1_m3"' in pmfs
    assert 'pfdiMode == "cpir_m1_m3"' in pmfs
    assert "'cpir_m1_m3': 'F01'" in launch
    assert 'F01) PFDI_MODE="cpir_m1_m3"' in runner

    print("CPIR_FACTORIAL_MODE_SELFTEST=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
