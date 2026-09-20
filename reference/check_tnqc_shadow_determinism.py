#!/usr/bin/env python3
"""Determinism audit for TNQC OFF versus SHADOW closed-loop runs.

SHADOW is allowed to compute diagnostics only.  It must not change the native
PMFS trajectory, measurement field, candidate simulations, posterior, or final
localization result.  Wall-clock columns and run UUID/path strings are ignored.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path
from typing import Dict, Iterable, Sequence, Tuple


def read_rows(path: Path):
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def close(a: float, b: float, atol: float, rtol: float) -> bool:
    return abs(a-b) <= atol + rtol * max(abs(a), abs(b))


def compare_numeric_records(a, b, key_fields: Sequence[str],
                            fields: Sequence[str], atol=1e-12, rtol=1e-10):
    def keyed(rows):
        out = {}
        for r in rows:
            k = tuple(r[x] for x in key_fields)
            if k in out:
                raise ValueError(f"duplicate key {k}")
            out[k] = r
        return out
    aa, bb = keyed(a), keyed(b)
    missing_a = sorted(set(bb)-set(aa))
    missing_b = sorted(set(aa)-set(bb))
    max_abs = 0.0
    mismatches = []
    for k in sorted(set(aa) & set(bb)):
        for f in fields:
            x, y = float(aa[k][f]), float(bb[k][f])
            max_abs = max(max_abs, abs(x-y))
            if not close(x, y, atol, rtol):
                mismatches.append({"key": k, "field": f, "off": x, "shadow": y})
                if len(mismatches) >= 20:
                    break
        if len(mismatches) >= 20:
            break
    return {
        "pass": not missing_a and not missing_b and not mismatches,
        "off_count": len(aa), "shadow_count": len(bb),
        "missing_in_off": missing_a[:20], "missing_in_shadow": missing_b[:20],
        "max_abs_difference": max_abs, "mismatches": mismatches,
    }


def timing_audit(off_bank: Path, shadow_bank: Path):
    fields = [
        "sim_time", "time_since_previous_update",
        "native_candidate_count", "native_forward_simulation_count",
        "robot_x", "robot_y", "robot_z", "robot_yaw",
        "grid_width", "grid_height", "cell_size", "origin_x", "origin_y",
    ]
    return compare_numeric_records(
        read_rows(off_bank/"source_update_timing.csv"),
        read_rows(shadow_bank/"source_update_timing.csv"),
        ["source_update_id"], fields, atol=1e-10, rtol=1e-10)


def final_update(bank: Path, budget: float):
    eligible=[]
    for r in read_rows(bank/"source_update_timing.csv"):
        t=float(r["sim_time"]); u=int(r["source_update_id"])
        if t <= budget+1e-9:
            eligible.append((t,u))
    if not eligible:
        raise ValueError("no update within budget")
    return max(eligible, key=lambda z:(z[0],z[1]))


def final_result(path: Path):
    pat=re.compile(r"RESULT IS: Success=([^,]+), Search_t=([0-9.eE+-]+), Error=([0-9.eE+-]+)")
    found=None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m=pat.search(line)
        if m:
            found={"success":m.group(1).strip(),"search_t":float(m.group(2)),
                   "error_m":float(m.group(3))}
    if found is None:
        raise ValueError(f"missing RESULT IS line in {path}")
    return found


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--off-dir", type=Path, required=True)
    ap.add_argument("--shadow-dir", type=Path, required=True)
    ap.add_argument("--budget-s", type=float, default=300.0)
    ap.add_argument("--json-out", type=Path)
    args=ap.parse_args()

    ob=args.off_dir/"context_bank"; sb=args.shadow_dir/"context_bank"
    ot=timing_audit(ob,sb)
    ou=final_update(ob,args.budget_s); su=final_update(sb,args.budget_s)
    same_final_update = ou == su
    od=ob/f"source_update_{ou[1]:04d}"
    sd=sb/f"source_update_{su[1]:04d}"

    measured_fields=["probability","logOdds","confidence","omega","distanceFromRobot",
                     "originalPropagationDirection_x","originalPropagationDirection_y"]
    measured=compare_numeric_records(
        read_rows(od/"measured_hit_probability.csv"),
        read_rows(sd/"measured_hit_probability.csv"),
        ["cell_index"], measured_fields, atol=1e-12, rtol=1e-10)

    posterior=compare_numeric_records(
        read_rows(od/"source_posterior.csv"),
        read_rows(sd/"source_posterior.csv"),
        ["cell_index"], ["x","y","source_probability"], atol=1e-12, rtol=1e-10)

    manifest_fields=["origin_i","origin_j","size_i","size_j","center_x","center_y",
                     "native_source_x","native_source_y","native_score"]
    manifest=compare_numeric_records(
        read_rows(od/"candidate_manifest.csv"),
        read_rows(sd/"candidate_manifest.csv"),
        ["candidate_id"], manifest_fields, atol=1e-12, rtol=1e-10)

    alignment=compare_numeric_records(
        read_rows(od/"candidate_support_alignment.csv"),
        read_rows(sd/"candidate_support_alignment.csv"),
        ["candidate_id","cell_index"],
        ["grid_i","grid_j","x","y","measured_probability","measured_confidence",
         "simulated_hit_probability","absolute_residual"],
        atol=1e-12, rtol=1e-10)

    off_result=final_result(args.off_dir/"launch.log")
    shadow_result=final_result(args.shadow_dir/"launch.log")
    result_pass=(off_result["success"]==shadow_result["success"] and
                 close(off_result["error_m"],shadow_result["error_m"],1e-9,0.0) and
                 close(off_result["search_t"],shadow_result["search_t"],1e-6,0.0))

    audits={
        "timing_scientific_columns":ot,
        "same_final_update":same_final_update,
        "measured_field":measured,
        "native_posterior":posterior,
        "candidate_manifest":manifest,
        "candidate_support_alignment":alignment,
        "final_result":{"pass":result_pass,"off":off_result,"shadow":shadow_result},
    }
    passed=all(
        v if isinstance(v,bool) else bool(v.get("pass",False))
        for v in audits.values()
    )
    payload={
        "contract":"TNQC_OFF_SHADOW_DETERMINISM_V1",
        "off_dir":str(args.off_dir),"shadow_dir":str(args.shadow_dir),
        "budget_s":args.budget_s,"audits":audits,"pass":passed,
        "verdict":"TNQC_SHADOW_DETERMINISM_PASS" if passed else "TNQC_SHADOW_DETERMINISM_FAIL",
    }
    text=json.dumps(payload,indent=2,sort_keys=True)
    print(text)
    out=args.json_out or args.shadow_dir/"tnqc_shadow_determinism.json"
    out.write_text(text+"\n",encoding="utf-8")
    if not passed:
        raise SystemExit(4)


if __name__=="__main__":
    main()
