#!/usr/bin/env python3
"""Fail-closed three-House environment alignment validator.

V2 fixes binary-PGM parsing so a raster whose first pixel byte happens to be a
whitespace value is not truncated.  It also treats ROS map free_thresh as a
strict-free boundary: occupancy_probability must be < free_thresh.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import yaml

HOUSES = ("H01", "H02", "H03")
ARMS = ("A0", "F00", "F10", "F11")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def require(cond: bool, code: str) -> None:
    if not cond:
        raise RuntimeError(code)


def resolve(base: Path, value: str) -> Path:
    p = Path(value)
    return (p if p.is_absolute() else base / p).resolve()


def check_file(path: Path, expected_sha: str, label: str) -> None:
    require(path.is_file(), f"CSTAR_ENV_MISSING_FILE:{label}:{path}")
    actual = sha256_file(path)
    require(actual == expected_sha,
            f"CSTAR_ENV_HASH_MISMATCH:{label}:{actual}:{expected_sha}:{path}")


def parse_scalar(text: str):
    text = text.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        return text[1:-1]
    if text.startswith("[") and text.endswith("]"):
        return [float(x.strip()) for x in text[1:-1].split(",") if x.strip()]
    try:
        return int(text)
    except ValueError:
        try:
            return float(text)
        except ValueError:
            return text


def parse_map_yaml(path: Path) -> dict:
    out = yaml.safe_load(path.read_text(encoding="utf-8"))
    require(isinstance(out, dict), f"CSTAR_ENV_MAP_YAML_MAPPING:{path}")
    for k in ("image", "resolution", "origin", "negate", "occupied_thresh", "free_thresh"):
        require(k in out, f"CSTAR_ENV_MAP_YAML_MISSING:{k}:{path}")
    require(isinstance(out["origin"], list) and len(out["origin"]) == 3,
            f"CSTAR_ENV_MAP_YAML_ORIGIN:{path}")
    require(all(math.isfinite(float(v)) for v in out["origin"])
            and float(out["origin"][2]) == 0.0,
            f"CSTAR_ENV_MAP_YAW_OR_NONFINITE:{path}")
    require(math.isfinite(float(out["resolution"])) and out["resolution"] > 0
            and out["negate"] in (0, 1)
            and 0 < out["free_thresh"] < out["occupied_thresh"] <= 1,
            f"CSTAR_ENV_MAP_PARAMETERS:{path}")
    return out


def _read_noncomment_header_line(f) -> bytes:
    while True:
        line = f.readline()
        require(line != b"", "CSTAR_ENV_PGM_EOF_HEADER")
        stripped = line.strip()
        if not stripped or stripped.startswith(b"#"):
            continue
        return stripped


def read_pgm(path: Path):
    """Read standard ROS-generated P2/P5 PGM without consuming raster bytes."""
    with path.open("rb") as f:
        magic = _read_noncomment_header_line(f)
        dims = _read_noncomment_header_line(f).split()
        while len(dims) < 2:
            dims += _read_noncomment_header_line(f).split()
        max_line = _read_noncomment_header_line(f)
        width, height = int(dims[0]), int(dims[1])
        maxval = int(max_line.split()[0])
        require(width > 0 and height > 0 and 0 < maxval <= 255,
                f"CSTAR_ENV_PGM_HEADER:{path}")
        if magic == b"P5":
            raster = f.read()
            require(len(raster) == width * height,
                    f"CSTAR_ENV_PGM_RASTER_SIZE:{path}:{len(raster)}:{width*height}")
            pixels = list(raster)
        elif magic == b"P2":
            tokens = []
            for line in f:
                line = line.split(b"#", 1)[0]
                tokens.extend(line.split())
            require(len(tokens) == width * height,
                    f"CSTAR_ENV_PGM_RASTER_SIZE:{path}:{len(tokens)}:{width*height}")
            pixels = [int(x) for x in tokens]
        else:
            raise RuntimeError(f"CSTAR_ENV_PGM_MAGIC:{path}:{magic!r}")
    require(all(0 <= p <= maxval for p in pixels), f"CSTAR_ENV_PGM_PIXEL_RANGE:{path}")
    return width, height, maxval, pixels


def world_to_pixel(x, y, resolution, origin_xy, width, height):
    col = math.floor((x - origin_xy[0]) / resolution)
    bottom_row = math.floor((y - origin_xy[1]) / resolution)
    return int(height - 1 - bottom_row), int(col)


def p_occ(pixel: int, maxval: int, negate: int) -> float:
    q = pixel / maxval
    return q if int(negate) else 1.0 - q


def validate_probe(path: Path, expected_sha: str, spec: dict, map_yaml: dict,
                   width: int, height: int, maxval: int, pixels: list[int]) -> dict:
    check_file(path, expected_sha, f"probe:{spec['kind']}")
    xcol, ycol = spec.get("x_col", "x"), spec.get("y_col", "y")
    origin = (float(map_yaml["origin"][0]), float(map_yaml["origin"][1]))
    resolution = float(map_yaml["resolution"])
    free_thresh = float(map_yaml["free_thresh"])
    negate = int(map_yaml["negate"])
    n = 0
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        require(reader.fieldnames is not None and xcol in reader.fieldnames and ycol in reader.fieldnames,
                f"CSTAR_ENV_PROBE_COLUMNS:{spec['kind']}:{path}")
        for line_no, row in enumerate(reader, 2):
            x, y = float(row[xcol]), float(row[ycol])
            require(math.isfinite(x) and math.isfinite(y),
                    f"CSTAR_ENV_PROBE_NONFINITE:{spec['kind']}:{line_no}")
            rr, cc = world_to_pixel(x, y, resolution, origin, width, height)
            require(0 <= rr < height and 0 <= cc < width,
                    f"CSTAR_ENV_PROBE_OUTSIDE:{spec['kind']}:{path}:{line_no}:{x}:{y}")
            occ = p_occ(pixels[rr * width + cc], maxval, negate)
            require(occ < free_thresh,
                    f"CSTAR_ENV_PROBE_NOT_FREE:{spec['kind']}:{path}:{line_no}:{x}:{y}:{occ}:{free_thresh}")
            n += 1
    require(n > 0, f"CSTAR_ENV_PROBE_EMPTY:{spec['kind']}:{path}")
    return {"kind": spec["kind"], "path": str(path), "rows": n, "all_free": True}


def validate_runtime_audit(path: Path, expected_sha: str, house: str, row: dict,
                           common: dict, code: dict) -> dict:
    check_file(path, expected_sha, f"runtime_audit:{house}")
    a = json.loads(path.read_text(encoding="utf-8"))
    require(a.get("pass") is True, f"CSTAR_ENV_RUNTIME_NOT_PASS:{house}")
    require(a.get("git_sha") == code["git_sha"], f"CSTAR_ENV_RUNTIME_GIT:{house}")
    require(a.get("runtime_map_parity") is True, f"CSTAR_ENV_RUNTIME_MAP_PARITY:{house}")
    frame_path = resolve(path.parent, a["frame_jsonl_path"])
    wind_path = resolve(path.parent, a["wind_position_csv_path"])
    check_file(frame_path, a["frame_jsonl_sha256"], "runtime_frames")
    check_file(wind_path, a["wind_position_csv_sha256"], "runtime_wind")
    frames = [json.loads(line) for line in frame_path.read_text().splitlines()]
    require(len(frames) >= 9 and a["aligned_frame_count"] == len(frames),
            f"CSTAR_ENV_RUNTIME_FRAME_COUNT:{house}")
    require(a["first_stamp_ns"] == 0 and
            a["last_stamp_ns"] == (len(frames)-1)*200000000,
            f"CSTAR_ENV_RUNTIME_ENDPOINTS:{house}")
    with wind_path.open(newline="") as f:
        wind_rows = list(csv.DictReader(f))
    require(len(wind_rows) == len(frames)-1, f"CSTAR_ENV_RUNTIME_WIND_COUNT:{house}")
    for i, fr in enumerate(frames):
        require(type(fr["stamp_ns"]) is int and fr["stamp_ns"] == i*200000000,
                f"CSTAR_ENV_RUNTIME_STAMP:{house}:{i}")
        require(len(fr["pose_xy"]) == 2 and len(fr["wind_uv"]) == 2 and
                all(math.isfinite(float(v)) for v in fr["pose_xy"]+fr["wind_uv"]+[fr["gas_ppm"]])
                and fr["gas_ppm"] >= 0, f"CSTAR_ENV_RUNTIME_VALUES:{house}:{i}")
        if i == 0:
            require(fr["gas_ppm"] == 0, f"CSTAR_ENV_RUNTIME_INITIAL_SENSOR:{house}")
            continue  # bootstrap wind is not an observed sample
        wr = wind_rows[i-1]
        require(int(wr["stamp_ns"]) == fr["stamp_ns"] and
                [float(wr[k]) for k in ("x", "y", "wind_u", "wind_v")] ==
                fr["pose_xy"] + fr["wind_uv"], f"CSTAR_ENV_RUNTIME_WIND_JOIN:{house}:{i}")
    wind_probes = [p for p in row["free_space_probe_csvs"] if p["kind"] == "wind_observation"]
    require(len(wind_probes) == 1 and wind_probes[0]["sha256"] == a["wind_position_csv_sha256"],
            f"CSTAR_ENV_RUNTIME_WIND_SUBSTITUTED:{house}")
    required = (
        "contract", "house", "git_sha", "geometry_identity", "map_yaml_path",
        "map_yaml_sha256", "map_image_path", "map_image_sha256", "world_frame",
        "pose_topic", "gas_topic", "wind_topic", "wind_direction_convention",
        "wind_vector_units", "stamp_units", "cadence_ns", "candidate_frame",
        "route_frame", "source_estimate_frame", "ingress_code_sha256",
        "wind_adapter_code_sha256", "loader_started_before_scientific_model",
        "old_native_gmrf_anemometer_subscription_used")
    missing = [k for k in required if k not in a]
    require(not missing, f"CSTAR_ENV_RUNTIME_AUDIT_FIELDS:{house}:{missing}")
    require(a["contract"] == "CSTAR_RUNTIME_INPUT_LOAD_AUDIT_V1" and a["house"] == house,
            f"CSTAR_ENV_RUNTIME_AUDIT_ID:{house}")
    expected = {
        "geometry_identity": row["geometry_identity"],
        "map_yaml_sha256": row["map_yaml_sha256"],
        "map_image_sha256": row["map_image_sha256"],
        "world_frame": common["world_frame"],
        "wind_direction_convention": common["wind_direction_convention"],
        "wind_vector_units": common["wind_vector_units"],
        "stamp_units": common["stamp_units"],
        "cadence_ns": common["expected_cadence_ns"],
        "candidate_frame": common["candidate_frame"],
        "route_frame": common["route_frame"],
        "source_estimate_frame": common["source_estimate_frame"],
        "ingress_code_sha256": code["ingress_code_sha256"],
        "wind_adapter_code_sha256": code["wind_adapter_code_sha256"],
    }
    for k, v in expected.items():
        require(a.get(k) == v,
                f"CSTAR_ENV_RUNTIME_AUDIT_MISMATCH:{house}:{k}:{a.get(k)!r}:{v!r}")
    require(a["loader_started_before_scientific_model"] is True,
            f"CSTAR_ENV_RUNTIME_LOADER_ORDER:{house}")
    require(a["old_native_gmrf_anemometer_subscription_used"] is False,
            f"CSTAR_ENV_RUNTIME_OLD_GMRF_SUBSCRIPTION:{house}")
    for k in ("pose_topic", "gas_topic", "wind_topic"):
        require(isinstance(a[k], str) and a[k].startswith("/"),
                f"CSTAR_ENV_RUNTIME_TOPIC:{house}:{k}")
    return {"path": str(path), "sha256": expected_sha,
            "pose_topic": a["pose_topic"], "gas_topic": a["gas_topic"],
            "wind_topic": a["wind_topic"]}


def validate_house(base: Path, house: str, row: dict, common: dict, code: dict) -> dict:
    required = ("geometry_identity", "map_yaml_path", "map_yaml_sha256",
                "map_image_path", "map_image_sha256", "navigation_height_m",
                "resolution_m", "origin_xy_m", "expected_width_px",
                "expected_height_px", "free_space_probe_csvs",
                "runtime_load_audit_path", "runtime_load_audit_sha256")
    missing = [k for k in required if k not in row]
    require(not missing, f"CSTAR_ENV_HOUSE_FIELDS:{house}:{missing}")
    ypath = resolve(base, row["map_yaml_path"])
    ipath = resolve(base, row["map_image_path"])
    check_file(ypath, row["map_yaml_sha256"], f"map_yaml:{house}")
    check_file(ipath, row["map_image_sha256"], f"map_image:{house}")
    y = parse_map_yaml(ypath)
    image_from_yaml = Path(str(y["image"]))
    image_from_yaml = (ypath.parent / image_from_yaml).resolve() if not image_from_yaml.is_absolute() else image_from_yaml.resolve()
    require(image_from_yaml == ipath,
            f"CSTAR_ENV_YAML_IMAGE_IDENTITY:{house}:{image_from_yaml}:{ipath}")
    require(abs(float(y["resolution"]) - float(row["resolution_m"])) <= 1e-9,
            f"CSTAR_ENV_RESOLUTION:{house}")
    origin = row["origin_xy_m"]
    require(isinstance(origin, list) and len(origin) == 2,
            f"CSTAR_ENV_ORIGIN_SHAPE:{house}")
    require(abs(float(y["origin"][0]) - float(origin[0])) <= 1e-9 and
            abs(float(y["origin"][1]) - float(origin[1])) <= 1e-9,
            f"CSTAR_ENV_ORIGIN:{house}")
    require(math.isfinite(float(row["navigation_height_m"])),
            f"CSTAR_ENV_NAV_HEIGHT:{house}")
    width, height, maxval, pixels = read_pgm(ipath)
    require(width == int(row["expected_width_px"]) and height == int(row["expected_height_px"]),
            f"CSTAR_ENV_MAP_DIMENSIONS:{house}:{width}x{height}")
    probes = row["free_space_probe_csvs"]
    require(isinstance(probes, list) and probes, f"CSTAR_ENV_PROBES_MISSING:{house}")
    kinds = {p.get("kind") for p in probes if isinstance(p, dict)}
    require({"candidate", "wind_observation", "route"} <= kinds,
            f"CSTAR_ENV_PROBE_KIND_MISSING:{house}:{kinds}")
    probe_results = [validate_probe(resolve(base, p["path"]), p["sha256"], p,
                                    y, width, height, maxval, pixels) for p in probes]
    runtime = validate_runtime_audit(resolve(base, row["runtime_load_audit_path"]),
                                     row["runtime_load_audit_sha256"], house,
                                     row, common, code)
    return {"geometry_identity": row["geometry_identity"],
            "map_yaml": str(ypath), "map_image": str(ipath),
            "resolution_m": float(row["resolution_m"]),
            "origin_xy_m": [float(origin[0]), float(origin[1])],
            "navigation_height_m": float(row["navigation_height_m"]),
            "width_px": width, "height_px": height,
            "probes": probe_results, "runtime_load_audit": runtime, "pass": True}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    mpath = args.manifest.resolve()
    m = json.loads(mpath.read_text(encoding="utf-8"))
    require(m.get("contract") == "CSTAR_ENVIRONMENT_ALIGNMENT_V1",
            f"CSTAR_ENV_CONTRACT:{m.get('contract')}")
    for k in ("git_sha", "repo_root", "common_runtime_contract",
              "runtime_code_identity", "houses", "shared_arm_input_identity"):
        require(k in m, f"CSTAR_ENV_TOP_FIELD:{k}")
    common = m["common_runtime_contract"]
    frozen = {"world_frame": "map", "pose_units": "m", "gas_units": "ppm",
              "wind_vector_units": "m/s", "wind_direction_convention": "downwind_vector_uv",
              "stamp_units": "ns", "expected_cadence_ns": 200000000,
              "candidate_frame": "map", "route_frame": "map",
              "source_estimate_frame": "map", "future_pose_or_wind_reads_forbidden": True,
              "house_id_as_model_feature_forbidden": True,
              "deployment_predictive_bank_forbidden": True, "gmrf_required": False}
    for k, v in frozen.items():
        require(common.get(k) == v,
                f"CSTAR_ENV_COMMON_CONTRACT:{k}:{common.get(k)!r}:{v!r}")
    base = mpath.parent
    code = m["runtime_code_identity"]
    code = {**code, "git_sha": m["git_sha"]}
    for stem in ("ingress", "wind_adapter"):
        pkey, skey = f"{stem}_code_path", f"{stem}_code_sha256"
        require(pkey in code and skey in code, f"CSTAR_ENV_CODE_IDENTITY:{stem}")
        check_file(resolve(base, code[pkey]), code[skey], f"code:{stem}")
    require(set(m["houses"]) == set(HOUSES), f"CSTAR_ENV_HOUSES:{sorted(m['houses'])}")
    houses = {h: validate_house(base, h, m["houses"][h], common, code) for h in HOUSES}
    arm_id = m["shared_arm_input_identity"]
    require(set(arm_id) == set(ARMS), f"CSTAR_ENV_ARMS:{sorted(arm_id)}")
    vals = [arm_id[a] for a in ARMS]
    require(all(isinstance(v, str) and v for v in vals) and len(set(vals)) == 1,
            f"CSTAR_ENV_ARM_INPUT_IDENTITY_NOT_SHARED:{arm_id}")
    out = {"contract": "CSTAR_ENVIRONMENT_ALIGNMENT_AUDIT_V1",
           "input_manifest": str(mpath), "input_manifest_sha256": sha256_file(mpath),
           "validator_version": "V2.1", "git_sha": m["git_sha"],
           "repo_root": m["repo_root"], "houses": houses,
           "shared_arm_input_identity": arm_id, "pass": True,
           "verdict": "CSTAR_ENVIRONMENT_ALIGNMENT=PASS",
           "scope": "short shared-loader geometry/frame/local-wind/clock/point feasibility only; arm identity is a future binding contract, not four-arm execution evidence; not GMRF accuracy or M1/M2/M3 effectiveness"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(out["verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
