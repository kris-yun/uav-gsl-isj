#!/usr/bin/env python3
"""Post-hoc discovery diagnostic for predictive memory.

This script is not a preregistered gate. It reuses the frozen 64 OCB-R2
10x30 tensors and evaluates a parameter-free nearest-history predictive-memory
gain.
"""
from __future__ import annotations

import csv
from pathlib import Path
import numpy as np

REPO = Path(__file__).resolve().parents[3]
E = REPO / "evidence/ocb_r2/mechanism_census_r0"
I = E / "inputs"
TARGETS = E / "R0_TARGET_EFFECTS.tsv"


def rows(path: Path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def ham(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.mean(a != b))


def hist_dist(y: np.ndarray, r: np.ndarray, t: int, h: int) -> float:
    return float(np.mean(y[t-h+1:t+1] != r[t-h+1:t+1]))


def predictive_gain(y: np.ndarray, refs: np.ndarray, h: int) -> float:
    gains = []
    for t in range(h - 1, 9):
        d = np.array([hist_dist(y, r, t, h) for r in refs])
        best = np.flatnonzero(np.isclose(d, d.min(), atol=1e-12, rtol=0))
        intact = np.mean([ham(y[t+1], refs[i, t+1]) for i in best])
        shuffled = np.mean([ham(y[t+1], r[t+1]) for r in refs])
        gains.append(shuffled - intact)
    return float(np.mean(gains))


def exact_context_signflip(context_values):
    vals = np.asarray(context_values, dtype=float)
    observed = float(vals.mean())
    null = []
    for mask in range(1 << len(vals)):
        signs = np.array([1 if (mask >> i) & 1 else -1 for i in range(len(vals))])
        null.append(float(np.mean(signs * vals)))
    return observed, sum(v >= observed - 1e-15 for v in null) / len(null)


def main():
    primary = [r for r in rows(TARGETS) if r["primary_omission"] == "1"]
    assert len(primary) == 64

    meta = {
        r["run_id"]: dict(
            context=r["context"],
            house=r["house"],
            source=r["truth_source"],
            rep=int(r["target_replicate"]),
        )
        for r in primary
    }

    tensors = {}
    for run_id in meta:
        x = np.load(I / f"{run_id}.pooled.npy", allow_pickle=False)
        assert x.shape == (10, 30)
        tensors[run_id] = x > 0

    lookup = {
        (m["context"], m["source"], m["rep"]): tensors[run_id]
        for run_id, m in meta.items()
    }

    out = []
    for context in sorted({m["context"] for m in meta.values()}):
        ids = [i for i, m in meta.items() if m["context"] == context]
        house = meta[ids[0]]["house"]
        sources = sorted({meta[i]["source"] for i in ids})
        assert len(sources) == 2

        for truth in sources:
            alt = next(s for s in sources if s != truth)
            target_rows = []
            for rep in range(1, 5):
                y = lookup[(context, truth, rep)]
                truth_refs = np.stack([
                    lookup[(context, truth, r)] for r in range(1, 5) if r != rep
                ])
                alt_refs = np.stack([
                    lookup[(context, alt, r)] for r in range(1, 5) if r != rep
                ])
                rec = {}
                for h in range(1, 6):
                    mt = predictive_gain(y, truth_refs, h)
                    ma = predictive_gain(y, alt_refs, h)
                    rec[f"M_truth_H{h}"] = mt
                    rec[f"M_alt_H{h}"] = ma
                    rec[f"J_H{h}"] = mt - ma
                target_rows.append(rec)

            g = dict(context=context, house=house, truth_source=truth)
            for h in range(1, 6):
                g[f"M_truth_H{h}"] = float(np.mean([r[f"M_truth_H{h}"] for r in target_rows]))
                g[f"M_alt_H{h}"] = float(np.mean([r[f"M_alt_H{h}"] for r in target_rows]))
                g[f"J_H{h}"] = float(np.mean([r[f"J_H{h}"] for r in target_rows]))
            g["D31_truth"] = g["M_truth_H3"] - g["M_truth_H1"]
            g["D51_truth"] = g["M_truth_H5"] - g["M_truth_H1"]
            out.append(g)

    for key in ["M_truth_H1", "M_truth_H3", "M_truth_H5", "D31_truth", "D51_truth",
                "J_H3", "J_H5"]:
        vals = np.array([g[key] for g in out])
        h1 = np.array([g[key] for g in out if g["house"] == "House01"])
        h2 = np.array([g[key] for g in out if g["house"] == "House02"])
        ctx = np.array([
            np.mean([g[key] for g in out if g["context"] == c])
            for c in sorted({g["context"] for g in out})
        ])
        obs, ref = exact_context_signflip(ctx)
        print(
            key,
            "pooled_median=", float(np.median(vals)),
            "H01_median=", float(np.median(h1)),
            "H02_median=", float(np.median(h2)),
            "positive_groups=", int(np.sum(vals > 0)),
            "positive_contexts=", int(np.sum(ctx > 0)),
            "context_mean=", obs,
            "exact_signflip=", ref,
        )


if __name__ == "__main__":
    main()
