#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import importlib.util
from pathlib import Path
import sys

import numpy as np

from pf_dei_v3_sensor_forward import (
    AUTHORITATIVE_SENSOR_SOURCE_SHA256,
    SENSOR_CONFIG,
    SENSOR_SEED,
    forward_sensor,
    forward_sensor_batch,
    parameter_sha256,
)


EXPECTED_PARAMETER_SHA256 = "c0d6ce446ee3172b203147f8f7884b05d55f7f03dcd86d78a83b732dc119aa76"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authoritative", type=Path)
    args = parser.parse_args()
    assert parameter_sha256() == EXPECTED_PARAMETER_SHA256
    rng = np.random.default_rng(20260828)
    physical = rng.lognormal(mean=-1.0, sigma=1.5, size=1000)
    physical[100:170] = 0.0
    physical[500:650] *= 10.0
    actual = forward_sensor(physical)
    assert np.isfinite(actual).all() and (actual >= 0).all()
    reset = np.concatenate([forward_sensor(physical[:500]), forward_sensor(physical[500:])])
    assert not np.array_equal(actual, reset)
    batch = np.stack((physical, physical * 0.5, physical * 2.0))
    batched = forward_sensor_batch(batch)
    expected_batch = np.stack([forward_sensor(row) for row in batch])
    assert float(np.max(np.abs(batched - expected_batch))) < 1e-11
    assert np.array_equal(batched.astype(np.float32), expected_batch.astype(np.float32))

    if args.authoritative:
        digest = hashlib.sha256(args.authoritative.read_bytes()).hexdigest()
        assert digest == AUTHORITATIVE_SENSOR_SOURCE_SHA256, digest
        spec = importlib.util.spec_from_file_location("authoritative_sensor", args.authoritative)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        kwargs = {key: value for key, value in SENSOR_CONFIG.items() if key != "mode"}
        reference = module.SensorModel(mode="dynamic", seed=SENSOR_SEED, **kwargs)
        expected = np.asarray([reference.process(float(value), 0.2) for value in physical])
        assert np.array_equal(actual, expected), float(np.max(np.abs(actual - expected)))

    print("PF_DEI_V3_SENSOR_FORWARD_SELFTEST PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
