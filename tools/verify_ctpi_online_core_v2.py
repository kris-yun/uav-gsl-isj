#!/usr/bin/env python3
"""Check compiled C++ FOPDT against source and spent R4 traces (evaluation only)."""
import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import numpy as np


def cpp_sensor(executable, steps):
    result = subprocess.run([str(executable), "sensor"],
                            input="".join(f"{dt:.17g} {value:.17g}\n" for dt, value in steps),
                            text=True, capture_output=True, check=True)
    values = np.asarray([float(x) for x in result.stdout.splitlines()])
    assert len(values) == len(steps)
    return values


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--executable", required=True, type=Path)
    ap.add_argument("--sensor-source", required=True, type=Path)
    ap.add_argument("--spent-r4-root", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    native = subprocess.run([str(args.executable)], capture_output=True, text=True, check=True)
    assert "CTPI_ONLINE_CORE_V2_SELFTEST=PASS" in native.stdout
    spec = importlib.util.spec_from_file_location("ctpi_sensor_reference", args.sensor_source)
    reference = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = reference
    spec.loader.exec_module(reference)
    rng = np.random.default_rng(20260905)
    streams = {
        "zero": [(.2, 0.)]*30,
        "step_and_recovery": [(.2, 0.)]*5 + [(.2, 1.)]*30 + [(.2, 0.)]*40,
        "variable_dt": list(zip(rng.uniform(.04, .35, 500), rng.uniform(0, 5, 500))),
    }
    parity = {}
    for name, steps in streams.items():
        sensor = reference.SensorModel("fopdt")
        expected = np.asarray([sensor.process(value, dt) for dt, value in steps])
        error = float(np.max(np.abs(cpp_sensor(args.executable, steps)-expected)))
        assert error < 1e-12, (name,error)
        parity[name] = error
    records = []
    for house in ("H01", "H02", "H03"):
        for arm in ("A0", "F00", "F01"):
            path = args.spent_r4_root / f"{house}_seed12_{arm}" / "sensor_trace.csv"
            with path.open(newline="") as f:
                rows = list(csv.DictReader(f))
            stamps = np.asarray([float(r["t_sim_s"]) for r in rows])
            assert abs(stamps[0]-.2)<1e-8 and np.max(np.abs(np.diff(stamps)-.2))<1e-8
            # Ground-truth gas enters THIS OFFLINE EVALUATOR ONLY, never the core's source estimator.
            steps = [(.2,float(r["true_gas_ppm"])) for r in rows]
            predicted = cpp_sensor(args.executable, steps)
            measured = np.asarray([float(r["measured_gas_ppm"]) for r in rows])
            error = float(np.max(np.abs(predicted-measured)))
            # Both columns are rounded to 6 decimals. A stable gain-one filter
            # adds at most .5e-6 input error to .5e-6 output rounding error.
            assert error <= 1.00001e-6, (house,arm,error)
            records.append(dict(house=house,arm=arm,samples=len(rows),max_abs_ppm=error,
                                input_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    report = dict(status="LOCAL_CORE_PASS_RUNTIME_NOT_CONNECTED", cpp_selftest=native.stdout.strip(),
                  synthetic_sensor_parity_max_abs=parity, spent_r4_sensor_replay=records,
                  sensor_reference_sha256=hashlib.sha256(args.sensor_source.read_bytes()).hexdigest(),
                  executable_sha256=hashlib.sha256(args.executable.read_bytes()).hexdigest(),
                  boundaries=["No ROS build or closed-loop run", "No source posterior efficacy claim",
                              "Legacy field PASS does not transfer to this new no-flux solver",
                              "Sensor parity is to local source plus recorded streams, not a claim of VM source identity"])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))


if __name__ == "__main__":
    main()
