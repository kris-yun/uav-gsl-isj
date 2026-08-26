#!/usr/bin/env python3
"""CG-PC-CTT V15 proximal causal bridge (regularized sieve-GMM).

The bridge is deliberately separate from frozen CTT M1.  It estimates h(R,S)
from development data using candidate/source-side proxy Z only through moment
conditions:

    E[ g(Z,S) * (Y - h(R,S)) ] = 0.

Z is never an input to h at inference.  R must be candidate-independent within
one observation event.  Truth labels are allowed only in the offline panel
used to score source ordering after the model and regularization are frozen.

This is an operational proximal bridge diagnostic, not a claim that the
project-specific finite-dimensional sieve proves a general proximal
identification theorem.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import pathlib

import numpy as np


RIDGE_GRID = np.array([1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 1e-1], dtype=float)
EPS = 1e-12
SEED = 20260827

TRAIN_KEYS = {"y", "r", "s", "z"}
PANEL_KEYS = {"event_id", "candidate_id", "is_true", "y", "r", "s", "z"}
FORBIDDEN_RUNTIME_NAMES = {
    "source_truth", "truth_x", "truth_y", "wind_id", "route_id",
    "plume_seed", "simulator_phase", "oracle_field", "future_data",
}


def load_npz(path: pathlib.Path, panel: bool):
    data = np.load(path, allow_pickle=False)
    keys = set(data.files)
    expected = PANEL_KEYS if panel else TRAIN_KEYS
    missing = expected - keys
    if missing:
        raise ValueError(f"{path}: missing keys {sorted(missing)}")
    forbidden = keys & FORBIDDEN_RUNTIME_NAMES
    if forbidden:
        raise ValueError(f"{path}: forbidden fields {sorted(forbidden)}")
    return {k: np.asarray(data[k]) for k in expected}


def read_contract(path: pathlib.Path):
    contract_path = path.with_suffix(path.suffix + ".contract.json")
    c = json.loads(contract_path.read_text())
    required_true = [
        "runtime_forbidden_fields_absent",
        "r_candidate_independent",
        "source_coordinates_are_synthetic_interventions_or_queries",
        "test_not_used_for_tuning",
    ]
    bad = [k for k in required_true if c.get(k) is not True]
    if bad:
        raise ValueError(f"{contract_path}: contract fields not true: {bad}")
    return c


def as2(x):
    x = np.asarray(x, dtype=np.float64)
    return x[:, None] if x.ndim == 1 else x


class Standardizer:
    def fit(self, x):
        x = as2(x)
        self.mean = x.mean(axis=0)
        self.std = x.std(axis=0)
        self.std[self.std < 1e-8] = 1.0
        return self

    def transform(self, x):
        return (as2(x) - self.mean) / self.std


def poly2(x):
    """Compact fixed second-order sieve: 1, x, squares, pair interactions."""
    x = as2(x)
    n, d = x.shape
    cols = [np.ones((n, 1), dtype=np.float64), x, x * x]
    if d > 1:
        inter = [x[:, i:i+1] * x[:, j:j+1]
                 for i in range(d) for j in range(i + 1, d)]
        cols.extend(inter)
    return np.concatenate(cols, axis=1)


class Bridge:
    def __init__(self, ridge: float):
        self.ridge = float(ridge)

    def fit(self, d):
        y = as2(d["y"])
        r = as2(d["r"])
        s = as2(d["s"])
        z = as2(d["z"])
        n = len(y)
        if not (len(r) == len(s) == len(z) == n):
            raise ValueError("row count mismatch")

        self.rs_scaler = Standardizer().fit(np.concatenate([r, s], axis=1))
        self.zs_scaler = Standardizer().fit(np.concatenate([z, s], axis=1))
        h = poly2(self.rs_scaler.transform(np.concatenate([r, s], axis=1)))
        g = poly2(self.zs_scaler.transform(np.concatenate([z, s], axis=1)))

        # Scale columns after basis expansion using training data only.
        self.h_basis_scale = np.sqrt((h * h).mean(axis=0))
        self.g_basis_scale = np.sqrt((g * g).mean(axis=0))
        self.h_basis_scale[self.h_basis_scale < 1e-8] = 1.0
        self.g_basis_scale[self.g_basis_scale < 1e-8] = 1.0
        h = h / self.h_basis_scale
        g = g / self.g_basis_scale

        a = (g.T @ h) / n
        b = (g.T @ y) / n
        lhs = a.T @ a + self.ridge * np.eye(a.shape[1])
        rhs = a.T @ b
        self.beta = np.linalg.solve(lhs, rhs)
        return self

    def _h(self, r, s):
        x = np.concatenate([as2(r), as2(s)], axis=1)
        return poly2(self.rs_scaler.transform(x)) / self.h_basis_scale

    def _g(self, z, s):
        x = np.concatenate([as2(z), as2(s)], axis=1)
        return poly2(self.zs_scaler.transform(x)) / self.g_basis_scale

    def predict(self, r, s):
        return self._h(r, s) @ self.beta

    def moment_loss(self, d):
        y = as2(d["y"])
        residual = y - self.predict(d["r"], d["s"])
        g = self._g(d["z"], d["s"])
        moment = (g.T @ residual) / len(y)
        return float(np.mean(moment * moment))

    def mse(self, d):
        residual = as2(d["y"]) - self.predict(d["r"], d["s"])
        return float(np.mean(residual * residual))


class DirectRidge:
    """Non-proximal same-sieve comparator fit by prediction loss."""

    def __init__(self, ridge):
        self.ridge = float(ridge)

    def fit(self, d):
        y = as2(d["y"])
        r = as2(d["r"])
        s = as2(d["s"])
        x = np.concatenate([r, s], axis=1)
        self.scaler = Standardizer().fit(x)
        h = poly2(self.scaler.transform(x))
        self.scale = np.sqrt((h * h).mean(axis=0))
        self.scale[self.scale < 1e-8] = 1.0
        h = h / self.scale
        self.beta = np.linalg.solve(
            h.T @ h + self.ridge * np.eye(h.shape[1]),
            h.T @ y,
        )
        return self

    def predict(self, r, s):
        x = np.concatenate([as2(r), as2(s)], axis=1)
        h = poly2(self.scaler.transform(x)) / self.scale
        return h @ self.beta

    def mse(self, d):
        residual = as2(d["y"]) - self.predict(d["r"], d["s"])
        return float(np.mean(residual * residual))


def audit_panel(d):
    event = d["event_id"]
    cand = d["candidate_id"]
    truth = np.asarray(d["is_true"]).astype(int)
    if not np.all(np.isin(truth, [0, 1])):
        raise ValueError("is_true must be binary evaluation-only marker")
    for e in np.unique(event):
        idx = np.flatnonzero(event == e)
        if truth[idx].sum() != 1:
            raise ValueError(f"event {e}: expected exactly one true candidate")
        if len(np.unique(cand[idx])) != len(idx):
            raise ValueError(f"event {e}: duplicate candidate_id")
        r = as2(d["r"])[idx]
        y = as2(d["y"])[idx]
        if np.max(np.abs(r - r[0])) > 1e-10:
            raise ValueError(f"event {e}: R changes across candidates")
        if np.max(np.abs(y - y[0])) > 1e-10:
            raise ValueError(f"event {e}: Y changes across candidates")


def panel_scores(model, d):
    audit_panel(d)
    pred = model.predict(d["r"], d["s"])
    y = as2(d["y"])
    err = np.mean((y - pred) ** 2, axis=1)
    margins = []
    ranks = []
    for e in np.unique(d["event_id"]):
        idx = np.flatnonzero(d["event_id"] == e)
        local = err[idx]
        true_local = int(np.flatnonzero(np.asarray(d["is_true"])[idx] == 1)[0])
        false = np.delete(local, true_local)
        margin = float(false.min() - local[true_local])
        rank = int(np.argsort(local).tolist().index(true_local) + 1)
        margins.append(margin)
        ranks.append(rank)
    margins = np.asarray(margins)
    ranks = np.asarray(ranks)
    return {
        "events": int(len(margins)),
        "top1": float(np.mean(ranks == 1)),
        "median_rank": float(np.median(ranks)),
        "margin_mean": float(margins.mean()),
        "margin_median": float(np.median(margins)),
        "positive_margin_fraction": float(np.mean(margins > 0)),
    }


def select_ridge(train, dev):
    rows = []
    for ridge in RIDGE_GRID:
        b = Bridge(ridge).fit(train)
        rows.append({
            "ridge": float(ridge),
            "dev_moment_loss": b.moment_loss(dev),
            "dev_mse": b.mse(dev),
        })
    # The moment restriction is primary. MSE breaks numerical ties only.
    best = min(rows, key=lambda x: (x["dev_moment_loss"], x["dev_mse"], x["ridge"]))
    return best["ridge"], rows


def select_direct_ridge(train, dev):
    rows = []
    for ridge in RIDGE_GRID:
        b = DirectRidge(ridge).fit(train)
        rows.append({"ridge": float(ridge), "dev_mse": b.mse(dev)})
    best = min(rows, key=lambda x: (x["dev_mse"], x["ridge"]))
    return best["ridge"], rows


def z_shuffle_control(train):
    rng = np.random.default_rng(SEED)
    out = {k: np.array(v, copy=True) for k, v in train.items()}
    out["z"] = out["z"][rng.permutation(len(out["z"]))]
    return out


def s_shuffle_control(train):
    rng = np.random.default_rng(SEED + 1)
    out = {k: np.array(v, copy=True) for k, v in train.items()}
    out["s"] = out["s"][rng.permutation(len(out["s"]))]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("train_npz", type=pathlib.Path)
    ap.add_argument("dev_npz", type=pathlib.Path)
    ap.add_argument("dev_panel_npz", type=pathlib.Path)
    ap.add_argument("test_panel_npz", type=pathlib.Path)
    ap.add_argument("output_root", type=pathlib.Path)
    args = ap.parse_args()

    if args.output_root.exists():
        raise SystemExit(f"refuse overwrite: {args.output_root}")
    args.output_root.mkdir(parents=True)

    for p in (args.train_npz, args.dev_npz, args.dev_panel_npz, args.test_panel_npz):
        read_contract(p)

    train = load_npz(args.train_npz, panel=False)
    dev = load_npz(args.dev_npz, panel=False)
    dev_panel = load_npz(args.dev_panel_npz, panel=True)
    test_panel = load_npz(args.test_panel_npz, panel=True)
    audit_panel(dev_panel)
    audit_panel(test_panel)

    ridge, bridge_grid = select_ridge(train, dev)
    direct_ridge, direct_grid = select_direct_ridge(train, dev)
    bridge = Bridge(ridge).fit(train)
    direct = DirectRidge(direct_ridge).fit(train)

    dev_bridge = panel_scores(bridge, dev_panel)
    dev_direct = panel_scores(direct, dev_panel)

    # Freeze bridge/ridge before touching final panel.
    test_bridge = panel_scores(bridge, test_panel)
    test_direct = panel_scores(direct, test_panel)

    zc = Bridge(ridge).fit(z_shuffle_control(train))
    sc = Bridge(ridge).fit(s_shuffle_control(train))
    test_z_shuffle = panel_scores(zc, test_panel)
    test_s_shuffle = panel_scores(sc, test_panel)

    # Minimal preregistered GO: bridge must improve the frozen source-ordering
    # endpoint over the same-sieve direct predictor on both dev and test; the
    # final gain cannot survive both causal negative controls.
    dev_gain = dev_bridge["margin_mean"] - dev_direct["margin_mean"]
    test_gain = test_bridge["margin_mean"] - test_direct["margin_mean"]
    control_erased = (
        test_z_shuffle["margin_mean"] <= test_bridge["margin_mean"] - 0.5 * max(test_gain, 0.0)
        or test_s_shuffle["margin_mean"] <= test_bridge["margin_mean"] - 0.5 * max(test_gain, 0.0)
    )
    go = (
        dev_gain > 0.0
        and test_gain > 0.0
        and test_bridge["positive_margin_fraction"] >= test_direct["positive_margin_fraction"]
        and control_erased
    )

    result = {
        "gate": "CG_PC_CTT_V15_PROXIMAL_BRIDGE_MOMENT_GATE",
        "status": "GO" if go else "NO_GO",
        "scientific_boundary": (
            "finite-dimensional regularized sieve-GMM operationalization of a "
            "proximal bridge moment condition; not a general identification theorem"
        ),
        "ridge_selected_on_dev_only": ridge,
        "direct_ridge_selected_on_dev_only": direct_ridge,
        "bridge_grid": bridge_grid,
        "direct_grid": direct_grid,
        "dev": {"bridge": dev_bridge, "direct": dev_direct, "margin_gain": dev_gain},
        "final_test": {
            "bridge": test_bridge,
            "direct": test_direct,
            "margin_gain": test_gain,
            "z_shuffle_control": test_z_shuffle,
            "source_shuffle_control": test_s_shuffle,
            "control_erased": control_erased,
        },
    }
    (args.output_root / "proximal_bridge_result.json").write_text(json.dumps(result, indent=2))
    contract = {
        "script_sha256": hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
        "ridge_grid": RIDGE_GRID.tolist(),
        "seed": SEED,
        "test_used_for_tuning": False,
        "z_used_at_inference": False,
        "r_must_be_candidate_independent": True,
    }
    (args.output_root / "proximal_bridge_contract.json").write_text(json.dumps(contract, indent=2))
    print(json.dumps(result, indent=2))
    return 0 if go else 2


if __name__ == "__main__":
    raise SystemExit(main())
