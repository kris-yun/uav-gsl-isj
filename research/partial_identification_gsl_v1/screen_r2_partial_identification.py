#!/usr/bin/env python3
"""R2 partial-identification diagnostic for frozen PMFS/TNQC context banks.

Scientific object
-----------------
For each source candidate s and each common supported free cell i,

    r_i(s) = confidence_i * |measured_probability_i - simulated_probability_i|.

Assume an additive, cellwise-bounded forward-model discrepancy with radius rho.
The minimal discrepancy radius required to make candidate s non-rejectable is

    rho_star(s) = max_i r_i(s).

Thus the identified candidate set at a predeclared radius rho is

    I_rho = {s : rho_star(s) <= rho}.

This is a genuine feasibility/partial-identification object, not a posterior
temperature.  Duplicating support rows cannot strengthen evidence and deleting
observations can only weakly enlarge I_rho.

The script is source-blind.  It does not use source truth and never chooses a
radius from endpoint outcomes.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

DEFAULT_RADII = (0.01, 0.02, 0.05, 0.10, 0.15, 0.20, 0.30, 0.50, 1.00)


def read_rows(path: Path) -> List[dict]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def discover_context_banks(root: Path) -> List[Path]:
    out = []
    for p in root.rglob("source_update_timing.csv"):
        if p.parent.name == "context_bank":
            out.append(p.parent)
    return sorted(set(out))


def choose_final_update(bank: Path, budget: float) -> Tuple[int, float]:
    eligible = []
    for r in read_rows(bank / "source_update_timing.csv"):
        t = float(r["sim_time"])
        u = int(r["source_update_id"])
        if t <= budget + 1e-9:
            eligible.append((t, u))
    if not eligible:
        raise ValueError(f"{bank}: no source update <= {budget}s")
    t, u = max(eligible, key=lambda z: (z[0], z[1]))
    return u, t


def find_update_dir(bank: Path, update_id: int) -> Path:
    candidates = [
        bank / f"source_update_{update_id:04d}",
        bank / f"source_update_{update_id}",
    ]
    for d in candidates:
        if d.is_dir():
            return d
    for d in bank.glob("source_update_*"):
        try:
            if int(d.name.rsplit("_", 1)[-1]) == update_id:
                return d
        except ValueError:
            pass
    raise FileNotFoundError(f"{bank}: source-update directory {update_id}")


def load_manifest(d: Path) -> Dict[str, dict]:
    rows = read_rows(d / "candidate_manifest.csv")
    out = {}
    for r in rows:
        cid = r["candidate_id"]
        if cid not in out:
            out[cid] = r
    if not out:
        raise ValueError(f"{d}: empty candidate manifest")
    return out


def load_alignment(d: Path) -> Dict[str, Dict[int, Tuple[float, float, float]]]:
    out: Dict[str, Dict[int, Tuple[float, float, float]]] = {}
    for r in read_rows(d / "candidate_support_alignment.csv"):
        cid = r["candidate_id"]
        idx = int(r["cell_index"])
        out.setdefault(cid, {})[idx] = (
            float(r["measured_probability"]),
            float(r["measured_confidence"]),
            float(r["simulated_hit_probability"]),
        )
    if not out:
        raise ValueError(f"{d}: empty candidate support alignment")
    return out


def load_posterior_summary(d: Path) -> dict:
    p = d / "source_posterior.csv"
    if not p.exists():
        return {}
    vals = []
    for r in read_rows(p):
        for key in ("source_probability", "probability"):
            if key in r and r[key] != "":
                vals.append(float(r[key]))
                break
    vals = [x for x in vals if math.isfinite(x) and x >= 0.0]
    s = sum(vals)
    if not vals or s <= 0:
        return {}
    vals = [x / s for x in vals]
    entropy = -sum(x * math.log(max(x, 1e-300)) for x in vals)
    ess = 1.0 / sum(x * x for x in vals)
    return {
        "posterior_cell_count": len(vals),
        "posterior_max_cell_probability": max(vals),
        "posterior_entropy_nats": entropy,
        "posterior_effective_cells": ess,
    }


def analyse_update(d: Path, radii: Iterable[float]) -> Tuple[dict, List[dict]]:
    manifest = load_manifest(d)
    alignment = load_alignment(d)

    cids = sorted(set(manifest) & set(alignment))
    if len(cids) < 2:
        raise ValueError(f"{d}: need >=2 candidates, got {len(cids)}")

    common = set(alignment[cids[0]])
    for cid in cids[1:]:
        common &= set(alignment[cid])
    if len(common) < 4:
        raise ValueError(f"{d}: common support too small: {len(common)}")

    detail = []
    for cid in cids:
        res = []
        unweighted = []
        for idx in common:
            m, conf, sim = alignment[cid][idx]
            if not all(map(math.isfinite, (m, conf, sim))):
                continue
            e = abs(m - sim)
            unweighted.append(e)
            res.append(max(0.0, min(1.0, conf)) * e)
        if len(res) < 4:
            continue
        r = manifest[cid]
        detail.append({
            "candidate_id": cid,
            "rho_star_inf": max(res),
            "mean_weighted_abs_residual": sum(res) / len(res),
            "mean_abs_residual": sum(unweighted) / len(unweighted),
            "support_count_common": len(res),
            "center_x": float(r["center_x"]),
            "center_y": float(r["center_y"]),
            "origin_i": int(r["origin_i"]),
            "origin_j": int(r["origin_j"]),
            "size_i": int(r["size_i"]),
            "size_j": int(r["size_j"]),
            "native_score": float(r["native_score"]),
        })

    if len(detail) < 2:
        raise ValueError(f"{d}: insufficient valid candidates")

    detail.sort(key=lambda z: (z["rho_star_inf"], z["candidate_id"]))
    best = detail[0]
    second = detail[1]

    native = max(detail, key=lambda z: (z["native_score"], z["candidate_id"]))

    curve = []
    for rho in radii:
        feasible = [x for x in detail if x["rho_star_inf"] <= rho + 1e-15]
        curve.append({
            "rho": rho,
            "identified_candidate_count": len(feasible),
            "identified_fraction": len(feasible) / len(detail),
            "identified_candidate_ids": [x["candidate_id"] for x in feasible],
        })

    summary = {
        "candidate_count": len(detail),
        "common_support_count": len(common),
        "robust_best_candidate_id": best["candidate_id"],
        "robust_best_rho_star": best["rho_star_inf"],
        "robust_second_candidate_id": second["candidate_id"],
        "robust_second_rho_star": second["rho_star_inf"],
        "robust_best_to_second_gap": second["rho_star_inf"] - best["rho_star_inf"],
        "native_best_candidate_id": native["candidate_id"],
        "native_best_rho_star": native["rho_star_inf"],
        "native_best_excess_rho_over_robust_best":
            native["rho_star_inf"] - best["rho_star_inf"],
        "native_and_robust_best_agree":
            native["candidate_id"] == best["candidate_id"],
        "identified_set_curve": curve,
    }
    summary.update(load_posterior_summary(d))
    return summary, detail


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("release_root", type=Path,
                    help="extracted TNQC R2 release root or any parent directory")
    ap.add_argument("--budget-s", type=float, default=300.0)
    ap.add_argument("--radii", type=float, nargs="*", default=list(DEFAULT_RADII))
    ap.add_argument("--out", type=Path, default=Path("partial_id_r2_screen.json"))
    args = ap.parse_args()

    banks = discover_context_banks(args.release_root)
    if not banks:
        raise SystemExit(f"no context_bank/source_update_timing.csv below {args.release_root}")

    result = {
        "contract": "PARTIAL_IDENTIFICATION_R2_ROBUSTNESS_RADIUS_V1",
        "budget_s": args.budget_s,
        "radii": args.radii,
        "radius_definition":
            "max over common support of confidence*abs(measured_probability-simulated_hit_probability)",
        "source_truth_used": False,
        "cases": [],
    }

    for bank in banks:
        u, t = choose_final_update(bank, args.budget_s)
        d = find_update_dir(bank, u)
        summary, detail = analyse_update(d, args.radii)
        case_name = bank.parent.name
        result["cases"].append({
            "case": case_name,
            "source_update_id": u,
            "source_update_time_s": t,
            "summary": summary,
            "candidates": detail,
        })

    result["case_count"] = len(result["cases"])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(json.dumps({
        "output": str(args.out),
        "case_count": result["case_count"],
        "cases": [
            {
                "case": c["case"],
                "native_and_robust_best_agree":
                    c["summary"]["native_and_robust_best_agree"],
                "robust_best_to_second_gap":
                    c["summary"]["robust_best_to_second_gap"],
                "native_best_excess_rho_over_robust_best":
                    c["summary"]["native_best_excess_rho_over_robust_best"],
            }
            for c in result["cases"]
        ],
    }, indent=2))


if __name__ == "__main__":
    main()
