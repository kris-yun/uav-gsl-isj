#!/usr/bin/env python3
"""Truth-free CTT M1 wind-conditioned first-passage premise gate.

The script never accepts or reads a real source truth.  It compares two
capacity-matched coordinate neural fields on simulator traces.  The only
difference is whether current wind-path features or the training-mean wind
features are supplied.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import pathlib
import random
import struct
import time

import numpy as np
import torch
from scipy.spatial import cKDTree


TRAIN_CONTEXTS = (0, 3, 5, 6, 8, 9)
VAL_CONTEXTS = (4, 7)
TEST_CONTEXTS = (1, 2)
TRAIN_MEMBERS = (0, 1, 2, 3, 4, 5)
HELDOUT_MEMBERS = (6, 7)
TIMESTEPS = 200
NEVER = TIMESTEPS
SEED = 20260826
RAY_SAMPLES = 9
MAX_EPOCHS = 30
PATIENCE = 5
BATCH_SIZE = 4096
HIDDEN = 128
BOOTSTRAPS = 10000


def read_csv(path: pathlib.Path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def read_first_hits(path: pathlib.Path) -> np.ndarray:
    with path.open("rb") as f:
        header = f.read(7 * 8)
        if len(header) != 56:
            raise ValueError(f"short header: {path}")
        _, version, _, _, timesteps, cell_count, _ = struct.unpack("<7Q", header)
        if version != 1 or timesteps != TIMESTEPS:
            raise ValueError((path, version, timesteps))
        f.seek(56 + 4 * timesteps)
        raw = f.read(4 * cell_count)
        if len(raw) != 4 * cell_count:
            raise ValueError(f"short firstHit payload: {path}")
    arr = np.frombuffer(raw, dtype="<i4").copy()
    arr[arr < 0] = NEVER
    if np.any(arr > NEVER):
        raise ValueError(f"invalid firstHit: {path}")
    return arr.astype(np.int16)


def load_bank(root: pathlib.Path):
    manifest = read_csv(root / "context_manifest.csv")
    by_index = {int(r["context_index"]): r for r in manifest}
    if set(by_index) != set(range(10)):
        raise ValueError("expected exactly contexts 0..9")

    dirs = {}
    winds = {}
    hits = None
    carriers = None
    free_indices = None
    query_xy = None
    for c in range(10):
        matches = list(root.glob(f"context_{c:02d}_*"))
        if len(matches) != 1:
            raise ValueError((c, matches))
        d = matches[0]
        dirs[c] = d
        contract = json.loads((d / "ctt_trace_bank_contract.json").read_text())
        if contract["source_truth_used"] is not False:
            raise ValueError("truth-bearing bank is prohibited")
        if contract["timesteps"] != TIMESTEPS or contract["transport_members"] != 8:
            raise ValueError("trace contract mismatch")
        wind_rows = read_csv(d / "estimated_wind.csv")
        idx = np.array([int(r["cell_index"]) for r in wind_rows], dtype=np.int32)
        xy = np.array([[float(r["x"]), float(r["y"])] for r in wind_rows], dtype=np.float32)
        w = np.array([[float(r["wind_x"]), float(r["wind_y"])] for r in wind_rows], dtype=np.float32)
        if c == 0:
            free_indices, query_xy = idx, xy
            carrier_rows = read_csv(d / "carrier_manifest.csv")
            carriers = np.array([[float(r["x"]), float(r["y"])] for r in carrier_rows], dtype=np.float32)
            hits = np.empty((10, len(carriers), len(query_xy), 8), dtype=np.int16)
        elif not np.array_equal(idx, free_indices) or not np.allclose(xy, query_xy, atol=1e-7):
            raise ValueError(f"free support drift in context {c}")
        winds[c] = w
        for s in range(len(carriers)):
            for k in range(8):
                a = read_first_hits(d / "records" / f"carrier_{s:04d}_member_{k:02d}.cttbin")
                hits[c, s, :, k] = a[free_indices]
    return carriers, query_xy, np.stack([winds[c] for c in range(10)]), hits


def build_features(carriers: np.ndarray, query_xy: np.ndarray, winds: np.ndarray):
    ns, nq = len(carriers), len(query_xy)
    sxy = np.repeat(carriers, nq, axis=0)
    qxy = np.tile(query_xy, (ns, 1))
    delta = qxy - sxy
    dist = np.linalg.norm(delta, axis=1, keepdims=True)
    unit = delta / np.maximum(dist, 1e-6)

    # Geometry is enforced by a fixed free-support mask and summarized along
    # the straight source-query chord; it never uses truth or posterior data.
    tree = cKDTree(query_xy)
    alphas = np.linspace(0.0, 1.0, RAY_SAMPLES, dtype=np.float32)
    ray = sxy[:, None, :] * (1.0 - alphas[None, :, None]) + qxy[:, None, :] * alphas[None, :, None]
    nearest_dist, nearest_idx = tree.query(ray.reshape(-1, 2), k=1)
    nearest_dist = nearest_dist.reshape(-1, RAY_SAMPLES).astype(np.float32)
    nearest_idx = nearest_idx.reshape(-1, RAY_SAMPLES)
    free_fraction = (nearest_dist <= 0.16).mean(axis=1, keepdims=True).astype(np.float32)
    base = np.concatenate([sxy, qxy, delta, dist, unit, free_fraction], axis=1).astype(np.float32)

    contextual = np.empty((10, ns * nq, 10), dtype=np.float32)
    source_nearest = tree.query(carriers, k=1)[1]
    for c in range(10):
        w = winds[c]
        ws = np.repeat(w[source_nearest], nq, axis=0)
        wq = np.tile(w, (ns, 1))
        wray = w[nearest_idx]
        meanw = wray.mean(axis=1)
        stdw = wray.std(axis=1)
        parallel = np.sum(meanw * unit, axis=1, keepdims=True)
        perp = meanw[:, 0:1] * (-unit[:, 1:2]) + meanw[:, 1:2] * unit[:, 0:1]
        contextual[c] = np.concatenate([ws, wq, meanw, stdw, parallel, perp], axis=1)
    return base, contextual


class Field(torch.nn.Module):
    def __init__(self, in_dim: int):
        super().__init__()
        self.net = torch.nn.Sequential(
            torch.nn.Linear(in_dim, HIDDEN), torch.nn.SiLU(),
            torch.nn.Linear(HIDDEN, HIDDEN), torch.nn.SiLU(),
            torch.nn.Linear(HIDDEN, HIDDEN), torch.nn.SiLU(),
            torch.nn.Linear(HIDDEN, TIMESTEPS + 1),
        )

    def forward(self, x):
        return self.net(x)


def fit_one(name, x_train, y_train, x_val, y_val, out: pathlib.Path):
    torch.manual_seed(SEED)
    model = Field(x_train.shape[1])
    opt = torch.optim.AdamW(model.parameters(), lr=2e-3, weight_decay=1e-5)
    gen = torch.Generator().manual_seed(SEED)
    best = math.inf
    best_epoch = -1
    stale = 0
    history = []
    train_ds = torch.utils.data.TensorDataset(torch.from_numpy(x_train), torch.from_numpy(y_train))
    loader = torch.utils.data.DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True, generator=gen)
    xv = torch.from_numpy(x_val)
    yv = torch.from_numpy(y_val)
    for epoch in range(MAX_EPOCHS):
        model.train()
        total = count = 0
        for xb, labels in loader:
            logp = torch.log_softmax(model(xb), dim=1)
            loss = -logp.gather(1, labels.long()).mean()
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            total += float(loss) * len(xb)
            count += len(xb)
        model.eval()
        with torch.no_grad():
            val_total = 0.0
            for start in range(0, len(xv), BATCH_SIZE):
                logp = torch.log_softmax(model(xv[start:start+BATCH_SIZE]), dim=1)
                labels = yv[start:start+BATCH_SIZE].long()
                val_total += float(-logp.gather(1, labels).sum())
            val_nll = val_total / yv.numel()
        history.append({"epoch": epoch, "train_nll": total / count, "val_nll": val_nll})
        if val_nll < best - 1e-5:
            best, best_epoch, stale = val_nll, epoch, 0
            torch.save(model.state_dict(), out / f"{name}_best.pt")
        else:
            stale += 1
            if stale >= PATIENCE:
                break
    model.load_state_dict(torch.load(out / f"{name}_best.pt", weights_only=True))
    (out / f"{name}_history.json").write_text(json.dumps(history, indent=2))
    return model, best_epoch, best


def predict(model, x):
    model.eval()
    chunks = []
    t0 = time.perf_counter()
    with torch.no_grad():
        tx = torch.from_numpy(x)
        for start in range(0, len(tx), BATCH_SIZE):
            chunks.append(torch.softmax(model(tx[start:start+BATCH_SIZE]), dim=1).numpy())
    elapsed = time.perf_counter() - t0
    return np.concatenate(chunks), elapsed


def scores(prob: np.ndarray, labels: np.ndarray):
    # labels: [pairs, heldout_members]; return one score per pair/member.
    p = np.clip(prob, 1e-12, 1.0)
    nll = -np.log(np.take_along_axis(p[:, None, :], labels[:, :, None], axis=2)[:, :, 0])
    cdf = np.cumsum(prob[:, :TIMESTEPS], axis=1)
    thresholds = np.arange(TIMESTEPS)[None, None, :]
    obs = (labels[:, :, None] <= thresholds).astype(np.float32)
    brier = np.mean((cdf[:, None, :] - obs) ** 2, axis=2)
    return nll, brier


def cluster_scores(values: np.ndarray, contexts, ns, nq):
    # Average query cells, leaving context x carrier x member as independent
    # resampling clusters.
    return values.reshape(len(contexts), ns, nq, len(HELDOUT_MEMBERS)).mean(axis=2).reshape(-1)


def bootstrap_ci(delta: np.ndarray):
    rng = np.random.default_rng(SEED)
    means = np.empty(BOOTSTRAPS, dtype=np.float64)
    n = len(delta)
    for i in range(BOOTSTRAPS):
        means[i] = delta[rng.integers(0, n, n)].mean()
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bank_root", type=pathlib.Path)
    ap.add_argument("output_root", type=pathlib.Path)
    args = ap.parse_args()
    if args.output_root.exists():
        raise SystemExit(f"refuse overwrite: {args.output_root}")
    args.output_root.mkdir(parents=True)
    random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)
    torch.set_num_threads(4)

    carriers, queries, winds, hits = load_bank(args.bank_root)
    base, wind_feat = build_features(carriers, queries, winds)
    ns, nq = len(carriers), len(queries)
    npairs = ns * nq

    train_wind_mean = wind_feat[list(TRAIN_CONTEXTS)].mean(axis=(0, 1), keepdims=True)
    static_wind = np.broadcast_to(train_wind_mean, (10, npairs, wind_feat.shape[2])).copy()
    all_cond = np.concatenate([np.broadcast_to(base, (10, *base.shape)), wind_feat], axis=2)
    all_static = np.concatenate([np.broadcast_to(base, (10, *base.shape)), static_wind], axis=2)

    # Fit normalization only on training contexts.  Both arms share it.
    norm_source = all_cond[list(TRAIN_CONTEXTS)].reshape(-1, all_cond.shape[2])
    mean = norm_source.mean(axis=0)
    std = norm_source.std(axis=0); std[std < 1e-8] = 1.0
    all_cond = ((all_cond - mean) / std).astype(np.float32)
    all_static = ((all_static - mean) / std).astype(np.float32)

    def xy(contexts, x):
        xx = x[list(contexts)].reshape(-1, x.shape[2])
        yy = hits[list(contexts)][..., list(TRAIN_MEMBERS)].reshape(-1, len(TRAIN_MEMBERS))
        return xx, yy

    xc_tr, ytr = xy(TRAIN_CONTEXTS, all_cond)
    xs_tr, _ = xy(TRAIN_CONTEXTS, all_static)
    xc_va = all_cond[list(VAL_CONTEXTS)].reshape(-1, all_cond.shape[2])
    xs_va = all_static[list(VAL_CONTEXTS)].reshape(-1, all_static.shape[2])
    yva = hits[list(VAL_CONTEXTS)][..., list(HELDOUT_MEMBERS)].reshape(-1, len(HELDOUT_MEMBERS))

    conditional, ce, cv = fit_one("conditional", xc_tr, ytr, xc_va, yva, args.output_root)
    static, se, sv = fit_one("static", xs_tr, ytr, xs_va, yva, args.output_root)

    xc_te = all_cond[list(TEST_CONTEXTS)].reshape(-1, all_cond.shape[2])
    xs_te = all_static[list(TEST_CONTEXTS)].reshape(-1, all_static.shape[2])
    yte = hits[list(TEST_CONTEXTS)][..., list(HELDOUT_MEMBERS)].reshape(-1, len(HELDOUT_MEMBERS))
    pc, tc = predict(conditional, xc_te)
    ps, ts = predict(static, xs_te)
    cn, cb = scores(pc, yte); sn, sb = scores(ps, yte)

    cn_c = cluster_scores(cn, TEST_CONTEXTS, ns, nq)
    sn_c = cluster_scores(sn, TEST_CONTEXTS, ns, nq)
    cb_c = cluster_scores(cb, TEST_CONTEXTS, ns, nq)
    sb_c = cluster_scores(sb, TEST_CONTEXTS, ns, nq)
    dn = sn_c - cn_c
    db = sb_c - cb_c
    nci = bootstrap_ci(dn); bci = bootstrap_ci(db)
    per_context = {}
    for j, c in enumerate(TEST_CONTEXTS):
        sl = slice(j * npairs, (j + 1) * npairs)
        per_context[str(c)] = {
            "conditional_nll": float(cn[sl].mean()), "static_nll": float(sn[sl].mean()),
            "conditional_brier": float(cb[sl].mean()), "static_brier": float(sb[sl].mean()),
        }

    normalization_error = float(np.max(np.abs(pc.sum(axis=1) - 1.0)))
    result = {
        "gate": "CTT_M1_WIND_CONDITIONED_FIRST_PASSAGE_V1",
        "truth_used": False,
        "train_contexts": TRAIN_CONTEXTS, "val_contexts": VAL_CONTEXTS, "test_contexts": TEST_CONTEXTS,
        "train_members": TRAIN_MEMBERS, "heldout_members": HELDOUT_MEMBERS,
        "native_classes": TIMESTEPS + 1,
        "conditional_best_epoch": ce, "static_best_epoch": se,
        "conditional_val_nll": cv, "static_val_nll": sv,
        "conditional_test_nll": float(cn.mean()), "static_test_nll": float(sn.mean()),
        "nll_improvement": float(dn.mean()), "nll_improvement_95ci": nci,
        "conditional_test_brier": float(cb.mean()), "static_test_brier": float(sb.mean()),
        "brier_improvement": float(db.mean()), "brier_improvement_95ci": bci,
        "per_test_context": per_context,
        "normalization_max_abs": normalization_error,
        "conditional_inference_seconds": tc,
        "conditional_microseconds_per_source_query": 1e6 * tc / len(xc_te),
    }
    context_consistent = all(
        v["conditional_nll"] < v["static_nll"] and v["conditional_brier"] < v["static_brier"]
        for v in per_context.values())
    passed = (dn.mean() > 0 and nci[0] > 0 and db.mean() > 0 and bci[0] > 0
              and context_consistent and normalization_error < 1e-5)
    result["verdict"] = "M1_DIRECT_GO" if passed else "M1_DIRECT_NO_GO"
    (args.output_root / "m1_gate_result.json").write_text(json.dumps(result, indent=2))
    contract = {
        "script_sha256": hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
        "bank_manifest_sha256": hashlib.sha256((args.bank_root / "context_manifest.csv").read_bytes()).hexdigest(),
        "architecture": f"MLP-{HIDDEN}x3-SiLU-{TIMESTEPS+1}",
        "max_epochs": MAX_EPOCHS, "patience": PATIENCE, "batch_size": BATCH_SIZE,
        "seed": SEED, "bootstrap_clusters": "context-carrier-heldout_member",
    }
    (args.output_root / "frozen_gate_contract.json").write_text(json.dumps(contract, indent=2))
    print(json.dumps(result, indent=2))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
