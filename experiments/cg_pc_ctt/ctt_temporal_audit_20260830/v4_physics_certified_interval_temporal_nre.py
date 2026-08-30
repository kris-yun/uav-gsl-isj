#!/usr/bin/env python3
"""CTT V4: physics-certified interval causal temporal NRE.

The neural temporal term is structurally confined to a candidate-specific
transport-uncertainty interval derived only from the frozen native forward
ensemble.  Non-overlapping physical intervals therefore induce hard pairwise
ordering constraints that the network cannot violate.

This is a development reference implementation for the H01 offline gate.  It
must not be used for closed-loop control unless its frozen gates pass and a
separate runtime parity contract is satisfied.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

sys.path.insert(0, "/mnt/data/h01_temporal_gate")
import train_eval_ctt_temporal_nre as v1
import v3_physics_order_temporal_nre as v3

OUT = Path("/mnt/data/h01_temporal_gate/v4")
OUT.mkdir(exist_ok=True)

INPUT = v1.INPUT
PRED_MEMBERS = (0, 1, 2)
TRAIN_OBS = (4, 5)
VAL_OBS = 6
TEST_OBS = 7
TRAIN_TRAJ = (0, 1, 2)
VAL_TRAJ = 3
TEST_TRAJ = 4
SEEDS = (1801, 1802, 1803)
STEPS = 300
FRESH_COUNT = 48
CONTRACT = "CTT_PHYSICS_CERTIFIED_INTERVAL_CAUSAL_TEMPORAL_NRE_V4"


class PhysicsCertifiedIntervalTemporalNRE(nn.Module):
    """Causal TCN selector constrained to a frozen physical evidence interval."""

    def __init__(self, width: int = 32):
        super().__init__()
        self.enc = nn.Sequential(nn.Linear(INPUT, width), nn.GELU())
        self.blocks = nn.ModuleList([v1.CausalBlock(width, d) for d in (1, 2, 4, 8, 16, 32)])
        self.selector = nn.Sequential(
            nn.Linear(2 * width, 32), nn.GELU(), nn.Linear(32, 1)
        )

    def forward(self, x: torch.Tensor, mask: torch.Tensor,
                lower: torch.Tensor, upper: torch.Tensor) -> torch.Tensor:
        h = self.enc(x)
        for block in self.blocks:
            h = block(h)
        w = mask[..., None].to(h.dtype)
        length = mask.sum(1)
        mean = (h * w).sum(1) / length[:, None]
        final = h[torch.arange(len(h)), length - 1]
        lam = torch.sigmoid(self.selector(torch.cat([mean, final], 1)).squeeze(1))
        # Structural contract: no learned coefficient can move the score outside
        # the transport-certified interval.
        return lower + lam * (upper - lower)


def energy_evidence_subset(data: v1.Data, tr: int, true: int, obs_member: int,
                           cut: float, members: tuple[int, ...]) -> np.ndarray:
    """Higher-is-better energy-score evidence for all candidate sources."""
    n = data.nblocks(tr, cut)
    obs = data.bm[tr, true, obs_member, :n].astype(np.float64)
    pred = data.bm[tr][:, list(members), :n].astype(np.float64)
    m = len(members)
    first = np.linalg.norm(pred - obs[None, None, :], axis=2).mean(1)
    pair = np.zeros(pred.shape[0], dtype=np.float64)
    for i in range(m):
        for j in range(m):
            pair += np.linalg.norm(pred[:, i] - pred[:, j], axis=1)
    energy = (first - 0.5 * pair / (m * m)) / math.sqrt(n)
    return -energy


def certified_interval_all(data: v1.Data, tr: int, true: int, obs_member: int,
                           cut: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return full standardized evidence and full+LOO certified interval.

    The same affine standardization obtained from the full three-member score is
    applied to every leave-one-member-out score.  This avoids member-dependent
    rescaling and makes the interval a genuine nuisance-transport uncertainty
    set on one common evidence axis.
    """
    full = energy_evidence_subset(data, tr, true, obs_member, cut, PRED_MEMBERS)
    loo = []
    for drop in PRED_MEMBERS:
        members = tuple(m for m in PRED_MEMBERS if m != drop)
        loo.append(energy_evidence_subset(data, tr, true, obs_member, cut, members))
    center = float(full.mean())
    scale = max(float(full.std()), 1e-8)
    full_z = (full - center) / scale
    support = [full_z] + [(x - center) / scale for x in loo]
    stack = np.stack(support, axis=0)
    lower = stack.min(axis=0)
    upper = stack.max(axis=0)
    return full_z, lower, upper, stack


def prim(data: v1.Data, tr: int, true: int, obs_member: int, cand: int, cut: float) -> np.ndarray:
    n = data.nblocks(tr, cut)
    return v1.primitives(
        data.bm[tr, true, obs_member, :n],
        data.bm[tr, cand, list(PRED_MEMBERS), :n],
    )


def pad(seq: list[np.ndarray]) -> tuple[torch.Tensor, torch.Tensor]:
    return v1.pad_batch(seq)


def deterministic_perm(n: int, key: str) -> np.ndarray:
    return v1.deterministic_perm(n, key)


def make_pairs(data: v1.Data, rng: np.random.Generator, batch: int,
               split: str, seedkey: int):
    a, b, ap, bp = [], [], [], []
    alo, ahi, blo, bhi = [], [], [], []
    for k in range(batch):
        if split == "train":
            tr = int(rng.choice(TRAIN_TRAJ))
            obs_member = int(rng.choice(TRAIN_OBS))
        else:
            tr = VAL_TRAJ
            obs_member = VAL_OBS
        true = int(rng.integers(210))
        neg = int(rng.integers(209))
        neg += int(neg >= true)
        update = int(rng.integers(1, 6))
        cut = (float(data.bytime[update][int(rng.integers(10))])
               if split == "train" else float(data.med[update]))
        _, lower, upper, _ = certified_interval_all(data, tr, true, obs_member, cut)
        pa = prim(data, tr, true, obs_member, true, cut)
        pb = prim(data, tr, true, obs_member, neg, cut)
        q = deterministic_perm(
            len(pa),
            f"V4|{seedkey}|{split}|{tr}|{obs_member}|{true}|{neg}|{update}|{k}",
        )
        a.append(v1.sequence_features(pa))
        b.append(v1.sequence_features(pb))
        ap.append(v1.sequence_features(pa, q))
        bp.append(v1.sequence_features(pb, q))
        alo.append(lower[true]); ahi.append(upper[true])
        blo.append(lower[neg]); bhi.append(upper[neg])
    return (
        a, b, ap, bp,
        np.asarray(alo, np.float32), np.asarray(ahi, np.float32),
        np.asarray(blo, np.float32), np.asarray(bhi, np.float32),
    )


def loss_fn(model: nn.Module, batch):
    a, b, ap, bp, alo, ahi, blo, bhi = batch
    n = len(a)
    x, mask = pad(a + b + ap + bp)
    lower = torch.from_numpy(np.r_[alo, blo, alo, blo])
    upper = torch.from_numpy(np.r_[ahi, bhi, ahi, bhi])
    score = model(x, mask, lower, upper)
    sa, sb, sap, sbp = torch.split(score, n)
    # Pairwise source discrimination.  No calibration temperature/bias is used.
    rank_loss = F.softplus(-(sa - sb)).mean()
    # Same physical intervals and same block multiset; only chronological order
    # differs.  Therefore this term can be improved only through ordered time.
    order_loss = F.softplus(-((sa - sb) - (sap - sbp))).mean()
    return rank_loss + order_loss, rank_loss, order_loss


def train(data: v1.Data, seed: int) -> nn.Module:
    torch.set_num_threads(4)
    torch.manual_seed(seed)
    model = PhysicsCertifiedIntervalTemporalNRE()
    opt = torch.optim.AdamW(model.parameters(), lr=2e-3, weight_decay=1e-4)
    rng = np.random.default_rng(seed + 20260830)
    vrng = np.random.default_rng(seed + 99000)
    val = make_pairs(data, vrng, 96, "val", seed)
    best = None
    hist = []
    for step in range(1, STEPS + 1):
        model.train()
        total, rank_loss, order_loss = loss_fn(
            model, make_pairs(data, rng, 24, "train", seed + step * 37)
        )
        opt.zero_grad()
        total.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        opt.step()
        if step == 1 or step % 50 == 0:
            model.eval()
            with torch.no_grad():
                vt, vr, vo = loss_fn(model, val)
            row = {
                "step": step,
                "val_total": float(vt),
                "val_rank": float(vr),
                "val_order": float(vo),
            }
            hist.append(row)
            print("V4TRAIN", seed, row, flush=True)
            if best is None or float(vt) < best[0]:
                best = (
                    float(vt), step,
                    {k: v.detach().cpu().clone() for k, v in model.state_dict().items()},
                )
                torch.save(
                    {
                        "seed": seed,
                        "best_step": step,
                        "state_dict": best[2],
                        "contract": CONTRACT,
                    },
                    OUT / f"model_{seed}.pt",
                )
                (OUT / f"train_{seed}.json").write_text(
                    json.dumps({"best_step": step, "best_val": best[0], "history": hist}, indent=2)
                )
    assert best is not None
    model.load_state_dict(best[2])
    model.eval()
    return model


def get_models(data: v1.Data) -> list[nn.Module]:
    result = []
    for seed in SEEDS:
        path = OUT / f"model_{seed}.pt"
        if path.exists():
            ck = torch.load(path, map_location="cpu", weights_only=False)
            if ck.get("contract") != CONTRACT:
                raise ValueError(f"wrong checkpoint contract: {path}")
            model = PhysicsCertifiedIntervalTemporalNRE()
            model.load_state_dict(ck["state_dict"])
            model.eval()
            result.append(model)
        else:
            result.append(train(data, seed))
    return result


def fresh_sources(data: v1.Data) -> list[int]:
    # Preserve all source carriers whose held-test ranks were already opened in
    # V1/V2 and V3.  V4's final evaluator gets a disjoint truth-source subset.
    old = set(v1.coverage_indices(v1.carrier_rows(), 32)) | set(v3.fresh_sources(data))
    remaining = [i for i in range(210) if i not in old]
    remaining.sort(
        key=lambda i: hashlib.sha256(
            f"CTT-V4-FRESH-SOURCE|H01|{data.cids[i]}".encode()
        ).digest()
    )
    return remaining[:FRESH_COUNT]


def write_pretest_contract(data: v1.Data) -> dict:
    indices = fresh_sources(data)
    ids = [data.cids[i] for i in indices]
    source_hash = hashlib.sha256(("\n".join(ids) + "\n").encode()).hexdigest()
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    contract = {
        "contract": "CTT_PHYSICS_CERTIFIED_INTERVAL_CAUSAL_TEMPORAL_NRE_V4_PRETEST",
        "method": {
            "physics_evidence": "three-member proper energy score",
            "transport_interval": "min/max over full energy evidence plus all three leave-one-member-out energy evidences after one common full-score affine standardization",
            "neural_operator": "causal TCN outputs lambda=sigmoid(r) and score=lower+lambda*(upper-lower)",
            "hard_guarantee": "if lower_a > upper_b then score_a > score_b for every network parameter value",
            "loss": "pairwise source ranking + chronological-vs-time-permute margin",
            "loss_weights": [1.0, 1.0],
            "predictor_members": list(PRED_MEMBERS),
            "train_obs_members": list(TRAIN_OBS),
            "val_obs_member": VAL_OBS,
            "fresh_test_obs_member": TEST_OBS,
            "train_trajectories": [4001, 4002, 4003],
            "val_trajectory": 4004,
            "fresh_test_trajectory": 4005,
            "steps": STEPS,
            "model_seeds": list(SEEDS),
        },
        "fresh_source_count": len(indices),
        "fresh_source_indices": indices,
        "fresh_source_ids": ids,
        "fresh_source_list_sha256": source_hash,
        "fresh_source_exclusion": "disjoint from all 32 V1/V2 held-test truth sources and all 64 V3 held-test truth sources",
        "first_gate_timing": "median of the ten frozen actual H01 PMFS source-update times for each update 1..5",
        "stress_timing": "all ten actual historical H01 update times only if every median gate passes",
        "gates": {
            "time": "wins>losses; exact two-sided sign p<=0.01; chronological Top10 >= TIME-PERMUTE Top10 + 0.05",
            "physics_non_degradation": "network Top5 >= energy Top5 - 0.05; network Top10 >= energy Top10; network mean normalized rank <= energy mean normalized rank",
            "online": "every update network median normalized rank <=0.25; update1 network mean normalized rank <= energy +0.05",
            "posterior_safety": "diagnostic only in V4 median gate; no closed-loop authorization until a separately frozen deployable posterior operator also passes",
        },
        "posterior_policy": "V4 qualifies the likelihood/evidence operator only. Geometry-prior fusion that failed V3 is not silently reused as a deployment posterior.",
        "code_sha256": code_hash,
        "no_post_test_changes": True,
    }
    (OUT / "PRETEST_CONTRACT.json").write_text(json.dumps(contract, indent=2))
    return contract


def score_all(models: list[nn.Module], data: v1.Data, true: int, cut: float,
              permuted: bool = False) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    tr = TEST_TRAJ
    obs_member = TEST_OBS
    n = data.nblocks(tr, cut)
    order = (
        deterministic_perm(n, f"V4TEST|traj={tr}|member={obs_member}|cut={cut:.9f}|n={n}")
        if permuted else None
    )
    full_z, lower, upper, _ = certified_interval_all(data, tr, true, obs_member, cut)
    seq = []
    for cand in range(210):
        p = prim(data, tr, true, obs_member, cand, cut)
        seq.append(v1.sequence_features(p, order))
    x, mask = pad(seq)
    lo = torch.from_numpy(lower.astype(np.float32))
    hi = torch.from_numpy(upper.astype(np.float32))
    with torch.no_grad():
        scores = np.mean(np.stack([m(x, mask, lo, hi).numpy() for m in models]), axis=0)
    return scores, full_z, lower, upper


def aggregate(df):
    out = {}
    for key in ("network", "perm", "energy"):
        out[key] = {
            "top5": float((df[key] <= 5).mean()),
            "top10": float((df[key] <= 10).mean()),
            "median_rank": float(df[key].median()),
            "mean_norm_rank": float(((df[key] - 1) / 209).mean()),
        }
    return out


def exact_sign_p(wins: int, losses: int) -> float:
    from math import comb
    n = wins + losses
    if not n:
        return 1.0
    tail = sum(comb(n, i) for i in range(min(wins, losses) + 1)) / (2 ** n)
    return min(1.0, 2.0 * tail)


def evaluate_one_update(update: int) -> Path:
    """Worker-safe single-update median evaluator."""
    import pandas as pd
    torch.set_num_threads(1)
    data = v1.Data()
    models = get_models(data)
    cut = float(data.med[update])
    rows = []
    for true in fresh_sources(data):
        score, full_z, lower, upper = score_all(models, data, true, cut, False)
        perm_score, _, _, _ = score_all(models, data, true, cut, True)
        r = v1.rank_desc(score, true)
        rp = v1.rank_desc(perm_score, true)
        re = v1.rank_desc(full_z, true)
        certainly_better = int(np.sum(lower > upper[true] + 1e-12))
        certainly_worse = int(np.sum(upper < lower[true] - 1e-12))
        rows.append([
            update, cut, data.nblocks(TEST_TRAJ, cut), true,
            r, rp, re,
            float(lower[true]), float(upper[true]), float(upper[true] - lower[true]),
            certainly_better, certainly_worse,
        ])
    path = OUT / f"median_update{update}_cases.csv"
    pd.DataFrame(rows, columns=[
        "update", "cut_time_s", "blocks", "true", "network", "perm", "energy",
        "true_interval_lower", "true_interval_upper", "true_interval_width",
        "certainly_better_than_true", "certainly_worse_than_true",
    ]).to_csv(path, index=False)
    return path


def finalize_median(paths: list[Path]) -> dict:
    import pandas as pd
    df = pd.concat([pd.read_csv(p) for p in paths], ignore_index=True)
    df.to_csv(OUT / "median_cases.csv", index=False)
    overall = aggregate(df)
    by_update = {str(u): aggregate(g) for u, g in df.groupby("update")}
    wins = int((df.network < df.perm).sum())
    losses = int((df.network > df.perm).sum())
    ties = int(len(df) - wins - losses)
    p = exact_sign_p(wins, losses)
    time_gate = (
        wins > losses and p <= 0.01 and
        overall["network"]["top10"] >= overall["perm"]["top10"] + 0.05
    )
    physics_gate = (
        overall["network"]["top5"] >= overall["energy"]["top5"] - 0.05 and
        overall["network"]["top10"] >= overall["energy"]["top10"] and
        overall["network"]["mean_norm_rank"] <= overall["energy"]["mean_norm_rank"]
    )
    online_gate = (
        all(by_update[str(u)]["network"]["median_rank"] <= 1 + 0.25 * 209 for u in range(1, 6)) and
        by_update["1"]["network"]["mean_norm_rank"] <= by_update["1"]["energy"]["mean_norm_rank"] + 0.05
    )
    summary = {
        "contract": "CTT_PHYSICS_CERTIFIED_INTERVAL_CAUSAL_TEMPORAL_NRE_V4_H01_MEDIAN_GATE",
        "fresh_test": "trajectory4005_member7_on_disjoint_48_source_subset",
        "fresh_source_count": len(fresh_sources(v1.Data())),
        "overall": overall,
        "by_update": by_update,
        "time_permute": {"wins": wins, "losses": losses, "ties": ties, "sign_p": p},
        "interval_diagnostics": {
            "median_true_interval_width": float(df.true_interval_width.median()),
            "mean_certainly_better_than_true": float(df.certainly_better_than_true.mean()),
            "mean_certainly_worse_than_true": float(df.certainly_worse_than_true.mean()),
        },
        "gates": {
            "time": bool(time_gate),
            "physics_non_degradation": bool(physics_gate),
            "online": bool(online_gate),
        },
        "verdict": "PASS_FOR_STRESS" if time_gate and physics_gate and online_gate else "NO_GO",
        "closed_loop_authorized": False,
    }
    (OUT / "median_summary.json").write_text(json.dumps(summary, indent=2))
    return summary


def checkpoint_freeze() -> dict:
    rows = []
    for seed in SEEDS:
        path = OUT / f"model_{seed}.pt"
        if not path.exists():
            raise FileNotFoundError(path)
        ck = torch.load(path, map_location="cpu", weights_only=False)
        rows.append({
            "seed": seed,
            "best_step": int(ck["best_step"]),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        })
    out = {"contract": CONTRACT, "checkpoints": rows}
    (OUT / "CHECKPOINT_FREEZE.json").write_text(json.dumps(out, indent=2))
    return out


def selftest(data: v1.Data, models: list[nn.Module] | None = None) -> dict:
    cut = float(data.med[3])
    true = 0
    n = data.nblocks(TEST_TRAJ, cut)
    obs = data.bm[TEST_TRAJ, true, TEST_OBS, :n]
    pred = data.bm[TEST_TRAJ, true, list(PRED_MEMBERS), :n]
    pa = v1.primitives(obs, pred)
    pb = v1.primitives(obs, pred[[2, 0, 1]])
    member_perm_err = float(np.max(np.abs(pa - pb)))
    assert member_perm_err < 1e-7

    full_z, lower, upper, _ = certified_interval_all(data, TEST_TRAJ, true, TEST_OBS, cut)
    # Recompute after a predictor-member permutation.  The interval support is
    # a set over full+LOO members and must be invariant to member labels.
    original = PRED_MEMBERS
    # The helper uses the frozen tuple, so set-level invariance is checked
    # directly by reconstructing all subsets under a relabeling.
    perm_members = (2, 0, 1)
    full2 = energy_evidence_subset(data, TEST_TRAJ, true, TEST_OBS, cut, perm_members)
    loo2 = []
    for drop in perm_members:
        loo2.append(energy_evidence_subset(
            data, TEST_TRAJ, true, TEST_OBS, cut,
            tuple(m for m in perm_members if m != drop),
        ))
    center = float(full2.mean())
    scale = max(float(full2.std()), 1e-8)
    stack2 = np.stack([(full2 - center) / scale] + [(x - center) / scale for x in loo2])
    interval_perm_err = float(max(
        np.max(np.abs(full_z - (full2 - center) / scale)),
        np.max(np.abs(lower - stack2.min(0))),
        np.max(np.abs(upper - stack2.max(0))),
    ))
    assert interval_perm_err < 1e-7

    model = PhysicsCertifiedIntervalTemporalNRE()
    seq = [v1.sequence_features(pa)]
    x, mask = pad(seq)
    lo = torch.tensor([-0.7], dtype=torch.float32)
    hi = torch.tensor([1.3], dtype=torch.float32)
    with torch.no_grad():
        q = float(model(x, mask, lo, hi)[0])
    assert -0.7 <= q <= 1.3

    # Algebraic hard-dominance check over random selector values.
    rng = np.random.default_rng(20260830)
    hard_ok = True
    min_gap = float("inf")
    for _ in range(1000):
        b_hi = float(rng.normal())
        a_lo = b_hi + abs(float(rng.normal())) + 1e-6
        a_hi = a_lo + abs(float(rng.normal()))
        b_lo = b_hi - abs(float(rng.normal()))
        la = float(rng.random()); lb = float(rng.random())
        sa = a_lo + la * (a_hi - a_lo)
        sb = b_lo + lb * (b_hi - b_lo)
        min_gap = min(min_gap, sa - sb)
        hard_ok &= sa > sb
    assert hard_ok and min_gap > 0

    result = {
        "predictor_member_permutation_max_abs": member_perm_err,
        "certified_interval_permutation_max_abs": interval_perm_err,
        "score_inside_interval": True,
        "hard_nonoverlap_dominance": True,
        "hard_nonoverlap_min_random_gap": min_gap,
        "test_observation_member": TEST_OBS,
        "test_member_not_in_predictors_or_train_or_val": TEST_OBS not in (PRED_MEMBERS + TRAIN_OBS + (VAL_OBS,)),
        "pass": True,
    }
    (OUT / "selftest.json").write_text(json.dumps(result, indent=2))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", action="store_true", help="write pre-test contract and static selftest only")
    parser.add_argument("--train", action="store_true", help="train/freeze all checkpoints; do not evaluate fresh test")
    parser.add_argument("--median", action="store_true", help="run fresh median gate after frozen checkpoints")
    args = parser.parse_args()

    data = v1.Data()
    contract = write_pretest_contract(data)
    print("V4PRETEST", contract["fresh_source_list_sha256"], contract["code_sha256"], flush=True)
    print("V4SELFTEST", selftest(data), flush=True)
    if args.prepare and not args.train and not args.median:
        return 0

    models = get_models(data)
    freeze = checkpoint_freeze()
    print("V4CHECKPOINTS", freeze, flush=True)
    if args.train and not args.median:
        return 0

    if args.median:
        # Sequential fallback; the audit driver may call evaluate_one_update in
        # parallel without changing any score definition.
        paths = [evaluate_one_update(u) for u in range(1, 6)]
        summary = finalize_median(paths)
        print(json.dumps(summary, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
