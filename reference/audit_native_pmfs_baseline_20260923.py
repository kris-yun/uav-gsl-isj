#!/usr/bin/env python3
"""Reproduce the source and parameter audit without modifying the reference ZIP."""

import argparse
import csv
import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path


PREFIX = "GasSourceLocalization-humble/"
OFFICIAL_LAUNCH = "Environment_config/PMFS/launch/main_simbot_launch.py"
OFFICIAL_CMAKE = "gsl_server/CMakeLists.txt"
PMFS_PREFIX = "gsl_server/src/gsl_server/algorithms/PMFS/"

ALGORITHM = set("""useWindGroundTruth stepsSourceUpdate maxRegionSize sourceDiscriminationPower refineFraction
deltaTime noiseSTDev iterationsToRecord maxWarmupIterations minWarmupIterations blurSigmaX blurSigmaY
hitPriorProbability maxUpdatesPerStop kernelSigma kernelStretchConstant confidenceMeasurementWeight
confidenceSigmaSpatial localEstimationWindowSize openMoveSetExpasion explorationProbability
initialExplorationMoves distanceWeight infoTaxis
use_infotaxis allowMovementRepetition""".split())
ADAPTER = set("""vgr_data_path config_id algorithm method flight_height start_x start_y source_x source_y
source_z environment_id scenario_id dataset source_config wind_config start_config gas_backend
raw_query_executable raw_env_root raw_gas_results repo_root gmrf_update_on_new_observation_only
gaden_iteration_mode realtime_factor sim_stop_at_s nav_command_quantum_s robot_location_topic
anemometer_frame markers_height use_sim_time useDiffusionTerm stdevHit stdevMiss step
scenario simulation robot_name map_topic sensor_topic cell_size exec_freq worldFile speed
use_map_ref_system fixed_frame sensor_frame scale""".split())
MEASUREMENT = set("""sensor_config sensor_model_mode measurement_settle_samples
measurement_block_samples measurement_deduplicate_sim_timestamps th_gas_present
th_wind_present stop_and_measure_time sensor_model noise_std""".split())
BUDGET = set("""timeout_sec path_budget_m maxSearchTime distanceThreshold maxSearchDistance
seed random_seed maxUpdatesPerStopBudget convergence_thr ground_truth_x ground_truth_y""".split())


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(*args: str, cwd: Path) -> str:
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


def launch_defaults(text: str) -> dict[str, str]:
    return dict(re.findall(r"DeclareLaunchArgument\(['\"]([^'\"]+)['\"],\s*default_value=([^,\n\)]+)", text))


def official_params(text: str) -> tuple[dict[str, str], dict[str, str]]:
    # Limit extraction to the GSL node: other nodes have their own parameter dictionaries.
    block = text.split("# Common", 1)[1].split("on_exit=Shutdown()", 1)[0]
    values = dict(re.findall(r"\{['\"]([^'\"]+)['\"]:\s*([^\n}]+)\}", block))
    setup = dict(re.findall(r'SetLaunchConfiguration\(\s*name="([^"]+)",\s*value="([^"]+)"', text))
    arguments = launch_defaults(text)
    resolved = {}
    for key, value in values.items():
        value = value.rstrip(", ")
        m = re.search(r"\$\(var ([^)]+)\)", value)
        if m and m.group(1) in setup:
            resolved[key] = setup[m.group(1)]
        elif m and m.group(1) in arguments:
            resolved[key] = arguments[m.group(1)].strip("[]'\" ")
        elif m:
            resolved[key] = "<launch var " + m.group(1) + ">"
        else:
            resolved[key] = value
    # This launch configuration is never put in the GSL Node parameter map.
    resolved["minWarmupIterations"] = "200"
    resolved["localEstimationWindowSize"] = "2"
    return resolved, setup


def runner_args(text: str) -> dict[str, str]:
    return dict(re.findall(r'"([A-Za-z][A-Za-z0-9_]*):=([^"\n]*)"', text))


def normalize(value: str) -> str:
    value = value.strip().strip("'").strip('"')
    default = re.fullmatch(r"\$\{[A-Za-z_][A-Za-z0-9_]*:-(.*)\}", value)
    if default:
        value = default.group(1)
    return {"True": "true", "False": "false", "0.0": "0", "1.0": "1"}.get(value, value)


def category(key: str) -> str:
    if key in ALGORITHM:
        return "official PMFS algorithm/forward parameter"
    if key in MEASUREMENT:
        return "measurement/sensor protocol"
    if key in BUDGET:
        return "budget/evaluation protocol"
    if key in ADAPTER:
        return "VGR environment adapter"
    return "research instrumentation only"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--runner", type=Path, required=True)
    parser.add_argument("--r2-launch", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    archive_sha = sha256(args.archive.read_bytes())
    archive_files = {}
    with zipfile.ZipFile(args.archive) as archive:
        names = archive.namelist()
        for name in names:
            if not name.startswith(PREFIX) or name.endswith("/"):
                continue
            relative = name[len(PREFIX):]
            if relative.startswith(PMFS_PREFIX) or relative.startswith("Environment_config/PMFS/launch/") or relative == OFFICIAL_CMAKE:
                archive_files[relative] = archive.read(name)
    upstream_commit = git("rev-parse", "HEAD", cwd=args.upstream)
    upstream_branch = git("branch", "--show-current", cwd=args.upstream)
    fingerprint_rows = []
    for relative, content in sorted(archive_files.items()):
        # Compare committed blobs. Windows checkout can apply core.autocrlf to files.
        try:
            upstream_content = subprocess.check_output(["git", "show", "HEAD:" + relative], cwd=args.upstream)
        except subprocess.CalledProcessError:
            upstream_content = None
        fingerprint_rows.append({"relative_path": relative, "archive_sha256": sha256(content),
                                 "upstream_sha256": sha256(upstream_content) if upstream_content is not None else "MISSING",
                                 "byte_identical": upstream_content == content})
    with (args.output / "OFFICIAL_PACKAGE_FILE_FINGERPRINTS_20260923.tsv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(fingerprint_rows[0]), delimiter="\t")
        writer.writeheader(); writer.writerows(fingerprint_rows)
    official_text = archive_files[OFFICIAL_LAUNCH].decode()
    official, setup = official_params(official_text)
    r2_runner_text = args.runner.read_text(encoding="utf-8")
    r2_launch_text = args.r2_launch.read_text(encoding="utf-8")
    r2_explicit = runner_args(r2_runner_text)
    r2_defaults = launch_defaults(r2_launch_text)
    # Official launch uses these aliases while R2 passes the direct node parameter.
    aliases = {"maxSearchTime": "timeout_sec", "ground_truth_x": "source_x", "ground_truth_y": "source_y",
               "th_gas_present": "th_gas_present", "th_wind_present": "th_wind_present"}
    rows = []
    for key in sorted(set(official) | set(r2_explicit) | set(r2_defaults)):
        r2_key = aliases.get(key, key)
        r2_value = r2_explicit.get(r2_key, r2_defaults.get(r2_key, "<not declared>"))
        official_value = official.get(key, "<not set in official GSL node>")
        note = ""
        if key == "minWarmupIterations":
            note = "Official SetLaunchConfiguration says 0 but is not passed to GSL; PMFSLib default is 200."
        if "${" in r2_value:
            note += " Runner expression; effective value depends on environment/default."
        rows.append({"parameter": key, "category": category(key), "official_effective_or_declared": normalize(official_value),
                     "r2_runner_or_launch_default": normalize(r2_value), "r2_source": "runner" if r2_key in r2_explicit else "launch default" if r2_key in r2_defaults else "not declared",
                     "note": note.strip()})
    with (args.output / "OFFICIAL_VS_R2_PARAMETER_DIFF_20260923.tsv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader(); writer.writerows(rows)
    provenance = {
        "archive_path": str(args.archive), "archive_sha256": archive_sha,
        "archive_top_level": sorted({name.split("/")[0] for name in names if name}),
        "archive_embedded_git_metadata": any("/.git/" in name for name in names),
        "upstream_repository": git("remote", "get-url", "origin", cwd=args.upstream),
        "upstream_branch": upstream_branch, "upstream_commit": upstream_commit,
        "official_launch_git_blob": subprocess.check_output(["git", "hash-object", "--stdin"], input=archive_files[OFFICIAL_LAUNCH], cwd=args.upstream).decode().strip(),
        "upstream_launch_git_blob": git("rev-parse", "HEAD:" + OFFICIAL_LAUNCH, cwd=args.upstream),
        "official_cmake_use_gaden_default": "OFF" if "set(USE_GADEN OFF)" in archive_files[OFFICIAL_CMAKE].decode() else "REVIEW",
        "compared_files": len(fingerprint_rows),
        "identical_files": sum(row["byte_identical"] for row in fingerprint_rows),
        "r2_runner_path": str(args.runner), "r2_runner_sha256": sha256(args.runner.read_bytes()),
        "r2_launch_path": str(args.r2_launch), "r2_launch_sha256": sha256(args.r2_launch.read_bytes()),
        "r2_launch_matches_recorded_h01_manifest": sha256(args.r2_launch.read_bytes()) == "0cd1ae4ad852bf548fd1ebc131e7f46f0d6d20603a2e4e71ae37c6831e40f2c9",
        "r2_runner_argument_count": len(r2_explicit), "official_gsl_parameter_count": len(official),
        "diff_rows": len(rows),
    }
    (args.output / "OFFICIAL_PACKAGE_PROVENANCE_20260923.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(provenance, indent=2))


if __name__ == "__main__":
    main()
