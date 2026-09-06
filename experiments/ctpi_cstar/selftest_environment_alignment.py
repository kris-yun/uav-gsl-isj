from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import validate_environment_alignment_v2 as env


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_p5(path: Path, width: int, height: int, pixels: bytes) -> None:
    assert len(pixels) == width * height
    path.write_bytes(f"P5\n{width} {height}\n255\n".encode("ascii") + pixels)


def write_csv(path: Path, rows) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["x", "y"])
        w.writerows(rows)


def runtime_audit(path: Path, house: str, geom: str, yaml_path: Path,
                  image_path: Path, ingress_sha: str, wind_sha: str) -> None:
    frames_path = path.parent / "frames.jsonl"
    wind_path = path.parent / "wind_observation.csv"
    frames = [{"stamp_ns": i*200000000, "pose_xy": [1.5, 1.5],
               "wind_uv": [0.1, 0.2], "gas_ppm": 0.0} for i in range(9)]
    frames_path.write_text("".join(json.dumps(f)+"\n" for f in frames))
    with wind_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["stamp_ns", "x", "y", "wind_u", "wind_v"])
        for fr in frames[1:]:
            w.writerow([fr["stamp_ns"], *fr["pose_xy"], *fr["wind_uv"]])
    obj = {
        "pass": True, "runtime_map_parity": True,
        "aligned_frame_count": 9, "first_stamp_ns": 0, "last_stamp_ns": 1600000000,
        "frame_jsonl_path": str(frames_path), "frame_jsonl_sha256": sha(frames_path),
        "wind_position_csv_path": str(wind_path), "wind_position_csv_sha256": sha(wind_path),
        "contract": "CSTAR_RUNTIME_INPUT_LOAD_AUDIT_V1",
        "house": house,
        "git_sha": "synthetic",
        "geometry_identity": geom,
        "map_yaml_path": str(yaml_path),
        "map_yaml_sha256": sha(yaml_path),
        "map_image_path": str(image_path),
        "map_image_sha256": sha(image_path),
        "world_frame": "map",
        "pose_topic": "/pose",
        "gas_topic": "/gas",
        "wind_topic": "/wind",
        "wind_direction_convention": "downwind_vector_uv",
        "wind_vector_units": "m/s",
        "stamp_units": "ns",
        "cadence_ns": 200000000,
        "candidate_frame": "map",
        "route_frame": "map",
        "source_estimate_frame": "map",
        "ingress_code_sha256": ingress_sha,
        "wind_adapter_code_sha256": wind_sha,
        "loader_started_before_scientific_model": True,
        "old_native_gmrf_anemometer_subscription_used": False,
    }
    path.write_text(json.dumps(obj, sort_keys=True) + "\n", encoding="utf-8")


def build_manifest(root: Path) -> Path:
    ingress = root / "ingress.py"
    wind = root / "wind.py"
    ingress.write_text("# synthetic ingress\n", encoding="utf-8")
    wind.write_text("# synthetic wind adapter\n", encoding="utf-8")
    houses = {}
    for house in ("H01", "H02", "H03"):
        d = root / house
        d.mkdir()
        pgm = d / "navigation_slice.pgm"
        write_p5(pgm, 4, 4, bytes([255] * 16))
        yaml = d / "navigation_slice.yaml"
        yaml.write_text(
            "image: navigation_slice.pgm\n"
            "resolution: 1.0\n"
            "origin: [0.0, 0.0, 0.0]\n"
            "negate: 0\n"
            "occupied_thresh: 0.65\n"
            "free_thresh: 0.196\n",
            encoding="utf-8",
        )
        probes = []
        for kind, xy in (
            ("candidate", (0.5, 0.5)),
            ("wind_observation", (1.5, 1.5)),
            ("route", (2.5, 2.5)),
        ):
            p = d / f"{kind}.csv"
            write_csv(p, [xy])
            probes.append({"kind": kind, "path": str(p), "sha256": sha(p)})
        audit = d / "runtime_load_audit.json"
        geom = f"{house}_geom"
        runtime_audit(audit, house, geom, yaml, pgm, sha(ingress), sha(wind))
        for probe in probes:
            probe["sha256"] = sha(Path(probe["path"]))
        houses[house] = {
            "geometry_identity": geom,
            "map_yaml_path": str(yaml),
            "map_yaml_sha256": sha(yaml),
            "map_image_path": str(pgm),
            "map_image_sha256": sha(pgm),
            "navigation_height_m": 0.3,
            "resolution_m": 1.0,
            "origin_xy_m": [0.0, 0.0],
            "expected_width_px": 4,
            "expected_height_px": 4,
            "free_space_probe_csvs": probes,
            "runtime_load_audit_path": str(audit),
            "runtime_load_audit_sha256": sha(audit),
        }
    manifest = {
        "contract": "CSTAR_ENVIRONMENT_ALIGNMENT_V1",
        "git_sha": "synthetic",
        "repo_root": str(root),
        "common_runtime_contract": {
            "world_frame": "map",
            "pose_units": "m",
            "gas_units": "ppm",
            "wind_vector_units": "m/s",
            "wind_direction_convention": "downwind_vector_uv",
            "stamp_units": "ns",
            "expected_cadence_ns": 200000000,
            "candidate_frame": "map",
            "route_frame": "map",
            "source_estimate_frame": "map",
            "future_pose_or_wind_reads_forbidden": True,
            "house_id_as_model_feature_forbidden": True,
            "deployment_predictive_bank_forbidden": True,
            "gmrf_required": False,
        },
        "runtime_code_identity": {
            "ingress_code_path": str(ingress),
            "ingress_code_sha256": sha(ingress),
            "wind_adapter_code_path": str(wind),
            "wind_adapter_code_sha256": sha(wind),
        },
        "houses": houses,
        "shared_arm_input_identity": {
            "A0": "synthetic_shared_input_v1",
            "F00": "synthetic_shared_input_v1",
            "F10": "synthetic_shared_input_v1",
            "F11": "synthetic_shared_input_v1",
        },
    }
    path = root / "environment.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return path


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)

        # Regression: P5 raster's first pixel is 0x0a (newline-like).  It must
        # remain a pixel rather than being consumed as extra header whitespace.
        p = root / "first_pixel_whitespace.pgm"
        write_p5(p, 2, 1, bytes([10, 255]))
        w, h, maxv, pixels = env.read_pgm(p)
        assert (w, h, maxv, pixels) == (2, 1, 255, [10, 255])

        # Strict free threshold / occupied cell rejection.
        probe = root / "probe.csv"
        write_csv(probe, [(0.5, 0.5)])
        try:
            env.validate_probe(
                probe, sha(probe), {"kind": "candidate"},
                {"resolution": 1.0, "origin": [0.0, 0.0, 0.0],
                 "free_thresh": 0.196, "negate": 0},
                1, 1, 255, [0],
            )
        except RuntimeError as exc:
            assert "CSTAR_ENV_PROBE_NOT_FREE" in str(exc)
        else:
            raise AssertionError("occupied probe unexpectedly accepted")

        # Full three-House happy path.
        manifest = build_manifest(root)
        output = root / "audit.json"
        script = ROOT / "validate_environment_alignment.py"
        proc = subprocess.run(
            [sys.executable, str(script), "--manifest", str(manifest),
             "--output", str(output)],
            text=True, capture_output=True,
        )
        assert proc.returncode == 0, (proc.stdout, proc.stderr)
        audit = json.loads(output.read_text(encoding="utf-8"))
        assert audit["pass"] is True
        assert audit["validator_version"] == "V2.1"
        assert set(audit["houses"]) == {"H01", "H02", "H03"}

        # Real exporter uses a block-style YAML origin, not the inline fixture.
        yaml_path = root / "block.yaml"
        yaml_path.write_text("image: a.pgm\nresolution: 1.0\norigin:\n- 0\n- 0\n- 0\n"
                             "negate: 0\nfree_thresh: 0.1\noccupied_thresh: 0.9\n")
        assert env.parse_map_yaml(yaml_path)["origin"] == [0, 0, 0]
        yaml_path.write_text(yaml_path.read_text().replace("- 0\nnegate", "- 0.5\nnegate"))
        try:
            env.parse_map_yaml(yaml_path)
        except RuntimeError as exc:
            assert "YAW" in str(exc)
        else:
            raise AssertionError("nonzero yaw silently ignored")

        m = json.loads(manifest.read_text())
        row = m["houses"]["H01"]
        runtime_path = Path(row["runtime_load_audit_path"])
        original = json.loads(runtime_path.read_text())
        for change, error in [({"pass": False}, "NOT_PASS"),
                              ({"git_sha": "other"}, "RUNTIME_GIT"),
                              ({"runtime_map_parity": False}, "MAP_PARITY"),
                              ({"aligned_frame_count": 2}, "FRAME_COUNT")]:
            runtime_path.write_text(json.dumps({**original, **change}))
            try:
                env.validate_runtime_audit(runtime_path, sha(runtime_path), "H01", row,
                    m["common_runtime_contract"], {**m["runtime_code_identity"], "git_sha": "synthetic"})
            except RuntimeError as exc:
                assert error in str(exc), str(exc)
            else:
                raise AssertionError(f"forged runtime accepted: {change}")

    print("CSTAR_ENVIRONMENT_ALIGNMENT_SELFTEST PASS")


if __name__ == "__main__":
    main()
