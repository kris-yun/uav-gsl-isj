#!/usr/bin/env python3
"""Read-only, post-hoc R4 diagnostics; not a replacement qualification gate.

Uses sealed traces only. Does not load banks, run ROS, or reconstruct missing
posterior grids. Sensor/pose/wind summaries use their full recorded spans,
not an assumed alignment to the GSL-relative 240-second estimate horizon.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

from ctpi_g2_m12_seed12_performance import ARMS, GT, metrics


def read_csv(path):
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def state(row, house):
    x, y = float(row["estimate_x"]), float(row["estimate_y"])
    gx, gy = GT[house]
    return dict(t=float(row["sim_time"]), x=x, y=y,
                error_m=math.hypot(x-gx, y-gy),
                entropy_nats=float(row["posterior_entropy"]),
                variance_m2=float(row["posterior_variance"]))


def auc_between(states, lo, hi):
    # Same trapezoidal interpolation and constant endpoint extension as gate.
    points = sorted({r["t"]: r["error_m"] for r in states}.items())
    points = [(0., points[0][1])] + points + [(240., points[-1][1])]
    total = 0.
    for (a, ea), (b, eb) in zip(points, points[1:]):
        l, h = max(a, lo), min(b, hi)
        if h <= l or b <= a:
            continue
        el = ea + (eb-ea)*(l-a)/(b-a)
        eh = ea + (eb-ea)*(h-a)/(b-a)
        total += .5*(el+eh)*(h-l)
    return total


def compressed_xy(states):
    result = []
    for r in states:
        xy = [r["x"], r["y"]]
        if not result or xy != result[-1]:
            result.append(xy)
    return result


def summarize(root, house, arm):
    path = root / f"{house}_seed12_{arm}"
    manifest = json.loads((path / "formal_runtime_manifest.json").read_text())
    terminal = json.loads((path / "CTPI_FASTTRACK_CASE_TERMINAL.json").read_text())
    assert manifest["arm"] == arm and manifest["house"] == house and manifest["seed"] == 12
    assert terminal["pass"] is True
    states = [state(r, house) for r in read_csv(path / "source_estimate_trace.csv")
              if r["estimate_available"].lower() in ("true", "1")
              and 0 <= float(r["sim_time"]) <= 240]
    assert states and all(a["t"] <= b["t"] for a, b in zip(states, states[1:]))
    updates = []
    for audit in read_csv(path / "ctpi_audit/cpir_update_audit.csv"):
        t = float(audit["sim_time"])
        after = next((r for r in states if r["t"] >= t-1e-6), None)
        assert after is not None and after["t"]-t < 2., (path, t, after)
        updates.append(dict(update=int(audit["source_update_id"]), audit_t=t,
                            max_probability=float(audit["max_probability"]),
                            completed_stops=int(audit["completed_stops"]),
                            posterior=after))
    goals = [dict(t=float(r["sim_time"]), x=float(r["goal_x"]), y=float(r["goal_y"]))
             for r in read_csv(path / "navigation_trace.csv") if r["event"] == "SENT"]
    goal_xy = [(r["x"], r["y"]) for r in goals]
    pose = read_csv(path / "sim_pose_trace.csv")
    sensor = read_csv(path / "sensor_trace.csv")
    wind = read_csv(path / "wind_trace.csv")
    xy = [(float(r["x"]), float(r["y"])) for r in pose]
    gx, gy = GT[house]
    angles = [float(r["wind_direction_rad"]) for r in wind]
    speeds = [float(r["wind_speed"]) for r in wind]
    # This is a trajectory-conditioned descriptive statistic, not a House regime.
    resultant = math.hypot(sum(map(math.cos, angles)), sum(map(math.sin, angles)))/len(angles)
    frozen = metrics(path / "source_estimate_trace.csv", house)
    windows = [auc_between(states, a, a+60) for a in (0, 60, 120, 180)]
    assert abs(sum(windows)-frozen["error_auc_m_s"]) < 1e-8
    return dict(house=house, arm=arm, manifest=manifest, terminal_guard_pass=True, metrics=frozen,
                ever_estimate_within_2m=any(r["error_m"] <= 2 for r in states),
                initial=states[0], final=states[-1],
                entropy_drop_nats=states[0]["entropy_nats"]-states[-1]["entropy_nats"],
                auc_60s_windows_m_s=windows, updates=updates,
                map_change_sequence=compressed_xy(states), goals=goals,
                repeated_goal_count=len(goal_xy)-len(set(goal_xy)),
                raw_recording_only=dict(
                    warning="Full stream including startup/teardown; NOT the aligned GSL 0-240 s window. Wind and hits are path-conditioned.",
                    pose_span_s=[float(pose[0]["t_sim_s"]), float(pose[-1]["t_sim_s"])],
                    path_length_m=sum(math.dist(a,b) for a,b in zip(xy,xy[1:])),
                    closest_physical_source_distance_m=min(math.hypot(x-gx,y-gy) for x,y in xy),
                    unique_rounded_0p3m_bins=len({(round(x/.3),round(y/.3)) for x,y in xy}),
                    measured_peak_ppm=max(float(r["measured_gas_ppm"]) for r in sensor),
                    measured_positive_fraction=sum(float(r["measured_gas_ppm"])>0 for r in sensor)/len(sensor),
                    wind_speed_mean=sum(speeds)/len(speeds), wind_direction_circular_variance=1-resultant))


def compare(left, right, root):
    lg, rg = left["goals"], right["goals"]
    different = next((i for i in range(min(len(lg), len(rg)))
                      if (lg[i]["x"],lg[i]["y"]) != (rg[i]["x"],rg[i]["y"])), None)
    if different is None and len(lg) != len(rg):
        different = min(len(lg),len(rg))
    cutoff = min(u["audit_t"] for r in (left,right) for u in r["updates"])
    ls = [state(r,left["house"]) for r in read_csv(root/f"{left['house']}_seed12_{left['arm']}/source_estimate_trace.csv")]
    rs = [state(r,right["house"]) for r in read_csv(root/f"{right['house']}_seed12_{right['arm']}/source_estimate_trace.csv")]
    divergence = None if different is None else dict(goal_index_1based=different+1,
        left=lg[different] if different<len(lg) else None,
        right=rg[different] if different<len(rg) else None)
    return dict(house=left["house"], contrast=f"{right['arm']}-{left['arm']}",
                goal_coordinates_differ=different is not None,
                map_sequence_ignoring_timestamps_and_repetitions_differs=left["map_change_sequence"] != right["map_change_sequence"],
                first_goal_divergence=divergence,
                earliest_cpir_update_s=cutoff,
                divergence_precedes_both_first_cpir_updates=bool(divergence and divergence["left"] and divergence["right"] and max(divergence["left"]["t"],divergence["right"]["t"])<cutoff),
                auc_delta_before_earliest_cpir_update_m_s=auc_between(rs,0,cutoff)-auc_between(ls,0,cutoff),
                auc_delta_after_earliest_cpir_update_m_s=auc_between(rs,cutoff,240)-auc_between(ls,cutoff,240))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-root", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    records = [summarize(args.run_root,h,a) for h in GT for a in ARMS]
    frozen = json.loads((args.run_root/"CTPI_G2_M12_SEED12_PERFORMANCE.json").read_text())
    for record in records:
        original = next(r for r in frozen["records"] if r["house"]==record["house"] and r["arm"]==record["arm"])
        for k,v in record["metrics"].items():
            assert abs(v-original[k])<1e-8, (record["house"],record["arm"],k)
    contrasts = []
    for h in GT:
        by_arm = {r["arm"]: r for r in records if r["house"]==h}
        contrasts.extend(compare(by_arm[a],by_arm[b],args.run_root) for a,b in (("A0","F00"),("F00","F01")))
    inputs = {str(p.relative_to(args.run_root)):hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(args.run_root.rglob("*.csv")) if "ros_log" not in p.parts}
    result = dict(status="POST_HOC_DESCRIPTIVE_NOT_CAUSAL_IDENTIFICATION", frozen_metrics_reproduced=True,
                  input_csv_sha256=inputs, records=records, contrasts=contrasts,
                  missing=["full posterior grid / true-source rank / near-truth mass", "actual ESS (CSV placeholder is zero)",
                           "candidate prediction residuals / plume field displacement", "native-vs-selected goal with trust flag per decision",
                           "validated common origin for raw simulator and GSL-relative timestamps"])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"metrics_reproduced":True,"records":len(records),"contrasts":contrasts},indent=2))


if __name__ == "__main__":
    main()
