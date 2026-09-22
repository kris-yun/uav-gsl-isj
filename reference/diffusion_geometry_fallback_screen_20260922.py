#!/usr/bin/env python3
"""Discovery-only fallback screen for hypothesis-conditioned diffusion geometry.

IMPORTANT:
- old frozen six-case discovery archive only;
- rapid Python ceil/stable-tie endpoint clone;
- not the authoritative linked-native endpoint used by the active HCMC gate;
- do not tune the active independent HCMC validation from these results.
"""
import os, glob, json, math
import numpy as np
import pandas as pd
from scipy.stats import rankdata
from scipy.sparse import coo_matrix, diags, eye
from scipy.sparse.linalg import expm_multiply

BASE = os.environ.get(
    "HCDG_NATIVE_ROOT",
    "/path/to/tnqc_r2_six_offline_20260921_authoritative/native",
)
TRUTH = {
    "House01": (-0.4, -2.9),
    "House02": (0.0, -1.0),
    "House03": (-0.45, 1.9),
}
CONF = 1e-6
FAMILIES = {
    "fast": [0, 0.25, 0.5, 1, 2, 4],
    "mid": [0, 0.5, 1, 2, 4, 8],
    "slow": [0, 1, 2, 4, 8, 16],
}

def endpoint(meas, weights):
    free = meas.occupancy.eq("Free").to_numpy()
    inds = np.flatnonzero(free)
    order = np.argsort(-weights[inds], kind="stable")
    n = max(1, math.ceil(0.05 * len(inds)))
    sel = inds[order[:n]]
    mass = weights[sel].sum()
    x = np.dot(meas.x.to_numpy()[sel], weights[sel]) / mass
    y = np.dot(meas.y.to_numpy()[sel], weights[sel]) / mass
    return x, y

def percentile_ranks(scores, ids):
    values = np.array([scores.get(cid, np.nan) for cid in ids])
    good = np.isfinite(values)
    density = np.zeros(len(values))
    density[good] = rankdata(values[good], method="average") / good.sum()
    return dict(zip(ids, density))

def posterior_from_leaf_density(density, ids, manifest, meas):
    gi = meas.grid_i.to_numpy()
    gj = meas.grid_j.to_numpy()
    free = meas.occupancy.eq("Free").to_numpy()
    w = np.zeros(len(meas))
    for row in manifest[manifest.candidate_id.isin(ids)].itertuples(index=False):
        mask = (
            (gi >= row.origin_i)
            & (gi < row.origin_i + row.size_i)
            & (gj >= row.origin_j)
            & (gj < row.origin_j + row.size_j)
            & free
        )
        w[mask] = density.get(row.candidate_id, 0.0)
    w /= w.sum()
    return w

def prepare_case(run):
    update = os.path.join(run, "context_bank", "source_update_0005")
    align = pd.read_csv(os.path.join(update, "candidate_support_alignment.csv"))
    manifest = pd.read_csv(os.path.join(update, "candidate_manifest.csv"))
    meas = pd.read_csv(os.path.join(update, "measured_hit_probability.csv"))
    evaluation = json.load(open(os.path.join(run, "tnqc_fixed_trajectory_evaluation.json")))
    ids = evaluation["tnqc_gate_scope_audit"]["final_leaf_candidate_ids"]

    ref = align[
        (align.candidate_id == ids[0]) & (align.measured_confidence > CONF)
    ].sort_values(["grid_j", "grid_i"])
    coords = list(zip(ref.grid_i.astype(int), ref.grid_j.astype(int)))
    index = {coord: k for k, coord in enumerate(coords)}

    rr, cc = [], []
    for (i, j), k in index.items():
        for nb in ((i+1,j),(i-1,j),(i,j+1),(i,j-1)):
            q = index.get(nb)
            if q is not None:
                rr.append(k)
                cc.append(q)
    A = coo_matrix(
        (np.ones(len(rr)), (rr, cc)), shape=(len(coords), len(coords))
    ).tocsr()
    degree = np.asarray(A.sum(1)).ravel()
    inv = np.zeros(len(coords))
    inv[degree > 0] = 1.0 / np.sqrt(degree[degree > 0])
    L = eye(len(coords)) - diags(inv) @ A @ diags(inv)

    confidence = ref.measured_confidence.to_numpy(float)
    confidence /= confidence.sum()
    columns = [ref.measured_probability.to_numpy(float)]
    valid_ids = []

    for cid in ids:
        rows = align[
            (align.candidate_id == cid) & (align.measured_confidence > CONF)
        ]
        sim = {
            (int(r.grid_i), int(r.grid_j)): float(r.simulated_hit_probability)
            for r in rows.itertuples()
        }
        if all(coord in sim for coord in coords):
            columns.append(np.array([sim[coord] for coord in coords]))
            valid_ids.append(cid)

    F = np.column_stack(columns)
    F = F - (confidence[:, None] * F).sum(axis=0, keepdims=True)
    return align, manifest, meas, evaluation, ids, valid_ids, L, confidence, F

def hcdg_scores(L, F, times):
    eps = 1e-12
    energies = []
    for t in times:
        H = F if t == 0 else expm_multiply(-t * L, F)
        energies.append(np.sum(H * (L @ H), axis=0))
    energies = np.stack(energies)
    log_decay = np.log(np.maximum(energies / (energies[0:1] + eps), eps))
    measured = log_decay[:, 0]
    return -np.mean(np.abs(log_decay[:, 1:] - measured[:, None]), axis=0)

cases = []
for run in sorted(glob.glob(os.path.join(BASE, "House*_seed*_off_off"))):
    prepared = prepare_case(run)
    align, manifest, meas, evaluation, ids, valid_ids, L, confidence, F = prepared
    house = os.path.basename(run).split("_")[0]
    tx, ty = TRUTH[house]
    record = {
        "case": os.path.basename(run),
        "native": float(evaluation["native_exported"]["pmfs_top5_error_m"]),
    }
    for family, times in FAMILIES.items():
        score = hcdg_scores(L, F, times)
        density = percentile_ranks(dict(zip(valid_ids, score)), ids)
        weights = posterior_from_leaf_density(density, ids, manifest, meas)
        x, y = endpoint(meas, weights)
        record[family] = math.hypot(x - tx, y - ty)
    cases.append((run, prepared, record))

df = pd.DataFrame([item[2] for item in cases])
print(df.to_csv(index=False))
for family in FAMILIES:
    gain = 100 * (df.native.mean() - df[family].mean()) / df.native.mean()
    print(f"{family}: mean={df[family].mean():.9f}, gain={gain:.4f}%, "
          f"improved={(df[family] < df.native).sum()}/6")

# Destructive nulls: freeze the mid family only.
real_mean = float(df["mid"].mean())
leaf_null = []
for seed in range(150):
    rng = np.random.default_rng(93000 + seed)
    errors = []
    for run, prepared, record in cases:
        align, manifest, meas, evaluation, ids, valid_ids, L, confidence, F = prepared
        score = hcdg_scores(L, F, FAMILIES["mid"])
        density = percentile_ranks(dict(zip(valid_ids, score)), ids)
        values = np.array([density[cid] for cid in ids])
        rng.shuffle(values)
        permuted = dict(zip(ids, values))
        weights = posterior_from_leaf_density(permuted, ids, manifest, meas)
        x, y = endpoint(meas, weights)
        house = os.path.basename(run).split("_")[0]
        tx, ty = TRUTH[house]
        errors.append(math.hypot(x - tx, y - ty))
    leaf_null.append(np.mean(errors))

shuffle_null = []
for seed in range(30):
    rng = np.random.default_rng(94000 + seed)
    errors = []
    for run, prepared, record in cases:
        align, manifest, meas, evaluation, ids, valid_ids, L, confidence, F = prepared
        shuffled = F.copy()
        for j in range(1, shuffled.shape[1]):
            rng.shuffle(shuffled[:, j])
        score = hcdg_scores(L, shuffled, FAMILIES["mid"])
        density = percentile_ranks(dict(zip(valid_ids, score)), ids)
        weights = posterior_from_leaf_density(density, ids, manifest, meas)
        x, y = endpoint(meas, weights)
        house = os.path.basename(run).split("_")[0]
        tx, ty = TRUTH[house]
        errors.append(math.hypot(x - tx, y - ty))
    shuffle_null.append(np.mean(errors))

out = {
    "real_mid_mean": real_mean,
    "leaf_150": {
        "mean": float(np.mean(leaf_null)),
        "q05": float(np.quantile(leaf_null, 0.05)),
        "q95": float(np.quantile(leaf_null, 0.95)),
        "frac_as_good": float(np.mean(np.array(leaf_null) <= real_mean)),
    },
    "shuffle_30": {
        "mean": float(np.mean(shuffle_null)),
        "q05": float(np.quantile(shuffle_null, 0.05)),
        "q95": float(np.quantile(shuffle_null, 0.95)),
        "frac_as_good": float(np.mean(np.array(shuffle_null) <= real_mean)),
    },
}
print(json.dumps(out, indent=2))
