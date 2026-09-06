#!/usr/bin/env python3
"""Validate the three-House CSTAR environment/input alignment.

This is deliberately independent of learned M1/M2/M3 metrics.  It verifies the
actual geometry files, world->grid free-space probes, local-wind/clock/frame
semantics and the runtime loader audit that must precede controlled scientific
validation.

The input manifest is a realised artifact with contract
CSTAR_ENVIRONMENT_ALIGNMENT_V1.  The companion
CSTAR_ENVIRONMENT_ALIGNMENT_CONTRACT_V1.json documents the frozen semantics.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

CONTRACT = "CSTAR_ENVIRONMENT_ALIGNMENT_V1"
AUDIT_CONTRACT = "CSTAR_RUNTIME_INPUT_LOAD_AUDIT_V1"
HOUSES = ("H01", "H02", "H03")
ARMS = ("A0", "F00", "F10", "F11")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def require_file(path: Path, expected_sha: str, label: str) -> None:
    if not path.is_file():
        raise RuntimeError(f"CSTAR_ENV_MISSING_FILE:{label}:{path}")
    actual = sha256_file(path)
    if actual != expected_sha:
        raise RuntimeError(
            f"CSTAR_ENV_HASH_MISMATCH:{label}:{actual}:{expected_sha}:{path}"
        )


def parse_scalar(text: str) -> Any:
    text = text.strip()
    if (len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'"):
        return text[1:-1]
    if text.lower() in ("true", "false"):
        return text.lower() == "true"
    if text.startswith("[") and text.endswith("]"):
        parts = [p.strip() for p in text[1:-1].split(",")]
        return [float(p) for p in parts if p]
    try:
        return int(text)
    except ValueError:
        try:
            return float(text)
        except ValueError:
            return text


def parse_map_yaml(path: Path) -> dict[str, Any]:
    """Parse only the ROS map YAML scalar fields needed by this validator."""
    out: dict[str, Any] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        out[key.strip()] = parse_scalar(value)
    for key in ("image", "resolution", "origin", "negate", "occupied_thresh", "free_thresh"):
        if key not in out:
            raise RuntimeError(f"CSTAR_ENV_MAP_YAML_MISSING:{key}:{path}")
    if not isinstance(out["origin"], list) or len(out["origin"]) < 2:
        raise RuntimeError(f"CSTAR_ENV_MAP_YAML_ORIGIN:{path}")
    return out


def _next_pgm_token(data: bytes, pos: int) -> tuple[bytes, int]:
    n = len(data)
    while pos < n:
        if data[pos] in b" \t\r\n":
            pos += 1
            continue
        if data[pos] == ord("#"):
            while pos < n and data[pos] not in b"\r\n":
                pos += 1
            continue
        break
    start = pos
    while pos < n and data[pos] not in b" \t\r\n#":
        pos += 1
    if start == pos:
        raise RuntimeError("CSTAR_ENV_PGM_TOKEN")
    return data[start:pos], pos


def read_pgm(path: Path) -> tuple[int, int, int, list[int]]:
    data = path.read_bytes()
    pos = 0
    magic, pos = _next_pgm_token(data, pos)
    w_b, pos = _next_pgm_token(data, pos)
    h_b, pos = _next_pgm_token(data, pos)
    max_b, pos = _next_pgm_token(data, pos)
    try:
        width, height, maxval = int(w_b), int(h_b), int(max_b)
    except ValueError as exc:
        raise RuntimeError(f"CSTAR_ENV_PGM_HEADER:{path}") from exc
    if width <= 0 or height <= 0 or maxval <= 0 or maxval > 255:
        raise RuntimeError(f"CSTAR_ENV_PGM_UNSUPPORTED_HEADER:{path}")
    if magic == b"P5":
        # One whitespace byte is required after maxval.  Skip all whitespace,
        # but not arbitrary comments after the binary raster begins.
        while pos < len(data) and data[pos] in b" \t\r\n":
            pos += 1
        raster = data[pos:]
        if len(raster) != width * height:
            raise RuntimeError(
                f"CSTAR_ENV_PGM_RASTER_SIZE:{path}:{len(raster)}:{width*height}"
            )
        pixels = list(raster)
    elif magic == b"P2":
        pixels = []
        for _ in range(width * height):
            tok, pos = _next_pgm_token(data, pos)
            pixels.append(int(tok))
    else:
        raise RuntimeError(f"CSTAR_ENV_PGM_MAGIC:{path}:{magic!r}")
    return width, height, maxval, pixels


def as_path(base: Path, value: str) -> Path:
    p = Path(value)
    return p if p.is_absolute() else (base / p)


def close(a: float, b: float, tol: float = 1e-9) -> bool:
    return math.isfinite(a) and math.isfinite(b) and abs(a - b) <= tol


def world_to_pixel(x: float, y: float, resolution: float,
                   origin_xy: tuple[float, float], width: int, height: int) -> tuple[int, int]:
    col = math.floor((x - origin_xy[0]) / resolution)
    map_row_from_bottom = math.floor((y - origin_xy[1]) / resolution)
    row = height - 1 - map_row_from_bottom
    return int(row), int(col)


def occupancy_probability(pixel: int, maxval: int, negate: int) -> float:
    scaled = pixel / maxval
    return scaled if int(negate) else 1.0 - scaled


def validate_probe_csv(path: Path, expected_sha: str, kind: str, x_col: str,
                       y_col: str, map_data: dict[str, Any], pixels: list[int],
                       width: int, height: int, maxval: int) -> dict[str, Any]:
    require_file(path, expected_sha, f"probe:{kind}")
    resolution = float(map_data["resolution"])
    origin = (float(map_data["origin"][0]), float(map_data["origin"][1]))
    free_thresh = float(map_data["free_thresh"])
    negate = int(map_data["negate"])
    total = 0
    invalid = []
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or x_col not in reader.fieldnames or y_col not in reader.fieldnames:
            raise RuntimeError(f"CSTAR_ENV_PROBE_COLUMNS:{kind}:{path}")
        for line_no, row in enumerate(reader, start=2):
            try:
                x, y = float(row[x_col]), float(row[y_col])
            except (TypeError, ValueError, KeyError) as exc:
                raise RuntimeError(f"CSTAR_ENV_PROBE_VALUE:{kind}:{path}:{line_no}") from exc
            if not math.isfinite(x) or not math.isfinite(y):
                raise RuntimeError(f"CSTAR_ENV_PROBE_NONFINITE:{kind}:{path}:{line_no}")
            rr, cc = world_to_pixel(x, y, resolution, origin, width, height)
            total += 1
            if rr < 0 or rr >= height or cc < 0 or cc >= width:
                invalid.append({"line": line_no, "x": x, "y": y, "reason": "OUTSIDE_MAP"})
                continue
            p_occ = occupancy_probability(pixels[rr * width + cc], maxval, negate)
            if p_occ > free_thresh + 1e-12:
                invalid.append({
                    "line": line_no, "x": x, "y": y,
                    "row": rr, "col": cc, "occupancy_probability": p_occ,
                    "free_thresh": free_thresh, "reason": "NOT_FREE",
                })
    if total < 1:
        raise RuntimeError(f"CSTAR_ENV_PROBE_EMPTY:{kind}:{path}")
    if invalid:
        sample = invalid[:10]
        raise RuntimeError(
            f"CSTAR_ENV_PROBE_INVALID:{kind}:{path}:count={len(invalid)}:sample={sample}"
        )
    return {"kind": kind, "path": str(path), "rows": total, "all_free": True}


def validate_runtime_audit(path: Path, expected_sha: str, house: str,
                           house_row: dict[str, Any], common: dict[str, Any],
                           code_identity: dict[str, Any]) -> dict[str, Any]:
    require_file(path, expected_sha, f"runtime_audit:{house}")
    obj = json.loads(path.read_text(encoding="utf-8"))
    required = (
        "contract", "house", "git_sha", "geometry_identity", "map_yaml_path",
        "map_yaml_sha256", "map_image_path", "map_image_sha256", "world_frame",
        "pose_topic", "gas_topic", "wind_topic", "wind_direction_convention",
        "wind_vector_units", "stamp_units", "cadence_ns", "candidate_frame",
        "route_frame", "source_estimate_frame", "ingress_code_sha256",
        "wind_adapter_code_sha256", "loader_started_before_scientific_model",
        "old_native_gmrf_anemometer_subscription_used",
    )
    missing = [k for k in required if k not in obj]
    if missing:
        raise RuntimeError(f"CSTAR_ENV_RUNTIME_AUDIT_FIELDS:{house}:{missing}")
    if obj["contract"] != AUDIT_CONTRACT or obj["house"] != house:
        raise RuntimeError(f"CSTAR_ENV_RUNTIME_AUDIT_ID:{house}")
    equality = {
        "geometry_identity": house_row["geometry_identity"],
        "map_yaml_sha256": house_row["map_yaml_sha256"],
        "map_image_sha256": house_row["map_image_sha256"],
        "world_frame": common["world_frame"],
        "wind_direction_convention": common["wind_direction_convention"],
        "wind_vector_units": common["wind_vector_units"],
        "stamp_units": common["stamp_units"],
        "cadence_ns": common["expected_cadence_ns"],
        "candidate_frame": common["candidate_frame"],
        "route_frame": common["route_frame"],
        "source_estimate_frame": common["source_estimate_frame"],
        "ingress_code_sha256": code_identity["ingress_code_sha256"],
        "wind_adapter_code_sha256": code_identity["wind_adapter_code_sha256"],
    }
    for key, expected in equality.items():
        if obj.get(key) != expected:
            raise RuntimeError(
                f"CSTAR_ENV_RUNTIME_AUDIT_MISMATCH:{house}:{key}:{obj.get(key)!r}:{expected!r}"
            )
    if obj["loader_started_before_scientific_model"] is not True:
        raise RuntimeError(f"CSTAR_ENV_RUNTIME_LOADER_ORDER:{house}")
    if obj["old_native_gmrf_anemometer_subscription_used"] is not False:
        raise RuntimeError(f"CSTAR_ENV_RUNTIME_OLD_GMRF_SUBSCRIPTION:{house}")
    for topic in ("pose_topic", "gas_topic", "wind_topic"):
        if not isinstance(obj[topic], str) or not obj[topic].startswith("/"):
            raise RuntimeError(f"CSTAR_ENV_RUNTIME_TOPIC:{house}:{topic}")
    return {
        "path": str(path),
        "sha256": expected_sha,
        "pose_topic": obj["pose_topic"],
        "gas_topic": obj["gas_topic"],
        "wind_topic": obj["wind_topic"],
    }


def validate_house(base: Path, house: str, row: dict[str, Any], common: dict[str, Any],
                   code_identity: dict[str, Any]) -> dict[str, Any]:
    required = (
        "geometry_identity", "map_yaml_path", "map_yaml_sha256", "map_image_path",
        "map_image_sha256", "navigation_height_m", "resolution_m", "origin_xy_m",
        "expected_width_px", "expected_height_px", "free_space_probe_csvs",
        "runtime_load_audit_path", "runtime_load_audit_sha256",
    )
    missing = [k for k in required if k not in row]
    if missing:
        raise RuntimeError(f"CSTAR_ENV_HOUSE_FIELDS:{house}:{missing}")
    yaml_path = as_path(base, row["map_yaml_path"]).resolve()
    image_path = as_path(base, row["map_image_path"]).resolve()
    require_file(yaml_path, row["map_yaml_sha256"], f"map_yaml:{house}")
    require_file(image_path, row["map_image_sha256"], f"map_image:{house}")
    map_data = parse_map_yaml(yaml_path)
    yaml_image = Path(str(map_data["image"]))
    yaml_image = (yaml_path.parent / yaml_image).resolve() if not yaml_image.is_absolute() else yaml_image.resolve()
    if yaml_image != image_path:
        raise RuntimeError(f"CSTAR_ENV_YAML_IMAGE_IDENTITY:{house}:{yaml_image}:{image_path}")
    if not close(float(map_data["resolution"]), float(row["resolution_m"])):
        raise RuntimeError(f"CSTAR_ENV_RESOLUTION:{house}")
    origin = row["origin_xy_m"]
    if not isinstance(origin, list) or len(origin) != 2:
        raise RuntimeError(f"CSTAR_ENV_ORIGIN_SHAPE:{house}")
    if not (close(float(map_data["origin"][0]), float(origin[0])) and
            close(float(map_data["origin"][1]), float(origin[1]))):
        raise RuntimeError(f"CSTAR_ENV_ORIGIN:{house}")
    if not math.isfinite(float(row["navigation_height_m"])):
        raise RuntimeError(f"CSTAR_ENV_NAV_HEIGHT:{house}")
    width, height, maxval, pixels = read_pgm(image_path)
    if width != int(row["expected_width_px"]) or height != int(row["expected_height_px"]):
        raise RuntimeError(
            f"CSTAR_ENV_MAP_DIMENSIONS:{house}:{width}x{height}:"
            f"expected={row['expected_width_px']}x{row['expected_height_px']}"
        )
    probes = row["free_space_probe_csvs"]
    if not isinstance(probes, list) or not probes:
        raise RuntimeError(f"CSTAR_ENV_PROBES_MISSING:{house}")
    kinds = {p.get("kind") for p in probes if isinstance(p, dict)}
    for required_kind in ("candidate", "wind_observation", "route"):
        if required_kind not in kinds:
            raise RuntimeError(f"CSTAR_ENV_PROBE_KIND_MISSING:{house}:{required_kind}")
    probe_results = []
    for p in probes:
        probe_path = as_path(base, p["path"]).resolve()
        probe_results.append(validate_probe_csv(
            probe_path, p["sha256"], p["kind"], p.get("x_col", "x"), p.get("y_col", "y"),
            map_data, pixels, width, height, maxval,
        ))
    runtime_path = as_path(base, row["runtime_load_audit_path"]).resolve()
    runtime_result = validate_runtime_audit(
        runtime_path, row["runtime_load_audit_sha256"], house, row, common, code_identity
    )
    return {
        "geometry_identity": row["geometry_identity"],
        "map_yaml": str(yaml_path), "map_image": str(image_path),
        "resolution_m": float(row["resolution_m"]),
        "origin_xy_m": [float(origin[0]), float(origin[1])],
        "navigation_height_m": float(row["navigation_height_m"]),
        "width_px": width, "height_px": height,
        "probes": probe_results, "runtime_load_audit": runtime_result,
        "pass": True,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    manifest_path = args.manifest.resolve()
    obj = json.loads(manifest_path.read_text(encoding="utf-8"))
    if obj.get("contract") != CONTRACT:
        raise RuntimeError(f"CSTAR_ENV_CONTRACT:{obj.get('contract')}")
    for key in ("git_sha", "repo_root", "common_runtime_contract", "runtime_code_identity",
                "houses", "shared_arm_input_identity"):
        if key not in obj:
            raise RuntimeError(f"CSTAR_ENV_TOP_FIELD:{key}")
    common = obj["common_runtime_contract"]
    frozen = {
        "world_frame": "map", "pose_units": "m", "gas_units": "ppm",
        "wind_vector_units": "m/s", "wind_direction_convention": "downwind_vector_uv",
        "stamp_units": "ns", "expected_cadence_ns": 200000000,
        "candidate_frame": "map", "route_frame": "map", "source_estimate_frame": "map",
        "future_pose_or_wind_reads_forbidden": True,
        "house_id_as_model_feature_forbidden": True,
        "deployment_predictive_bank_forbidden": True, "gmrf_required": False,
    }
    for key, expected in frozen.items():
        if common.get(key) != expected:
            raise RuntimeError(f"CSTAR_ENV_COMMON_CONTRACT:{key}:{common.get(key)!r}:{expected!r}")
    base = manifest_path.parent
    code_identity = obj["runtime_code_identity"]
    for stem in ("ingress", "wind_adapter"):
        path_key, sha_key = f"{stem}_code_path", f"{stem}_code_sha256"
        if path_key not in code_identity or sha_key not in code_identity:
            raise RuntimeError(f"CSTAR_ENV_CODE_IDENTITY:{stem}")
        require_file(as_path(base, code_identity[path_key]).resolve(), code_identity[sha_key], f"code:{stem}")
    houses = obj["houses"]
    if set(houses) != set(HOUSES):
        raise RuntimeError(f"CSTAR_ENV_HOUSES:{sorted(houses)}")
    house_results = {
        h: validate_house(base, h, houses[h], common, code_identity) for h in HOUSES
    }
    arm_identity = obj["shared_arm_input_identity"]
    if set(arm_identity) != set(ARMS):
        raise RuntimeError(f"CSTAR_ENV_ARMS:{sorted(arm_identity)}")
    identity_values = [arm_identity[a] for a in ARMS]
    if any(not isinstance(v, str) or not v for v in identity_values) or len(set(identity_values)) != 1:
        raise RuntimeError(f"CSTAR_ENV_ARM_INPUT_IDENTITY_NOT_SHARED:{arm_identity}")
    report = {
        "contract": "CSTAR_ENVIRONMENT_ALIGNMENT_AUDIT_V1",
        "input_manifest": str(manifest_path),
        "input_manifest_sha256": sha256_file(manifest_path),
        "git_sha": obj["git_sha"],
        "repo_root": obj["repo_root"],
        "houses": house_results,
        "shared_arm_input_identity": arm_identity,
        "pass": True,
        "verdict": "CSTAR_ENVIRONMENT_ALIGNMENT=PASS",
        "scope": "geometry/frame/local-wind/clock/route input identity only; not GMRF accuracy and not M1/M2/M3 scientific effectiveness",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(report["verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
