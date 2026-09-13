from __future__ import annotations

import numpy as np

from metric_subspaces import orthonormal_basis, overlap_and_source_safe_projection


def main():
    # Rank-deficient source contrasts: third column is dependent.
    d = np.array([[1., 0., 1.], [0., 1., 1.], [0., 0., 0.], [1., 1., 2.]])
    q, rank = orthonormal_basis(d)
    assert rank == 2
    assert np.allclose(q.T @ q, np.eye(rank), atol=1e-12)

    b_w = np.array([[2., 0.], [0., 3.], [1., 1.], [0., 1.]])
    w = np.array([1., 2., 3., 4.])
    rho, bperp_w, bperp, leak, rank_b = overlap_and_source_safe_projection(q, b_w, w)
    assert 0.0 <= rho <= 1.0 + 1e-12
    assert rank_b == 2
    assert leak <= 1e-12
    assert np.allclose(bperp * w[:, None], bperp_w)
    print("MC_SCSP_METRIC_PROPERTIES_PASS")


if __name__ == "__main__":
    main()

