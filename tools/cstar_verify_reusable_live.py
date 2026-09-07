"""Independent real ROS-frame to numeric raw-file wind check after input probes."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.ctpi_cstar.environment_runtime import NumericWindReader, require, sha256, verify_bindings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", type=Path, required=True)
    parser.add_argument("--live", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    require(not args.out.exists(), "OUTPUT_ALREADY_EXISTS")
    report = json.loads(args.preflight.read_text())
    require(report["pass"] is True, "PREFLIGHT_NOT_PASS")
    verify_bindings(report["bindings"])
    geometry = json.loads(Path(report["inputs"]["geometry"]).read_text())
    clock = report["clock_sensor"]["clock"]
    result = {"scope": "real stationary ROS frames vs numeric physical wind files; not navigation or model utility",
              "preflight_sha256": sha256(args.preflight), "verifier_sha256": sha256(Path(__file__)),
              "source_code_commit": "a16ffa346a0d643c73c21591d4694f4e4413a106",
              "maps": {}, "pass": False}
    for house in report["maps"]:
        target = args.live / house
        status = json.loads((target / "run_status.json").read_text())
        require(status["pass"] is True and not status["scientific_models_loaded"] and not status["gmrf_loaded"],
                "LIVE_STATUS")
        require(status["environment_preflight_sha256"] == sha256(args.preflight), "LIVE_PREFLIGHT_BINDING")
        require(status["git_sha"] == result["source_code_commit"], "LIVE_CODE_IDENTITY")
        entry = next(r for r in report["entries"] if r["realization_path"] == status["realization"])
        reader = NumericWindReader(status["realization"], geometry[house]["occupancy_path"])
        frames = [json.loads(line) for line in (target / "aligned_input_frames.jsonl").read_text().splitlines()]
        sensor = json.loads((target / "sensor_manifest.json").read_text())
        require(sensor["sensor"] == report["clock_sensor"]["resolved_sensor"], "LIVE_RESOLVED_SENSOR")
        positive = [r for r in frames if r["stamp_ns"] > 0]
        require(len(positive) == 8, "LIVE_FRAME_COUNT")
        max_error = 0.0
        for step, frame in enumerate(positive, 1):
            require(frame["stamp_ns"] == round(step * clock["sensor_dt_s"] * 1e9), "LIVE_DUAL_CLOCK")
            maximum_iteration = entry["iterations"] - 1
            usable = max(1, maximum_iteration - 1)
            iteration = ((7919 * (clock["seed"] + 1)) % usable + step) % usable
            vector, _ = reader.expected(iteration, [*frame["pose_xy"], geometry[house]["navigation_height_m"]])
            max_error = max(max_error, *(abs(float(v) - w) for v, w in zip(vector[:2], frame["wind_uv"])))
        require(max_error < 1e-6, "LIVE_PHYSICAL_WIND")
        result["maps"][house] = {"frames": len(positive), "max_abs_numeric_wind_error": max_error,
                                 "frames_sha256": sha256(target / "aligned_input_frames.jsonl"),
                                 "run_status_sha256": sha256(target / "run_status.json"), "pass": True}
    result["stored_controlled_frames"] = sum(r["raw_wind_reverification"]["frames"] for r in report["entries"])
    result["stored_max_abs_numeric_wind_error"] = max(r["raw_wind_reverification"]["max_abs_wind_error"] for r in report["entries"])
    result["pass"] = True
    with args.out.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
