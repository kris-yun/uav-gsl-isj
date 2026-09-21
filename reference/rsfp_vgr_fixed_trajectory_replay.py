#!/usr/bin/env python3
"""RSFP fixed-trajectory 300-s replay.

Renormalization Source Fixed Point (RSFP) asks whether source-hypothesis
evidence survives a predeclared spatial coarse-graining flow.

This script deliberately reuses the frozen TNQC V7 data loaders, native PMFS
posterior reconstruction, final-leaf partition semantics, and linked-native C++
ExpectedValue(..., 0.05) endpoint evaluator.  It does NOT reuse TNQC's local
order gate or its frozen fusion equation.

Predeclared scales: 1, 2, 4, 8 fine-grid cells.

Variants evaluated without truth-dependent selection:
  fine_only      : factor-1 canonical score only
  coarse_only    : factor-8 canonical score only
  mean_only      : equal mean over all four scales
  lower_envelope_only : minimum candidate score over all four scales
  fixed_only     : scale-stable pairwise dominance score; a candidate pair
                   contributes only when its ordering has the same nonzero
                   sign at every predeclared scale
  *_tilt         : same bounded score added once to native candidate log score

The scientific primary is fixed_only.  fine/coarse/mean/lower-envelope are
required controls.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from pathlib import Path
from typing import Dict, Mapping, Sequence

from tnqc_vgr_fixed_trajectory_replay import (
    Cell,
    choose_final_update,
    cpp_endpoint_metrics,
    diff,
    exported_posterior,
    final_partition,
    load_alignment,
    load_candidates,
    load_cells,
    load_grid_metadata,
    metrics,
    native_log_score,
    native_result_line,
    posterior,
    safe_logit,
    write_endpoint_posterior,
)

DEFAULT_FACTORS = (1, 2, 4, 8)


def coarse_canonical_score(
        alignment,
        cells: Mapping[int, Cell],
        factor: int,
):
    """Positive-affine-invariant weighted cosine after block coarse graining."""
    if factor <= 0:
        raise ValueError("factor must be positive")

    blocks = {}
    support_count = 0
    for idx, triple in alignment.items():
        if idx not in cells:
            continue
        cell = cells[idx]
        if not (
            cell.confidence > 0.0
            and math.isfinite(cell.logodds)
            and math.isfinite(triple[2])
        ):
            continue
        support_count += 1
        key = (cell.grid_i // factor, cell.grid_j // factor)
        w = float(cell.confidence)
        rec = blocks.setdefault(
            key, {"w": 0.0, "obs": 0.0, "pred": 0.0}
        )
        rec["w"] += w
        rec["obs"] += w * float(cell.logodds)
        rec["pred"] += w * safe_logit(float(triple[2]))

    vals = []
    for rec in blocks.values():
        if rec["w"] <= 0.0:
            continue
        vals.append(
            (
                rec["w"],
                rec["obs"] / rec["w"],
                rec["pred"] / rec["w"],
            )
        )

    if len(vals) < 4:
        return {
            "valid": False,
            "factor": factor,
            "support_count": support_count,
            "coarse_block_count": len(vals),
            "canonical_cosine": 0.0,
        }

    sw = sum(w for w, _, _ in vals)
    mo = sum(w * o for w, o, _ in vals) / sw
    mp = sum(w * p for w, _, p in vals) / sw
    cross = no = np = 0.0
    for w, o, p in vals:
        xo, xp = o - mo, p - mp
        cross += w * xo * xp
        no += w * xo * xo
        np += w * xp * xp

    if not (no > 1e-18 and np > 1e-18):
        return {
            "valid": False,
            "factor": factor,
            "support_count": support_count,
            "coarse_block_count": len(vals),
            "canonical_cosine": 0.0,
        }

    q = max(-1.0, min(1.0, cross / math.sqrt(no * np)))
    return {
        "valid": True,
        "factor": factor,
        "support_count": support_count,
        "coarse_block_count": len(vals),
        "canonical_cosine": q,
    }


def candidate_multiscale(alignment, cells, factors: Sequence[int]):
    out = {}
    for factor in factors:
        out[int(factor)] = coarse_canonical_score(
            alignment, cells, int(factor)
        )
    return out


def bounded(x: float) -> float:
    return max(-1.0, min(1.0, float(x)))


def evidence_variants(ms, factors: Sequence[int]):
    factors = tuple(int(x) for x in factors)
    valid_all = all(ms[f]["valid"] for f in factors)
    q = {f: ms[f]["canonical_cosine"] for f in factors}

    fine = q[factors[0]] if ms[factors[0]]["valid"] else 0.0
    coarse = q[factors[-1]] if ms[factors[-1]]["valid"] else 0.0

    if valid_all:
        qs = [q[f] for f in factors]
        mean = statistics.fmean(qs)
        lower = min(qs)
        q_range = max(qs) - min(qs)
    else:
        mean = lower = 0.0
        q_range = None

    return {
        "valid_all_scales": valid_all,
        "fine_scalar": bounded(fine),
        "coarse_scalar": bounded(coarse),
        "mean_scalar": bounded(mean),
        "lower_envelope_scalar": bounded(lower),
        "scale_range": q_range,
        "per_scale": {str(f): ms[f] for f in factors},
    }


def pairwise_variant_scores(
        diag,
        active_ids,
        hypothesis_measure,
        factors: Sequence[int],
):
    """Compute all RSFP/control scores with identical pairwise semantics.

    Every active candidate pair has physical mass m_i*m_j.  The same reference
    pair mass is used for fine/coarse/mean/lower-envelope/fixed variants.

    Controls decide the pair using one scalar candidate statistic.
    RSFP fixed_only decides the pair only when q_i(f)-q_j(f) has the same
    nonzero sign at every frozen scale.  Crossings/ties abstain for the primary
    but remain in its denominator, so instability attenuates evidence.
    """
    factors = tuple(int(x) for x in factors)
    variant_scalar_key = {
        "fine_only": "fine_scalar",
        "coarse_only": "coarse_scalar",
        "mean_only": "mean_scalar",
        "lower_envelope_only": "lower_envelope_scalar",
    }
    variants = tuple(variant_scalar_key) + ("fixed_only",)
    signed = {
        key: {cid: 0.0 for cid in active_ids}
        for key in variants
    }
    reference = {cid: 0.0 for cid in active_ids}
    pair_count = {cid: 0 for cid in active_ids}
    fixed_stable_weight = {cid: 0.0 for cid in active_ids}
    fixed_stable_pairs = {cid: 0 for cid in active_ids}

    global_reference_weight = 0.0
    global_reference_pairs = 0
    global_fixed_stable_weight = 0.0
    global_fixed_stable_pairs = 0

    for i in range(len(active_ids)):
        for j in range(i + 1, len(active_ids)):
            a, b = active_ids[i], active_ids[j]
            da, db = diag[a], diag[b]
            if not (da["valid_all_scales"] and db["valid_all_scales"]):
                continue

            ma = float(hypothesis_measure[a])
            mb = float(hypothesis_measure[b])
            pair_weight = ma * mb
            for cid in (a, b):
                reference[cid] += pair_weight
                pair_count[cid] += 1
            global_reference_weight += pair_weight
            global_reference_pairs += 1

            # Required controls: identical pairwise map, different scalar.
            for key, scalar_key in variant_scalar_key.items():
                xa, xb = da[scalar_key], db[scalar_key]
                s = (xa > xb) - (xa < xb)
                if not s:
                    continue
                winner, loser = (a, b) if s > 0 else (b, a)
                signed[key][winner] += pair_weight
                signed[key][loser] -= pair_weight

            # Scientific primary: the pair is allowed to speak only if the
            # ordering has the same nonzero sign at every frozen scale.
            signs = []
            stable = True
            for factor in factors:
                qa = da["per_scale"][str(factor)]["canonical_cosine"]
                qb = db["per_scale"][str(factor)]["canonical_cosine"]
                s = (qa > qb) - (qa < qb)
                if not s:
                    stable = False
                    break
                signs.append(s)
            if stable and signs and all(s == signs[0] for s in signs[1:]):
                winner, loser = (a, b) if signs[0] > 0 else (b, a)
                signed["fixed_only"][winner] += pair_weight
                signed["fixed_only"][loser] -= pair_weight
                fixed_stable_weight[a] += pair_weight
                fixed_stable_weight[b] += pair_weight
                fixed_stable_pairs[a] += 1
                fixed_stable_pairs[b] += 1
                global_fixed_stable_weight += pair_weight
                global_fixed_stable_pairs += 1

    scores = {key: {} for key in variants}
    candidate_stats = {}
    for cid in active_ids:
        ref = reference[cid]
        candidate_stats[cid] = {
            "reference_weight": ref,
            "reference_pair_count": pair_count[cid],
            "fixed_stable_weight": fixed_stable_weight[cid],
            "fixed_stable_pair_count": fixed_stable_pairs[cid],
            "fixed_stable_weight_fraction":
                fixed_stable_weight[cid] / ref if ref > 0.0 else None,
        }
        for key in variants:
            score = signed[key][cid] / ref if ref > 0.0 else 0.0
            scores[key][cid] = bounded(score)
            candidate_stats[cid][f"{key}_score"] = scores[key][cid]

    return {
        "scores": scores,
        "candidate_stats": candidate_stats,
        "global_reference_pair_count": global_reference_pairs,
        "global_reference_weight": global_reference_weight,
        "global_fixed_stable_pair_count": global_fixed_stable_pairs,
        "global_fixed_stable_weight": global_fixed_stable_weight,
        "global_fixed_stable_weight_fraction": (
            global_fixed_stable_weight / global_reference_weight
            if global_reference_weight > 0.0 else None
        ),
    }

def scale_order_stability(diag, active_ids, factors: Sequence[int]):
    """Truth-blind bank-level pair ordering stability across adjacent scales."""
    factors = tuple(int(x) for x in factors)
    stable = total = 0
    per_transition = []

    for f0, f1 in zip(factors[:-1], factors[1:]):
        same = n = 0
        for i in range(len(active_ids)):
            for j in range(i + 1, len(active_ids)):
                a, b = active_ids[i], active_ids[j]
                da, db = diag[a], diag[b]
                if not (
                    da["valid_all_scales"] and db["valid_all_scales"]
                ):
                    continue
                x0 = da["per_scale"][str(f0)]["canonical_cosine"]
                y0 = db["per_scale"][str(f0)]["canonical_cosine"]
                x1 = da["per_scale"][str(f1)]["canonical_cosine"]
                y1 = db["per_scale"][str(f1)]["canonical_cosine"]
                s0 = (x0 > y0) - (x0 < y0)
                s1 = (x1 > y1) - (x1 < y1)
                if not s0 or not s1:
                    continue
                n += 1
                if s0 == s1:
                    same += 1
        total += n
        stable += same
        per_transition.append(
            {
                "from_factor": f0,
                "to_factor": f1,
                "pair_count": n,
                "stable_pair_count": same,
                "stable_fraction": same / n if n else None,
            }
        )

    return {
        "pair_transition_count": total,
        "stable_pair_transition_count": stable,
        "stable_fraction": stable / total if total else None,
        "per_transition": per_transition,
    }


def make_scores(native_s, diag, active_set, key, tilt: bool):
    scores = {}
    for cid, native in native_s.items():
        e = diag[cid][key] if cid in active_set else 0.0
        scores[cid] = native + e if tilt else e
    return scores


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", type=Path, required=True)
    ap.add_argument("--truth-x", type=float, required=True)
    ap.add_argument("--truth-y", type=float, required=True)
    ap.add_argument("--budget-s", type=float, default=300.0)
    ap.add_argument("--source-discrimination-power", type=float, default=1.0)
    ap.add_argument(
        "--factors",
        default="1,2,4,8",
        help="Predeclared comma-separated coarse factors; default 1,2,4,8",
    )
    ap.add_argument("--native-reconstruction-max-abs", type=float, default=5e-6)
    ap.add_argument("--native-reconstruction-l1", type=float, default=5e-4)
    ap.add_argument(
        "--native-endpoint-rounding-tolerance-m",
        type=float,
        default=0.011,
    )
    ap.add_argument("--cpp-endpoint-evaluator", type=Path, required=True)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()

    factors = tuple(int(x) for x in args.factors.split(",") if x.strip())
    if factors != DEFAULT_FACTORS:
        raise ValueError(
            f"RSFP V1 factors are frozen to {DEFAULT_FACTORS}, got {factors}"
        )

    bank = args.run_dir / "context_bank"
    uid, sim_time = choose_final_update(bank, args.budget_s)
    d = bank / f"source_update_{uid:04d}"
    grid_meta = load_grid_metadata(bank, uid)
    cells, _ = load_cells(d)
    candidates = load_candidates(d)
    alignment = load_alignment(d, cells)
    missing = sorted(set(candidates) - set(alignment))
    if missing:
        raise ValueError(
            f"{len(missing)} candidates missing alignment: {missing[:3]}"
        )
    part = final_partition(cells, candidates)

    native_s = {}
    diag = {}
    for cid in candidates:
        native_s[cid] = native_log_score(
            alignment[cid], args.source_discrimination_power
        )
        ms = candidate_multiscale(alignment[cid], cells, factors)
        diag[cid] = evidence_variants(ms, factors)

    active_ids = sorted(set(part.values()))
    active_set = set(active_ids)
    active_measure = {}
    for cid in part.values():
        active_measure[cid] = active_measure.get(cid, 0) + 1

    pairwise = pairwise_variant_scores(
        diag, active_ids, active_measure, factors
    )
    for cid in candidates:
        for key in (
            "fine_only",
            "coarse_only",
            "mean_only",
            "lower_envelope_only",
            "fixed_only",
        ):
            diag[cid][key] = (
                pairwise["scores"][key].get(cid, 0.0)
                if cid in active_set else 0.0
            )

    stability = scale_order_stability(diag, active_ids, factors)

    native_replay = posterior(part, native_s)
    native_export = exported_posterior(d)
    reconstruction = diff(native_replay, native_export)
    reconstruction_pass = (
        reconstruction["max_abs"] <= args.native_reconstruction_max_abs
        and reconstruction["l1"] <= args.native_reconstruction_l1
    )

    variants = {}
    for key in (
        "fine_only",
        "coarse_only",
        "mean_only",
        "lower_envelope_only",
        "fixed_only",
    ):
        only_scores = make_scores(native_s, diag, active_set, key, tilt=False)
        tilt_scores = make_scores(native_s, diag, active_set, key, tilt=True)
        variants[key] = {
            "only_posterior": posterior(part, only_scores),
            "tilt_posterior": posterior(part, tilt_scores),
        }

    evaluator = args.cpp_endpoint_evaluator.resolve()
    if not evaluator.is_file():
        raise FileNotFoundError(evaluator)

    endpoint_dir = args.run_dir / "rsfp_endpoint_posteriors"
    endpoint_dir.mkdir(parents=True, exist_ok=True)
    native_csv = endpoint_dir / "native_exported.csv"
    write_endpoint_posterior(native_csv, native_export, cells)

    nm_py = metrics(native_export, cells, args.truth_x, args.truth_y)
    nm_cpp = cpp_endpoint_metrics(
        evaluator, native_csv, args.truth_x, args.truth_y, grid_meta
    )
    nm = {**nm_py, **nm_cpp}

    variant_metrics = {}
    for key, val in variants.items():
        variant_metrics[key] = {}
        for mode in ("only", "tilt"):
            p = val[f"{mode}_posterior"]
            path = endpoint_dir / f"{key}_{mode}.csv"
            write_endpoint_posterior(path, p, cells)
            py = metrics(p, cells, args.truth_x, args.truth_y)
            cpp = cpp_endpoint_metrics(
                evaluator, path, args.truth_x, args.truth_y, grid_meta
            )
            variant_metrics[key][mode] = {
                **py,
                **cpp,
                "posterior_csv": str(path),
                "improvement_fraction_vs_native": (
                    nm["pmfs_top5_error_m"] - cpp["pmfs_top5_error_m"]
                ) / max(nm["pmfs_top5_error_m"], 1e-12),
            }

    native_cpp = native_result_line(args.run_dir)
    endpoint_delta = abs(
        nm_cpp["pmfs_top5_error_m"] - native_cpp["reported_top5_error_m"]
    )
    endpoint_pass = (
        endpoint_delta <= args.native_endpoint_rounding_tolerance_m
    )
    endpoint_engine_pass = (
        nm_cpp["engine"] == "gsl_utils_expected_value_linked_native_v1"
        and all(
            variant_metrics[key][mode]["engine"]
            == "gsl_utils_expected_value_linked_native_v1"
            for key in variant_metrics
            for mode in ("only", "tilt")
        )
    )

    all_scale_valid_active = sum(
        bool(diag[cid]["valid_all_scales"]) for cid in active_ids
    )

    payload = {
        "contract": "RSFP_VGR_FIXED_TRAJECTORY_300S_REPLAY_V1",
        "method": "RENORMALIZATION_SOURCE_FIXED_POINT_V1",
        "run_dir": str(args.run_dir),
        "budget_s": args.budget_s,
        "selected_source_update_id": uid,
        "selected_source_update_sim_time": sim_time,
        "budget_to_last_update_gap_s": args.budget_s - sim_time,
        "truth": [args.truth_x, args.truth_y],
        "factors": list(factors),
        "scale_semantics": {
            "fine_grid_cell_size_m": grid_meta.cell_size,
            "effective_cell_sizes_m": [
                grid_meta.cell_size * f for f in factors
            ],
            "common_output_semantics":
                "all variants use the same final-partition-measure-weighted "
                "signed pairwise dominance score in [-1,1]",
            "fixed_point_score":
                "a candidate pair contributes only when its ordering has "
                "the same nonzero sign at every predeclared scale; crossing "
                "or tied pairs abstain but remain in the reference mass",
            "lower_envelope_control":
                "pairwise ranking of each candidate's minimum canonical "
                "cosine across scales",
            "mean_control":
                "pairwise ranking of equal-mean canonical cosine",
            "coarse_control":
                "pairwise ranking of factor-8 canonical cosine",
            "fine_control":
                "pairwise ranking of factor-1 canonical cosine",
        },
        "free_cell_count": len(cells),
        "candidate_count": len(candidates),
        "final_leaf_candidate_count": len(active_ids),
        "active_all_scale_valid_candidate_count": all_scale_valid_active,
        "final_leaf_hypothesis_measure_cells": active_measure,
        "scale_order_stability": stability,
        "pairwise_variant_evidence": pairwise,
        "candidate_diagnostics": {
            cid: diag[cid] for cid in active_ids
        },
        "native_reconstruction_audit": {
            **reconstruction,
            "max_abs_threshold": args.native_reconstruction_max_abs,
            "l1_threshold": args.native_reconstruction_l1,
            "pass": reconstruction_pass,
        },
        "native_cpp_endpoint_audit": {
            "cpp_result": native_cpp,
            "linked_native_top5_error_m": nm_cpp["pmfs_top5_error_m"],
            "absolute_error_difference_m": endpoint_delta,
            "rounding_tolerance_m":
                args.native_endpoint_rounding_tolerance_m,
            "pass": endpoint_pass,
        },
        "endpoint_evaluator": {
            "engine": nm_cpp["engine"],
            "engine_integrity_pass": endpoint_engine_pass,
            "binary": str(evaluator),
            "sha256": hashlib.sha256(evaluator.read_bytes()).hexdigest(),
        },
        "native_exported": nm,
        "variants": variant_metrics,
        "primary_variant": "fixed_only/only",
        "primary_metrics": variant_metrics["fixed_only"]["only"],
        "valid_for_gate":
            reconstruction_pass and endpoint_pass and endpoint_engine_pass,
        "gate_validity_requires": [
            "native_posterior_reconstruction",
            "linked_native_GSL_Utils_ExpectedValue_matches_native_pmfs",
            "same_linked_native_endpoint_binary_for_all_counterfactuals",
            "frozen_scales_1_2_4_8",
            "truth_not_used_before_endpoint_evaluation",
        ],
    }

    text = json.dumps(payload, indent=2, sort_keys=True)
    print(text)
    out = args.json_out or args.run_dir / "rsfp_fixed_trajectory_evaluation.json"
    out.write_text(text + "\n", encoding="utf-8")
    if not payload["valid_for_gate"]:
        raise SystemExit(3)


if __name__ == "__main__":
    main()
