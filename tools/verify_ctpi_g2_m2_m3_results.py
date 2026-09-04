#!/usr/bin/env python3
"""Independent recomputation of final CTPI-G2 M2/M3 gate summaries."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--m2", type=Path, required=True)
    parser.add_argument("--m3", type=Path, required=True)
    parser.add_argument("--m3-module", type=Path, required=True)
    args = parser.parse_args()
    m2 = json.loads(args.m2.read_text(encoding="utf-8"))
    m3 = json.loads(args.m3.read_text(encoding="utf-8"))
    assert m2["contract"] == "CTPI_G2_M2_CROSSHOUSE_FIELD_GATE_V1" and m2["status"] == "PASS"
    assert all(house["pass"] and all(house["criteria"].values()) for house in m2["houses"])
    assert m3["contract"] == "CTPI_G2_M3_HELDOUT_OFFLINE_GATE_V1"
    assert m3["observation_adapter_pass"] and m3["status"] == "NO_GO"
    assert m3["m3_module_sha256"] == sha256_file(args.m3_module)
    assert len(m3["worlds"]) == m3["world_count"] == 128
    delta = np.asarray([
        world["policies"]["h2"]["source_risk_auc"]
        - world["policies"]["myopic"]["source_risk_auc"]
        for world in m3["worlds"]
    ])
    wins = int(np.count_nonzero(delta < -1.0e-12))
    losses = int(np.count_nonzero(delta > 1.0e-12))
    ties = len(delta) - wins - losses
    assert [wins, losses, ties] == m3["primary"]["wins_losses_ties"] == [22, 106, 0]
    np.testing.assert_allclose(float(np.mean(delta)), m3["primary"]["mean_delta"], atol=1.0e-15)
    assert not all(m3["criteria"].values())
    print("CTPI_G2_M2_RESULT_RECOMPUTE=PASS")
    print("CTPI_G2_M3_RESULT_RECOMPUTE=PASS")
    print("CTPI_G2_M3_FROZEN_VERDICT=NO_GO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
