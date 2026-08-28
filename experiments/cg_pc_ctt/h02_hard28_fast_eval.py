#!/usr/bin/env python3
"""Frozen H02 hard-28 evaluator for CG-PC-CTT Gate V2.

No threshold fitting is performed here. It applies the already frozen V2 gate
(gamma>=0.05, exact sign-flip p<=0.01, rank_k=3) and adds a diagnostic
pair-specific replicated separation statistic for the declared true/hard-wrong
candidate. The pair statistic is diagnostic only and MUST NOT be used to retune
V2 after H02 visibility.

NPZ contract:
  phi[N,S,M,D]
  margin[N]                 # evaluation-only true_score - max_false_score
  true_idx[N]               # evaluation-only candidate index
  hard_wrong_idx[N]         # evaluation-only hardest/wrong candidate index
Optional:
  case_id[N]
  candidate_xy[S,2]
"""
from __future__ import annotations

import argparse
import csv
import json
from itertools import product
from pathlib import Path
import numpy as np

from completeness_gate import GateConfig, compute_gate

CFG = GateConfig(
    gamma_min=0.05,
    p_max=0.01,
    rank_k=3,
    member_semantics="exchangeable_realizations",
)


def _noise_scale(x: np.ndarray):
    """Same pair-difference feature scaling used by Gate V2."""
    S, M, D = x.shape
    ss = np.zeros(D, dtype=np.float64)
    n = 0
    for m in range(M):
        for h in range(m + 1, M):
            diff = x[:, m, :] - x[:, h, :]
            ss += np.sum(0.5 * diff * diff, axis=0)
            n += S
    v = ss / max(n, 1)
    ridge = max(1e-9, 1e-3 * max(float(np.mean(v)), 1e-9))
    return 1.0 / np.sqrt(v + ridge)


def pair_stat(x: np.ndarray, i: int, j: int):
    """Replicated separation of one source pair, with exact member sign-flip null."""
    M = x.shape[1]
    if M > 16:
        raise ValueError("exact sign-flip diagnostic limited to M<=16")
    w = _noise_scale(x)
    d = (x[i] - x[j]) * w[None, :]  # [M,D]

    def q(signs):
        z = d * signs[:, None]
        total = z.sum(axis=0)
        cross = (float(total @ total) - float(np.sum(z * z))) / float(M * (M - 1))
        return cross

    obs = q(np.ones(M))
    null = []
    for tail in product((-1.0, 1.0), repeat=M - 1):
        null.append(q(np.asarray((1.0,) + tail)))
    null = np.asarray(null)
    p = float(np.mean(null >= obs - 1e-12))
    return {
        "pair_cross_strength": float(obs),
        "pair_alpha_cf": float(np.sqrt(max(obs, 0.0))),
        "pair_p_signflip": p,
        "pair_null_patterns": int(len(null)),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("npz", type=Path)
    ap.add_argument("--out-csv", type=Path, required=True)
    ap.add_argument("--out-json", type=Path, required=True)
    args = ap.parse_args()

    d = np.load(args.npz, allow_pickle=True)
    phi = np.asarray(d["phi"], dtype=np.float64)
    margin = np.asarray(d["margin"], dtype=np.float64)
    true_idx = np.asarray(d["true_idx"], dtype=int)
    wrong_idx = np.asarray(d["hard_wrong_idx"], dtype=int)
    if phi.ndim != 4:
        raise ValueError(f"phi must be [N,S,M,D], got {phi.shape}")
    N, S, _, _ = phi.shape
    for name, a in [("margin", margin), ("true_idx", true_idx), ("hard_wrong_idx", wrong_idx)]:
        if len(a) != N:
            raise ValueError(f"{name} length mismatch")
    case_id = np.asarray(d["case_id"]).astype(str) if "case_id" in d else np.asarray([f"case_{i:02d}" for i in range(N)])

    rows = []
    for n in range(N):
        if not (0 <= true_idx[n] < S and 0 <= wrong_idx[n] < S):
            raise ValueError(f"candidate index out of range in {case_id[n]}")
        g = compute_gate(phi[n], CFG)
        p = pair_stat(phi[n], int(true_idx[n]), int(wrong_idx[n]))
        rows.append({
            "case_id": str(case_id[n]),
            "true_idx": int(true_idx[n]),
            "hard_wrong_idx": int(wrong_idx[n]),
            "margin": float(margin[n]),
            **g.to_dict(),
            **p,
        })

    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

    accepted = np.asarray([r["accepted"] for r in rows], dtype=bool)
    mar = np.asarray([r["margin"] for r in rows], dtype=float)
    coverage = float(np.mean(accepted))
    summary = {
        "contract": "CG_PC_CTT_H02_HARD28_FAST_EVAL_V1",
        "n": N,
        "coverage": coverage,
        "accepted": int(accepted.sum()),
        "rejected": int((~accepted).sum()),
        "all_historical_margins_negative": bool(np.all(mar < 0)),
        "overall_mean_margin": float(mar.mean()),
        "overall_median_margin": float(np.median(mar)),
        "accepted_mean_margin": float(mar[accepted].mean()) if accepted.any() else None,
        "rejected_mean_margin": float(mar[~accepted].mean()) if (~accepted).any() else None,
        "pair_alpha_median": float(np.median([r["pair_alpha_cf"] for r in rows])),
        "pair_p_le_0p01_fraction": float(np.mean([r["pair_p_signflip"] <= 0.01 for r in rows])),
        "interpretation": None,
    }
    if coverage >= 0.90:
        summary["interpretation"] = "GLOBAL_GATE_MODEL_SIDE_ONLY_UNLESS_PAIR_DIAGNOSTIC_STRATIFIES"
    elif accepted.any() and (~accepted).any() and mar[accepted].mean() > mar[~accepted].mean():
        summary["interpretation"] = "GLOBAL_GATE_RELIABILITY_STRATIFICATION_SUPPORTED"
    else:
        summary["interpretation"] = "GLOBAL_GATE_RELIABILITY_STRATIFICATION_NOT_SUPPORTED"

    args.out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
