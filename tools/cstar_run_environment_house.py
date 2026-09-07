"""Bounded real VGR hover input probe; no scientific model, no GMRF, no campaign."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.ctpi_cstar.environment_runtime import load_runtime_preflight, verify_qualified_helper, require


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--house", choices=("H01", "H02", "H03"), required=True)
    p.add_argument("--geometry-manifest", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--environment-preflight", type=Path, required=True,
                   help="Current reusable preflight bound to these launch inputs")
    p.add_argument("--raw-query-executable", type=Path, required=True,
                   help="Explicit live-qualified numeric helper; no historical H01 fallback")
    args = p.parse_args()
    # Fail before making output directories or launching any process. Keep old
    # commits available for historical reproduction, never as a silent default.
    attestation = ROOT / "evidence/cstar_controlled_assets_20260907_r2/WIND_INDEX_CORRECTION_AUDIT.json"
    verify_qualified_helper(args.raw_query_executable, ROOT / "tools/cstar_numeric_wind_raw_query.cpp",
                            json.loads(attestation.read_text()))
    h = args.house
    geometry = json.loads(args.geometry_manifest.read_text())[h]
    config, start = {"H01": ("2,4-1_fast", (-3.17, -1.75)),
                     "H02": ("3,5-1_fast", (-0.5, -2.5)),
                     "H03": ("1-2,5_fast", (2.0, 0.0))}[h]
    scenario = Path("/mnt/hgfs/workspace/GADEN_files/scenarios") / ("House0"+h[-1])
    realizations = sorted((scenario / "gas_simulations" / config).glob("FilamentSimulation*"))
    if len(realizations) != 1:
        raise RuntimeError(f"AMBIGUOUS_REALIZATION:{realizations}")
    realization = realizations[0]
    preflight = load_runtime_preflight(args.environment_preflight, args.raw_query_executable,
                                       args.geometry_manifest, h, realization)
    clock = preflight["clock_sensor"]["clock"]
    require(clock["seed"] == 12 and clock["sensor_dt_s"] == 0.2, "HOVER_PROFILE_CLOCK")
    args.out.mkdir(parents=True, exist_ok=False)
    env = {**os.environ, "ROS_DOMAIN_ID": str(201+int(h[-1])), "ROS_LOCALHOST_ONLY": "1"}
    procs, handles, commands = [], [], []

    def launch(name, cmd):
        logfile = (args.out / (name+".log")).open("x")
        handles.append(logfile)
        commands.append({"name": name, "argv": cmd})
        proc = subprocess.Popen(cmd, env=env, stdout=logfile, stderr=subprocess.STDOUT,
                                start_new_session=True)
        procs.append(proc)
        return proc

    archive_commit = os.environ.get("CSTAR_RUNTIME_ARCHIVE_COMMIT")
    if archive_commit:
        require(bool(re.fullmatch(r"[0-9a-f]{40}", archive_commit)), "ARCHIVE_COMMIT_FORMAT")
    code_commit = archive_commit or subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    status = {"house": h, "pass": False, "scope": "real VGR stationary endpoint dwell, seed12, eight positive 0.2s frames",
              "git_sha": code_commit, "source_is_git_archive": bool(archive_commit),
              "scenario": str(scenario), "realization": str(realization),
              "ros_domain_id": env["ROS_DOMAIN_ID"], "scientific_models_loaded": False,
              "gmrf_loaded": False, "commands": commands}
    try:
        if h != "H01":
            player = Path("/home/zyc/PF_DEI_FORWARD_CLOSURE_20260828/gaden_install/gaden_player/lib/gaden_player/player")
            status["player_sha256"] = hashlib.sha256(player.read_bytes()).hexdigest()
            launch("player", [str(player), "--ros-args", "-r", "__node:=gaden_player",
                "-p", "num_simulators:=1", "-p", f"simulation_data_0:={realization}",
                "-p", f"occupancyFile:={scenario / 'OccupancyGrid3D.csv'}", "-p", "initial_iteration:=0",
                "-p", "player_freq:=1.0", "-p", "manual_iteration_mode:=true"])
        bridge = [sys.executable, "-m", "vgr_bridge.vgr_sim_node", "--ros-args"]
        params = {"vgr_data_path": scenario, "config_id": config, "start_x": float(start[0]),
            "start_y": float(start[1]), "flight_height": 0.3, "seed": 12,
            "sensor_model_mode": "dynamic", "gaden_iteration_mode": "seeded_time_replay",
            "sim_dt_s": 0.2, "sim_stop_at_s": 1.6, "realtime_factor": 1.0,
            "gas_backend": "raw_house1_snapshot" if h == "H01" else "gaden_player",
            "raw_query_executable": args.raw_query_executable.resolve(),
            "raw_gas_results": realization, "sensor_manifest_file": args.out / "sensor_manifest.json",
            "wind_trace_file": args.out / "bridge_wind.csv", "pose_trace_file": args.out / "bridge_pose.csv"}
        for key, value in params.items():
            bridge.extend(["-p", f"{key}:={value}"])
        launch("bridge", bridge)
        probe = launch("probe", [sys.executable, str(ROOT / "closed_loop/ctpi/cstar_environment_runtime_probe.py"),
            "--house", h, "--geometry-identity", geometry["geometry_identity"],
            "--git-sha", status["git_sha"], "--map-yaml", geometry["map_yaml_path"],
            "--map-image", geometry["map_image_path"], "--output", str(args.out / "runtime_audit.json"),
            "--wind-position-csv", str(args.out / "wind_observation_positions.csv"),
            "--frame-jsonl", str(args.out / "aligned_input_frames.jsonl"),
            "--required-aligned-frames", "8", "--wall-timeout-s", "40", "--start-simulation"])
        status["probe_exit_code"] = probe.wait(timeout=50)
        status["pass"] = status["probe_exit_code"] == 0
        if status["pass"]:
            actual_sensor = json.loads((args.out / "sensor_manifest.json").read_text())["sensor"]
            require(actual_sensor == preflight["clock_sensor"]["resolved_sensor"], "LIVE_SENSOR_PARAMETER_DRIFT")
            status["environment_preflight_sha256"] = hashlib.sha256(args.environment_preflight.read_bytes()).hexdigest()
    except Exception as exc:
        status["pass"] = False
        status["error"] = str(exc)
    finally:
        # Only process groups created by this invocation; no broad pgrep/pkill.
        for proc in reversed(procs):
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        for proc in procs:
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait(timeout=3)
        for f in handles:
            f.close()
        (args.out / "run_status.json").write_text(json.dumps(status, indent=2)+"\n")
    print(json.dumps(status, indent=2))
    return 0 if status["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
