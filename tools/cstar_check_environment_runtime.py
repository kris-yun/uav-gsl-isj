"""Reusable read-only preflight. Checks input identities, not scientific utility.

No gas body decoding, no simulator launch, no seed/route selection. Paths and
scope are explicit inputs. Every invocation rehashes assets; no permanent PASS.
"""
import argparse
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.ctpi_cstar import environment_runtime as runtime
from experiments.ctpi_cstar import validate_environment_alignment_v2 as maps


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--split", type=Path, required=True)
    p.add_argument("--geometry", type=Path, required=True)
    p.add_argument("--sensor-manifest", type=Path, required=True)
    p.add_argument("--clock", type=Path, required=True)
    p.add_argument("--helper", type=Path, required=True)
    p.add_argument("--helper-attestation", type=Path, required=True)
    p.add_argument("--controlled-data", type=Path,
                   help="Optionally reverify existing evaluator raw frames against numeric wind files; never re-extract gas")
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    runtime.require(not args.out.exists(), "OUTPUT_ALREADY_EXISTS")
    bindings = {}

    def bind(path, expected=None):
        path = Path(path).resolve()
        digest = runtime.sha256(path)
        runtime.require(expected is None or digest == expected, "INPUT_HASH:" + str(path))
        bindings[str(path)] = {"path": str(path), "sha256": digest}
        return digest

    for path in (args.split, args.geometry, args.sensor_manifest, args.clock,
                 args.helper, args.helper_attestation, Path(__file__), Path(runtime.__file__), Path(maps.__file__)):
        bind(path)
    source = ROOT / "tools/cstar_numeric_wind_raw_query.cpp"
    bind(source)
    runtime.verify_qualified_helper(args.helper, source, json.loads(args.helper_attestation.read_text()))
    clock = runtime.validate_clock_sensor(json.loads(args.clock.read_text()),
                                         json.loads(args.sensor_manifest.read_text()))
    geometry = json.loads(args.geometry.read_text())
    records = json.loads(args.split.read_text())["records"]
    runtime.require(bool(records) and len({r['realization_id'] for r in records}) == len(records),
                    "EMPTY_OR_DUPLICATE_REALIZATIONS")
    houses = sorted({r["house"] for r in records})
    map_results, entries = {}, []
    for house in houses:
        row = geometry[house]
        for key in ("occupancy", "map_yaml", "map_image"):
            bind(row[key + "_path"], row[key + "_sha256"])
        spec = maps.parse_map_yaml(Path(row["map_yaml_path"]))
        width, height, maxval, pixels = maps.read_pgm(Path(row["map_image_path"]))
        runtime.require((Path(row["map_yaml_path"]).parent / spec["image"]).resolve() ==
                        Path(row["map_image_path"]).resolve(), "MAP_IMAGE_REFERENCE")
        runtime.require(width == row["expected_width_px"] and height == row["expected_height_px"], "MAP_DIMENSIONS")
        runtime.require(spec["origin"] == row["origin_xy_m"] + [0] and
                        spec["resolution"] == row["resolution_m"], "MAP_COORDINATES")
        grid = runtime.Grid3D.from_occupancy(row["occupancy_path"])
        runtime.require(grid.dimensions[:2] == (width, height) and grid.minimum[:2] == tuple(row["origin_xy_m"])
                        and math.isclose(grid.cell_size, spec["resolution"], abs_tol=1e-12), "MAP_OCCUPANCY_GEOMETRY")
        zi = math.floor((row["navigation_height_m"] - grid.minimum[2]) / grid.cell_size)
        runtime.require(0 <= zi < grid.dimensions[2] and zi == row["z_index"], "NAVIGATION_SLICE")
        probes = []
        for probe in row["free_space_probe_csvs"]:
            bind(probe["path"], probe["sha256"])
            probes.append(maps.validate_probe(Path(probe["path"]), probe["sha256"], probe,
                                              spec, width, height, maxval, pixels))
        map_results[house] = {"width": width, "height": height, "z_index": zi, "probes": probes}
    for record in records:
        row = geometry[record["house"]]
        reader = runtime.NumericWindReader(record["resolved_realization_path"], row["occupancy_path"])
        iterations = runtime.numeric_sequence(reader.realization, "iteration_")
        # Header-only samples cover boundaries and interior; every future raw
        # query must also call verify_reply. This is not an all-iteration audit.
        sample_ids = sorted({0, len(iterations)//2, len(iterations)-1})
        headers = []
        for index in sample_ids:
            header = runtime.legacy_header(iterations[index], reader.grid)
            reader.vectors(header["wind_index"])
            headers.append({k: v for k, v in header.items() if k != "sample_grid"} | {"iteration": index})
        wind_rows = []
        for index, path in enumerate(reader.files):
            _, identity = reader.vectors(index)
            bind(path, identity["sha256"])
            wind_rows.append(identity | {"index": index})
        raw_check = {"frames": 0, "max_abs_wind_error": 0.0, "files": []}
        if args.controlled_data:
            directory = args.controlled_data / "realizations" / record["realization_id"]
            files = [directory / "evaluator_raw_history.jsonl"] + sorted(directory.glob("*_evaluator_raw.jsonl"))
            runtime.require(len(files) > 1, "NO_CONTROLLED_ROUTES")
            for path in files:
                bind(path)
                count = 0
                with path.open(encoding="utf-8") as stream:
                    for line in stream:
                        frame = json.loads(line)
                        reply = "OK " + " ".join(map(str, [frame["true_gas_ppm"], *frame["wind_uv"],
                                                           frame["wind_w"], frame["wind_index"]]))
                        error = reader.verify_reply(frame["iteration"], [*frame["pose_xy"], frame["z"]], reply)
                        raw_check["max_abs_wind_error"] = max(raw_check["max_abs_wind_error"], error)
                        count += 1
                runtime.require(count > 0, "EMPTY_RAW_FRAMES")
                raw_check["frames"] += count
                raw_check["files"].append({"path": str(path.resolve()), "frames": count})
        entries.append({"realization_id": record["realization_id"], "house": record["house"],
                        "realization_path": str(reader.realization.resolve()), "raw_wind_reverification": raw_check,
                        "iterations": len(iterations), "header_samples": headers, "winds": wind_rows})
        print(record["house"], record["realization_id"], len(wind_rows), "numeric winds PASS", flush=True)
    result = {"schema": "CSTAR_REUSABLE_ENVIRONMENT_PREFLIGHT_V1", "pass": True,
              "scientific_gate_authority": False, "production_closed_loop_authorized": False,
              "scope": "input identities, all wind layouts, sampled gas headers, geometry probes, resolved sensor and clock",
              "limits": ["not a live ROS/navigation test", "not all gas headers", "not gas payload integrity",
                         "runtime dependency closure is not attested", "raw wind cache is immutable within one read session"],
              "gas_body_bytes_decoded": 0, "new_routes_or_seeds": 0,
              "inputs": {name: str(getattr(args, name).resolve()) for name in
                         ("split", "geometry", "sensor_manifest", "clock", "helper", "helper_attestation")},
              "clock_sensor": clock, "maps": map_results, "entries": entries,
              "bindings": list(bindings.values())}
    # Revalidate at the end too, to catch ordinary concurrent edits during scan.
    runtime.verify_bindings(result["bindings"])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8", newline="\n") as out:
        out.write(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print("CSTAR_REUSABLE_ENVIRONMENT_PREFLIGHT=PASS", flush=True)


if __name__ == "__main__":
    main()
