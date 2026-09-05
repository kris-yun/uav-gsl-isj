"""Read-only spent-log diagnostic, not a source estimator or utility gate.

Only compare adjacent 0.2 s records when BOTH pose records say stationary
and the printed x/y/z coordinates match. No gas, source truth, or outcome is
read. Exact equality refers to the precision of the archived CSV, not nature.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


def read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def key(row):
    return (int(row["step"]), round(float(row["t_sim_s"]) * 1_000_000))


def position(row):
    return tuple(float(row[c]) for c in ("x", "y", "z"))


def wind(row):
    values = tuple(float(row[c]) for c in ("wind_u", "wind_v", "wind_w"))
    if not all(math.isfinite(v) for v in (*values, *position(row))):
        raise ValueError("nonfinite wind or position")
    return values


def replay_resets(rows):
    """Report archival frame-index reversals, not inferred physical resets."""
    ordered = sorted(rows, key=key)
    return [{"time_s": float(b["t_sim_s"]), "step": int(b["step"]),
             "previous_iteration": int(a["iteration"]), "iteration": int(b["iteration"]),
             "same_printed_position": position(a) == position(b)}
            for a, b in zip(ordered, ordered[1:])
            if int(b["iteration"]) < int(a["iteration"])]


def summarize(winds, poses):
    pmap = {key(row): row for row in poses}
    if len(pmap) != len(poses):
        raise ValueError("duplicate pose keys")
    if len({key(row) for row in winds}) != len(winds):
        raise ValueError("duplicate wind keys")
    if set(pmap) != {key(row) for row in winds}:
        raise ValueError("wind/pose key mismatch")
    rows = sorted(winds, key=key)
    diffs, moving_diffs, segments = [], [], []
    segment = []
    previous = None
    for row in rows:
        pose = pmap[key(row)]
        if position(row) != position(pose):
            raise ValueError("wind/pose coordinate mismatch")
        vector = wind(row)
        stationary = int(pose["is_moving"]) == 0
        contiguous = previous is not None and key(row) == (
            key(previous)[0] + 1, key(previous)[1] + 200_000)
        comparable = contiguous and position(previous) == position(row)
        if comparable and stationary and int(pmap[key(previous)]["is_moving"]) == 0:
            delta = math.dist(vector, wind(previous))
            diffs.append(delta)
            segment.append(row)
        else:
            if len(segment) >= 2:
                segments.append(segment)
            segment = [row] if stationary else []
            if contiguous:
                moving_diffs.append(math.dist(vector, wind(previous)))
        previous = row
    if len(segment) >= 2:
        segments.append(segment)
    ranges = [max(max(wind(r)[i] for r in seg) - min(wind(r)[i] for r in seg)
                  for i in range(3)) for seg in segments]
    changed = [d for d in diffs if d > 0]
    return {
        "rows": len(rows), "matched_pose_rows": len(pmap),
        "stationary_adjacent_pairs": len(diffs),
        "stationary_changed_pairs_at_csv_precision": len(changed),
        "stationary_max_vector_delta_m_s": max(diffs, default=0),
        "stationary_rms_vector_delta_m_s": math.sqrt(sum(d*d for d in diffs) / len(diffs)) if diffs else None,
        "stationary_segments_at_least_two_samples": len(segments),
        "stationary_max_component_range_m_s": max(ranges, default=0),
        "longest_stationary_segment_s": max((float(s[-1]["t_sim_s"])-float(s[0]["t_sim_s"]) for s in segments), default=0),
        "other_adjacent_pairs": len(moving_diffs),
        "interpretation": "local temporal variation observed" if changed else "no local temporal variation observed at CSV precision",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--horizon", type=float, default=240.0,
                        help="Existing closed-loop contract horizon, not fit to outcomes")
    args = parser.parse_args()
    if not math.isfinite(args.horizon) or args.horizon <= 0:
        parser.error("horizon must be positive and finite")
    results = {}
    for house in ("H01", "H02", "H03"):
        for arm in ("A0", "F00", "F01"):
            name = f"{house}_seed12_{arm}"
            paths = [args.root / name / f for f in ("wind_trace.csv", "sim_pose_trace.csv")]
            raw = [read_rows(p) for p in paths]
            selected = [[r for r in rows if 0 <= float(r["t_sim_s"]) <= args.horizon] for rows in raw]
            result = summarize(*selected)
            result["replay_index_reversals"] = replay_resets(selected[0])
            result["rows_outside_contract_horizon"] = {p.name: len(a)-len(b) for p, a, b in zip(paths, raw, selected)}
            result["input_sha256"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
            results[name] = result
    report = {
        "status": "DESCRIPTIVE_INPUT_AUDIT_ONLY",
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "root": str(args.root.resolve()),
        "horizon_s": args.horizon,
        "selection": "All nine spent R4 runs within the declared horizon; adjacent steps 0.2 s apart, both is_moving=0, identical printed xyz; no outcome-based selection.",
        "limitations": ["Printed coordinates have finite precision; subprecision motion cannot be excluded.",
                       "Local wind changes do not identify the global transport operator, source, or nuisance.",
                       "No test of wind exogeneity, cross-arm causal effects, predictive skill, or closed-loop utility.",
                       "No source truth, gas observations, or banks were read."],
        "runs": results,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, allow_nan=False)
        handle.write("\n")
    for name, r in results.items():
        print(name, r["stationary_changed_pairs_at_csv_precision"], "/", r["stationary_adjacent_pairs"], "max_delta=", r["stationary_max_vector_delta_m_s"])


if __name__ == "__main__":
    main()
