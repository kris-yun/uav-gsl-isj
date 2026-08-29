#!/usr/bin/env python3
"""Deterministic self-tests for the PF-DEI V3 spatial-structure audit."""
from __future__ import annotations

import numpy as np

from evaluate_pf_dei_direct_set_nre_v3_spatial_structure import (
    normalize_mass,
    regional_summary,
    resolution_overlap_graph,
)


def main():
    ids = np.asarray(["a", "b", "c", "d"])
    xy = np.asarray([[0.0, 0.0], [0.4, 0.0], [3.0, 0.0], [6.0, 0.0]])
    radius = np.asarray([0.3, 0.3, 0.3, 0.3])
    prior = np.full(4, 0.25)
    posterior = normalize_mass(np.asarray([0.25, 0.24, 0.45, 0.06]))

    graph = resolution_overlap_graph(xy, radius)
    summary = regional_summary(posterior, prior, xy, graph, ids)

    assert int(np.argmax(posterior)) == 2, "synthetic exact MAP premise changed"
    assert ids[summary["mass_mode_index"]] == "a", "coherent local mass not recovered"
    np.testing.assert_allclose(summary["mass_mode_xy"], np.asarray([0.1959183673469388, 0.0]), atol=1e-12)

    perm = np.asarray([2, 0, 3, 1])
    p_summary = regional_summary(
        posterior[perm],
        prior[perm],
        xy[perm],
        resolution_overlap_graph(xy[perm], radius[perm]),
        ids[perm],
    )
    assert ids[summary["mass_mode_index"]] == ids[perm][p_summary["mass_mode_index"]]
    assert ids[summary["bf_mode_index"]] == ids[perm][p_summary["bf_mode_index"]]
    np.testing.assert_allclose(summary["mass_mode_xy"], p_summary["mass_mode_xy"], atol=1e-12)
    np.testing.assert_allclose(summary["bf_mode_xy"], p_summary["bf_mode_xy"], atol=1e-12)

    neutral = regional_summary(prior, prior, xy, graph, ids)
    np.testing.assert_allclose(neutral["log_region_bf"], 0.0, atol=1e-12)

    assert np.array_equal(graph, graph.T)
    assert np.all(np.diag(graph))

    print("PF_DEI_DIRECT_SET_NRE_V3_SPATIAL_STRUCTURE_SELFTEST_PASS")


if __name__ == "__main__":
    main()
