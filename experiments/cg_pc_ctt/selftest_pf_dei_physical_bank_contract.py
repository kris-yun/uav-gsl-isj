#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path
import numpy as np

from pf_dei_physical_bank_contract import validate_bank_mapping, validate_npz, assert_same_source_support


def h(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def fixture(house="House01", run_seed=0):
    S, M, T = 4, 3, 12
    return {
        "candidate_physical_ppm": np.abs(np.arange(S*M*T, dtype=np.float64).reshape(S,M,T) / 100.0),
        "sample_time_s": np.arange(T, dtype=np.float64) * 0.2,
        "pose_xyz_m": np.stack([np.arange(T), np.zeros(T), np.ones(T)], axis=1).astype(np.float64),
        "source_xyz_m": np.asarray([[0,0,0.2],[1,0,0.2],[0,1,0.2],[1,1,0.2]], dtype=np.float64),
        "geometry_prior": np.asarray([1,2,3,4], dtype=np.float64),
        "source_id": np.asarray(["s0","s1","s2","s3"]),
        "transport_id": np.asarray(["m0","m1","m2"]),
        "transport_seed": np.asarray([1000,1001,1002], dtype=np.int64),
        "house": np.asarray(house),
        "run_seed": np.asarray(run_seed, dtype=np.int64),
        "source_support_sha256": np.asarray(h("source-support")),
        "transport_manifest_sha256": np.asarray(h("transport")),
        "trajectory_sha256": np.asarray(h(f"trajectory-{run_seed}")),
        "query_binary_sha256": np.asarray(h("query")),
        "gaden_source_sha256": np.asarray(h("gaden-source")),
        "gaden_config_sha256": np.asarray(h("gaden-config")),
        "overlay_sha256": np.asarray(h("overlay")),
    }


def expect_fail(d, needle: str):
    try:
        validate_bank_mapping(d)
    except ValueError as e:
        if needle not in str(e):
            raise AssertionError((needle, str(e)))
    else:
        raise AssertionError(f"expected failure containing {needle!r}")


def main() -> int:
    d = fixture()
    meta = validate_bank_mapping(d)
    assert (meta["S"], meta["M"], meta["T"]) == (4,3,12)
    assert abs(float(meta["geometry_prior"].sum()) - 1.0) < 1e-15

    bad = dict(d); bad["true_source"] = np.asarray([0.0, 0.0])
    expect_fail(bad, "forbidden")
    bad = dict(d); bad["candidate_physical_ppm"] = d["candidate_physical_ppm"].copy(); bad["candidate_physical_ppm"][0,0,0] = -1.0
    expect_fail(bad, "negative")
    bad = dict(d); bad["source_id"] = np.asarray(["s0","s0","s2","s3"])
    expect_fail(bad, "unique")

    with tempfile.TemporaryDirectory() as td:
        p0 = Path(td) / "a.npz"; p1 = Path(td) / "b.npz"
        np.savez_compressed(p0, **fixture(run_seed=0))
        np.savez_compressed(p1, **fixture(run_seed=1))
        s = validate_npz(p0)
        assert (s.sources, s.members, s.samples) == (4,3,12)
        assert_same_source_support([p0,p1])

        drift = fixture(run_seed=2)
        drift["source_xyz_m"] = drift["source_xyz_m"].copy(); drift["source_xyz_m"][1,0] += 0.1
        p2 = Path(td) / "c.npz"; np.savez_compressed(p2, **drift)
        try:
            assert_same_source_support([p0,p2])
        except ValueError as e:
            assert "identity drift" in str(e)
        else:
            raise AssertionError("source identity drift was not rejected")

    print("PF_DEI_PHYSICAL_BANK_CONTRACT_SELFTEST PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
