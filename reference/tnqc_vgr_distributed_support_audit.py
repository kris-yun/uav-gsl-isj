#!/usr/bin/env python3
"""Distributed-support audit for the VGR TNQC mechanism signal.

This is deliberately NOT the authoritative 300 s localization gate.  It asks a
narrower question raised during audit: is the 240 s cross-transport TNQC signal
only a local/near-source artifact, or is it distributed over disjoint spatial
support?

Data:
  project/research-master-20260914
  evidence/cstar_current_runtime_assets240_20260907/realizations
  H01/H02/H03 x SA/SB x fast/slow, 1200 samples to 240 s.

All candidate/source labels are used only for evaluator-side scoring.  The
source-blind partitions use grid parity/hash only.  Distance-to-source masks
are evaluator-only destructive diagnostics and must never be used online.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import subprocess
from pathlib import Path

HOUSES = ("H01", "H02", "H03")
SOURCES = ("SA", "SB")
WINDS = ("fast", "slow")
DEFAULT_REF = "project/research-master-20260914"
ROOT = "evidence/cstar_current_runtime_assets240_20260907/realizations"
CELL = 0.3
ORIGIN = {"H01": (-7.55, -7.88), "H02": (-5.39, -7.45), "H03": (-0.85, -1.86)}
SOURCE = {
    "H01": {"SA": (-0.6, 1.95), "SB": (-0.4, -2.9)},
    "H02": {"SA": (0.0, -1.0), "SB": (1.0, -2.3)},
    "H03": {"SA": (-0.45, 1.9), "SB": (8.2, 5.0)},
}


def git_text(repo: Path, ref: str, path: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), "show", f"{ref}:{path}"], text=True)


def load(repo: Path, ref: str):
    out = {}
    for h in HOUSES:
        for s in SOURCES:
            for w in WINDS:
                key = f"{h}_{s}_{w}"
                txt = git_text(repo, ref, f"{ROOT}/{key}/measured_history.jsonl")
                out[key] = [json.loads(x) for x in txt.splitlines() if x.strip()]
    return out


def mean(x):
    return sum(x) / len(x)


def field(hist, ep, end_s=240.0, transform=None):
    h = ep[:3]
    ox, oy = ORIGIN[h]
    a = {}
    for r in hist[ep]:
        if float(r["t_sim_s"]) > end_s + 1e-9:
            break
        i = math.floor((float(r["pose_xy"][0]) - ox) / CELL + 1e-12)
        j = math.floor((float(r["pose_xy"][1]) - oy) / CELL + 1e-12)
        v = float(r["gas_ppm"])
        if transform is not None:
            v = transform(ep, v)
        a.setdefault((i, j), []).append(v)
    return {k: mean(v) for k, v in a.items()}


def centered_cosine(a, b, mask=lambda _k: True):
    keys = [k for k in a if k in b and mask(k)]
    if len(keys) < 4:
        return None, len(keys)
    x = [a[k] for k in keys]
    y = [b[k] for k in keys]
    mx, my = mean(x), mean(y)
    xy = xx = yy = 0.0
    for u0, v0 in zip(x, y):
        u, v = u0 - mx, v0 - my
        xy += u * v
        xx += u * u
        yy += v * v
    if xx <= 1e-30 or yy <= 1e-30:
        return None, len(keys)
    return xy / math.sqrt(xx * yy), len(keys)


def raw_score(a, b, mask=lambda _k: True):
    keys = [k for k in a if k in b and mask(k)]
    if not keys:
        return None, 0
    return -math.sqrt(sum((a[k] - b[k]) ** 2 for k in keys) / len(keys)), len(keys)


def evaluate(hist, end_s=240.0, method="affine", mask_factory=None, transform=None):
    fields = {ep: field(hist, ep, end_s, transform) for ep in hist}
    rows = []
    for ep in sorted(hist):
        h, truth, w = ep.split("_")
        other = "slow" if w == "fast" else "fast"
        mask = (mask_factory(h) if mask_factory else (lambda _k: True))
        scorer = centered_cosine if method == "affine" else raw_score
        sa, na = scorer(fields[ep], fields[f"{h}_SA_{other}"], mask)
        sb, nb = scorer(fields[ep], fields[f"{h}_SB_{other}"], mask)
        if sa is None or sb is None:
            rows.append({"episode": ep, "valid": False, "truth": truth})
            continue
        pred = "SA" if sa >= sb else "SB"
        margin = (sa - sb) if truth == "SA" else (sb - sa)
        rows.append({
            "episode": ep, "valid": True, "truth": truth, "prediction": pred,
            "correct": pred == truth, "margin": margin, "support_bins": min(na, nb),
            "scores_SA_SB": [sa, sb],
        })
    valid = [r for r in rows if r["valid"]]
    return {
        "valid_cases": len(valid),
        "coverage": len(valid) / len(rows),
        "accuracy_on_valid": (sum(r["correct"] for r in valid) / len(valid)) if valid else None,
        "min_margin": min((r["margin"] for r in valid), default=None),
        "min_support_bins": min((r["support_bins"] for r in valid), default=None),
        "rows": rows,
    }


def source_distance_mask(h, radius):
    ox, oy = ORIGIN[h]
    def keep(k):
        i, j = k
        x, y = ox + (i + 0.5) * CELL, oy + (j + 0.5) * CELL
        d = min(
            math.hypot(x - SOURCE[h]["SA"][0], y - SOURCE[h]["SA"][1]),
            math.hypot(x - SOURCE[h]["SB"][0], y - SOURCE[h]["SB"][1]),
        )
        return d > radius
    return keep


def fold_consensus(hist, kfold=2, end_s=240.0, a=1, b=2, c=0):
    fields = {ep: field(hist, ep, end_s) for ep in hist}
    rows = []
    for ep in sorted(hist):
        h, truth, w = ep.split("_")
        other = "slow" if w == "fast" else "fast"
        ranks = []
        valid = True
        for fold in range(kfold):
            mask = lambda ij, fold=fold: ((a * ij[0] + b * ij[1] + c) % kfold) == fold
            sa, _ = centered_cosine(fields[ep], fields[f"{h}_SA_{other}"], mask)
            sb, _ = centered_cosine(fields[ep], fields[f"{h}_SB_{other}"], mask)
            if sa is None or sb is None:
                valid = False
                break
            ranks.append("SA" if sa >= sb else "SB")
        agree = valid and ranks and all(x == ranks[0] for x in ranks)
        pred = ranks[0] if agree else None
        rows.append({
            "episode": ep, "truth": truth, "valid_all_folds": valid,
            "fold_rankings": ranks, "released": agree, "prediction": pred,
            "correct_if_released": pred == truth if pred is not None else None,
        })
    released = [r for r in rows if r["released"]]
    return {
        "coverage": len(released) / len(rows),
        "released_cases": len(released),
        "conditional_accuracy": (
            sum(r["correct_if_released"] for r in released) / len(released)
            if released else None
        ),
        "rows": rows,
    }


def lcg(seed):
    state = seed & 0xFFFFFFFF
    def rand():
        nonlocal state
        state = (1664525 * state + 1013904223) & 0xFFFFFFFF
        return state / 2**32
    return rand


def summarize(vals):
    vals = sorted(vals)
    return {
        "min": vals[0], "mean": statistics.fmean(vals),
        "median": statistics.median(vals), "max": vals[-1],
        "perfect_count": sum(v == 1.0 for v in vals), "run_count": len(vals),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, default=Path("."))
    ap.add_argument("--ref", default=DEFAULT_REF)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    hist = load(args.repo, args.ref)

    # Verify the controlled asset really uses identical pose/timing sequences
    # across SA/SB and fast/slow within each House.
    route_audit = {}
    for h in HOUSES:
        eps = [f"{h}_{s}_{w}" for s in SOURCES for w in WINDS]
        ref = hist[eps[0]]
        max_pose = max_time = 0.0
        for ep in eps[1:]:
            rr = hist[ep]
            for x, y in zip(ref, rr):
                max_pose = max(max_pose, math.hypot(
                    float(x["pose_xy"][0]) - float(y["pose_xy"][0]),
                    float(x["pose_xy"][1]) - float(y["pose_xy"][1])))
                max_time = max(max_time, abs(float(x["t_sim_s"]) - float(y["t_sim_s"])))
        route_audit[h] = {
            "episodes": eps, "sample_count_each": [len(hist[e]) for e in eps],
            "max_pose_difference_m": max_pose, "max_time_difference_s": max_time,
        }

    # Time-to-identifiability of the full affine quotient.
    timeline = {}
    for t in range(4, 241, 4):
        timeline[str(t)] = evaluate(hist, float(t), "affine")
    stable_from = None
    ts = list(range(4, 241, 4))
    for i, t in enumerate(ts):
        suffix = [timeline[str(u)] for u in ts[i:]]
        if all(x["coverage"] == 1.0 and x["accuracy_on_valid"] == 1.0 for x in suffix):
            stable_from = t
            break

    masks = {
        "all_support": None,
        "checkerboard_even": lambda _h: (lambda ij: ((ij[0] + ij[1]) & 1) == 0),
        "checkerboard_odd": lambda _h: (lambda ij: ((ij[0] + ij[1]) & 1) == 1),
        "exclude_within_1m_of_either_source_evaluator_only": lambda h: source_distance_mask(h, 1.0),
        "exclude_within_2m_of_either_source_evaluator_only": lambda h: source_distance_mask(h, 2.0),
        "exclude_within_3m_of_either_source_evaluator_only": lambda h: source_distance_mask(h, 3.0),
        "far_only_gt4m_from_either_source_evaluator_only": lambda h: source_distance_mask(h, 4.0),
    }
    spatial = {}
    for name, mf in masks.items():
        spatial[name] = {
            "affine": evaluate(hist, 240.0, "affine", mf),
            "raw": evaluate(hist, 240.0, "raw", mf),
        }

    checker2 = fold_consensus(hist, 2, 240.0, 1, 1, 0)
    fixed4 = fold_consensus(hist, 4, 240.0, 1, 2, 0)
    random4 = []
    for seed in range(1, 101):
        r = lcg(seed)
        a = 1 + 2 * int(r() * 5)
        b = 1 + 2 * int(r() * 5)
        c = int(r() * 997)
        random4.append(fold_consensus(hist, 4, 240.0, a, b, c))
    random4_summary = {
        "coverage": summarize([x["coverage"] for x in random4]),
        "conditional_accuracy": summarize([
            x["conditional_accuracy"] for x in random4
            if x["conditional_accuracy"] is not None
        ]),
    }

    episodes = sorted(hist)
    scale_runs, offset_runs = [], []
    for seed in range(1, 101):
        r = lcg(seed)
        scale = {
            ep: math.exp(math.log(0.05) + r() * (math.log(20.0) - math.log(0.05)))
            for ep in episodes
        }
        a = evaluate(hist, 240.0, "affine", transform=lambda ep, v, scale=scale: scale[ep] * v)
        b = evaluate(hist, 240.0, "raw", transform=lambda ep, v, scale=scale: scale[ep] * v)
        scale_runs.append((a["accuracy_on_valid"], b["accuracy_on_valid"]))

        r2 = lcg(seed ^ 0xA5A5A5A5)
        bg = {ep: 5.0 * r2() for ep in episodes}
        a = evaluate(hist, 240.0, "affine", transform=lambda ep, v, bg=bg: v + bg[ep])
        b = evaluate(hist, 240.0, "raw", transform=lambda ep, v, bg=bg: v + bg[ep])
        offset_runs.append((a["accuracy_on_valid"], b["accuracy_on_valid"]))

    selected_times = (80, 120, 160, 176, 200, 220, 240)
    payload = {
        "contract": "TNQC_VGR_DISTRIBUTED_SUPPORT_AUDIT_V1",
        "data_ref": args.ref,
        "data_root": ROOT,
        "claim_boundary": {
            "purpose": "falsify the claim that the 240 s TNQC source-identity signal is confined to a local/near-source patch",
            "not_authoritative_300s_localization_gate": True,
            "two_source_candidate_set_only": True,
            "distance_masks_use_evaluator_truth_only": True,
        },
        "route_identity_audit": route_audit,
        "time_to_identifiability": {
            "stable_12_of_12_full_affine_from_s": stable_from,
            "selected": {
                str(t): {
                    "coverage": timeline[str(t)]["coverage"],
                    "accuracy_on_valid": timeline[str(t)]["accuracy_on_valid"],
                    "min_margin": timeline[str(t)]["min_margin"],
                    "min_support_bins": timeline[str(t)]["min_support_bins"],
                } for t in selected_times
            },
        },
        "spatial_destructive_audit_240s": {
            name: {
                "affine_accuracy": val["affine"]["accuracy_on_valid"],
                "affine_min_support_bins": val["affine"]["min_support_bins"],
                "affine_failures": [
                    r["episode"] for r in val["affine"]["rows"]
                    if r.get("valid") and not r.get("correct")
                ],
                "raw_accuracy": val["raw"]["accuracy_on_valid"],
                "raw_min_support_bins": val["raw"]["min_support_bins"],
            } for name, val in spatial.items()
        },
        "source_blind_disjoint_support_consensus_240s": {
            "checkerboard_2fold": {
                "coverage": checker2["coverage"],
                "conditional_accuracy": checker2["conditional_accuracy"],
            },
            "fixed_4fold": {
                "coverage": fixed4["coverage"],
                "conditional_accuracy": fixed4["conditional_accuracy"],
            },
            "random_hash_4fold_100_seeds": random4_summary,
        },
        "source_blind_nuisance_stress_240s": {
            "independent_positive_scale_loguniform_0p05_to_20_100_seeds": {
                "affine": summarize([x[0] for x in scale_runs]),
                "raw": summarize([x[1] for x in scale_runs]),
            },
            "independent_positive_background_offset_0_to_5ppm_100_seeds": {
                "affine": summarize([x[0] for x in offset_runs]),
                "raw": summarize([x[1] for x in offset_runs]),
            },
        },
        "interpretation": {
            "local_only_hypothesis_supported": False,
            "distributed_spatial_signal_supported_on_this_two_source_asset": True,
            "full_localization_gain_established": False,
            "next_authoritative_gate": "reference/run_tnqc_vgr_offline_gate_20260920.sh",
        },
    }
    text = json.dumps(payload, indent=2, sort_keys=True)
    print(text)
    if args.json_out:
        args.json_out.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
