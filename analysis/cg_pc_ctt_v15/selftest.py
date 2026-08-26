#!/usr/bin/env python3
"""Small deterministic self-test for CG-PC-CTT V15 analysis code."""
from __future__ import annotations

import numpy as np

import completeness_gate as cg
import proximal_bridge as pb


def test_whitened_spectrum_scale_invariance():
    rng = np.random.default_rng(1)
    s_count, m_count, d = 12, 6, 16
    source_mean = rng.normal(size=(s_count, d))
    phi = source_mean[:, None, :] + 0.2 * rng.normal(size=(s_count, m_count, d))
    cov, mu = cg.transport_covariance(phi, range(m_count))
    w = cg.inverse_sqrt_psd(cov)
    cand = np.arange(cg.LOCAL_K)
    g1, a1 = cg.local_spectrum(mu, w, cand)

    cov2, mu2 = cg.transport_covariance(17.0 * phi, range(m_count))
    w2 = cg.inverse_sqrt_psd(cov2)
    g2, a2 = cg.local_spectrum(mu2, w2, cand)
    assert np.isclose(g1, g2, rtol=1e-8, atol=1e-8)
    assert np.isclose(a1, a2, rtol=1e-8, atol=1e-8)


def test_bridge_shapes_and_panel_audit():
    rng = np.random.default_rng(2)
    n = 500
    u = rng.normal(size=(n, 1))
    s = 0.7 * u + rng.normal(scale=0.7, size=(n, 1))
    r = u + rng.normal(scale=0.4, size=(n, 1))
    z = u + 0.5 * s + rng.normal(scale=0.4, size=(n, 1))
    y = 1.5 * s + 0.8 * u + rng.normal(scale=0.2, size=(n, 1))
    d = {"y": y, "r": r, "s": s, "z": z}
    model = pb.Bridge(1e-4).fit(d)
    pred = model.predict(r[:10], s[:10])
    assert pred.shape == (10, 1)
    assert np.isfinite(model.moment_loss(d))

    # Two events x three candidate sources.
    event_id = np.repeat(np.arange(2), 3)
    candidate_id = np.tile(np.arange(3), 2)
    is_true = np.array([1, 0, 0, 0, 1, 0])
    rr = np.repeat(r[:2], 3, axis=0)
    yy = np.repeat(y[:2], 3, axis=0)
    ss = rng.normal(size=(6, 1))
    zz = rng.normal(size=(6, 1))
    panel = {
        "event_id": event_id, "candidate_id": candidate_id, "is_true": is_true,
        "y": yy, "r": rr, "s": ss, "z": zz,
    }
    pb.audit_panel(panel)


def main():
    test_whitened_spectrum_scale_invariance()
    test_bridge_shapes_and_panel_audit()
    print("CG_PC_CTT_V15_SELFTEST=PASS")


if __name__ == "__main__":
    main()
