"""Tie-aware, log-space evaluation contract for the fixed-support arms."""

from __future__ import annotations

import time

import numpy as np


def cell_coords(fu):
    gx, gy = fu.grid_x, fu.grid_y
    ox, oy = fu.origin
    cs = fu.cell_size
    xs = np.arange(gx) * cs + ox
    ys = np.arange(gy) * cs + oy
    return xs, ys


def truth_cell(fu, truth_xy):
    xs, ys = cell_coords(fu)
    cx = int(np.clip(np.floor((truth_xy[0] - fu.origin[0]) / fu.cell_size), 0, fu.grid_x - 1))
    cy = int(np.clip(np.floor((truth_xy[1] - fu.origin[1]) / fu.cell_size), 0, fu.grid_y - 1))
    return cy * fu.grid_x + cx


def tie_aware_rank(scores: np.ndarray, true_idx: int):
    """r_min = 1 + #{scores > score*}, r_max = #{scores >= score*}."""
    sv = scores[true_idx]
    r_min = int(1 + np.sum(scores > sv))
    r_max = int(np.sum(scores >= sv))
    tie_size = int(np.sum(np.isclose(scores, sv)))
    return r_min, r_max, tie_size


def evaluate_arm(fu, posterior, log_ev, truth_idx, arm_name, prefix=""):
    occ = fu.occupancy
    post = posterior[occ]
    logev = log_ev[occ] if log_ev is not None else np.log(np.maximum(post, 1e-300))
    xs, ys = cell_coords(fu)
    free_idx = np.where(occ)[0]
    coords = np.stack([xs[free_idx % fu.grid_x], ys[free_idx // fu.grid_x]], axis=1)
    truth_pos = np.array([xs[truth_idx % fu.grid_x], ys[truth_idx // fu.grid_x]])
    t_free = int(np.where(free_idx == truth_idx)[0][0])

    r_min, r_max, tie = tie_aware_rank(logev, t_free)
    best_wrong = -np.inf
    for i in range(len(logev)):
        if i != t_free and logev[i] > best_wrong:
            best_wrong = logev[i]
    margin = logev[t_free] - best_wrong
    true_mass = float(post[t_free])
    map_i = int(np.argmax(post))
    map_err = float(np.linalg.norm(coords[map_i] - truth_pos))
    # posterior medoid: cell minimizing expected distance under the posterior
    dmat = np.sqrt(
        (coords[:, None, 0] - coords[None, :, 0]) ** 2
        + (coords[:, None, 1] - coords[None, :, 1]) ** 2
    )
    exp_dist = dmat @ post
    medoid_i = int(np.argmin(exp_dist))
    medoid_err = float(np.linalg.norm(coords[medoid_i] - truth_pos))
    order = np.argsort(-post)
    cum = np.cumsum(post[order])
    k90 = int(np.searchsorted(cum, 0.9) + 1)
    cov90 = int(truth_idx in free_idx[order[:k90]])
    H = float(-np.sum(post * np.log(np.maximum(post, 1e-300))))
    prior = fu.prior[occ]
    H0 = float(-np.sum(prior * np.log(np.maximum(prior, 1e-300))))
    contraction = 1.0 - H / max(H0, 1e-300)
    hc_wrong = float(np.sum(post[(coords[:, 0] - truth_pos[0]) ** 2 +
                                 (coords[:, 1] - truth_pos[1]) ** 2 > 4.0 * fu.cell_size**2]))
    return {
        f"{prefix}rank_min": r_min,
        f"{prefix}rank_max": r_max,
        f"{prefix}tie_size": tie,
        f"{prefix}true_best_wrong_margin": margin,
        f"{prefix}true_mass": true_mass,
        f"{prefix}map_error": map_err,
        f"{prefix}medoid_error": medoid_err,
        f"{prefix}cred90_cov": bool(cov90),
        f"{prefix}entropy": H,
        f"{prefix}contraction": contraction,
        f"{prefix}high_conf_wrong_mass": hc_wrong,
    }


def evaluate_update(fu, arm_results, truth_idx, mode="independent"):
    from arms import assignment_from_rects

    assign = assignment_from_rects(fu.candidates, fu.grid_x, fu.grid_y)
    truth_cand = int(assign[truth_idx])
    # candidate-level evidence
    cand_logev = {}
    for arm, res in arm_results.items():
        if res["log_ev"] is None:
            cand_logev[arm] = None
        else:
            cand_logev[arm] = res["log_ev"]
    rows = {}
    for arm, res in arm_results.items():
        log_ev_cell = (
            res["log_ev"][assign] if res["log_ev"] is not None else None
        )
        rows[arm] = evaluate_arm(fu, res["posterior"], log_ev_cell, truth_idx, arm)
        if cand_logev[arm] is not None:
            lev = cand_logev[arm]
            tr = lev[truth_cand]
            best_wrong = max((lev[i] for i in range(len(lev)) if i != truth_cand), default=-np.inf)
            r_min_c = 1 + int(np.sum(lev > tr))
            r_max_c = int(np.sum(lev >= tr))
            # posterior-based candidate mass + rank (operational decision output)
            post_ = res["posterior"]
            cand_mass = np.array([
                float(post_[assign == c].sum()) if (assign == c).any() else 0.0
                for c in range(len(lev))
            ])
            rows[arm]["post_cand_mass"] = float(cand_mass[truth_cand])
            rows[arm]["post_cand_rank"] = int(1 + np.sum(cand_mass > cand_mass[truth_cand]))
            rows[arm]["cand_rank_min"] = r_min_c
            rows[arm]["cand_rank_max"] = r_max_c
            rows[arm]["cand_tie_size"] = int(np.sum(np.isclose(lev, tr)))
            rows[arm]["cand_margin"] = float(tr - best_wrong)
        rows[arm]["abstained"] = res.get("abstained", False)
        rows[arm]["alpha"] = res.get("alpha", None)
        rows[arm]["rho"] = res.get("rho", None)
    return rows
