#!/usr/bin/env python3
"""Minimal AVESM action/observation closed-loop emulator.

This intentionally runs outside ROS: the controller chooses the next pose from
the current AVESM map, then queries the real GADEN runtime snapshot at that
pose.  It is therefore a closed-loop physical-runtime smoke, not a claim that
AVESM is already wired into the ROS action server.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
import random
import subprocess
import sys
from pathlib import Path

BINS = (0.0, 0.8, 1.2, 2.0, 3.0, 5.0, 99.0)
COORDS = {"A": (-0.6, 1.95), "B": (-0.4, -2.9)}
BOUNDS = (-7.3, 0.9, -7.6, 3.2)
THRESHOLD = 0.001
KAPPA = 0.1


def load_rows(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def bin_id(d: float) -> int:
    for i in range(len(BINS) - 1):
        if BINS[i] <= d < BINS[i + 1]:
            return i
    return len(BINS) - 2


def dist(x: float, y: float, source):
    return math.hypot(x - source[0], y - source[1])


def fit(rows, source):
    counts = [[1.0, 1.0] for _ in range(len(BINS) - 1)]
    for row in rows:
        x, y = row["pose_xy"]
        b = bin_id(dist(float(x), float(y), source))
        hit = int(float(row["gas_ppm"]) > THRESHOLD)
        counts[b][hit] += 1.0
    return [[v / sum(pair) for v in pair] for pair in counts]


def load_sensor(path: Path, manifest: Path):
    spec = importlib.util.spec_from_file_location("avesm_sensor", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("SENSOR_IMPORT")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    cfg = json.loads(manifest.read_text(encoding="utf-8"))
    return mod.SensorModel(seed=int(cfg["sensor"]["seed"]), **cfg["sensor"]["config"])


def js_divergence(p: float, q: float) -> float:
    m = 0.5 * (p + q)
    out = 0.0
    for a, b in ((p, m), (1.0 - p, 1.0 - m), (q, m), (1.0 - q, 1.0 - m)):
        if a > 0.0 and b > 0.0:
            out += 0.5 * a * math.log(a / b)
    return out


def choose_action(x, y, weights, models):
    # A small action set keeps the controller auditable and bounded.
    # Do not let a zero-motion tie silently win the action selection.
    candidates = []
    for angle in range(0, 360, 45):
        a = math.radians(angle)
        candidates.append((x + 0.4 * math.cos(a), y + 0.4 * math.sin(a)))
    scored = []
    for ax, ay in candidates:
        ax = min(max(ax, BOUNDS[0]), BOUNDS[1])
        ay = min(max(ay, BOUNDS[2]), BOUNDS[3])
        pa = models["A"][bin_id(dist(ax, ay, COORDS["A"]))][1]
        pb = models["B"][bin_id(dist(ax, ay, COORDS["B"]))][1]
        scored.append((js_divergence(pa, pb), -math.hypot(ax - x, ay - y), ax, ay))
    _, _, ax, ay = max(scored)
    return ax, ay


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--train-a", type=Path, required=True)
    ap.add_argument("--train-b", type=Path, required=True)
    ap.add_argument("--env-root", type=Path, required=True)
    ap.add_argument("--gas-results", type=Path, required=True)
    ap.add_argument("--helper", type=Path, required=True)
    ap.add_argument("--sensor-module", type=Path, required=True)
    ap.add_argument("--sensor-manifest", type=Path, required=True)
    ap.add_argument("--source", choices=("A", "B"), required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--steps", type=int, default=300)
    args = ap.parse_args()

    models = {"A": fit(load_rows(args.train_a), COORDS["A"]), "B": fit(load_rows(args.train_b), COORDS["B"])}
    sensor = load_sensor(args.sensor_module, args.sensor_manifest)
    env = dict(os.environ)
    proc_env = ":".join([
        "/opt/ros/humble/lib",
        "/home/zyc/PF_DEI_FORWARD_CLOSURE_20260828/gaden_install/gaden_common/lib",
        "/home/zyc/PF_DEI_FORWARD_CLOSURE_20260828/gaden_install/lib",
        "/home/zyc/PF_DEI_V3_GADEN_BUILD_REF/install/lib",
        env.get("LD_LIBRARY_PATH", ""),
    ])
    env["LD_LIBRARY_PATH"] = proc_env
    query = subprocess.Popen([str(args.helper), str(args.env_root), str(args.gas_results)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, env=env)
    logs = {"A": 0.0, "B": 0.0}
    x, y = -0.9, 0.15
    trace = []
    stop_step = None
    try:
        for step in range(1, args.steps + 1):
            weights_raw = {s: math.exp(-logs[s]) for s in logs}
            z = sum(weights_raw.values())
            weights = {s: weights_raw[s] / z for s in logs}
            x, y = choose_action(x, y, weights, models)
            raw_iteration = 2 * step
            query.stdin.write(f"{raw_iteration} {x:.17g} {y:.17g} 0.3\n")
            query.stdin.flush()
            line = query.stdout.readline().strip()
            parts = line.split()
            if len(parts) != 6 or parts[0] != "OK":
                raise RuntimeError(f"RAW_QUERY:{line!r}")
            gas = float(parts[1])
            observed = sensor.process(gas, 0.2)
            hit = int(observed > THRESHOLD)
            p = {s: models[s][bin_id(dist(x, y, COORDS[s]))][hit] for s in logs}
            for s in logs:
                rival = "B" if s == "A" else "A"
                logs[s] += KAPPA * math.log(p[rival] / p[s])
            weights_raw = {s: math.exp(-logs[s]) for s in logs}
            z = sum(weights_raw.values())
            weights = {s: weights_raw[s] / z for s in logs}
            estimate = sum(weights[s] * COORDS[s][0] for s in weights), sum(weights[s] * COORDS[s][1] for s in weights)
            margin = abs(logs["A"] - logs["B"])
            if stop_step is None and max(weights.values()) >= 0.95 and margin >= math.log(20.0):
                stop_step = step
            trace.append({"step": step, "raw_iteration": raw_iteration, "x": x, "y": y, "gas_ppm": gas, "sensor_ppm": observed, "hit": hit, "log_e_A": logs["A"], "log_e_B": logs["B"], "weight_A": weights["A"], "weight_B": weights["B"], "estimate_x": estimate[0], "estimate_y": estimate[1], "estimate_error_m": math.hypot(estimate[0] - COORDS[args.source][0], estimate[1] - COORDS[args.source][1])})
    finally:
        if query.stdin:
            query.stdin.close()
        query.wait(timeout=10)
    final = trace[-1]
    result = {"contract": "AVESM_CLOSED_LOOP_EMULATOR_V1", "source": args.source, "steps": len(trace), "stop_step": stop_step, "final_error_m": final["estimate_error_m"], "min_error_m": min(x["estimate_error_m"] for x in trace), "path_length_m": sum(math.hypot(trace[i]["x"] - trace[i - 1]["x"], trace[i]["y"] - trace[i - 1]["y"]) for i in range(1, len(trace))), "final_weight_A": final["weight_A"], "final_weight_B": final["weight_B"], "final_log_e_A": final["log_e_A"], "final_log_e_B": final["log_e_B"], "source_blind_controller": True, "ros_action_server_integrated": False, "scope": "physical GADEN runtime closed-loop emulator; not formal ROS closed-loop performance"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (args.output.with_suffix(".jsonl")).write_text("\n".join(json.dumps(x) for x in trace) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
