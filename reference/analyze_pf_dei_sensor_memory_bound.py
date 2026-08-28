#!/usr/bin/env python3
"""Independent truth-blind check of the claimed inter-stop sensor-memory bound."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
import math
import statistics
import os


MANIFEST = Path(os.environ.get(
    "PF_DEI_MANIFEST",
    str(Path(__file__).resolve().parents[1] / "artifacts/pf_dei_forward/observed_block_manifest.csv"),
))
OUT = MANIFEST.parent
TAU = 1.2
DT = 0.2
B = 10
THRESHOLD = 0.1


def floats(text: str) -> list[float]:
    return [float(x) for x in text.split(";") if x]


def main() -> int:
    with MANIFEST.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    by_run: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_run[(row["house"], row["seed"])].append(row)
    transitions: list[dict[str, object]] = []
    geometric_factor = sum(math.exp(-DT * k / TAU) for k in range(B)) / B

    for (house, seed), run_rows in sorted(by_run.items()):
        by_stop: dict[int, list[dict[str, str]]] = defaultdict(list)
        for row in run_rows:
            by_stop[int(row["physical_stop_id"])].append(row)
        stop_ids = sorted(by_stop)
        for prev_stop, next_stop in zip(stop_ids, stop_ids[1:]):
            prev_blocks = sorted(by_stop[prev_stop], key=lambda r: int(r["block_within_stop"]))
            next_blocks = sorted(by_stop[next_stop], key=lambda r: int(r["block_within_stop"]))
            prev_last = prev_blocks[-1]
            next_first = next_blocks[0]
            prev_values = floats(prev_last["measured_ppm"])
            next_times = floats(next_first["sample_times_s"])
            prev_times = floats(prev_last["sample_times_s"])
            if len(prev_values) != B or len(next_times) != B or len(prev_times) != B:
                raise RuntimeError(f"unexpected block size {house}/{seed}/{prev_stop}->{next_stop}")
            m0 = prev_values[-1]
            gap = next_times[0] - prev_times[-1]
            lb = m0 * math.exp(-gap / TAU) * geometric_factor
            archived_hit = next_first["archived_hit"] == "1"
            transitions.append({
                "house": house, "seed": int(seed),
                "prev_stop": prev_stop, "next_stop": next_stop,
                "prev_last_sample_time_s": prev_times[-1],
                "next_first_sample_time_s": next_times[0], "gap_s": gap,
                "previous_last_measured_ppm": m0,
                "memory_only_lower_bound_mean_ppm": lb,
                "memory_bound_exceeds_threshold": bool(lb > THRESHOLD),
                "next_block_archived_hit": archived_hit,
                "memory_bound_implies_hit": bool(lb > THRESHOLD and archived_hit),
            })

    assert len(transitions) == 484, len(transitions)
    qualifying = [r for r in transitions if r["memory_bound_exceeds_threshold"]]
    implied = [r for r in qualifying if r["next_block_archived_hit"]]
    summary = {
        "manifest": str(MANIFEST),
        "tau_s": TAU, "dt_s": DT, "block_samples": B, "threshold_ppm": THRESHOLD,
        "geometric_factor": geometric_factor,
        "transitions": len(transitions),
        "qualifying_memory_only_bound": len(qualifying),
        "qualifying_fraction": len(qualifying) / len(transitions),
        "qualifying_all_archived_hit": len(implied) == len(qualifying),
        "qualifying_archived_hits": len(implied),
        "gap_median_s": statistics.median(float(r["gap_s"]) for r in transitions),
        "gap_min_s": min(float(r["gap_s"]) for r in transitions),
        "gap_max_s": max(float(r["gap_s"]) for r in transitions),
        "by_house": {},
        "interpretation": (
            "A qualifying transition means the decayed previous measured state alone "
            "exceeds the PMFS threshold under the frozen zero-noise sensor model; it "
            "does not prove the physical concentration at the next stop was zero."
        ),
    }
    for house in sorted({str(r["house"]) for r in transitions}):
        subset = [r for r in transitions if r["house"] == house]
        q = [r for r in subset if r["memory_bound_exceeds_threshold"]]
        summary["by_house"][house] = {
            "transitions": len(subset),
            "qualifying": len(q),
            "fraction": len(q) / len(subset),
            "all_qualifying_archived_hit": all(r["next_block_archived_hit"] for r in q),
        }
    import io
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(transitions[0]))
    writer.writeheader(); writer.writerows(transitions)
    (OUT / "sensor_memory_bound_transitions.csv").write_text(buffer.getvalue(), encoding="utf-8")
    (OUT / "sensor_memory_bound_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
