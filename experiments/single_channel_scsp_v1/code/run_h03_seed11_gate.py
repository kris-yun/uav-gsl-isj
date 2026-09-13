"""One-shot H03 seed11 development replay for metric-consistent SCSP."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from arms import assignment_from_rects, run_arms
from ccde import matched_source_log_evidence, posterior_from_candidate_logev
from evaluate import evaluate_update, truth_cell
from frozen_inputs import load_update
from metric_subspaces import (
    mismatch_geometry,
    overlap_and_source_safe_projection,
    source_contrast_geometry,
)
from mox import mox_atoms
import subspaces as legacy_subspaces


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "work" / "ccde_holdout_v3_20260807" / "H03_seed11"
OUT = ROOT / "results" / "H03_SEED11_MC_SCSP_GATE.json"
TRUTH = (-0.45, 1.90)


def load_atoms(fu, atom_dir: Path) -> np.ndarray:
    raw = np.frombuffer((atom_dir / "atoms.f32").read_bytes(), dtype="<f4")
    physical = raw.reshape(-1, fu.n_cells).astype(np.float64)
    return np.vstack([physical, mox_atoms(fu.maps)])


def evaluate_msf(fu, prior, truth_index):
    logev = matched_source_log_evidence(fu)
    posterior = posterior_from_candidate_logev(fu, logev, prior)
    result = {"MSF": {"log_ev": logev, "posterior": posterior, "abstained": False}}
    return evaluate_update(fu, result, truth_index)["MSF"], posterior


def run():
    prereg = json.loads((ROOT / "PREREGISTRATION_H03_SEED11.json").read_text(encoding="utf-8"))
    if prereg["status"] != "FROZEN_BEFORE_EXPERIMENT":
        raise RuntimeError("preregistration is not frozen")
    if not DATA.exists():
        raise RuntimeError("input missing; run prepare_h03_seed11.py first")

    rows = []
    metric_prior = legacy_prior = msf_prior = None
    max_orthogonality = 0.0

    for update in (0, 1, 2):
        fu = load_update(
            str(DATA / "snapshots" / f"H03_UPDATE_{update}"),
            str(DATA / f"candidates_U{update}"),
        )
        truth_index = truth_cell(fu, TRUTH)
        atoms = load_atoms(fu, DATA / f"atoms_U{update}")
        metric_prior = fu.prior if update == 0 else metric_prior
        legacy_prior = fu.prior if update == 0 else legacy_prior
        msf_prior = fu.prior if update == 0 else msf_prior
        assignment = assignment_from_rects(fu.candidates, fu.grid_x, fu.grid_y)

        # Legacy implementation retained as a control.
        d_legacy, keep_legacy = legacy_subspaces.source_contrast_basis(fu)
        b_legacy, rank_b_legacy, _ = legacy_subspaces.mismatch_basis(
            atoms, keep_legacy, energy_threshold=0.95
        )
        rho_legacy, _ = legacy_subspaces.overlap(d_legacy, b_legacy)
        _, bperp_legacy = legacy_subspaces.decompose(b_legacy, d_legacy)
        legacy = run_arms(
            fu.measured_prob, fu.measured_conf, legacy_prior, fu.maps,
            assignment, keep_legacy, fu.posterior_official, fu.internal_official,
            B_full=b_legacy, B_perp=bperp_legacy, rho=rho_legacy,
        )
        legacy_eval = evaluate_update(fu, legacy, truth_index)
        legacy_prior = legacy["A4_protected"]["posterior"]

        # Corrected implementation: one metric, rank-revealing source basis.
        _, q_d, rank_d, keep, w = source_contrast_geometry(fu)
        b_w, b_metric, rank_b, cumulative = mismatch_geometry(
            atoms, keep, w, energy_threshold=0.95
        )
        rho, _, bperp_metric, orthogonality, rank_b_effective = (
            overlap_and_source_safe_projection(q_d, b_w, w)
        )
        max_orthogonality = max(max_orthogonality, orthogonality)
        metric = run_arms(
            fu.measured_prob, fu.measured_conf, metric_prior, fu.maps,
            assignment, keep, fu.posterior_official, fu.internal_official,
            B_full=b_metric, B_perp=bperp_metric, rho=rho,
        )
        metric_eval = evaluate_update(fu, metric, truth_index)
        metric_prior = metric["A4_protected"]["posterior"]

        msf_eval, msf_prior = evaluate_msf(fu, msf_prior, truth_index)
        rows.append({
            "update": update,
            "metric_geometry": {
                "source_rank": rank_d,
                "mismatch_rank_95pct": rank_b,
                "mismatch_effective_rank": rank_b_effective,
                "rho": rho,
                "weighted_source_nuisance_orthogonality_max_abs": orthogonality,
                "energy_at_rank": float(cumulative[rank_b - 1]) if rank_b else None,
            },
            "legacy_geometry": {
                "reported_source_rank": int(np.linalg.matrix_rank(d_legacy)),
                "mismatch_rank_95pct": rank_b_legacy,
                "rho": rho_legacy,
            },
            "native_pmfs": metric_eval["A0_native"],
            "plain_msf": msf_eval,
            "legacy_scsp": legacy_eval["A4_protected"],
            "metric_scsp": metric_eval["A4_protected"],
            "metric_unprotected": metric_eval["A3_structured"],
            "metric_evidence_blend_secondary": metric_eval["A4_protected_evidence"],
        })

    final = rows[-1]
    native = final["native_pmfs"]
    msf = final["plain_msf"]
    legacy = final["legacy_scsp"]
    primary = final["metric_scsp"]

    native_ratio = min(
        primary["map_error"] / max(native["map_error"], 1e-12),
        primary["medoid_error"] / max(native["medoid_error"], 1e-12),
    )
    mechanism_improvements = {
        "candidate_rank": primary["cand_rank_min"] < legacy["cand_rank_min"],
        "candidate_margin": primary["cand_margin"] > legacy["cand_margin"] + 1e-12,
        "coverage": bool(primary["cred90_cov"]) and not bool(legacy["cred90_cov"]),
        "high_conf_wrong_mass": (
            primary["high_conf_wrong_mass"] < legacy["high_conf_wrong_mass"] - 1e-12
        ),
    }
    criteria = {
        "weighted_orthogonality": max_orthogonality <= 1e-8,
        "native_error_improvement_20pct": native_ratio <= 0.8,
        "not_worse_than_msf_0p2m": (
            primary["map_error"] <= msf["map_error"] + 0.2
            and primary["medoid_error"] <= msf["medoid_error"] + 0.2
        ),
        "two_mechanism_metrics_vs_legacy": sum(mechanism_improvements.values()) >= 2,
        "not_entropy_only": any(mechanism_improvements.values()),
    }
    passed = all(criteria.values())
    marker = (
        prereg["pass_marker"] if passed else prereg["stop_marker"]
    )
    output = {
        "contract": prereg["contract"],
        "data_role": prereg["data_scope"]["role"],
        "rows": rows,
        "decision": {
            "criteria": criteria,
            "mechanism_improvements_vs_legacy": mechanism_improvements,
            "native_best_error_ratio": native_ratio,
            "max_weighted_orthogonality": max_orthogonality,
            "marker": marker,
        },
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output["decision"], indent=2))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(run())

