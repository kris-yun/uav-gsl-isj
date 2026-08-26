#!/usr/bin/env python3
"""Exact conditional-sequence and count-factor premise gates for CTT."""
from __future__ import annotations

import argparse
import csv
import json
import math
import pathlib
import struct

import numpy as np
from scipy.spatial import cKDTree

import ctt_m1_first_passage_gate as g1


EPS = 0.05
K_STATES = 6
MATCHED = 8
SHIFT = 3
BOOTSTRAPS = 10000


def read_trace(path: pathlib.Path):
    raw = path.read_bytes()
    header = struct.unpack_from("<7Q", raw, 0)
    _, version, _, _, timesteps, cell_count, words = header
    if version != 1 or timesteps != g1.TIMESTEPS:
        raise ValueError((path, header))
    offset = 56 + 4 * timesteps + 4 * cell_count
    occ = np.frombuffer(raw, dtype="<u8", count=timesteps * words, offset=offset).reshape(timesteps, words)
    fronts = [int.from_bytes(row.tobytes(), "little") for row in occ]
    return occ, fronts


def fixed_path(event_csv: pathlib.Path, query_xy, free_indices):
    with event_csv.open(newline="") as f:
        rows = list(csv.DictReader(f))
    t0 = float(rows[0]["sim_time"])
    rows = [r for r in rows if float(r["sim_time"]) - t0 <= 39.8 + 1e-8]
    if len(rows) < 16 or len(rows) > 20:
        raise ValueError(f"canonical sparse event coverage {len(rows)}")
    xy = np.array([[float(r["x"]), float(r["y"])] for r in rows])
    time_bins = np.array([round((float(r["sim_time"]) - t0) / 0.2) for r in rows], dtype=np.int32)
    if np.any(np.diff(time_bins) <= 0) or time_bins[-1] >= g1.TIMESTEPS:
        raise ValueError(f"invalid event time bins {time_bins}")
    tree = cKDTree(query_xy)
    dist, local = tree.query(xy, k=1)
    if np.max(dist) > 0.22:
        raise ValueError(f"path outside free support: {np.max(dist)}")
    return free_indices[local].astype(np.int32), xy, time_bins


def path_bits(occ, global_cells, time_bins):
    t = time_bins
    word = global_cells // 64
    bit = global_cells % 64
    return ((occ[t, word] >> bit.astype(np.uint64)) & np.uint64(1)).astype(np.int8)


def transitions(fronts_by_k, time_bins):
    A = np.empty((len(time_bins) - 1, K_STATES, K_STATES), dtype=np.float64)
    for t in range(len(time_bins) - 1):
        left = [fronts_by_k[k][time_bins[t]] for k in range(K_STATES)]
        right = [fronts_by_k[k][time_bins[t + 1]] for k in range(K_STATES)]
        nl = [x.bit_count() for x in left]; nr = [x.bit_count() for x in right]
        for i in range(K_STATES):
            for j in range(K_STATES):
                den = math.sqrt(nl[i] * nr[j])
                A[t, i, j] = ((left[i] & right[j]).bit_count() / den) if den else 0.0
            z = A[t, i].sum()
            if z == 0.0:
                A[t, i] = 0.0; A[t, i, i] = 1.0
            else:
                A[t, i] /= z
    return A


def hmm_loglik(y, e1, A):
    emission = np.where(y[:, None] == 1, e1, 1.0 - e1)
    alpha = emission[0] / K_STATES
    scale = alpha.sum(); logl = math.log(max(scale, 1e-300)); alpha /= max(scale, 1e-300)
    for t in range(1, len(y)):
        alpha = (alpha @ A[t - 1]) * emission[t]
        scale = alpha.sum(); logl += math.log(max(scale, 1e-300)); alpha /= max(scale, 1e-300)
    return logl


def hmm_log_count(n, e1, A):
    dp = np.zeros((n + 1, K_STATES), dtype=np.float64)
    dp[0] = (1.0 - e1[0]) / K_STATES
    if n >= 1:
        dp[1] = e1[0] / K_STATES
    for t in range(1, len(e1)):
        pred = dp @ A[t - 1]
        new = pred * (1.0 - e1[t])[None, :]
        new[1:] += pred[:-1] * e1[t][None, :]
        dp = new
    return math.log(max(dp[n].sum(), 1e-300))


def iid_scores(y, e1):
    q = e1.mean(axis=1)
    logl = np.sum(np.where(y == 1, np.log(q), np.log1p(-q)))
    n = int(y.sum())
    dp = np.zeros(n + 1); dp[0] = 1.0
    for qt in q:
        new = dp * (1.0 - qt)
        new[1:] += dp[:-1] * qt
        dp = new
    logc = math.log(max(dp[n], 1e-300))
    return logl - logc


def candidate_scores(y, candidate, bits, trans):
    state_bits = bits[candidate, :K_STATES].T
    e1 = EPS + (1.0 - 2.0 * EPS) * state_bits
    l2 = hmm_loglik(y, e1, trans[candidate])
    lc = hmm_log_count(int(y.sum()), e1, trans[candidate])
    return iid_scores(y, e1), l2 - lc, lc, l2


def bootstrap_ci(x):
    rng = np.random.default_rng(g1.SEED + 2)
    means = np.empty(BOOTSTRAPS)
    for i in range(BOOTSTRAPS):
        means[i] = x[rng.integers(0, len(x), len(x))].mean()
    return [float(np.quantile(means, .025)), float(np.quantile(means, .975))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bank_root", type=pathlib.Path)
    ap.add_argument("canonical_event_csv", type=pathlib.Path)
    ap.add_argument("output_root", type=pathlib.Path)
    args = ap.parse_args()
    if args.output_root.exists():
        raise SystemExit(f"refuse overwrite: {args.output_root}")
    args.output_root.mkdir(parents=True)

    carriers, query_xy, _, _ = g1.load_bank(args.bank_root)
    wind_rows = g1.read_csv(next(args.bank_root.glob("context_00_*/estimated_wind.csv")))
    free_indices = np.array([int(r["cell_index"]) for r in wind_rows], dtype=np.int32)
    path_cells, path_xy, time_bins = fixed_path(args.canonical_event_csv, query_xy, free_indices)
    with (args.output_root / "canonical_path.csv").open("w", newline="") as f:
        w = csv.writer(f); w.writerow(["event_index", "native_t_bin", "global_cell", "x", "y"])
        for event, (t, cell, xy) in enumerate(zip(time_bins, path_cells, path_xy)):
            w.writerow([event, int(t), int(cell), float(xy[0]), float(xy[1])])

    d2 = ((carriers[:, None] - carriers[None]) ** 2).sum(axis=2)
    near = np.argsort(d2, axis=1)[:, 1:MATCHED + 1]
    records = []
    for c in g1.TEST_CONTEXTS:
        d = next(args.bank_root.glob(f"context_{c:02d}_*"))
        bits = np.empty((len(carriers), 8, len(time_bins)), dtype=np.int8)
        trans = []
        for s in range(len(carriers)):
            fronts = []
            for k in range(8):
                occ, fr = read_trace(d / "records" / f"carrier_{s:04d}_member_{k:02d}.cttbin")
                bits[s, k] = path_bits(occ, path_cells, time_bins)
                if k < K_STATES:
                    fronts.append(fr)
            trans.append(transitions(fronts, time_bins))
        for truth in range(len(carriers)):
            candidates = np.concatenate(([truth], near[truth]))
            for k in g1.HELDOUT_MEMBERS:
                y = bits[truth, k]
                if not (2 <= int(y.sum()) <= len(time_bins) - 2):
                    continue
                rng = np.random.default_rng(g1.SEED + c * 100000 + truth * 10 + k)
                yp = y[rng.permutation(len(time_bins))]
                yshift = np.zeros_like(y); yshift[:-SHIFT] = y[SHIFT:]
                score = np.array([candidate_scores(y, x, bits, trans) for x in candidates])
                scorep = np.array([candidate_scores(yp, x, bits, trans) for x in candidates])
                # B1 J1, B2 J2, B3 J2+J3; shifted control uses original J2.
                margins = lambda col: score[0, col] - score[1:, col].max()
                j1m, j2m, j3m, fullm = margins(0), margins(1), margins(2), margins(3)
                j2pm = scorep[0, 1] - scorep[1:, 1].max()
                shifted_j3 = np.array([candidate_scores(yshift, x, bits, trans)[2] for x in candidates])
                shifted_full = score[:, 1] + shifted_j3
                shifted_margin = shifted_full[0] - shifted_full[1:].max()
                records.append({
                    "context": c, "truth": truth, "member": k, "count": int(y.sum()),
                    "m2_increment": j2m - j1m,
                    "m2_permuted_increment": j2pm - j1m,
                    "m3_increment": fullm - j2m,
                    "m3_shifted_increment": shifted_margin - j2m,
                })
    if len(records) < 30:
        raise SystemExit(f"INVALID_COVERAGE atoms={len(records)}")
    with (args.output_root / "atom_scores.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=records[0]); w.writeheader(); w.writerows(records)

    def summarize(key):
        x = np.array([r[key] for r in records])
        return {"mean": float(x.mean()), "median": float(np.median(x)), "ci95": bootstrap_ci(x),
                "per_context_median": {str(c): float(np.median([r[key] for r in records if r["context"] == c]))
                                       for c in g1.TEST_CONTEXTS}}
    m2 = summarize("m2_increment"); m2p = summarize("m2_permuted_increment")
    m3 = summarize("m3_increment"); m3s = summarize("m3_shifted_increment")
    m2_go = (m2["mean"] > 0 and m2["ci95"][0] > 0
             and all(v > 0 for v in m2["per_context_median"].values())
             and m2p["mean"] <= .25 * m2["mean"])
    m3_go = (m3["mean"] > 0 and m3["ci95"][0] > 0
             and all(v > 0 for v in m3["per_context_median"].values())
             and m3s["mean"] <= .25 * m3["mean"])
    result = {"gate": "CTT_M2_M3_EXACT_FACTOR_GATE_V1", "real_truth_used": False,
              "covered_atoms": len(records), "epsilon": EPS,
              "observation_count": len(time_bins), "native_time_bins": time_bins.tolist(),
              "m2": m2, "m2_time_permuted": m2p, "m3": m3, "m3_shifted": m3s,
              "candidate_constant_count_relative_margin": 0.0,
              "m2_verdict": "M2_INCREMENTAL_GO" if m2_go else "M2_INCREMENTAL_NO_GO",
              "m3_verdict": "M3_CONDITIONAL_GO" if m3_go else "M3_CONDITIONAL_NO_GO",
              "verdict": "M2_M3_GO" if m2_go and m3_go else "M2_M3_NO_GO"}
    (args.output_root / "m2_m3_gate_result.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    return 0 if m2_go and m3_go else 2


if __name__ == "__main__":
    raise SystemExit(main())
