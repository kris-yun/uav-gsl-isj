#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

HOUSES = ("H01", "H02", "H03")
ARMS = ("A0", "F00", "F01")
TRACE_FILES = ("sensor_trace.csv", "sim_pose_trace.csv", "wind_trace.csv")
DEFAULT_BANK_ROOT = Path("/mnt/hgfs/workspace/CPIR_M1_FULLGRID_LOOKUP_20260831_R1")
DEFAULT_PLACEMENT = Path("/home/zyc/PF_DEI_V3_REGION_SUPPORT_20260828/frozen_region_placement_manifest.json")
DEFAULT_SEARCH_ROOTS = (Path("/mnt/hgfs/workspace"), Path("/home/zyc"))


def valid_spent_root(root: Path) -> tuple[bool, list[str]]:
    missing: list[str] = []
    for house in HOUSES:
        for arm in ARMS:
            run = root / f"{house}_seed12_{arm}"
            for name in TRACE_FILES:
                path = run / name
                if not path.is_file():
                    missing.append(str(path))
    return not missing, missing


def discover_spent_roots(search_roots: list[Path], max_depth: int = 6) -> list[Path]:
    # Deliberately bounded search. We only accept a parent containing the exact
    # nine frozen seed12 arm directories and their three required trace files.
    found: list[Path] = []
    target = "H01_seed12_A0"
    for base in search_roots:
        if not base.is_dir():
            continue
        base_depth = len(base.resolve().parts)
        for path in base.rglob(target):
            try:
                depth = len(path.resolve().parts) - base_depth
            except OSError:
                continue
            if depth > max_depth or not path.is_dir():
                continue
            parent = path.parent
            ok, _ = valid_spent_root(parent)
            if ok and parent not in found:
                found.append(parent)
    return sorted(found)


def bank_status(bank_root: Path) -> dict:
    houses = {}
    complete = True
    for house in HOUSES:
        root = bank_root / house
        required = [
            root / "bank_summary.json",
            root / "cell_manifest.csv",
            root / "FILE_SHA256.tsv",
            root / "worlds" / "member_00",
            root / "worlds" / "member_07",
        ]
        missing = [str(p) for p in required if not p.exists()]
        if (root / "IN_PROGRESS").exists():
            missing.append(str(root / "IN_PROGRESS") + ":MUST_NOT_EXIST")
        houses[house] = {"root": str(root), "ready_for_integrity_verifier": not missing, "missing": missing}
        complete = complete and not missing
    return {"root": str(bank_root), "all_houses_present": complete, "houses": houses}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spent-root", type=Path)
    ap.add_argument("--bank-root", type=Path, default=DEFAULT_BANK_ROOT)
    ap.add_argument("--placement-manifest", type=Path, default=DEFAULT_PLACEMENT)
    ap.add_argument("--search-root", type=Path, action="append")
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    candidates: list[Path] = []
    if args.spent_root:
        candidates.append(args.spent_root)
    else:
        candidates.extend(discover_spent_roots(args.search_root or list(DEFAULT_SEARCH_ROOTS)))

    spent = []
    for root in candidates:
        ok, missing = valid_spent_root(root)
        spent.append({"root": str(root), "complete": ok, "missing": missing})

    report = {
        "contract": "CSTAR_VM_ASSET_PREFLIGHT_V1",
        "spent_candidates": spent,
        "selected_spent_root": next((r["root"] for r in spent if r["complete"]), None),
        "bank": bank_status(args.bank_root),
        "placement_manifest": {
            "path": str(args.placement_manifest),
            "present": args.placement_manifest.is_file(),
        },
    }
    report["m1_m2_assets_ready"] = report["selected_spent_root"] is not None
    report["m3_bank_assets_ready"] = bool(report["bank"]["all_houses_present"] and report["placement_manifest"]["present"])
    report["verdict"] = (
        "CSTAR_VM_ASSETS_READY"
        if report["m1_m2_assets_ready"] and report["m3_bank_assets_ready"]
        else "CSTAR_VM_ASSETS_INCOMPLETE"
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(report["verdict"])
    return 0 if report["verdict"] == "CSTAR_VM_ASSETS_READY" else 3


if __name__ == "__main__":
    raise SystemExit(main())
