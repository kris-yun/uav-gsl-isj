#!/usr/bin/env python3
"""CG-PC-CTT V15 completeness/identifiability gate.

This script is intentionally evaluation-only.  It leaves the frozen CTT M1
model and bank untouched and asks a narrower question:

    Does a truth-blind local source-separation spectrum, normalized by
    transport-member uncertainty, identify windows in which frozen M1 source
    ordering is reliable?

Thresholds are calibrated on development contexts only.  Final CTT test
contexts and held-out transport members are never used to tune thresholds.

The runtime object is the candidate x transport-member response ensemble.
Synthetic source indices are used only to score the offline qualification.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import pathlib
import sys

import numpy as np
import torch

HERE = pathlib.Path(__file__).resolve().parent
CTT_V13_DIR = HERE.parent / "ctt_v13"
if str(CTT_V13_DIR) not in sys.path:
    sys.path.insert(0, str(CTT_V13_DIR))

import ctt_m1_first_passage_gate as g1
import ctt_m1_ordering_gate as ordering


LOCAL_K = 9
FEATURE_TIME_CUTS = 12
SHRINKAGE = 0.10
MIN_DEV_COVERAGE = 0.20
MIN_TEST_COVERAGE = 0.10
MIN_DEV_ATOMS = 100
MIN_ACCEPTED_GAIN = 0.05
ALPHA_EXTRA_GAIN_TARGET = 0.02
EPS = 1e-10
CAL_QUANTILES = tuple(np.linspace(0.10, 0.90, 17))
SEED = 20260827


def _safe_moments(mask: np.ndarray, qxy: np.ndarray) -> np.ndarray:
    """Spatial moments of an arrival mask; zero when the mask is empty."""
    w = mask.astype(np.float64)
    mass = float(w.mean())
    count = float(w.sum())
    if count < 1.0:
        return np.array([mass, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float64)
    x = qxy[:, 0]
    y = qxy[:, 1]
    mx = float((w * x).sum() / count)
    my = float((w * y).sum() / count)
    dx = x - mx
    dy = y - my
    vx = float((w * dx * dx).sum() / count)
    vy = float((w * dy * dy).sum() / count)
    cxy = float((w * dx * dy).sum() / count)
    return np.array([mass, mx, my, math.sqrt(max(vx, 0.0)),
                     math.sqrt(max(vy, 0.0)), cxy], dtype=np.float64)


def build_response_features(hits_c: np.ndarray, query_xy: np.ndarray) -> np.ndarray:
    """Convert first-hit fields [source, query, member] to phi[source,member,d].

    The representation is deterministic and fixed before final test:
      * cumulative arrival mass + spatial moments at 12 time cuts;
      * finite-arrival time mean/std and four quantiles;
      * never-arrived fraction.

    It is deliberately low-dimensional so no 72x72/large singular covariance
    is inverted blindly.  Coordinates are normalized using query support only.
    """
    if hits_c.ndim != 3:
        raise ValueError(f"expected [S,Q,M], got {hits_c.shape}")
    s_count, q_count, m_count = hits_c.shape
    if len(query_xy) != q_count:
        raise ValueError("query support mismatch")

    center = query_xy.mean(axis=0, keepdims=True)
    scale = query_xy.std(axis=0, keepdims=True)
    scale[scale < 1e-6] = 1.0
    qxy = (query_xy - center) / scale

    cuts = np.linspace(0, g1.TIMESTEPS - 1, FEATURE_TIME_CUTS + 2, dtype=int)[1:-1]
    out = []
    for s in range(s_count):
        by_member = []
        for m in range(m_count):
            t = hits_c[s, :, m].astype(np.float64)
            feat = []
            for cut in cuts:
                feat.extend(_safe_moments(t <= cut, qxy))
            finite = t[t < g1.NEVER]
            if finite.size:
                norm = finite / float(g1.TIMESTEPS)
                feat.extend([
                    float(norm.mean()),
                    float(norm.std()),
                    *[float(x) for x in np.quantile(norm, [0.10, 0.25, 0.50, 0.75])],
                ])
            else:
                feat.extend([1.0, 0.0, 1.0, 1.0, 1.0, 1.0])
            feat.append(float((t >= g1.NEVER).mean()))
            by_member.append(feat)
        out.append(by_member)
    phi = np.asarray(out, dtype=np.float64)

    # Truth-free pooled standardization within one external context.
    flat = phi.reshape(-1, phi.shape[-1])
    mean = flat.mean(axis=0)
    std = flat.std(axis=0)
    keep = std > 1e-8
    if keep.sum() < LOCAL_K - 1:
        raise ValueError("response summary lost too many dimensions")
    phi = (phi[..., keep] - mean[keep]) / std[keep]
    return phi


def transport_covariance(phi: np.ndarray, members) -> tuple[np.ndarray, np.ndarray]:
    """Pooled within-candidate covariance and train-member candidate means."""
    members = tuple(int(x) for x in members)
    x = phi[:, members, :]
    mu = x.mean(axis=1)
    residual = x - mu[:, None, :]
    r = residual.reshape(-1, residual.shape[-1])
    cov = (r.T @ r) / max(1, len(r) - 1)
    scale = float(np.trace(cov) / cov.shape[0])
    if not scale > 0:
        scale = 1.0
    cov_reg = (1.0 - SHRINKAGE) * cov + SHRINKAGE * scale * np.eye(cov.shape[0])
    return cov_reg, mu


def inverse_sqrt_psd(cov: np.ndarray) -> np.ndarray:
    val, vec = np.linalg.eigh(cov)
    floor = max(float(val.max()) * 1e-8, 1e-10)
    val = np.maximum(val, floor)
    return (vec * (1.0 / np.sqrt(val))[None, :]) @ vec.T


def local_spectrum(mu: np.ndarray, whitener: np.ndarray, candidates: np.ndarray) -> tuple[float, float]:
    """Return relative conditioning gamma and absolute weakest strength alpha."""
    m = mu[candidates]
    m = m - m.mean(axis=0, keepdims=True)
    mw = m @ whitener
    s = np.linalg.svd(mw, compute_uv=False)
    rank_index = min(len(candidates) - 1, mw.shape[1]) - 1
    if rank_index < 0 or len(s) <= rank_index:
        return 0.0, 0.0
    alpha = float(s[rank_index])
    gamma = float(alpha / max(float(s[0]), EPS))
    return gamma, alpha


def source_neighbors(carriers: np.ndarray, k: int = LOCAL_K) -> np.ndarray:
    if len(carriers) < k:
        raise ValueError(f"need at least {k} source candidates")
    d2 = ((carriers[:, None, :] - carriers[None, :, :]) ** 2).sum(axis=2)
    return np.argsort(d2, axis=1)[:, :k]


def reconstruct_conditional_prob(bank_root: pathlib.Path, direct_gate_root: pathlib.Path):
    carriers, queries, winds, hits = g1.load_bank(bank_root)
    base, wind_feat = g1.build_features(carriers, queries, winds)
    b10 = np.broadcast_to(base, (10, *base.shape))
    cond = np.concatenate([b10, wind_feat], axis=2)

    norm_source = cond[list(g1.TRAIN_CONTEXTS)].reshape(-1, cond.shape[2])
    mean = norm_source.mean(axis=0)
    std = norm_source.std(axis=0)
    std[std < 1e-8] = 1.0
    cond = ((cond - mean) / std).astype(np.float32)

    model = g1.Field(cond.shape[2])
    model.load_state_dict(torch.load(direct_gate_root / "conditional_best.pt", weights_only=True))
    probs = {}
    for c in set(g1.VAL_CONTEXTS) | set(g1.TEST_CONTEXTS):
        p, _ = g1.predict(model, cond[c])
        probs[c] = p.reshape(len(carriers), len(queries), g1.TIMESTEPS + 1)
    return carriers, queries, hits, probs


def atom_table(bank_root: pathlib.Path, direct_gate_root: pathlib.Path):
    direct = json.loads((direct_gate_root / "m1_gate_result.json").read_text())
    if direct.get("verdict") != "M1_DIRECT_GO":
        raise SystemExit("refuse: frozen M1 direct gate is not GO")

    carriers, queries, hits, probs = reconstruct_conditional_prob(bank_root, direct_gate_root)
    neigh = source_neighbors(carriers)
    rows = []
    context_metrics = {}

    for c in tuple(g1.VAL_CONTEXTS) + tuple(g1.TEST_CONTEXTS):
        phi = build_response_features(hits[c], queries)
        cov, mu = transport_covariance(phi, g1.TRAIN_MEMBERS)
        whitener = inverse_sqrt_psd(cov)

        gammas = np.empty(len(carriers), dtype=np.float64)
        alphas = np.empty(len(carriers), dtype=np.float64)
        for truth in range(len(carriers)):
            gammas[truth], alphas[truth] = local_spectrum(mu, whitener, neigh[truth])

        # Qualification endpoint is the already-frozen M1 pre-Bayes ordering
        # margin. Gate values never read held-out member labels.
        for member in g1.HELDOUT_MEMBERS:
            labels = hits[c, :, :, member].astype(np.int64)
            margin = ordering.margins(probs[c], labels, carriers, "original", c, member)
            for truth in range(len(carriers)):
                rows.append({
                    "split": "dev" if c in g1.VAL_CONTEXTS else "test",
                    "context": int(c),
                    "truth_eval_only": int(truth),
                    "member_eval_only": int(member),
                    "gamma": float(gammas[truth]),
                    "alpha": float(alphas[truth]),
                    "m1_margin": float(margin[truth]),
                    "m1_correct": int(margin[truth] > 0.0),
                })
        context_metrics[str(c)] = {
            "gamma_median": float(np.median(gammas)),
            "alpha_median": float(np.median(alphas)),
            "gamma_q10_q90": [float(x) for x in np.quantile(gammas, [0.10, 0.90])],
            "alpha_q10_q90": [float(x) for x in np.quantile(alphas, [0.10, 0.90])],
        }

    return rows, context_metrics


def _metrics(rows, accept):
    accept = np.asarray(accept, dtype=bool)
    correct = np.asarray([r["m1_correct"] for r in rows], dtype=np.float64)
    margin = np.asarray([r["m1_margin"] for r in rows], dtype=np.float64)
    if accept.sum() == 0:
        return {
            "n": 0, "coverage": 0.0, "correct_fraction": None,
            "margin_mean": None, "margin_median": None,
        }
    return {
        "n": int(accept.sum()),
        "coverage": float(accept.mean()),
        "correct_fraction": float(correct[accept].mean()),
        "margin_mean": float(margin[accept].mean()),
        "margin_median": float(np.median(margin[accept])),
    }


def calibrate(rows, mode: str):
    gamma = np.asarray([r["gamma"] for r in rows])
    alpha = np.asarray([r["alpha"] for r in rows])
    baseline = float(np.mean([r["m1_correct"] for r in rows]))
    ggrid = np.unique(np.quantile(gamma, CAL_QUANTILES))
    agrid = np.unique(np.quantile(alpha, CAL_QUANTILES))

    if mode == "gamma":
        pairs = [(g, -math.inf) for g in ggrid]
    elif mode == "alpha":
        pairs = [(-math.inf, a) for a in agrid]
    elif mode == "dual":
        pairs = [(g, a) for g in ggrid for a in agrid]
    else:
        raise ValueError(mode)

    best = None
    for gt, at in pairs:
        accept = (gamma >= gt) & (alpha >= at)
        met = _metrics(rows, accept)
        if met["n"] < MIN_DEV_ATOMS or met["coverage"] < MIN_DEV_COVERAGE:
            continue
        gain = met["correct_fraction"] - baseline
        score = (gain, met["margin_mean"], met["coverage"])
        if best is None or score > best[0]:
            best = (score, float(gt), float(at), met)

    if best is None:
        return {
            "mode": mode, "calibration_ok": False, "gamma_threshold": None,
            "alpha_threshold": None, "dev_baseline_correct_fraction": baseline,
        }
    score, gt, at, met = best
    return {
        "mode": mode,
        "calibration_ok": bool(met["correct_fraction"] >= baseline + MIN_ACCEPTED_GAIN),
        "gamma_threshold": None if not math.isfinite(gt) else gt,
        "alpha_threshold": None if not math.isfinite(at) else at,
        "dev_baseline_correct_fraction": baseline,
        "dev_accepted": met,
        "dev_gain": float(met["correct_fraction"] - baseline),
    }


def apply_calibration(rows, cal):
    if not cal.get("calibration_ok"):
        return {"valid": False}
    gamma = np.asarray([r["gamma"] for r in rows])
    alpha = np.asarray([r["alpha"] for r in rows])
    gt = cal["gamma_threshold"]
    at = cal["alpha_threshold"]
    accept = np.ones(len(rows), dtype=bool)
    if gt is not None:
        accept &= gamma >= gt
    if at is not None:
        accept &= alpha >= at
    accepted = _metrics(rows, accept)
    rejected = _metrics(rows, ~accept)
    overall = _metrics(rows, np.ones(len(rows), dtype=bool))
    return {
        "valid": True,
        "accepted": accepted,
        "rejected": rejected,
        "overall": overall,
        "accepted_gain_vs_overall": (
            None if accepted["correct_fraction"] is None
            else float(accepted["correct_fraction"] - overall["correct_fraction"])
        ),
    }


def source_identity_control(bank_root: pathlib.Path):
    """Destroy persistent source identity across transport members.

    This control uses only the response ensemble and asks whether absolute
    source strength collapses when source identity is broken independently in
    each member. It does not participate in threshold calibration.
    """
    carriers, queries, _, hits = g1.load_bank(bank_root)
    neigh = source_neighbors(carriers)
    rng = np.random.default_rng(SEED)
    ratios = {}
    for c in g1.TEST_CONTEXTS:
        phi = build_response_features(hits[c], queries)
        cov, mu = transport_covariance(phi, g1.TRAIN_MEMBERS)
        w = inverse_sqrt_psd(cov)
        alpha = np.array([local_spectrum(mu, w, neigh[s])[1] for s in range(len(carriers))])

        x = phi.copy()
        for member in g1.TRAIN_MEMBERS:
            x[:, member, :] = x[rng.permutation(len(carriers)), member, :]
        covp, mup = transport_covariance(x, g1.TRAIN_MEMBERS)
        wp = inverse_sqrt_psd(covp)
        alphap = np.array([local_spectrum(mup, wp, neigh[s])[1] for s in range(len(carriers))])
        ratios[str(c)] = {
            "original_alpha_median": float(np.median(alpha)),
            "source_identity_broken_alpha_median": float(np.median(alphap)),
            "control_over_original": float(np.median(alphap) / max(np.median(alpha), EPS)),
        }
    return ratios


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bank_root", type=pathlib.Path)
    ap.add_argument("direct_gate_root", type=pathlib.Path)
    ap.add_argument("output_root", type=pathlib.Path)
    args = ap.parse_args()

    if args.output_root.exists():
        raise SystemExit(f"refuse overwrite: {args.output_root}")
    args.output_root.mkdir(parents=True)

    rows, context_metrics = atom_table(args.bank_root, args.direct_gate_root)
    dev = [r for r in rows if r["split"] == "dev"]
    test = [r for r in rows if r["split"] == "test"]

    calibrations = {m: calibrate(dev, m) for m in ("gamma", "alpha", "dual")}
    evaluation = {m: apply_calibration(test, calibrations[m]) for m in calibrations}
    dual = evaluation["dual"]
    gamma = evaluation["gamma"]

    dual_go = (
        calibrations["dual"].get("calibration_ok", False)
        and dual.get("valid", False)
        and dual["accepted"]["coverage"] >= MIN_TEST_COVERAGE
        and dual["accepted_gain_vs_overall"] is not None
        and dual["accepted_gain_vs_overall"] > 0.0
        and dual["accepted"]["margin_mean"] > dual["overall"]["margin_mean"]
    )
    alpha_adds_value = False
    if dual_go and gamma.get("valid") and gamma["accepted"]["correct_fraction"] is not None:
        alpha_adds_value = (
            dual["accepted"]["correct_fraction"]
            >= gamma["accepted"]["correct_fraction"] + ALPHA_EXTRA_GAIN_TARGET
            or dual["accepted"]["margin_mean"] > gamma["accepted"]["margin_mean"]
        )

    control = source_identity_control(args.bank_root)
    result = {
        "gate": "CG_PC_CTT_V15_COMPLETENESS_GATE",
        "status": "GO" if (dual_go and alpha_adds_value) else "NO_GO",
        "frozen_m1_modified": False,
        "real_source_truth_used": False,
        "synthetic_source_index_evaluation_only": True,
        "local_candidate_count": LOCAL_K,
        "transport_train_members": list(g1.TRAIN_MEMBERS),
        "transport_heldout_members": list(g1.HELDOUT_MEMBERS),
        "development_contexts": list(g1.VAL_CONTEXTS),
        "final_test_contexts": list(g1.TEST_CONTEXTS),
        "shrinkage": SHRINKAGE,
        "definitions": {
            "gamma": "sigma_(K-1) / sigma_1 after pooled transport-uncertainty whitening",
            "alpha": "sigma_(K-1) after pooled transport-uncertainty whitening",
        },
        "context_metrics": context_metrics,
        "calibration": calibrations,
        "final_test": evaluation,
        "dual_gate_go": dual_go,
        "alpha_adds_value_over_gamma_only": alpha_adds_value,
        "source_identity_break_control": control,
    }

    with (args.output_root / "gate_atoms.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    (args.output_root / "completeness_gate_result.json").write_text(json.dumps(result, indent=2))
    contract = {
        "script_sha256": hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
        "frozen_reference": "CTT V13 M1 GO checkpoint",
        "no_final_test_threshold_tuning": True,
        "feature_time_cuts": FEATURE_TIME_CUTS,
        "local_k": LOCAL_K,
        "shrinkage": SHRINKAGE,
        "seed": SEED,
    }
    (args.output_root / "completeness_gate_contract.json").write_text(json.dumps(contract, indent=2))
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "GO" else 2


if __name__ == "__main__":
    raise SystemExit(main())
