#!/usr/bin/env python3
"""Quadrature certificate for nuisance-conditioned source curvature.

Finite S,W,Q; a 2-D action; 1-D Gaussian gas measurement; uncertain common
release scale Q; noisy wind cue C. This is an analytic local mixture model,
not a plume model, a biological controller, or finite-step optimality claim.
"""
from pathlib import Path
import json
import math
import numpy as np


PI = 0.35
Q = np.array([0.6, 1.4])
PQ = np.array([0.4, 0.6])
D = np.array([[1.0, 0.15], [-0.1, 1.2]])
G = np.array([[1.0, 0.15], [0.15, 1.6]])
WIND_ERROR = 0.12
GH_X, GH_W = np.polynomial.hermite.hermgauss(80)
GH_W = GH_W / np.sqrt(np.pi)


def logsumexp(x, axis=-1):
    peak = np.max(x, axis=axis, keepdims=True)
    return np.squeeze(peak, axis=axis) + np.log(np.exp(x - peak).sum(axis=axis))


def information(a, pw, quadrature=None):
    """Integrate the exact source-marginal Gaussian-mixture MI in nats."""
    qx, qw = (GH_X, GH_W) if quadrature is None else quadrature
    eta_weights = np.outer(pw, PQ).reshape(-1)
    derivatives = (D[:, None, :] * Q[None, :, None]).reshape(4, 2)
    means = (np.array([0.0, 1.0])[:, None] - PI) * (derivatives @ a)[None, :]
    ps = np.array([1 - PI, PI])
    total = 0.0
    for s in range(2):
        for eta in range(4):
            ys = means[s, eta] + math.sqrt(2) * qx
            log_component = -0.5 * (ys[:, None, None] - means[None, :, :]) ** 2 - 0.5 * math.log(2 * math.pi)
            log_cond = logsumexp(log_component + np.log(eta_weights)[None, None, :], axis=2)
            log_pred = logsumexp(log_cond + np.log(ps)[None, :], axis=1)
            total += ps[s] * eta_weights[eta] * np.dot(qw, log_cond[:, s] - log_pred)
    return float(total)


def top(matrix):
    values, vectors = np.linalg.eigh(matrix)
    return float(values[-1]), vectors[:, -1]


def main():
    vals, vecs = np.linalg.eigh(G)
    ghalf = (vecs * np.sqrt(vals)[None, :]) @ vecs.T
    ginvhalf = (vecs / np.sqrt(vals)[None, :]) @ vecs.T
    beliefs = [np.array([1 - WIND_ERROR, WIND_ERROR]), np.array([WIND_ERROR, 1 - WIND_ERROR])]
    dbars = [np.dot(pw, D) * np.dot(PQ, Q) for pw in beliefs]
    ks = [np.outer(dbar, dbar) for dbar in dbars]
    d0 = np.mean(D, axis=0) * np.dot(PQ, Q)
    k0 = np.outer(d0, d0)
    whitened = [ginvhalf @ k @ ginvhalf for k in ks]
    whitened0 = ginvhalf @ k0 @ ginvhalf
    lambdas, vectors = zip(*(top(k) for k in whitened))
    coefficient_adaptive = float(np.mean(lambdas))
    coefficient_fixed, vfixed = top(np.mean(whitened, axis=0))
    coefficient_none, vnone = top(whitened0)
    variance = np.mean(ks, axis=0) - k0
    variance_direct = np.mean([np.outer(d - d0, d - d0) for d in dbars], axis=0)
    assert np.max(np.abs(variance - variance_direct)) < 1e-12
    assert np.linalg.eigvalsh(variance).min() > -1e-12
    assert coefficient_adaptive >= coefficient_fixed >= coefficient_none

    # An explicitly arbitrary rank-one body-basis illustration, not a
    # learned or empirically qualified biological proposal.
    b = np.array([math.cos(math.pi / 6), math.sin(math.pi / 6)])
    physical_b_unit = b / math.sqrt(b @ G @ b)
    ub = ghalf @ physical_b_unit
    restricted_coeffs = [float(ub @ k @ ub) for k in whitened]
    angular_upper = [lam * (1 - float(np.dot(ub, v)) ** 2) for lam, v in zip(lambdas, vectors)]
    angular_gaps = [lam - r for lam, r in zip(lambdas, restricted_coeffs)]
    assert all(g <= u + 1e-12 for g, u in zip(angular_gaps, angular_upper))
    assert abs(float(ub @ ub) - 1) < 1e-12
    kappa = PI * (1 - PI) / 2
    rows = []
    for alpha in [0.4, 0.2, 0.1, 0.05, 0.025]:
        avecs = [alpha * ginvhalf @ v for v in vectors]
        afixed, anone = alpha * ginvhalf @ vfixed, alpha * ginvhalf @ vnone
        abody = alpha * physical_b_unit
        for a in avecs + [afixed, anone, abody]:
            assert abs(float(a @ G @ a) - alpha**2) < 1e-12
        iadapt = float(np.mean([information(a, pw) for a, pw in zip(avecs, beliefs)]))
        ifixed = float(np.mean([information(afixed, pw) for pw in beliefs]))
        inone = information(anone, np.array([0.5, 0.5]))
        ibody = float(np.mean([information(abody, pw) for pw in beliefs]))
        leading = kappa * alpha**2
        row = {
            "alpha": alpha,
            "no_cue_information_nat": inone,
            "cue_fixed_direction_information_nat": ifixed,
            "cue_adaptive_direction_information_nat": iadapt,
            "cue_arbitrary_restricted_basis_information_nat": ibody,
            "adaptive_minus_fixed_information_nat": iadapt - ifixed,
            "predicted_adaptive_minus_fixed_information_nat": leading * (coefficient_adaptive - coefficient_fixed),
            "adaptive_normalized_remainder": iadapt / leading - coefficient_adaptive,
            "fixed_normalized_remainder": ifixed / leading - coefficient_fixed,
            "no_cue_normalized_remainder": inone / leading - coefficient_none,
        }
        assert iadapt > ifixed > inone
        rows.append(row)
    assert max(abs(rows[-1][k]) for k in (
        "adaptive_normalized_remainder", "fixed_normalized_remainder", "no_cue_normalized_remainder"
    )) < 1e-3
    fine_x, fine_w = np.polynomial.hermite.hermgauss(160)
    fine_quadrature = (fine_x, fine_w / np.sqrt(np.pi))
    quadrature_error = max(
        abs(information(0.4 * ginvhalf @ v, pw)
            - information(0.4 * ginvhalf @ v, pw, fine_quadrature))
        for v in list(vectors) + [vfixed, vnone]
        for pw in beliefs + [np.array([0.5, 0.5])]
    )
    assert quadrature_error < 1e-12
    result = {
        "status": "PASS: local mixture information evaluated by 80-node Gauss-Hermite quadrature",
        "scope": "S,W,Q are marginalized; fixed curvature-optimal directions evaluated, not global finite-step optima or physical plume/controller performance",
        "parameters": {"source_probability": PI, "release_values": Q.tolist(), "release_probabilities": PQ.tolist(),
                       "wind_error": WIND_ERROR, "wind_derivatives": D.tolist(), "common_cost_metric": G.tolist(),
                       "gas_variance": 1.0, "nuisance_prior_independent_of_source": True},
        "coefficients_before_kappa_alpha_squared": {
            "no_cue": coefficient_none,
            "cue_fixed_direction": coefficient_fixed,
            "cue_adaptive_direction": coefficient_adaptive,
            "direction_adaptation_gain": coefficient_adaptive - coefficient_fixed,
            "improved_interpretation_gain": coefficient_fixed - coefficient_none,
        },
        "variance_identity_max_error": float(np.max(np.abs(variance - variance_direct))),
        "quadrature_80_vs_160_max_absolute_difference_nat_at_alpha_0p4": quadrature_error,
        "variance_matrix_eigenvalues": np.linalg.eigvalsh(variance).tolist(),
        "restricted_basis": {"physical_column": b.tolist(), "branch_gaps": angular_gaps,
                             "branch_angular_upper_bounds": angular_upper},
        "small_step_quadrature": rows,
        "cost_warning": "The preliminary cue's time/energy cost is omitted here; these positive information gains are not net policy-utility guarantees.",
    }
    path = Path(__file__).with_name("local_curvature_results.json")
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
