#!/usr/bin/env python3
"""Verify the frozen ME-ACI V10 repository boundary."""

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EXPECTED = {
    "artifacts/gsl_actionserver_node": "14133117b9d24502acc8e45ad7c72fbd668fbe867fd73aeee17b70e52cfbe938",
    "ros2_package/src/gsl_server/algorithms/PMFS/internal/Simulations.cpp": "6f3955eef884f804df725eb0b39d39c3abe1c436b9f9cbb6419e6df881ef5198",
    "ros2_package/src/gsl_server/algorithms/PMFS/internal/Simulations.hpp": "ea358f1f23cefb807d7daf0f4efc31dd91e29c45717277f976955aa7109a8e00",
    "evidence/MEACI_V10_MAIN_INNOVATION_HOUSE123_SEED01_6OF6_20260824.zip": "2f9d261a1db7c455507482a85cb844d378c524985cc189de0678bf2cb66f532c",
}
RUN_CONTRACT = "MEACI_SEQUENTIAL_SPATIAL_REPLICATION_V4"


def sha256(path):
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def main():
    for relative, expected in EXPECTED.items():
        actual = sha256(ROOT / relative)
        assert actual == expected, "hash mismatch: {}: {}".format(relative, actual)

    with (ROOT / "evidence/RESULT_MATRIX.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 6
    assert all(row["pass"].lower() == "true" for row in rows)
    assert all(float(row["improvement_percent"]) >= 10.0 for row in rows)

    verification = json.loads((ROOT / "evidence/FREEZE_VERIFICATION.json").read_text(encoding="utf-8"))
    assert verification["status"] == "PASS"
    assert verification["run_contract"] == RUN_CONTRACT
    assert verification["case_count"] == verification["pass_count"] == 6
    assert verification["minimum_gain_fraction"] >= 0.10

    cases = sorted(path for path in (ROOT / "evidence/cases").iterdir() if path.is_dir())
    assert len(cases) == 6
    for case in cases:
        manifest = json.loads((case / "runtime_manifest.json").read_text(encoding="utf-8"))
        evaluation = json.loads((case / "meaci_evaluation.json").read_text(encoding="utf-8"))
        assert manifest["contract"] == RUN_CONTRACT
        assert manifest["algorithm_sha256"] == EXPECTED["artifacts/gsl_actionserver_node"]
        assert str(manifest["steps_source_update"]) == "3"
        assert evaluation["development_gate_pass"] is True
        assert evaluation["pmfs_paper_metric_improvement_fraction"] >= 0.10

    print(json.dumps({
        "status": "PASS",
        "contract": RUN_CONTRACT,
        "cases": len(cases),
        "pooled_improvement_fraction": verification["pooled_improvement_fraction"],
        "minimum_gain_fraction": verification["minimum_gain_fraction"],
        "verified_hashes": len(EXPECTED),
    }, indent=2))


if __name__ == "__main__":
    main()

