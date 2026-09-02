#!/usr/bin/env python3
"""Fail-closed CTPI V0.4 runtime-parity guard.

This script is intentionally conservative. The CTPI V0.4 offline reference
(CREL -> APRS for point scoring, with PSRG as a parallel metrology output) must
not be reported as a closed-loop runtime merely because an experiment is
labelled CTPI. In particular, inherited CPIR/TADM `pfdi_mode` paths are not
acceptable substitutes.

The guard exits 0 only when the ROS/C++ runtime advertises the explicit frozen
runtime/ownership/planner markers below. These strings are provenance markers,
not scientific parameters. Until the real runtime port deliberately satisfies
them, the correct result is BLOCKED_BY_RUNTIME_PARITY.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

RUNTIME_MARKER = "CTPI_V04_RUNTIME_CONTRACT_V1"
RUNTIME_MODE = "ctpi_v04"
POSTERIOR_MARKER = "applyCTPIV04Posterior"
APRS_OWNERSHIP_MARKER = "CTPI_V04_APRS_OWNS_CURRENT_OBSERVATION_V1"
PSRG_BOUNDARY_MARKER = "CTPI_V04_PSRG_TELEMETRY_ONLY_V1"
PLANNER_MARKER = "CTPI_V04_PLANNER_CONSUMES_POSTERIOR_V1"
REFERENCE_REL = Path("experiments/cg_pc_ctt/ctpi_v04_reference.py")
PMFS_CPP_REL = Path("ros2_package/src/gsl_server/algorithms/PMFS/PMFS.cpp")
PMFS_HPP_REL = Path("ros2_package/src/gsl_server/algorithms/PMFS/PMFS.hpp")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head(repo: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "UNKNOWN"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--binary", default="")
    ap.add_argument("--json-out", default="")
    args = ap.parse_args()

    repo = Path(args.repo_root).expanduser().resolve()
    ref = repo / REFERENCE_REL
    cpp = repo / PMFS_CPP_REL
    hpp = repo / PMFS_HPP_REL

    result = {
        "contract": "CTPI_V04_RUNTIME_PARITY_GUARD_V2",
        "repo_root": str(repo),
        "git_commit": git_head(repo),
        "required_runtime_marker": RUNTIME_MARKER,
        "required_runtime_mode": RUNTIME_MODE,
        "required_posterior_marker": POSTERIOR_MARKER,
        "required_aprs_ownership_marker": APRS_OWNERSHIP_MARKER,
        "required_psrg_boundary_marker": PSRG_BOUNDARY_MARKER,
        "required_planner_marker": PLANNER_MARKER,
        "checks": {},
        "warnings": [],
    }

    required_files = [ref, cpp, hpp]
    missing = [str(p) for p in required_files if not p.is_file()]
    result["checks"]["required_files_present"] = not missing
    if missing:
        result["missing_files"] = missing
    if ref.is_file():
        result["offline_reference_sha256"] = sha256(ref)

    source_text = ""
    if cpp.is_file():
        source_text += cpp.read_text(encoding="utf-8", errors="replace")
    if hpp.is_file():
        source_text += "\n" + hpp.read_text(encoding="utf-8", errors="replace")

    result["checks"]["explicit_ctpi_v04_mode"] = RUNTIME_MODE in source_text
    result["checks"]["runtime_contract_marker"] = RUNTIME_MARKER in source_text
    result["checks"]["ctpi_posterior_entrypoint"] = POSTERIOR_MARKER in source_text
    result["checks"]["aprs_current_observation_ownership"] = APRS_OWNERSHIP_MARKER in source_text
    result["checks"]["psrg_telemetry_only_boundary"] = PSRG_BOUNDARY_MARKER in source_text
    result["checks"]["planner_consumes_ctpi_posterior"] = PLANNER_MARKER in source_text

    # If a future patch merely adds `ctpi_v04` to the existing allowed-mode
    # list, this broad legacy assignment would route CTPI into TADM. That is a
    # hard wiring error, not an acceptable implementation shortcut.
    broad_tadm_assignment = 'tadmEnabled = pfdiMode != "off" && !cpirEnabled' in source_text
    unsafe_tadm_alias = result["checks"]["explicit_ctpi_v04_mode"] and broad_tadm_assignment
    result["checks"]["ctpi_not_aliased_to_legacy_tadm"] = not unsafe_tadm_alias
    if unsafe_tadm_alias:
        result["warnings"].append(
            "CTPI_V04_MODE_WOULD_ALIAS_TO_LEGACY_TADM; split an explicit ctpiV04Enabled path"
        )

    # CPIR may remain for historical controls, but it must never be the only
    # alternative-posterior runtime when a run is labelled CTPI V0.4.
    cpir_present = "applyCPIRPosterior" in source_text or "cpir_a3" in source_text
    result["checks"]["legacy_cpir_present"] = cpir_present
    if cpir_present and not result["checks"]["ctpi_posterior_entrypoint"]:
        result["warnings"].append(
            "LEGACY_CPIR_PRESENT_WITHOUT_CTPI_V04_RUNTIME; do not relabel CPIR as CTPI V0.4"
        )

    binary = Path(args.binary).expanduser().resolve() if args.binary else None
    if binary is not None:
        result["binary"] = str(binary)
        result["checks"]["binary_present"] = binary.is_file()
        if binary.is_file():
            result["binary_sha256"] = sha256(binary)
            blob = binary.read_bytes()
            for key, marker in (
                ("binary_runtime_contract_marker", RUNTIME_MARKER),
                ("binary_runtime_mode", RUNTIME_MODE),
                ("binary_posterior_entrypoint", POSTERIOR_MARKER),
                ("binary_aprs_ownership_marker", APRS_OWNERSHIP_MARKER),
                ("binary_psrg_boundary_marker", PSRG_BOUNDARY_MARKER),
                ("binary_planner_marker", PLANNER_MARKER),
            ):
                result["checks"][key] = marker.encode() in blob
        else:
            for key in (
                "binary_runtime_contract_marker",
                "binary_runtime_mode",
                "binary_posterior_entrypoint",
                "binary_aprs_ownership_marker",
                "binary_psrg_boundary_marker",
                "binary_planner_marker",
            ):
                result["checks"][key] = False

    blocking_keys = [
        "required_files_present",
        "explicit_ctpi_v04_mode",
        "runtime_contract_marker",
        "ctpi_posterior_entrypoint",
        "aprs_current_observation_ownership",
        "psrg_telemetry_only_boundary",
        "planner_consumes_ctpi_posterior",
        "ctpi_not_aliased_to_legacy_tadm",
    ]
    if binary is not None:
        blocking_keys += [
            "binary_present",
            "binary_runtime_contract_marker",
            "binary_runtime_mode",
            "binary_posterior_entrypoint",
            "binary_aprs_ownership_marker",
            "binary_psrg_boundary_marker",
            "binary_planner_marker",
        ]

    passed = all(bool(result["checks"].get(k)) for k in blocking_keys)
    result["verdict"] = (
        "CTPI_V04_RUNTIME_PARITY_PASS" if passed else "BLOCKED_BY_RUNTIME_PARITY"
    )

    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        out = Path(args.json_out).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload, encoding="utf-8")
    sys.stdout.write(payload)
    return 0 if passed else 42


if __name__ == "__main__":
    raise SystemExit(main())
