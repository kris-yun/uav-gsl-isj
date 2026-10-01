"""Read-only P0 audit of exactly the four frozen R1 TNQC cases.

No candidate scoring, map fitting, truth ownership, or simulator execution.
Run on the VM against the authoritative archive; output only new audit files.
"""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import tarfile

CASES = [f"{house}_seed{seed}_off_off" for house in ("House01", "House02") for seed in (0, 1)]
SOURCE_FILES = [
    "ros2_package/src/gsl_server/algorithms/Common/States/StopAndMeasureState.cpp",
    "ros2_package/src/gsl_server/algorithms/Common/States/StopAndMeasureState.hpp",
    "ros2_package/src/gsl_server/algorithms/Common/Algorithm.cpp",
    "ros2_package/src/gsl_server/algorithms/PMFS/PMFS.cpp",
    "ros2_package/src/gsl_server/algorithms/PMFS/PMFSLib.cpp",
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def audit(archive, extracted, output):
    output.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256()
    with archive.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(block)
    sidecar = json.loads(Path(str(archive) + ".sha256.json").read_text())
    report = {
        "archive_path": str(archive), "archive_bytes": archive.stat().st_size,
        "archive_sha256": h.hexdigest(), "sidecar_sha256": sidecar["sha256"],
        "archive_sidecar_match": h.hexdigest() == sidecar["sha256"] and archive.stat().st_size == sidecar["bytes"],
        "cases": {}, "scope": CASES,
        "execution": {"gaden": 0, "forward": 0, "training": 0, "h03_content": 0, "closed_loop": 0, "candidate_scoring": 0},
    }
    inventory, verified = [], []
    with tarfile.open(archive) as tar:
        members = {m.name: m for m in tar.getmembers() if m.isfile()}
        manifest_name = next(n for n in members if n.endswith("/SHA256SUMS.json"))
        prefix = manifest_name[:-len("SHA256SUMS.json")]
        manifest = json.loads(tar.extractfile(members[manifest_name]).read())
        report["manifest_sha256"] = sha(tar.extractfile(members[manifest_name]).read())

        def read_verified(relative, retain=True):
            data = tar.extractfile(members[prefix + relative]).read()
            archived_sha = sha(data)
            local = extracted / relative
            extracted_sha = sha(local.read_bytes()) if local.is_file() else None
            expected = manifest.get(relative)
            verified.append([relative, len(data), expected, archived_sha, extracted_sha,
                             expected == archived_sha, extracted_sha == archived_sha])
            if retain:
                target = output / "retained_inputs" / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            return data

        for case in CASES:
            root = "native/" + case + "/"
            relative_names = sorted(n[len(prefix):] for n in members if n.startswith(prefix + root))
            inventory.extend([case, n, members[prefix + n].size] for n in relative_names)
            event_like = [n for n in relative_names if re.search(r"event|measurement[_-](trace|samples)|continuous_measurement", Path(n).name, re.I)]
            runtime = json.loads(read_verified(root + "runtime_manifest.json"))
            # Do not load source ownership or result/posterior tables.
            parameters = {}
            for name in relative_names:
                if "/resolved_runtime/launch_params_" in name:
                    text = read_verified(name).decode()
                    if "pfdi_mode:" in text:
                        for key in ["pfdi_mode", "tadm_enabled", "measurement_trace_file", "continuous_measurement_samples_file",
                                    "measurement_block_samples", "measurement_settle_samples", "measurement_deduplicate_sim_timestamps",
                                    "kernelSigma", "kernelStretchConstant", "confidenceSigmaSpatial", "confidenceMeasurementWeight"]:
                            match = re.search(r"^\s*" + key + r":\s*(.*)$", text, re.M)
                            parameters[key] = match.group(1).strip() if match else None
            timing = list(csv.DictReader(io.StringIO(read_verified(root + "context_bank/source_update_timing.csv").decode())))
            updates = []
            map_fields = None
            for row in timing:
                update_id = int(row["source_update_id"])
                name = root + f"context_bank/source_update_{update_id:04d}/measured_hit_probability.csv"
                text = read_verified(name).decode()
                reader = csv.DictReader(io.StringIO(text))
                map_fields = reader.fieldnames
                map_rows = list(reader)
                updates.append({"id": update_id, "sim_time": float(row["sim_time"]), "wall_start_epoch": float(row["wall_start_epoch"]),
                                "map_sha256": sha(text.encode()), "map_rows": len(map_rows)})
            trace_info = {}
            for basename in ["sensor_trace.csv", "wind_trace.csv", "sim_pose_trace.csv"]:
                text = read_verified(root + basename).decode()
                rows = list(csv.DictReader(io.StringIO(text)))
                trace_info[basename] = {"rows": len(rows), "columns": list(rows[0]), "first_row": rows[0], "last_time": rows[-1]["t_sim_s"]}
            logname = next(n for n in relative_names if "/ros_log/gsl_actionserver_node_" in n and n.endswith(".log"))
            logtext = read_verified(logname).decode()
            averages = []
            for line in logtext.splitlines():
                m = re.search(r"\[([0-9]+\.[0-9]+)\].*avg_gas=([^;]+);\s*avg_windSpeed=([^;]+);\s*avg_wind_dir=([^\s\x1b]+)", line)
                if m:
                    averages.append({"wall_epoch": m[1], "gas_display": m[2], "wind_speed_display": m[3], "wind_direction_display": m[4]})
            last, previous = updates[-1], updates[-2]
            before = [r for r in averages if float(r["wall_epoch"]) < last["wall_start_epoch"]]
            report["cases"][case] = {
                "run_id": runtime["run_id"], "algorithm_sha256": runtime["algorithm_sha256"],
                "runtime_pfdi_mode": runtime["pfdi_mode"], "parameters": parameters,
                "event_like_members": event_like, "source_updates": updates,
                "terminal_map_fields": map_fields, "traces": trace_info,
                "gsl_log": logname, "logged_average_records": len(averages),
                "logged_average_records_before_terminal_update": len(before),
                "first_three_average_displays": averages[:3],
                "terminal_time": last["sim_time"], "previous_update_time": previous["sim_time"],
                "O40_requested_bounds": [last["sim_time"] - 40, last["sim_time"]],
                "Oupdate_requested_bounds": [previous["sim_time"], last["sim_time"]],
                "Oupdate_duration": last["sim_time"] - previous["sim_time"],
                "exact_event_inputs_recovered": False,
                "reason": "No completed-block event export; log averages use two significant digits; trace lacks callback/block ownership and full-precision transformed wind aggregates.",
            }
        source_tar = read_verified("freeze/exact_b24_source.tar.gz", retain=False)
        with tarfile.open(fileobj=io.BytesIO(source_tar)) as inner:
            report["frozen_source_sha256"] = {}
            for name in SOURCE_FILES:
                data = inner.extractfile(name).read()
                report["frozen_source_sha256"][name] = sha(data)
                target = output / "retained_inputs/frozen_code" / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
        report["all_selected_manifest_hashes_match"] = all(r[5] for r in verified)
        report["all_selected_extracted_bytes_match"] = all(r[6] for r in verified)
        report["verified_artifact_count"] = len(verified)
    for name, header, rows in [
        ("P0_ARCHIVE_INVENTORY.tsv", ["case", "archive_relative_path", "bytes"], inventory),
        ("P0_VERIFIED_INPUTS.tsv", ["path", "bytes", "manifest_sha256", "archive_sha256", "extracted_sha256", "manifest_match", "extracted_match"], verified),
    ]:
        with (output / name).open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter="\t", lineterminator="\n")
            writer.writerow(header); writer.writerows(rows)
    write_json(output / "P0_ARCHIVE_AUDIT.json", report)
    print(json.dumps({"archive_match": report["archive_sidecar_match"], "manifest_match": report["all_selected_manifest_hashes_match"],
                      "extracted_match": report["all_selected_extracted_bytes_match"], "verified": len(verified),
                      "cases": {c: {k: v for k, v in r.items() if k in ["event_like_members", "parameters", "logged_average_records_before_terminal_update", "terminal_time", "Oupdate_duration"]} for c, r in report["cases"].items()}}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--extracted", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    audit(args.archive, args.extracted, args.output)
