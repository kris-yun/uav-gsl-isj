#!/usr/bin/env python3
"""Truth-blind lower bound on inter-stop sensor-memory contamination.

This diagnostic uses only the reconstructed measured-ppm block manifest and the
source-proven native sensor parameters.  It does NOT read true gas, true source,
localization error, or any ON/OFF performance label.

For the frozen historical VGR configuration:
  gain = 1, baseline = 0, noise = 0,
  tau_rise = tau_recovery = tau,
  concentration input is non-negative,
  sensor state is run-persistent.

The homogeneous contribution of the previous measured sensor state m0 to a
future sample after elapsed time t is m0*exp(-t/tau).  Because every physical
input contribution is non-negative, this is a lower bound on the future output
contribution due to inherited state alone.

For the first B samples of the next stop, with sample interval dt and elapsed gap
g from the previous stop's last consumed sample to the next stop's first consumed
sample, the inherited-state-only lower bound on the next block mean is

  LB = m_prev * exp(-g/tau) * mean_{k=0..B-1} exp(-k*dt/tau).

If LB > thresholdGas, then the previous sensor state alone is sufficient to force
the next first PMFS block to HIT even under a counterfactual zero physical-gas
input throughout the gap and block.  Native non-negative gas input can only add
to this contribution.

This result is a mechanism diagnostic, not a localization-performance metric.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


def _parse_series(text: str) -> np.ndarray:
    return np.asarray([float(x) for x in str(text).split(";") if x != ""], dtype=float)


def analyze(path: Path, tau: float, sample_dt: float, samples_per_block: int,
            threshold: float) -> dict:
    if not (tau > 0 and sample_dt > 0 and samples_per_block > 0 and threshold >= 0):
        raise ValueError("invalid sensor parameters")
    df = pd.read_csv(path)
    required = {
        "house", "seed", "physical_stop_id", "sample_times_s", "measured_ppm",
        "archived_hit", "block_within_stop",
    }
    missing = sorted(required.difference(df.columns))
    if missing:
        raise ValueError(f"missing manifest columns: {missing}")
    forbidden = {"true_gas_ppm", "true_source", "localization_error", "final_error"}
    if any(col in df.columns for col in forbidden):
        raise ValueError("forbidden truth/performance column present")

    work = df.copy()
    work["_times"] = work["sample_times_s"].map(_parse_series)
    work["_measured"] = work["measured_ppm"].map(_parse_series)
    if not all(len(x) == samples_per_block for x in work["_times"]):
        raise ValueError("not every block has the frozen number of consumed timestamps")
    if not all(len(x) == samples_per_block for x in work["_measured"]):
        raise ValueError("not every block has the frozen number of measured samples")
    work["first_time"] = work["_times"].map(lambda x: float(x[0]))
    work["last_time"] = work["_times"].map(lambda x: float(x[-1]))
    work["first_measured"] = work["_measured"].map(lambda x: float(x[0]))
    work["last_measured"] = work["_measured"].map(lambda x: float(x[-1]))

    # Collapse completed blocks to physical stops while preserving run chronology.
    stops = (
        work.sort_values(["house", "seed", "first_time"])
        .groupby(["house", "seed", "physical_stop_id"], sort=False)
        .agg(
            first_time=("first_time", "min"),
            last_time=("last_time", "max"),
            first_measured=("first_measured", "first"),
            last_measured=("last_measured", "last"),
            first_block_hit=("archived_hit", "first"),
            block_count=("block_within_stop", "count"),
        )
        .reset_index()
    )

    block_history_factor = float(np.mean([
        math.exp(-sample_dt * k / tau) for k in range(samples_per_block)
    ]))
    transitions = []
    for (house, seed), run in stops.groupby(["house", "seed"], sort=False):
        rows = run.sort_values("first_time").to_dict("records")
        for prev, nxt in zip(rows[:-1], rows[1:]):
            gap = float(nxt["first_time"] - prev["last_time"])
            if gap < -1e-9:
                raise ValueError("non-monotone stop timing")
            inherited_lb = float(
                prev["last_measured"] * math.exp(-max(gap, 0.0) / tau)
                * block_history_factor
            )
            transitions.append({
                "house": str(house),
                "seed": int(seed),
                "gap_s": gap,
                "previous_last_measured_ppm": float(prev["last_measured"]),
                "next_first_measured_ppm": float(nxt["first_measured"]),
                "history_only_next_block_mean_lower_bound_ppm": inherited_lb,
                "history_alone_guarantees_hit": bool(inherited_lb > threshold),
                "next_first_block_archived_hit": bool(nxt["first_block_hit"]),
            })

    tdf = pd.DataFrame(transitions)
    guaranteed = tdf["history_alone_guarantees_hit"].astype(bool)
    if guaranteed.any() and not tdf.loc[guaranteed, "next_first_block_archived_hit"].astype(bool).all():
        raise RuntimeError("positive-system lower-bound contract violated")

    by_house = {}
    for house, hdf in tdf.groupby("house"):
        mask = hdf["history_alone_guarantees_hit"].astype(bool)
        by_house[str(house)] = {
            "transitions": int(len(hdf)),
            "history_guaranteed_hits": int(mask.sum()),
            "fraction": float(mask.mean()),
            "median_gap_s": float(hdf["gap_s"].median()),
            "median_previous_last_measured_ppm": float(hdf["previous_last_measured_ppm"].median()),
        }

    summary = {
        "contract": "PF_DEI_SENSOR_MEMORY_LOWER_BOUND_V1",
        "manifest": str(path),
        "tau_s": float(tau),
        "sample_dt_s": float(sample_dt),
        "samples_per_block": int(samples_per_block),
        "threshold_ppm": float(threshold),
        "block_history_factor": block_history_factor,
        "previous_state_ppm_needed_to_force_zero_input_block_hit_at_zero_gap": float(threshold / block_history_factor),
        "stops": int(len(stops)),
        "inter_stop_transitions": int(len(tdf)),
        "history_guaranteed_hits": int(guaranteed.sum()),
        "history_guaranteed_fraction": float(guaranteed.mean()),
        "all_history_guaranteed_transitions_archived_hit": bool(
            tdf.loc[guaranteed, "next_first_block_archived_hit"].astype(bool).all()
        ) if guaranteed.any() else True,
        "by_house": by_house,
        "interpretation": (
            "A guaranteed transition means inherited sensor state alone is sufficient "
            "to force the next first block HIT under a counterfactual zero physical-gas "
            "suffix; it does not claim that the real suffix contained zero gas."
        ),
    }
    return summary, tdf


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--tau", type=float, default=1.2)
    parser.add_argument("--sample-dt", type=float, default=0.2)
    parser.add_argument("--samples-per-block", type=int, default=10)
    parser.add_argument("--threshold", type=float, default=0.1)
    parser.add_argument("--out-json", type=Path)
    parser.add_argument("--out-csv", type=Path)
    args = parser.parse_args()
    summary, transitions = analyze(
        args.manifest, args.tau, args.sample_dt, args.samples_per_block, args.threshold
    )
    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    if args.out_csv:
        args.out_csv.parent.mkdir(parents=True, exist_ok=True)
        transitions.to_csv(args.out_csv, index=False)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
