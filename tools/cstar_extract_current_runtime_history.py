"""Extract a fixed-route measured history from a current GADEN runtime case.

This is a truth-blind runtime adapter: the helper is queried only at the
frozen route points and the evaluator-only gas value is immediately passed
through the frozen sensor law.  Source coordinates never enter the output.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
from pathlib import Path
import subprocess
import sys


def load_sensor(path: Path):
    spec = importlib.util.spec_from_file_location("cstar_sensor", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("CSTAR_SENSOR_IMPORT")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod.SensorModel


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--env-root", type=Path, required=True)
    ap.add_argument("--gas-results", type=Path, required=True)
    ap.add_argument("--route", type=Path, required=True)
    ap.add_argument("--helper", type=Path, required=True)
    ap.add_argument("--sensor-module", type=Path, required=True)
    ap.add_argument("--sensor-manifest", type=Path, required=True)
    ap.add_argument("--raw-dt", type=float, default=0.1,
                    help="Current-runtime raw snapshot interval in seconds")
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--candidate-forward-output", type=Path,
                    help="isolated evaluator/development export of the candidate simulator input before sensor dynamics")
    args = ap.parse_args()

    rows = list(csv.DictReader(args.route.open(encoding="utf-8", newline="")))
    if not rows or rows[0].get("t_sim_s") != "0.0":
        raise RuntimeError("CSTAR_ROUTE_MUST_START_AT_ZERO")
    times = [float(r["t_sim_s"]) for r in rows]
    if any(abs(t - i * 0.2) > 1e-8 for i, t in enumerate(times)):
        raise RuntimeError("CSTAR_ROUTE_CADENCE")
    if args.raw_dt <= 0:
        raise RuntimeError("CSTAR_RAW_DT")

    manifest = json.loads(args.sensor_manifest.read_text(encoding="utf-8"))
    sensor = load_sensor(args.sensor_module)(seed=int(manifest["sensor"]["seed"]),
                                             **manifest["sensor"]["config"])
    proc = subprocess.Popen(
        [str(args.helper), str(args.env_root), str(args.gas_results)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, bufsize=1,
    )
    measured = []
    candidate_forward = []
    try:
        for step, row in enumerate(rows[1:], start=1):
            # The runtime saves at raw_dt; the frozen route is sampled every 0.2 s.
            raw_iteration = int(round(float(row["t_sim_s"]) / args.raw_dt))
            if abs(raw_iteration * args.raw_dt - float(row["t_sim_s"])) > 1e-7:
                raise RuntimeError("CSTAR_ROUTE_NOT_ON_RAW_GRID")
            proc.stdin.write(f"{raw_iteration} {float(row['x']):.17g} {float(row['y']):.17g} {float(row['z']):.17g}\n")
            proc.stdin.flush()
            line = proc.stdout.readline()
            parts = line.split()
            if len(parts) != 6 or parts[0] != "OK":
                raise RuntimeError(f"CSTAR_RAW_QUERY:{line!r}")
            gas, u, v, w = map(float, parts[1:5])
            measured.append({
                "t_sim_s": round(step * 0.2, 9),
                "stamp_ns": step * 200000000,
                "step": step,
                "raw_iteration": raw_iteration,
                "pose_xy": [float(row["x"]), float(row["y"])],
                "wind_uv": [u, v],
                "wind_w": w,
                "gas_ppm": sensor.process(gas, 0.2),
            })
            # This is not appended to the controller-visible history.  It is
            # the physical forward input generated under the declared source
            # hypothesis and is only meaningful as an offline candidate trace
            # or a future auditable forward-provider cache.
            candidate_forward.append({
                "t_sim_s": round(step * 0.2, 9),
                "stamp_ns": step * 200000000,
                "step": step,
                "pose_xy": [float(row["x"]), float(row["y"])],
                "candidate_forward_input_ppm": gas,
            })
    finally:
        if proc.stdin:
            proc.stdin.close()
        proc.wait(timeout=10)
        stderr = proc.stderr.read() if proc.stderr else ""
    if proc.returncode != 0:
        raise RuntimeError(f"CSTAR_RAW_QUERY_EXIT:{proc.returncode}:{stderr[-500:]}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as f:
        for row in measured:
            f.write(json.dumps(row, sort_keys=True) + "\n")
    if args.candidate_forward_output is not None:
        args.candidate_forward_output.parent.mkdir(parents=True, exist_ok=True)
        with args.candidate_forward_output.open("w", encoding="utf-8", newline="\n") as f:
            for row in candidate_forward:
                f.write(json.dumps(row, sort_keys=True) + "\n")
    print(json.dumps({"contract": "CSTAR_CURRENT_RUNTIME_HISTORY_V1",
                      "frames": len(measured), "output": str(args.output),
                      "truth_blind_output": True,
                      "candidate_forward_output": str(args.candidate_forward_output) if args.candidate_forward_output else None}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
