#!/usr/bin/env python3
"""Mechanism-only flat-wall probe for M5.

Not a House/GADEN experiment.
Shows that Gaussian proposals + hard wall projection yield a non-Gaussian
realized transition distribution.
"""

import argparse
import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=500_000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--wall-distance", type=float, default=0.02)
    ap.add_argument("--mu-x", type=float, default=-0.03)
    ap.add_argument("--mu-y", type=float, default=0.02)
    ap.add_argument("--std", type=float, default=0.02)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    mu = np.array([args.mu_x, args.mu_y], dtype=float)
    d = rng.normal(mu, args.std, size=(args.n, 2))

    # Wall x=0, free domain x>0, current position=(wall_distance,0).
    x = np.empty_like(d)
    crosses = args.wall_distance + d[:, 0] < 0
    x[:, 0] = args.wall_distance + d[:, 0]
    x[:, 1] = d[:, 1]

    # Local flat-wall approximation to tangential projection.
    x[crosses, 0] = 0.0

    normal = x[:, 0]
    z = (normal - normal.mean()) / normal.std()
    skew = float(np.mean(z**3))
    excess_kurtosis = float(np.mean(z**4) - 3.0)

    print("M5 flat-wall mechanism probe")
    print(f"n={args.n}")
    print(f"collision_fraction={crosses.mean():.8f}")
    print(f"normal_skewness={skew:.8f}")
    print(f"normal_excess_kurtosis={excess_kurtosis:.8f}")
    print("NOTE: mechanism unit test only; not House evidence.")


if __name__ == "__main__":
    main()
