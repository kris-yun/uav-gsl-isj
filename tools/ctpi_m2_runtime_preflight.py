#!/usr/bin/env python3
"""Fail-closed VM runtime identity preflight for CTPI M2 world generation."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any


CONTRACT = "CTPI_M2_GENERATOR_RUNTIME_IDENTITY_V1"
EXPECTED_ENV = {
    "OMP_NUM_THREADS": "4",
    "OMP_DYNAMIC": "FALSE",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "PYTHONHASHSEED": "0",
}
PATHS = {
    "native_binary": Path("/home/zyc/PF_DEI_V3_STREAM_BUILD/install/bin/pf_dei_v3_native_multistream"),
    "native_source": Path("/home/zyc/PF_DEI_V3_STREAM_BUILD/src/pf_dei_v3_native_multistream.cpp"),
    "gaden_library": Path("/home/zyc/PF_DEI_V3_GADEN_BUILD/install/lib/libgaden.so"),
    "libbsc": Path("/home/zyc/PF_DEI_V3_GADEN_BUILD/build/gaden_common/third_party/gaden_core/third_party/libbsc/libbsc.so"),
    "rng_hook_source": Path("/home/zyc/PF_DEI_V3_GADEN_SRC/gaden_common/third_party/gaden_core/src/RngHook.cpp"),
    "mathutils_source": Path("/home/zyc/PF_DEI_V3_GADEN_SRC/gaden_common/third_party/gaden_core/include/gaden/internal/MathUtils.hpp"),
    "running_simulation_source": Path("/home/zyc/PF_DEI_V3_GADEN_SRC/gaden_common/third_party/gaden_core/src/RunningSimulation.cpp"),
    "running_simulation_header": Path("/home/zyc/PF_DEI_V3_GADEN_SRC/gaden_common/third_party/gaden_core/include/gaden/RunningSimulation.hpp"),
}
EXPECTED_SHA256 = {
    "native_binary": "ad0772d994875d009a1e8720928a9f40db56c20f6bf83a03b309049696a7ead4",
    "native_source": "7a1570637eac1ca97758baddd05e7762b47fcd2e12afd77239698bd1132b01b4",
    "gaden_library": "0b6a2160917a1e8791c1980635b0969c40794b96d591abba31d743758fc5f048",
    "libbsc": "8e7873a03fc27c42715f579d5dad25d99f8e69de9bacc857fe71489d7ac2b89b",
    "rng_hook_source": "826fbe242e152a09d03bc50849f6b882b58b0b3fc41a6b3e595c3811b20a9131",
    "mathutils_source": "374ec0ed56cbd38ff5bc017ad668a831c8da5c19e34b5b81186e4e8a5eee4c05",
    "running_simulation_source": "b699492b816980b583301e025cdbd04d5b9adedff90b9419593b2160a091ae2a",
    "running_simulation_header": "1f57a0ccfd02fa6cc3a18714cd96b795c49e4e81e41f4d4b136fc05f35040abe",
}
OVERLAY_ORDER = ["/opt/ros/humble/setup.bash", "/home/zyc/ros2_ws/install/setup.bash"]
LD_PREFIX = [
    "/opt/ros/humble/lib",
    "/home/zyc/PF_DEI_V3_GADEN_BUILD/install/lib",
    "/home/zyc/PF_DEI_V3_GADEN_BUILD/build/gaden_common/third_party/gaden_core/third_party/libbsc",
]
HOUSE_ASSETS = {
    "H01": (Path("/home/zyc/rmfe_cl_env/H01/OccupancyGrid3D.csv"), Path("/home/zyc/rmfe_cl_env/H01/wind")),
    "H02": (Path("/home/zyc/H02_ACIT_TRANSPORT_MISMATCH_AUDIT_WORK/assets/House02/OccupancyGrid3D.csv"), Path("/home/zyc/PF_DEI_FORWARD_CLOSURE_20260828/converted_wind_house02")),
    "H03": (Path("/home/zyc/rmfe_cl_env/H03/OccupancyGrid3D.csv"), Path("/home/zyc/rmfe_cl_env/H03/wind")),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def build(bank_root: Path) -> dict[str, Any]:
    env_checks = {key: os.environ.get(key) == value for key, value in EXPECTED_ENV.items()}
    ld_parts = os.environ.get("LD_LIBRARY_PATH", "").split(":")
    ld_prefix_match = ld_parts[:len(LD_PREFIX)] == LD_PREFIX
    file_records = {}
    for name, path in PATHS.items():
        actual = sha256_file(path)
        file_records[name] = {"path": str(path), "sha256": actual,
                              "expected_sha256": EXPECTED_SHA256[name],
                              "match": actual == EXPECTED_SHA256[name]}

    completed = subprocess.run(
        ["ldd", str(PATHS["native_binary"])], text=True,
        capture_output=True, check=False, env=os.environ.copy(),
    )
    ldd_text = completed.stdout + completed.stderr
    loader_records: dict[str, str] = {}
    for line in completed.stdout.splitlines():
        match = re.match(r"\s*(\S+)\s+=>\s+(\S+)", line)
        if match is not None:
            loader_records[match.group(1)] = match.group(2)
    loader_checks = {
        "ldd_exit_zero": completed.returncode == 0,
        "no_library_not_found": "not found" not in ldd_text,
        "frozen_gaden_library_loaded": loader_records.get("libgaden.so") == str(PATHS["gaden_library"]),
        "frozen_libbsc_loaded": loader_records.get("libbsc.so") == str(PATHS["libbsc"]),
    }

    houses: dict[str, Any] = {}
    for house, (environment, wind_dir) in HOUSE_ASSETS.items():
        summary_path = bank_root / house / "bank_summary.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        wind_hashes = {
            path.name: sha256_file(path)
            for path in sorted(wind_dir.glob("wind_iteration_*")) if path.is_file()
        }
        checks = {
            "environment_hash_match": sha256_file(environment) == summary["environment_sha256"],
            "wind_hashes_match": wind_hashes == summary["wind_iteration_hashes"],
            "native_binary_hash_match": file_records["native_binary"]["sha256"] == summary["native_binary_sha256"],
        }
        houses[house] = {
            "environment": str(environment), "environment_sha256": sha256_file(environment),
            "wind_dir": str(wind_dir), "wind_iteration_hashes": wind_hashes,
            "bank_summary": str(summary_path), "bank_summary_sha256": sha256_file(summary_path),
            "checks": checks,
        }

    checks = {
        "process_environment_exact": all(env_checks.values()),
        "ld_library_prefix_exact": ld_prefix_match,
        "all_frozen_files_match": all(row["match"] for row in file_records.values()),
        "loader_identity": all(loader_checks.values()),
        "all_house_physical_assets_match_frozen_bank": all(
            all(row["checks"].values()) for row in houses.values()
        ),
    }
    result = {
        "contract": CONTRACT,
        "generator_environment_required": EXPECTED_ENV,
        "generator_environment_observed": {key: os.environ.get(key) for key in EXPECTED_ENV},
        "environment_checks": env_checks,
        "overlay_order": OVERLAY_ORDER,
        "ld_library_path_prefix": LD_PREFIX,
        "ld_library_path_observed": os.environ.get("LD_LIBRARY_PATH"),
        "file_identity": file_records,
        "loaded_library_paths": loader_records,
        "loader_checks": loader_checks,
        "houses": houses,
        "checks": checks,
        "pass": all(checks.values()),
    }
    result["verdict"] = (
        "CTPI_M2_GENERATOR_RUNTIME=PASS" if result["pass"]
        else "CTPI_M2_GENERATOR_RUNTIME=FAIL"
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bank-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.bank_root)
    data = canonical_bytes(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    args.output.with_suffix(args.output.suffix + ".sha256").write_text(
        f"{digest}  {args.output.name}\n", encoding="ascii"
    )
    print(result["verdict"])
    print(f"CTPI_M2_GENERATOR_RUNTIME_SHA256={digest}")
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
