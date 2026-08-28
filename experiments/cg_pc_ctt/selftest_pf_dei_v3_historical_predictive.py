#!/usr/bin/env python3

import numpy as np
import torch

from qualify_pf_dei_v3_historical_predictive import (
    forward_boundaries,
    normalized_posterior,
    weighted_energy_score,
)


def main() -> int:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    assert forward_boundaries(100).tolist() == [0, 20, 40, 60, 80, 100]

    prior = np.asarray([0.2, 0.3, 0.5])
    assert np.allclose(normalized_posterior(prior, np.zeros(3)), prior)
    posterior = normalized_posterior(prior, np.asarray([4.0, 0.0, 0.0]))
    assert posterior[0] > posterior[1] and np.isclose(posterior.sum(), 1.0)

    observed = np.asarray([0.0, 0.0, 0.0, 0.0], dtype=np.float32)
    ensemble = np.asarray([
        [0.0, 0.0, 0.0, 0.0],
        [1.0, 1.0, 1.0, 1.0],
        [2.0, 2.0, 2.0, 2.0],
    ], dtype=np.float32)
    concentrated = weighted_energy_score(observed, ensemble, np.asarray([1.0, 0.0, 0.0]), device)
    diffuse = weighted_energy_score(observed, ensemble, np.asarray([1 / 3, 1 / 3, 1 / 3]), device)
    assert abs(concentrated) < 1e-12 and diffuse > concentrated

    permutation = np.asarray([2, 0, 1])
    weights = np.asarray([0.2, 0.5, 0.3])
    base = weighted_energy_score(observed, ensemble, weights, device)
    permuted = weighted_energy_score(observed, ensemble[permutation], weights[permutation], device)
    assert abs(base - permuted) < 1e-7
    print("PF_DEI_V3_HISTORICAL_PREDICTIVE_SELFTEST=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
