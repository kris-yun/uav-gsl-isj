#!/usr/bin/env python3
"""HCTLA V1 discovery reproduction on the frozen TNQC V5 R2 archive.

HCTLA V1:
- authoritative final-leaf IDs;
- keep only candidate IDs present in all five source updates;
- common support across all five updates with measured_confidence > 1e-6;
- cardinal 5-point local stencil;
- per-snapshot spatial z-normalization;
- four transition-specific ridge maps, alpha=1.0, intercept included;
- source score = mean cosine alignment of measured/candidate transition coefficients;
- average-percentile candidate density; invalid final leaves = 0.

This script is for discovery reproduction and destructive controls only.
Its local endpoint uses ceil top-5% with stable Python tie-breaking.
Independent validation must export the source-blind HCTLA posterior and evaluate
with the linked-native C++ ExpectedValue executable.
"""
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.stats import rankdata

if len(sys.argv) != 2:
    raise SystemExit("usage: hctla_v1_discovery_screen_20260922.py <native_root>")

ROOT = Path(sys.argv[1]).resolve()
CASES = [f"House{h:02d}_seed{s}_off_off" for h in (1,2,3) for s in (0,1)]
TRUTH = {
    "House01": (-0.4,-2.9),
    "House02": (0.0,-1.0),
    "House03": (-0.45,1.9),
}
CONF_FLOOR = 1e-6
RIDGE_ALPHA = 1.0

def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def fit_transition(f0, f1, stencil):
    s0 = max(float(np.std(f0)), 1e-9)
    s1 = max(float(np.std(f1)), 1e-9)
    z0 = (f0 - np.mean(f0)) / s0
    z1 = (f1 - np.mean(f1)) / s1
    X = z0[stencil]
    y = z1[stencil[:,0]]
    Xa = np.column_stack([X, np.ones(len(X))])
    A = Xa.T @ Xa
    A[:5,:5] += RIDGE_ALPHA * np.eye(5)
    b = Xa.T @ y
    try:
        beta = np.linalg.solve(A,b)
    except np.linalg.LinAlgError:
        beta = np.linalg.pinv(A) @ b
    return beta

def signature(sequence, stencil):
    return np.vstack([
        fit_transition(sequence[k], sequence[k+1], stencil)
        for k in range(4)
    ])

def hctla_score(measured_signature, candidate_signature):
    values = []
    for k in range(4):
        a = measured_signature[k]
        b = candidate_signature[k]
        values.append(float(np.dot(a,b) / (
            (np.linalg.norm(a)+1e-12) * (np.linalg.norm(b)+1e-12)
        )))
    return float(np.mean(values))

def percentile_density(scores, final_ids, valid_ids):
    values = np.asarray([scores[c] for c in valid_ids], dtype=float)
    ranks = rankdata(values, method="average") / len(values)
    mapping = dict(zip(valid_ids, ranks))
    return np.asarray([mapping.get(c,0.0) for c in final_ids], dtype=float)

class Case:
    def __init__(self, name):
        self.name = name
        self.house = name[:7]
        self.run = ROOT / name
        with open(self.run / "tnqc_fixed_trajectory_evaluation.json") as f:
            self.evaluation = json.load(f)
        self.final_ids = list(
            self.evaluation["tnqc_gate_scope_audit"]["final_leaf_candidate_ids"]
        )

        updates = []
        candidate_sets = []
        coord_sets = []
        for k in range(1,6):
            rows = read_csv(
                self.run / "context_bank" / f"source_update_{k:04d}"
                / "candidate_support_alignment.csv"
            )
            updates.append(rows)
            candidate_sets.append({r["candidate_id"] for r in rows})
            rep = rows[0]["candidate_id"]
            coord_sets.append({
                (int(r["grid_i"]), int(r["grid_j"]))
                for r in rows
                if r["candidate_id"] == rep
                and float(r["measured_confidence"]) > CONF_FLOOR
            })

        common_candidate_ids = set.intersection(*candidate_sets)
        self.valid_ids = [
            c for c in self.final_ids if c in common_candidate_ids
        ]
        self.coords = sorted(set.intersection(*coord_sets))
        coord_index = {c:i for i,c in enumerate(self.coords)}

        stencil = []
        for i,j in self.coords:
            neighbours = [
                (i,j),(i+1,j),(i-1,j),(i,j+1),(i,j-1)
            ]
            if all(c in coord_index for c in neighbours):
                stencil.append([coord_index[c] for c in neighbours])
        self.stencil = np.asarray(stencil, dtype=int)

        def field_array(rows, candidate_id, column):
            d = {
                (int(r["grid_i"]), int(r["grid_j"])): float(r[column])
                for r in rows
                if r["candidate_id"] == candidate_id
            }
            return np.asarray([d[c] for c in self.coords], dtype=float)

        rep = next(iter(common_candidate_ids))
        measured_sequence = np.vstack([
            field_array(rows, rep, "measured_probability")
            for rows in updates
        ])
        self.measured_signature = signature(
            measured_sequence, self.stencil
        )
        self.candidate_sequences = {
            cid: np.vstack([
                field_array(rows, cid, "simulated_hit_probability")
                for rows in updates
            ])
            for cid in self.valid_ids
        }
        self.scores = {
            cid: hctla_score(
                self.measured_signature,
                signature(self.candidate_sequences[cid], self.stencil),
            )
            for cid in self.valid_ids
        }

        update = self.run / "context_bank" / "source_update_0005"
        manifest = read_csv(update / "candidate_manifest.csv")
        posterior = read_csv(update / "source_posterior.csv")
        timing = read_csv(
            self.run / "context_bank" / "source_update_timing.csv"
        )[-1]
        ox = float(timing["origin_x"])
        oy = float(timing["origin_y"])
        cs = float(timing["cell_size"])
        geom = {
            r["candidate_id"]: (
                int(r["origin_i"]), int(r["origin_j"]),
                int(r["size_i"]), int(r["size_j"]),
            )
            for r in manifest if r["candidate_id"] in self.final_ids
        }
        owner = []
        self.xy = []
        for r in posterior:
            x = float(r["x"]); y = float(r["y"])
            i = int(round((x-ox)/cs - 0.5))
            j = int(round((y-oy)/cs - 0.5))
            found = -1
            for z,cid in enumerate(self.final_ids):
                a,b,w,h = geom[cid]
                if a <= i < a+w and b <= j < b+h:
                    found = z
                    break
            if found < 0:
                raise RuntimeError((name,r["cell_index"],i,j))
            owner.append(found)
            self.xy.append((x,y))
        self.owner = np.asarray(owner, dtype=int)
        self.xy = np.asarray(self.xy, dtype=float)

    def endpoint(self, density):
        w = density[self.owner].astype(float)
        if w.sum() <= 0:
            return float("inf")
        w /= w.sum()
        n = max(1, math.ceil(0.05 * len(w)))
        selected = np.argsort(-w, kind="stable")[:n]
        mass = w[selected].sum()
        point = np.sum(
            self.xy[selected] * w[selected,None], axis=0
        ) / mass
        tx,ty = TRUTH[self.house]
        return float(math.hypot(point[0]-tx, point[1]-ty))

cases = [Case(name) for name in CASES]
native = np.asarray([
    float(c.evaluation["native_exported"]["pmfs_top5_error_m"])
    for c in cases
])
real = np.asarray([
    c.endpoint(percentile_density(c.scores,c.final_ids,c.valid_ids))
    for c in cases
])

# Persistence-only negative control.
uniform_persistent = []
for c in cases:
    valid = set(c.valid_ids)
    density = np.asarray([
        1.0 if cid in valid else 0.0 for cid in c.final_ids
    ])
    uniform_persistent.append(c.endpoint(density))
uniform_persistent = np.asarray(uniform_persistent)

leaf_null = []
for seed in range(300):
    rng = np.random.default_rng(771000+seed)
    errors = []
    for c in cases:
        values = np.asarray([c.scores[x] for x in c.valid_ids])
        rng.shuffle(values)
        shuffled = dict(zip(c.valid_ids,values))
        errors.append(c.endpoint(
            percentile_density(shuffled,c.final_ids,c.valid_ids)
        ))
    leaf_null.append(float(np.mean(errors)))

time_null = []
for seed in range(30):
    rng = np.random.default_rng(772000+seed)
    errors = []
    for c in cases:
        order = np.arange(5)
        while np.all(order == np.arange(5)):
            rng.shuffle(order)
        scores = {}
        for cid in c.valid_ids:
            qsig = signature(
                c.candidate_sequences[cid][order], c.stencil
            )
            scores[cid] = hctla_score(c.measured_signature, qsig)
        errors.append(c.endpoint(
            percentile_density(scores,c.final_ids,c.valid_ids)
        ))
    time_null.append(float(np.mean(errors)))

spatial_null = []
for seed in range(30):
    rng = np.random.default_rng(773000+seed)
    errors = []
    for c in cases:
        scores = {}
        for cid in c.valid_ids:
            q = c.candidate_sequences[cid].copy()
            for k in range(5):
                rng.shuffle(q[k])
            qsig = signature(q,c.stencil)
            scores[cid] = hctla_score(c.measured_signature,qsig)
        errors.append(c.endpoint(
            percentile_density(scores,c.final_ids,c.valid_ids)
        ))
    spatial_null.append(float(np.mean(errors)))

def summarize(values, real_mean):
    a = np.asarray(values,dtype=float)
    return {
        "mean": float(np.mean(a)),
        "median": float(np.median(a)),
        "q05": float(np.quantile(a,0.05)),
        "q95": float(np.quantile(a,0.95)),
        "min": float(np.min(a)),
        "max": float(np.max(a)),
        "fraction_as_good_or_better": float(np.mean(a <= real_mean)),
    }

real_mean = float(np.mean(real))
result = {
    "native_errors_m": native.tolist(),
    "hctla_errors_m": real.tolist(),
    "native_mean_m": float(np.mean(native)),
    "hctla_mean_m": real_mean,
    "pooled_reduction_percent": float(
        100*(np.mean(native)-real_mean)/np.mean(native)
    ),
    "improved_cases": int(np.sum(real < native)),
    "uniform_persistent_candidate_errors_m":
        uniform_persistent.tolist(),
    "uniform_persistent_candidate_mean_m":
        float(np.mean(uniform_persistent)),
    "leaf_permutation_300": summarize(leaf_null,real_mean),
    "time_permutation_30": summarize(time_null,real_mean),
    "spatial_shuffle_30": summarize(spatial_null,real_mean),
}
print(json.dumps(result, indent=2))
