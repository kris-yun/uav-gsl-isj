#!/usr/bin/env python3
"""Formula-level self-tests for CG-PC-CTT V3 shared mathematics."""
from __future__ import annotations
import numpy as np
from v3_math import (
    coordinate_quotient, nuisance_metric, delaunay_neighbors,
    tangent_information_for_source, pair_cross_stat, assimilation_resolution_gain
)

rng = np.random.default_rng(20260827)


def assert_close(a, b, tol=1e-8, msg=""):
    if not np.allclose(a, b, rtol=tol, atol=tol):
        raise AssertionError(msg or f"not close: {a} vs {b}")


def synthetic_grid(n=6):
    x = np.linspace(-1, 1, n)
    xx, yy = np.meshgrid(x, x)
    return np.c_[xx.ravel(), yy.ravel()]


def build_phi(xy, M=8, D=6, rank1=False):
    A = rng.normal(size=(2, D))
    if rank1:
        A[1] = 0.0
    base = xy @ A
    member_common = 0.05 * rng.normal(size=(M, D))
    eps = 0.02 * rng.normal(size=(len(xy), M, D))
    return base[:, None, :] + member_common[None, :, :] + eps


# 1. Coordinate aliases quotient to one physical state.
xy = synthetic_grid(4)
phi = build_phi(xy)
xy2 = np.vstack([xy, xy[3]])
phi2 = np.concatenate([phi, phi[3:4]], axis=0)
qphi, qxy, groups, drift = coordinate_quotient(phi2, xy2)
assert len(qxy) == len(xy)
assert drift == 0.0
assert any(len(g) == 2 for g in groups)

# 2. Exact local twin has zero replicated pair information.
metric = nuisance_metric(phi)
twin = phi.copy()
twin[1] = twin[0]
metric_twin = nuisance_metric(twin)
ps = pair_cross_stat(twin, 0, 1, metric_twin)
assert abs(ps["pair_cross_strength"]) < 1e-12
assert ps["pair_p_signflip"] == 1.0
assert ps["resolved_proto"] is False

# 3. Full 2-D response gives positive second local source-information direction.
nb, _ = delaunay_neighbors(xy)
metric = nuisance_metric(phi)
vals = [tangent_information_for_source(phi, xy, i, nb[i], metric) for i in range(len(xy))]
interior = [v for v in vals if v["geometry_rank"] == 2]
assert interior
assert np.median([v["lambda_min"] for v in interior]) > 0

# 4. Rank-1 physical response cannot support a robust second direction.
phi_r1 = build_phi(xy, rank1=True)
metric_r1 = nuisance_metric(phi_r1)
vals_r1 = [tangent_information_for_source(phi_r1, xy, i, nb[i], metric_r1) for i in range(len(xy))]
med_r1 = np.median([max(v["lambda_min"], 0.0) for v in vals_r1 if v["geometry_rank"] == 2])
med_r2 = np.median([max(v["lambda_min"], 0.0) for v in interior])
assert med_r1 < 0.15 * med_r2

# 5. Duplicate feature embeddings do not create extra Mahalanobis information.
Adup = np.concatenate([np.eye(phi.shape[2]), np.tile(np.eye(phi.shape[2])[0:1], (10, 1))], axis=0)
phi_dup = phi @ Adup.T
metric_dup = nuisance_metric(phi_dup)
i = len(xy)//2
F0 = tangent_information_for_source(phi, xy, i, nb[i], metric)["F"]
F1 = tangent_information_for_source(phi_dup, xy, i, nb[i], metric_dup)["F"]
assert_close(F0, F1, tol=1e-7, msg="feature duplication changed tangent information")
p0 = pair_cross_stat(phi, 2, 3, metric)
p1 = pair_cross_stat(phi_dup, 2, 3, metric_dup)
assert_close(p0["pair_cross_strength"], p1["pair_cross_strength"], tol=1e-7,
             msg="feature duplication changed pair information")

# 6. Orthogonal rotation of physical source coordinates preserves tangent eigenvalues.
theta = 0.73
R = np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])
xy_rot = xy @ R.T
Fr = tangent_information_for_source(phi, xy_rot, i, nb[i], metric)["F"]
assert_close(np.linalg.eigvalsh(F0), np.linalg.eigvalsh(Fr), tol=1e-6,
             msg="coordinate rotation changed tangent eigenvalues")

# 7. ACI/data-assimilation information gain is zero with F=0 and positive with F>0.
P0 = np.eye(2) * 0.25
g0 = assimilation_resolution_gain(np.zeros((2,2)), P0)
assert_close(g0["information_gain_nats_positive_part"], 0.0)
g1 = assimilation_resolution_gain(F0, P0)
assert g1["information_gain_nats_positive_part"] > 0

print("CG_PC_CTT_V3_MATH_SELFTEST PASS")
