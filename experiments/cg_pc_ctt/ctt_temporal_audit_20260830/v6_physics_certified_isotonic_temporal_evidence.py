#!/usr/bin/env python3
"""CTT V6: physics-certified isotonic temporal evidence projection.

The frozen V3 causal temporal ensemble proposes a real-valued source evidence
vector.  Full+leave-one-transport-member-out energy intervals define a robust
physical partial order.  V6 computes the Euclidean-near isotonic correction by
Dykstra projection onto the corresponding order cone, using only the transitive
reduction of the DAG.  Unlike V4, scores are not confined to narrow absolute
intervals; unlike V5, candidates are not globally re-ranked by a discrete Kahn
extension.  Only actual physical-order violations are corrected.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
import torch

sys.path.insert(0, "/mnt/data/h01_temporal_gate")
import train_eval_ctt_temporal_nre as v1
import v3_physics_order_temporal_nre as v3
import v4_physics_certified_interval_temporal_nre as v4
import v5_physics_certified_partial_order_temporal_ranker as v5

OUT = Path("/mnt/data/h01_temporal_gate/v6")
OUT.mkdir(exist_ok=True)
CONTRACT = "CTT_PHYSICS_CERTIFIED_ISOTONIC_TEMPORAL_EVIDENCE_V6"
TEST_TRAJ = 4
TEST_OBS = 7
FRESH_COUNT = 16
NUMERIC_DOMINANCE_EPS = 1e-12
SOLVER_TOL = 1e-10
RANK_TIE_TOL = 1e-8
MAX_SWEEPS = 1000

EXPECTED_V3_CHECKPOINTS = v5.EXPECTED_V3_CHECKPOINTS


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_v3_checkpoints() -> dict:
    return v5.verify_v3_checkpoints()


def fresh_sources(data: v1.Data) -> list[int]:
    used = (
        set(v1.coverage_indices(v1.carrier_rows(), 32))
        | set(v3.fresh_sources(data))
        | set(v4.fresh_sources(data))
        | set(v5.fresh_sources(data))
    )
    remaining = [i for i in range(210) if i not in used]
    remaining.sort(
        key=lambda i: hashlib.sha256(
            f"CTT-V6-FRESH-SOURCE|H01|{data.cids[i]}".encode()
        ).digest()
    )
    return remaining[:FRESH_COUNT]


def rank_desc_tol(values: np.ndarray, idx: int, tol: float = RANK_TIE_TOL) -> int:
    x = np.asarray(values, dtype=np.float64)
    return 1 + int(np.sum(x > x[idx] + tol))


def raw_temporal_scores(models, data: v1.Data, true: int, cut: float,
                        permuted: bool = False) -> np.ndarray:
    n = data.nblocks(TEST_TRAJ, cut)
    order = (
        v1.deterministic_perm(
            n, f"V6TEST|traj={TEST_TRAJ}|member={TEST_OBS}|cut={cut:.9f}|n={n}"
        ) if permuted else None
    )
    _, energy_z = v3.energy_all(data, TEST_TRAJ, true, TEST_OBS, cut)
    seq = []
    for cand in range(210):
        p = v3.prim(data, TEST_TRAJ, true, TEST_OBS, cand, cut)
        seq.append(v1.sequence_features(p, order))
    x, mask = v1.pad_batch(seq)
    ez = torch.from_numpy(energy_z.astype(np.float32))
    with torch.no_grad():
        return np.mean(np.stack([m(x, mask, ez).numpy() for m in models]), axis=0)


def dominance_matrix(lower: np.ndarray, upper: np.ndarray) -> np.ndarray:
    d = np.asarray(lower)[:, None] > (np.asarray(upper)[None, :] + NUMERIC_DOMINANCE_EPS)
    np.fill_diagonal(d, False)
    return d


def transitive_reduction_edges(dom: np.ndarray) -> list[tuple[int, int]]:
    g = nx.DiGraph()
    n = dom.shape[0]
    g.add_nodes_from(range(n))
    a, b = np.nonzero(dom)
    g.add_edges_from((int(i), int(j)) for i, j in zip(a, b))
    if not nx.is_directed_acyclic_graph(g):
        raise RuntimeError("PHYSICAL_DOMINANCE_GRAPH_NOT_ACYCLIC")
    tr = nx.transitive_reduction(g)
    return [(int(a), int(b)) for a, b in tr.edges()]


def dykstra_order_projection(raw: np.ndarray, lower: np.ndarray, upper: np.ndarray) -> tuple[np.ndarray, dict]:
    """Project raw score onto x_a >= x_b for each robust physical order a>b.

    Each halfspace correction has only two nonzero coordinates, so Dykstra's
    correction vector is represented by one scalar alpha per transitive-reduction
    edge.  The projection is deterministic and has no learned/tuned parameter.
    """
    raw = np.asarray(raw, dtype=np.float64)
    dom = dominance_matrix(lower, upper)
    edges = transitive_reduction_edges(dom)
    x = raw.copy()
    alpha = np.zeros(len(edges), dtype=np.float64)
    sweeps = 0
    max_reduced_violation = float("inf")
    for sweep in range(1, MAX_SWEEPS + 1):
        max_change = 0.0
        for k, (a, b) in enumerate(edges):
            # Stored Dykstra correction is alpha * (-e_a + e_b).
            ya = x[a] - alpha[k]
            yb = x[b] + alpha[k]
            violation = yb - ya
            new_alpha = 0.5 * violation if violation > 0.0 else 0.0
            xa = ya + new_alpha
            xb = yb - new_alpha
            max_change = max(max_change, abs(xa - x[a]), abs(xb - x[b]))
            x[a] = xa
            x[b] = xb
            alpha[k] = new_alpha
        if edges:
            max_reduced_violation = max(max(x[b] - x[a], 0.0) for a, b in edges)
        else:
            max_reduced_violation = 0.0
        sweeps = sweep
        if max_reduced_violation <= SOLVER_TOL and max_change <= SOLVER_TOL:
            break
    # Verify the original dense certificate, not merely the reduction edges.
    aa, bb = np.nonzero(dom)
    max_dense_violation = (
        float(np.max(x[bb] - x[aa])) if len(aa) else 0.0
    )
    violation_count = (
        int(np.sum((x[bb] - x[aa]) > RANK_TIE_TOL)) if len(aa) else 0
    )
    if max_dense_violation > RANK_TIE_TOL or violation_count:
        raise RuntimeError(
            f"ISOTONIC_CERTIFICATE_FAIL max={max_dense_violation} count={violation_count}"
        )
    return x, {
        "dense_constraint_count": int(dom.sum()),
        "reduced_edge_count": len(edges),
        "sweeps": sweeps,
        "max_dense_violation": max_dense_violation,
        "violation_count": violation_count,
        "l2_correction": float(np.linalg.norm(x - raw)),
        "max_abs_correction": float(np.max(np.abs(x - raw))),
    }


def write_pretest_contract(data: v1.Data) -> dict:
    ids = [data.cids[i] for i in fresh_sources(data)]
    source_hash = hashlib.sha256(("\n".join(ids) + "\n").encode()).hexdigest()
    contract = {
        "contract": "CTT_PHYSICS_CERTIFIED_ISOTONIC_TEMPORAL_EVIDENCE_V6_PRETEST",
        "network": "frozen V3 causal temporal ensemble; no V6 training",
        "v3_checkpoint_hashes": EXPECTED_V3_CHECKPOINTS,
        "physical_certificate": "full+all three LOO energy evidence intervals on one common standardized evidence axis",
        "projection": "Dykstra Euclidean projection of raw temporal score onto robust physical order cone; constraints reduced by exact DAG transitive reduction then verified against dense original constraints",
        "test": {"trajectory": 4005, "observation_member": TEST_OBS},
        "fresh_source_count": len(ids),
        "fresh_source_indices": fresh_sources(data),
        "fresh_source_ids": ids,
        "fresh_source_list_sha256": source_hash,
        "fresh_source_exclusion": "disjoint from V1/V2, V3, V4, and V5 held-test truth-source subsets",
        "numeric_contract": {
            "dominance_epsilon": NUMERIC_DOMINANCE_EPS,
            "solver_tolerance": SOLVER_TOL,
            "rank_tie_tolerance_standardized_score": RANK_TIE_TOL,
            "max_dykstra_sweeps": MAX_SWEEPS,
            "interpretation": "numerical equivalence only; not a scientific performance threshold",
        },
        "first_gate_timing": "median of ten frozen actual H01 source-update times for updates 1..5",
        "stress_timing": "all ten actual update times only after every median gate passes",
        "gates": {
            "time": "wins>losses; exact sign p<=0.01; projected chronological Top10 >= projected TIME-PERMUTE Top10 +0.05",
            "physics_non_degradation": "projected Top5 >= energy Top5 -0.05; projected Top10 >= energy Top10; projected mean normalized rank <= energy mean normalized rank",
            "online": "every update projected median normalized rank <=0.25; update1 projected mean normalized rank <= energy +0.05",
            "certificate": "zero dense robust-order reversals above rank tie tolerance in every case",
        },
        "posterior_policy": "V6 first qualifies a continuous evidence score. Closed-loop remains unauthorized until a separate posterior reconstruction/parity gate passes.",
        "code_sha256": sha256(Path(__file__)),
        "no_post_test_changes": True,
    }
    (OUT / "PRETEST_CONTRACT.json").write_text(json.dumps(contract, indent=2))
    return contract


def selftest() -> dict:
    raw = np.array([0.0, 3.0, 9.0, 2.0], dtype=float)
    lower = np.array([3.0, 2.5, 1.0, -1.0], dtype=float)
    upper = np.array([4.0, 3.5, 2.0, 0.0], dtype=float)
    proj, diag = dykstra_order_projection(raw, lower, upper)
    dom = dominance_matrix(lower, upper)
    aa, bb = np.nonzero(dom)
    assert np.all(proj[aa] + RANK_TIE_TOL >= proj[bb])
    # Idempotence: a feasible physical evidence vector must remain unchanged.
    feasible = np.array([4.0, 3.0, 2.0, 0.0], dtype=float)
    feasible_proj, _ = dykstra_order_projection(feasible, lower, upper)
    idem = float(np.max(np.abs(feasible_proj - feasible)))
    assert idem <= RANK_TIE_TOL
    return {"projection": proj.tolist(), "feasible_idempotence_max_abs": idem, **diag, "pass": True}


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
    if not n:
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
            raw = raw_temporal_scores(models, data, true, cut, False)
            raw_perm = raw_temporal_scores(models, data, true, cut, True)
            full_z, lower, upper, _ = v4.certified_interval_all(data, TEST_TRAJ, true, TEST_OBS, cut)
            proj, diag = dykstra_order_projection(raw, lower, upper)
            pproj, pdiag = dykstra_order_projection(raw_perm, lower, upper)
            rows.append({
                "update": update,
                "timing_index": timing_index,
                "cut_time_s": cut,
                "blocks": data.nblocks(TEST_TRAJ, cut),
                "true": true,
                "projected": rank_desc_tol(proj, true),
                "perm_projected": rank_desc_tol(pproj, true),
                "raw_temporal": rank_desc_tol(raw, true),
                "energy": rank_desc_tol(full_z, true),
                "dense_constraints": diag["dense_constraint_count"],
                "reduced_edges": diag["reduced_edge_count"],
                "projection_sweeps": diag["sweeps"],
                "certificate_violations": diag["violation_count"],
                "projection_l2": diag["l2_correction"],
                "projection_max_abs": diag["max_abs_correction"],
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
    gates = {"time": bool(time_gate), "physics_non_degradation": bool(physics_gate),
             "online": bool(online_gate), "certificate": bool(certificate_gate)}
    summary = {
        "contract": f"{CONTRACT}_H01_{timing_mode.upper()}_GATE",
        "fresh_test": "trajectory4005_member7_on_disjoint_16_source_subset",
        "fresh_source_count": len(fresh_sources(v1.Data())),
        "overall": overall,
        "by_update": by_update,
        "time_permute": {"wins": wins, "losses": losses, "ties": ties, "sign_p": p},
        "projection": {
            "median_dense_constraints": float(df.dense_constraints.median()),
            "median_reduced_edges": float(df.reduced_edges.median()),
            "median_sweeps": float(df.projection_sweeps.median()),
            "median_l2_correction": float(df.projection_l2.median()),
            "total_certificate_violations": int(df.certificate_violations.sum()),
        },
        "gates": gates,
        "verdict": "PASS_FOR_STRESS" if all(gates.values()) and timing_mode == "median" else (
            "PASS_EVIDENCE_QUALIFIED" if all(gates.values()) else "NO_GO"
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
    print("V6V3FREEZE", verify_v3_checkpoints(), flush=True)
    c = write_pretest_contract(data)
    print("V6PRETEST", c["fresh_source_list_sha256"], c["code_sha256"], flush=True)
    print("V6SELFTEST", selftest(), flush=True)
    if args.prepare and not args.median and not args.stress:
        return 0
    mode = "stress" if args.stress else "median"
    paths = [evaluate_one_update(u, mode) for u in range(1, 6)]
    print(json.dumps(finalize(paths, mode), indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
