"""Recompute physical identities; free-form names/literal presence are not proof."""
import hashlib
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from cstar_collect_provenance_metadata import parse_launch, header_only
from cstar_inspect_wind_provenance import wind_identity

RELEASE_FIELDS = ("sim_time", "time_step", "num_filaments_sec", "variable_rate",
    "filament_stop_steps", "ppm_filament_center", "filament_initial_std",
    "filament_growth_gamma", "filament_noise_std", "temperature", "pressure",
    "concentration_unit_choice", "results_time_step", "results_min_time", "writeConcentrations")
TRANSPORT_FIELDS = ("wind_time_step", "allow_looping", "loop_from_step", "loop_to_step")


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def scalar(value):
    if value in ("true", "false"):
        return value == "true"
    return float(value)


def derive_claims(generator_path, simulation_dir, wind_files):
    sim = Path(simulation_dir)
    parsed = parse_launch(Path(generator_path).read_bytes(), sim.parents[4])
    params = parsed["simulator_params"]
    if Path(params["results_location"]) != sim:
        raise ValueError("GENERATOR_RESULT_PATH_MISMATCH")
    xyz = [float(params["source_position_"+axis]) for axis in "xyz"]
    release = {key: scalar(params[key]) for key in RELEASE_FIELDS}
    transport = {key: scalar(params[key]) for key in TRANSPORT_FIELDS}
    # Paths/encoding cannot manufacture physical variation.
    transport["normalized_wind_sequence"] = [f["normalized_vector_sha256"] for f in wind_files]
    sensor = {"stage": "raw_gaden_filament_state", "measurement_sensor": "absent"}
    return {"source_xyz_m": xyz, "gas_type_id": str(int(params["gas_type"])),
            "release_parameters": release, "transport_parameters": transport,
            "sensor_parameters": sensor, "release_fingerprint": fingerprint(release),
            "transport_fingerprint": fingerprint(transport), "sensor_mechanism_fingerprint": fingerprint(sensor)}


def verify_claims(row, base, checked):
    proof = row.get("physical_binding")
    if not isinstance(proof, dict):
        raise ValueError("PHYSICAL_CLAIM_BINDINGS_MISSING")
    generator = checked[proof["generator_evidence_index"]]
    if generator["kind"] != "generator_config":
        raise ValueError("GENERATOR_EVIDENCE_KIND")
    wind_evidence = checked[proof["wind_evidence_index"]]
    if wind_evidence["kind"] != "transport_config":
        raise ValueError("WIND_EVIDENCE_KIND")
    wind_doc = json.loads(Path(wind_evidence["path"]).read_text())
    item = next(e for e in wind_doc["entries"] if e["realization_id"] == row["realization_id"])
    if item["errors"] or not item["files"]:
        raise ValueError("WIND_IDENTITY_INVALID")
    sim = Path(row["simulation_dir_path"])
    occupancy = sim.parents[2] / "OccupancyGrid3D.csv"
    occupancy_raw = occupancy.read_bytes()
    occupancy_sha = hashlib.sha256(occupancy_raw).hexdigest()
    if row["geometry_identity"] != f'{row["house"]}:occupancy-{occupancy_sha}:z0.3:full-slice':
        raise ValueError("ORIGINAL_OCCUPANCY_IDENTITY_MISMATCH")
    meta = {}
    for line in occupancy_raw.decode().splitlines()[:4]:
        tokens = line.split()
        meta[tokens[0].split("(")[0]] = tokens[1:]
    header, raw, compressed = header_only(sim / "iteration_0")
    if header.get("version") != 1 or header["header_sha256"] != proof["header_sha256"]:
        raise ValueError("HEADER_IDENTITY_MISMATCH")
    expected_coords = list(map(float, meta["#env_min"]+meta["#env_max"]))
    coordinate_matches = [all(abs(a-b) <= 1e-5 for a, b in zip(header[k], expected_coords))
                          for k in ("environment_slots_native_double", "environment_slots_float_prefix")]
    if (not any(coordinate_matches) or header["dimensions"] != list(map(int, meta["#num_cells"]))
            or header["cell_size"] != float(meta["#cell_size"][0])):
        raise ValueError("HEADER_GEOMETRY_MISMATCH")
    cells = 1
    for dim in header["dimensions"]:
        cells *= dim
    actual_files = sorted((sim / "wind").glob("wind_iteration_*"), key=lambda p: int(p.name.rsplit("_", 1)[1]))
    if [p.name for p in actual_files] != [f["name"] for f in item["files"]]:
        raise ValueError("WIND_SEQUENCE_INCOMPLETE")
    for path, expected in zip(actual_files, item["files"]):
        actual = wind_identity(path, cells)
        if actual != expected:
            raise ValueError("WIND_IDENTITY_MISMATCH")
    claims = derive_claims(generator["path"], sim, item["files"])
    if list(struct.unpack_from("<3d", raw, 88)) != claims["source_xyz_m"]:
        raise ValueError("HEADER_SOURCE_GENERATOR_MISMATCH")
    if str(header["gas_type_id"]) != claims["gas_type_id"]:
        raise ValueError("HEADER_GAS_GENERATOR_MISMATCH")
    for key in ("source_xyz_m", "gas_type_id", "release_fingerprint", "transport_fingerprint", "sensor_mechanism_fingerprint"):
        if row[key] != claims[key]:
            raise ValueError("PHYSICAL_CLAIM_MISMATCH:"+key)
    if claims["release_parameters"]["writeConcentrations"] is not False:
        raise ValueError("RAW_FILAMENT_SENSOR_STAGE_NOT_SUPPORTED")
    return claims
