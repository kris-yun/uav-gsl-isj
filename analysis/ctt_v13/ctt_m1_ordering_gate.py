#!/usr/bin/env python3
"""Synthetic-source evaluator for CTT M1 pre-Bayes evidence ordering."""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib

import numpy as np
import torch

import ctt_m1_first_passage_gate as g1


MATCHED_NEIGHBORS = 8
DELAY_MULTIPLIER = 73
DELAY_OFFSET = 19


def bootstrap_ci(delta, n=10000):
    rng = np.random.default_rng(g1.SEED + 1)
    means = np.empty(n)
    for i in range(n):
        means[i] = delta[rng.integers(0, len(delta), len(delta))].mean()
    return [float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))]


def margins(prob, labels_by_source, carriers, control, context, member):
    ns, nq = len(carriers), labels_by_source.shape[1]
    prob = prob.reshape(ns, nq, g1.TIMESTEPS + 1)
    d2 = ((carriers[:, None, :] - carriers[None, :, :]) ** 2).sum(axis=2)
    nearest = np.argsort(d2, axis=1)[:, 1:MATCHED_NEIGHBORS + 1]
    out = np.empty(ns, dtype=np.float64)
    cell = np.arange(nq)
    for truth in range(ns):
        labels = labels_by_source[truth].copy()
        if control == "time_shuffle":
            rng = np.random.default_rng(g1.SEED + context * 100000 + truth * 10 + member)
            labels = labels[rng.permutation(nq)]
        elif control == "reverse_causal_time":
            arrived = labels < g1.NEVER
            labels[arrived] = (g1.TIMESTEPS - 1) - labels[arrived]
        elif control == "delay_permutation":
            arrived = labels < g1.NEVER
            delays = (cell * DELAY_MULTIPLIER + DELAY_OFFSET) % g1.TIMESTEPS
            labels[arrived] = (labels[arrived] + delays[arrived]) % g1.TIMESTEPS
        elif control != "original":
            raise ValueError(control)
        candidates = np.concatenate(([truth], nearest[truth]))
        scores = np.empty(len(candidates))
        for j, candidate in enumerate(candidates):
            p = prob[candidate, cell, labels]
            scores[j] = np.log(np.clip(p, 1e-12, 1.0)).mean()
        out[truth] = scores[0] - scores[1:].max()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bank_root", type=pathlib.Path)
    ap.add_argument("direct_gate_root", type=pathlib.Path)
    ap.add_argument("output_root", type=pathlib.Path)
    args = ap.parse_args()
    if args.output_root.exists():
        raise SystemExit(f"refuse overwrite: {args.output_root}")
    args.output_root.mkdir(parents=True)
    direct = json.loads((args.direct_gate_root / "m1_gate_result.json").read_text())
    if direct["verdict"] != "M1_DIRECT_GO":
        raise SystemExit("direct M1 gate is not GO")

    carriers, queries, winds, hits = g1.load_bank(args.bank_root)
    base, wind_feat = g1.build_features(carriers, queries, winds)
    ns, nq = len(carriers), len(queries)
    npairs = ns * nq
    train_mean_wind = wind_feat[list(g1.TRAIN_CONTEXTS)].mean(axis=(0, 1), keepdims=True)
    static_wind = np.broadcast_to(train_mean_wind, (10, npairs, wind_feat.shape[2])).copy()
    b10 = np.broadcast_to(base, (10, *base.shape))
    cond = np.concatenate([b10, wind_feat], axis=2)
    stat = np.concatenate([b10, static_wind], axis=2)
    norm_source = cond[list(g1.TRAIN_CONTEXTS)].reshape(-1, cond.shape[2])
    mean = norm_source.mean(axis=0); std = norm_source.std(axis=0); std[std < 1e-8] = 1.0
    cond = ((cond - mean) / std).astype(np.float32)
    stat = ((stat - mean) / std).astype(np.float32)

    mc = g1.Field(cond.shape[2]); ms = g1.Field(stat.shape[2])
    mc.load_state_dict(torch.load(args.direct_gate_root / "conditional_best.pt", weights_only=True))
    ms.load_state_dict(torch.load(args.direct_gate_root / "static_best.pt", weights_only=True))
    controls = ("original", "time_shuffle", "reverse_causal_time", "delay_permutation")
    deltas = {x: [] for x in controls}
    cmargins = {x: [] for x in controls}
    smargins = {x: [] for x in controls}
    atom_context = []
    for c in g1.TEST_CONTEXTS:
        pc, _ = g1.predict(mc, cond[c])
        ps, _ = g1.predict(ms, stat[c])
        for k in g1.HELDOUT_MEMBERS:
            labels = hits[c, :, :, k].astype(np.int64)
            for control in controls:
                cm = margins(pc, labels, carriers, control, c, k)
                sm = margins(ps, labels, carriers, control, c, k)
                cmargins[control].append(cm); smargins[control].append(sm)
                deltas[control].append(cm - sm)
            atom_context.extend([c] * ns)

    result = {
        "gate": "CTT_M1_PRE_BAYES_MATCHED_ORDERING_V1",
        "real_source_truth_used": False,
        "synthetic_source_index_used_for_evaluation_only": True,
        "matched_neighbors": MATCHED_NEIGHBORS,
        "test_contexts": g1.TEST_CONTEXTS,
        "heldout_members": g1.HELDOUT_MEMBERS,
        "controls": {},
    }
    context_ids = np.asarray(atom_context)
    for control in controls:
        d = np.concatenate(deltas[control])
        cm = np.concatenate(cmargins[control]); sm = np.concatenate(smargins[control])
        result["controls"][control] = {
            "conditional_margin_mean": float(cm.mean()),
            "static_margin_mean": float(sm.mean()),
            "increment_mean": float(d.mean()),
            "increment_95ci": bootstrap_ci(d),
            "conditional_positive_fraction": float((cm > 0).mean()),
            "static_negative_to_conditional_positive_count": int(((sm <= 0) & (cm > 0)).sum()),
            "per_context_increment": {
                str(c): float(d[context_ids == c].mean()) for c in g1.TEST_CONTEXTS
            },
        }
    original = result["controls"]["original"]
    original_ok = (original["increment_mean"] > 0 and original["increment_95ci"][0] > 0
                   and all(v > 0 for v in original["per_context_increment"].values())
                   and original["static_negative_to_conditional_positive_count"] > 0)
    # A valid causal control must erase at least 75% of the original increment;
    # negative increments also count as erased, never as an improvement.
    control_ok = all(
        result["controls"][x]["increment_mean"] <= 0.25 * original["increment_mean"]
        for x in controls[1:]
    )
    result["verdict"] = "M1_ORDERING_GO" if original_ok and control_ok else "M1_ORDERING_NO_GO"
    result["original_gate_pass"] = original_ok
    result["causal_controls_pass"] = control_ok
    (args.output_root / "m1_ordering_result.json").write_text(json.dumps(result, indent=2))
    contract = {
        "script_sha256": hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
        "direct_gate_script_sha256": hashlib.sha256((pathlib.Path(g1.__file__)).read_bytes()).hexdigest(),
        "delay_multiplier": DELAY_MULTIPLIER, "delay_offset": DELAY_OFFSET,
        "control_erase_fraction": 0.75,
    }
    (args.output_root / "ordering_contract.json").write_text(json.dumps(contract, indent=2))
    print(json.dumps(result, indent=2))
    return 0 if result["verdict"] == "M1_ORDERING_GO" else 2


if __name__ == "__main__":
    raise SystemExit(main())
