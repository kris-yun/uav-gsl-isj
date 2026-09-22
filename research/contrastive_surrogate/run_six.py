#!/usr/bin/env python3
"""Run and aggregate the frozen six-case CSL V1 manifold screen."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


CASES = (
    "House01_seed0", "House01_seed1",
    "House02_seed0", "House02_seed1",
    "House03_seed0", "House03_seed1",
)


def run_case(repo: Path, responses_root: Path, out_root: Path, case: str) -> dict:
    design = repo / "evidence/active_deconfounding_v1/pre_response" / f"{case}.json"
    bank = responses_root / case
    out = out_root / f"{case}.json"
    cmd = [
        sys.executable,
        str(repo / "research/contrastive_surrogate/screen.py"),
        "--design", str(design),
        "--bank", str(bank),
        "--out", str(out),
    ]
    subprocess.run(cmd, check=True)
    return json.loads(out.read_text(encoding="utf-8"))


def weighted_mean(payloads, getter, weight_getter):
    num = den = 0.0
    for p in payloads:
        w = float(weight_getter(p))
        num += w * float(getter(p))
        den += w
    return num / den if den > 0 else float("nan")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path,
                    default=Path(__file__).resolve().parents[2])
    ap.add_argument("--responses-root", type=Path, required=True)
    ap.add_argument("--out-root", type=Path, required=True)
    args = ap.parse_args()

    args.out_root.mkdir(parents=True, exist_ok=True)
    payloads = [
        run_case(args.repo, args.responses_root, args.out_root, case)
        for case in CASES
    ]

    per_case = []
    for p in payloads:
        raw = p["raw_geometry"]
        csl = p["contrastive_proxy"]
        per_case.append({
            "case": p["case"],
            "status": p["status"],
            "pass": bool(p["go_for_next_offline_stage"]),
            "raw_top1": raw["unique_top1_weighted"],
            "csl_top1": csl["unique_top1_weighted"],
            "top1_gain": p["diagnostics"]["top1_gain"],
            "raw_error_m": raw["mean_xy_error_m_weighted"],
            "csl_error_m": csl["mean_xy_error_m_weighted"],
            "error_reduction_fraction":
                p["diagnostics"]["weighted_xy_error_reduction_fraction"],
            "shuffle_top1_gap": p["diagnostics"]["shuffle_top1_gap"],
        })

    # Each held-out generated source-world pair carries source physical measure.
    # Case banks differ in candidate partition size, so aggregate each case
    # equally rather than allowing one quadtree to dominate the six-case gate.
    pooled_raw_top1 = sum(x["raw_top1"] for x in per_case) / len(per_case)
    pooled_csl_top1 = sum(x["csl_top1"] for x in per_case) / len(per_case)
    pooled_top1_gain = pooled_csl_top1 - pooled_raw_top1
    pooled_raw_err = sum(x["raw_error_m"] for x in per_case) / len(per_case)
    pooled_csl_err = sum(x["csl_error_m"] for x in per_case) / len(per_case)
    pooled_err_reduction = (
        (pooled_raw_err - pooled_csl_err) / max(pooled_raw_err, 1e-12)
    )
    pooled_shuffle_gap = (
        sum(x["shuffle_top1_gap"] for x in per_case) / len(per_case)
    )

    passing = [x for x in per_case if x["pass"]]
    house_pass = {
        h: any(x["pass"] and x["case"].startswith(h) for x in per_case)
        for h in ("House01", "House02", "House03")
    }
    worst_case_top1_delta = min(x["top1_gain"] for x in per_case)

    criteria = {
        "at_least_5_of_6_case_gates": len(passing) >= 5,
        "all_houses_covered": all(house_pass.values()),
        "pooled_top1_gain_at_least_0p05": pooled_top1_gain >= 0.05,
        "pooled_error_reduction_at_least_0p10":
            pooled_err_reduction >= 0.10,
        "no_case_top1_loss_below_minus_0p05":
            worst_case_top1_delta >= -0.05,
        "pooled_shuffle_gap_at_least_0p20":
            pooled_shuffle_gap >= 0.20,
    }
    go = all(criteria.values())

    out = {
        "contract": "CSL_V1_SIX_CASE_AGGREGATE_GATE",
        "status": "GO_FOR_ACTUAL_OBSERVATION_OFFLINE_STAGE"
                  if go else "NO_GO_STAGE1",
        "cases": per_case,
        "passing_cases": len(passing),
        "house_coverage": house_pass,
        "pooled": {
            "raw_top1": pooled_raw_top1,
            "csl_top1": pooled_csl_top1,
            "top1_gain": pooled_top1_gain,
            "raw_error_m": pooled_raw_err,
            "csl_error_m": pooled_csl_err,
            "error_reduction_fraction": pooled_err_reduction,
            "shuffle_top1_gap": pooled_shuffle_gap,
            "worst_case_top1_delta": worst_case_top1_delta,
        },
        "criteria": criteria,
        "go_for_actual_observation_offline_stage": go,
        "closed_loop_authorized": False,
    }
    target = args.out_root / "FINAL_GATE.json"
    target.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
