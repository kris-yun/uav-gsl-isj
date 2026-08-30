#!/usr/bin/env python3
"""CTT V5: physics-certified partial-order temporal ranker.

V5 freezes the already-qualified V3 causal temporal network checkpoints.  Native
transport uncertainty defines a truth-blind partial order: source a must precede
source b only when a's entire full+LOO physical evidence interval lies above b's.
A deterministic Kahn linear extension uses the temporal network score solely to
order currently incomparable candidates.

No model training, blending coefficient, margin threshold, or House-outcome-tuned
parameter is introduced in V5.
"""
from __future__ import annotations

import argparse
import hashlib
import heapq
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch

sys.path.insert(0, "/mnt/data/h01_temporal_gate")
import train_eval_ctt_temporal_nre as v1
import v3_physics_order_temporal_nre as v3
import v4_physics_certified_interval_temporal_nre as v4

OUT = Path("/mnt/data/h01_temporal_gate/v5")
OUT.mkdir(exist_ok=True)
FRESH_COUNT = 40
TEST_OBS = 3
TEST_TRAJ = 4
NUMERIC_EPS = 1e-12
CONTRACT = "CTT_PHYSICS_CERTIFIED_PARTIAL_ORDER_TEMPORAL_RANKER_V5"
EXPECTED_V3_CHECKPOINTS = {
    1701: "e43afa379cbbc16d467a6bdbe1c5f5386610a3c8493780fa68008afcb1144901",
    1702: "877337556b8f01969a03e1aa89873389abd4d0b3bbd427bf02e9355771f30dc4",
    1703: "c0955aedf9ad0405fa639857dda3651560ca77b92a4e84daac391495fb3a19c8",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_v3_checkpoints() -> dict:
    rows = []
    for seed, expected in EXPECTED_V3_CHECKPOINTS.items():
        path = v3.OUT / f"model_{seed}.pt"
        got = sha256(path)
        if got != expected:
            raise ValueError(f"V3_CHECKPOINT_HASH_MISMATCH seed={seed} got={got} expected={expected}")
        ck = torch.load(path, map_location="cpu", weights_only=False)
        rows.append({"seed": seed, "best_step": int(ck["best_step"]), "sha256": got})
    return {"status": "PASS", "checkpoints": rows}


def dominance_matrix(lower: np.ndarray, upper: np.ndarray) -> np.ndarray:
    """dominance[a,b] iff all certified evidence for a exceeds all for b."""
    d = lower[:, None] > (upper[None, :] + NUMERIC_EPS)
    np.fill_diagonal(d, False)
    return d


def certified_linear_extension(raw_score: np.ndarray, lower: np.ndarray,
                               upper: np.ndarray, carrier_ids: list[str]) -> tuple[np.ndarray, dict]:
    """Return 1-based ranks satisfying every robust physical dominance edge.

    Kahn's algorithm exposes only zero-indegree candidates.  Among that feasible
    frontier, the higher chronological temporal score wins; carrier id is the
    deterministic final tie break.  Temporal evidence can therefore act freely
    only where physical transport uncertainty leaves candidates incomparable.
    """
    raw = np.asarray(raw_score, dtype=np.float64)
    lower = np.asarray(lower, dtype=np.float64)
    upper = np.asarray(upper, dtype=np.float64)
    n = len(raw)
    if not (len(lower) == len(upper) == len(carrier_ids) == n):
        raise ValueError("shape mismatch")
    dom = dominance_matrix(lower, upper)
    indegree = dom.sum(axis=0).astype(np.int64)
    outgoing = [np.flatnonzero(dom[i]).astype(np.int64).tolist() for i in range(n)]
    heap = []
    for i in range(n):
        if indegree[i] == 0:
            heapq.heappush(heap, (-float(raw[i]), str(carrier_ids[i]), i))
    order = []
    while heap:
        _, _, i = heapq.heappop(heap)
        order.append(i)
        for j in outgoing[i]:
            indegree[j] -= 1
            if indegree[j] == 0:
                heapq.heappush(heap, (-float(raw[j]), str(carrier_ids[j]), j))
    if len(order) != n:
        raise RuntimeError("PHYSICAL_DOMINANCE_GRAPH_NOT_ACYCLIC")
    rank = np.empty(n, dtype=np.int64)
    for pos, i in enumerate(order, 1):
        rank[i] = pos
    violations = int(np.sum(dom & (rank[:, None] > rank[None, :])))
    if violations != 0:
        raise RuntimeError(f"CERTIFIED_ORDER_VIOLATION count={violations}")
    return rank, {
        "robust_constraint_count": int(dom.sum()),
        "zero_indegree_initial": int(np.sum(dom.sum(axis=0) == 0)),
        "violations": violations,
    }


def fresh_sources(data: v1.Data) -> list[int]:
    old = (
        set(v1.coverage_indices(v1.carrier_rows(), 32))
        | set(v3.fresh_sources(data))
        | set(v4.fresh_sources(data))
    )
    remaining = [i for i in range(210) if i not in old]
    remaining.sort(
        key=lambda i: hashlib.sha256(
            f"CTT-V5-FRESH-SOURCE|H01|{data.cids[i]}".encode()
        ).digest()
    )
    return remaining[:FRESH_COUNT]


def write_pretest_contract(data: v1.Data) -> dict:
    ids = [data.cids[i] for i in fresh_sources(data)]
    source_hash = hashlib.sha256(("\n".join(ids) + "\n").encode()).hexdigest()
    code_hash = sha256(Path(__file__))
    contract = {
        "contract": "CTT_PHYSICS_CERTIFIED_PARTIAL_ORDER_TEMPORAL_RANKER_V5_PRETEST",
        "network": "frozen V3 causal temporal ensemble; no V5 training",
        "v3_checkpoint_hashes": EXPECTED_V3_CHECKPOINTS,
        "physical_certificate": "full three-member energy evidence + all three leave-one-member-out energy evidences, common full-score affine scale",
        "dominance_rule": "a dominates b iff lower_a > upper_b + 1e-12; epsilon is numerical-only and fixed before test",
        "ranking_operator": "Kahn topological linear extension; chronological temporal score breaks ties only among currently feasible incomparable candidates; carrier id final deterministic tie-break",
        "fresh_test": {"trajectory": 4005, "observation_member": TEST_OBS},
        "fresh_source_count": len(ids),
        "fresh_source_ids": ids,
        "fresh_source_indices": fresh_sources(data),
        "fresh_source_list_sha256": source_hash,
        "fresh_source_exclusion": "disjoint from V1/V2 32-source, V3 64-source, and V4 48-source held-test truth subsets",
        "first_gate_timing": "median of ten frozen actual H01 PMFS source-update times for updates 1..5",
        "stress_timing": "all ten actual historical source-update times only if every median gate passes",
        "gates": {
            "time": "wins>losses; exact two-sided sign p<=0.01; projected chronological Top10 >= projected TIME-PERMUTE Top10 + 0.05",
            "physics_non_degradation": "projected Top5 >= energy Top5 - 0.05; projected Top10 >= energy Top10; projected mean normalized rank <= energy mean normalized rank",
            "online": "every update projected median normalized rank <=0.25; update1 projected mean normalized rank <= energy +0.05",
            "certificate": "zero robust physical-order violations in every case",
        },
        "posterior_policy": "V5 qualifies ranking only. No closed-loop posterior is authorized by a rank-only PASS.",
        "code_sha256": code_hash,
        "no_post_test_changes": True,
    }
    (OUT / "PRETEST_CONTRACT.json").write_text(json.dumps(contract, indent=2))
    return contract


def selftest() -> dict:
    raw = np.array([0.1, 3.0, 9.0, 2.0], dtype=float)
    lower = np.array([3.0, 2.5, 1.0, -1.0], dtype=float)
    upper = np.array([4.0, 3.5, 2.0, 0.0], dtype=float)
    ids = ["a", "b", "c", "d"]
    rank, diag = certified_linear_extension(raw, lower, upper, ids)
    # c has the largest temporal score but is physically dominated by a and b.
    assert rank[0] < rank[2] and rank[1] < rank[2]
    # a and b overlap physically; temporal score b>a must be allowed to order b first.
    assert rank[1] < rank[0]
    # d is robustly below everyone and cannot jump ahead despite any raw tie break.
    assert rank[3] == 4
    assert diag["violations"] == 0
    return {"synthetic_rank": rank.tolist(), **diag, "pass": True}


def aggregate(df: pd.DataFrame) -> dict:
    out = {}
    for key in ("projected", "perm_projected", "raw_temporal", "energy"):
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
    if n == 0:
        return 1.0
    tail = sum(comb(n, i) for i in range(min(wins, losses) + 1)) / (2 ** n)
    return min(1.0, 2.0 * tail)


def evaluate_one_update(update: int, timing_mode: str = "median") -> Path:
    torch.set_num_threads(1)
    data = v1.Data()
    models = v3.get_models(data)
    cuts = [float(data.med[update])] if timing_mode == "median" else [float(x) for x in data.bytime[update]]
    rows = []
    for timing_index, cut in enumerate(cuts):
        for true in fresh_sources(data):
            raw = v3.score_all(models, data, true, cut, False)
            raw_perm = v3.score_all(models, data, true, cut, True)
            full_z, lower, upper, _ = v4.certified_interval_all(data, TEST_TRAJ, true, TEST_OBS, cut)
            rank, diag = certified_linear_extension(raw, lower, upper, data.cids)
            prank, pdiag = certified_linear_extension(raw_perm, lower, upper, data.cids)
            if diag["violations"] or pdiag["violations"]:
                raise RuntimeError("V5_CERTIFICATE_BROKEN")
            rows.append({
                "update": update,
                "timing_index": timing_index,
                "cut_time_s": cut,
                "blocks": data.nblocks(TEST_TRAJ, cut),
                "true": true,
                "projected": int(rank[true]),
                "perm_projected": int(prank[true]),
                "raw_temporal": int(v1.rank_desc(raw, true)),
                "energy": int(v1.rank_desc(full_z, true)),
                "robust_constraint_count": diag["robust_constraint_count"],
                "certificate_violations": 0,
            })
    path = OUT / f"{timing_mode}_update{update}_cases.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def finalize(paths: list[Path], timing_mode: str) -> dict:
    df = pd.concat([pd.read_csv(p) for p in paths], ignore_index=True)
    df.to_csv(OUT / f"{timing_mode}_cases.csv", index=False)
    overall = aggregate(df)
    by_update = {str(u): aggregate(g) for u, g in df.groupby("update")}
    wins = int((df.projected < df.perm_projected).sum())
    losses = int((df.projected > df.perm_projected).sum())
    ties = int(len(df) - wins - losses)
    p = exact_sign_p(wins, losses)
    time_gate = (
        wins > losses and p <= 0.01 and
        overall["projected"]["top10"] >= overall["perm_projected"]["top10"] + 0.05
    )
    physics_gate = (
        overall["projected"]["top5"] >= overall["energy"]["top5"] - 0.05 and
        overall["projected"]["top10"] >= overall["energy"]["top10"] and
        overall["projected"]["mean_norm_rank"] <= overall["energy"]["mean_norm_rank"]
    )
    online_gate = (
        all(by_update[str(u)]["projected"]["median_rank"] <= 1 + 0.25 * 209 for u in range(1, 6)) and
        by_update["1"]["projected"]["mean_norm_rank"] <= by_update["1"]["energy"]["mean_norm_rank"] + 0.05
    )
    certificate_gate = int(df.certificate_violations.sum()) == 0
    gates = {
        "time": bool(time_gate),
        "physics_non_degradation": bool(physics_gate),
        "online": bool(online_gate),
        "certificate": bool(certificate_gate),
    }
    summary = {
        "contract": f"{CONTRACT}_H01_{timing_mode.upper()}_GATE",
        "fresh_test": "trajectory4005_member3_on_disjoint_40_source_subset",
        "fresh_source_count": len(fresh_sources(v1.Data())),
        "overall": overall,
        "by_update": by_update,
        "time_permute": {"wins": wins, "losses": losses, "ties": ties, "sign_p": p},
        "certificate": {
            "total_violations": int(df.certificate_violations.sum()),
            "median_constraint_count": float(df.robust_constraint_count.median()),
        },
        "gates": gates,
        "verdict": "PASS_FOR_STRESS" if all(gates.values()) and timing_mode == "median" else (
            "PASS_RANKING_QUALIFIED" if all(gates.values()) else "NO_GO"
        ),
        "closed_loop_authorized": False,
    }
    (OUT / f"{timing_mode}_summary.json").write_text(json.dumps(summary, indent=2))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--median", action="store_true")
    parser.add_argument("--stress", action="store_true")
    args = parser.parse_args()
    data = v1.Data()
    print("V5V3FREEZE", verify_v3_checkpoints(), flush=True)
    contract = write_pretest_contract(data)
    print("V5PRETEST", contract["fresh_source_list_sha256"], contract["code_sha256"], flush=True)
    print("V5SELFTEST", selftest(), flush=True)
    if args.prepare and not args.median and not args.stress:
        return 0
    mode = "stress" if args.stress else "median"
    paths = [evaluate_one_update(u, mode) for u in range(1, 6)]
    print(json.dumps(finalize(paths, mode), indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
