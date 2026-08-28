#!/usr/bin/env python3

from __future__ import annotations

import numpy as np

from pf_dei_v3_features import CarrierDescriptor, build_features


def main() -> int:
    schedule = {
        "x": np.array([1.0, 1.1, 1.2], dtype=np.float32),
        "y": np.array([2.0, 2.0, 2.0], dtype=np.float32),
        "dt": np.array([0.2, 0.2, 0.2], dtype=np.float32),
        "stop_start": np.array([1, 0, 0], dtype=np.float32),
        "block_boundary": np.array([1, 0, 0], dtype=np.float32),
    }
    carrier = CarrierDescriptor("H01", 0, "c0", 0.5, 1.5, 0.6, 0.6, (1, 0, 1, 1), 3, 0.25)
    ppm = np.array([0.0, 0.1, 0.3])
    wind = np.arange(9, dtype=np.float32).reshape(3, 3)
    features = build_features(schedule, ppm, wind, carrier)
    assert features.shape == (3, 16)
    assert np.allclose(features[:, 0], np.array([0.5, 0.6, 0.7], dtype=np.float32))
    assert np.array_equal(features[:, 4:8], np.array([[1, 0, 1, 1]] * 3, dtype=np.float32))
    assert np.array_equal(features[:, 10:13], wind)
    assert np.allclose(features[:, 9], np.log1p(ppm / 0.1))
    assert np.isfinite(features).all()
    print("PF_DEI_V3_FEATURE_SELFTEST PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
