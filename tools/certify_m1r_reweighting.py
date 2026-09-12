"""Oracle ceiling for candidate-common nonnegative weighting of frozen M2 logs.

This is a hindsight impossibility/feasibility diagnostic, never a deployable
policy. max_{w>=0,sum w=1} min_{r!=s} sum_i w_i (ell_i(s)-ell_i(r)).
Dual probability weights over rivals give a checkable upper bound. Includes
event selection, delayed release, and positive likelihood tempering at fixed
scores; excludes changing forward maps, observation law, candidates or paths.
"""
import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

from check_m1r_pairwise_premise import event_scores, sha


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    premise_path = args.repo / "evidence/m1r_causal_repair_20260912/PAIRWISE_PREMISE.json"
    premise = json.loads(premise_path.read_text(encoding="utf-8"))
    result = {
        "contract": "M1R_ORACLE_NONNEGATIVE_REWEIGHTING_CEILING_V1",
        "class": "candidate-common nonnegative event weights, fixed logged M2 score vectors and support",
        "excluded": "changed observation/forward laws, changed candidate support, changed closed-loop histories, candidate-specific weights",
        "strict_identification_scope": "source-containing first-level leaf against every other exported first-level leaf",
        "not_a_source_coordinate_error_bound": True,
        "prior_and_leaf_area_terms": "not included; certificate concerns likelihood evidence ordering, not full native posterior ordering",
        "oracle": True, "deployable": False,
        "interpretation": "positive optimum is only oracle feasibility; zero upper bound excludes strict unique discrimination within this weighting class",
        "primal_dual_tolerance": 1e-7,
        "premise_sha256": sha(premise_path), "analyzer_sha256": sha(Path(__file__)), "houses": {}}
    for house, hd in premise["houses"].items():
        path = args.repo / f"evidence/m1r_instrumented_20260912/{house}_seed12_M1R/context_bank/contrastive_event_attribution.csv"
        grouped = defaultdict(lambda: defaultdict(list))
        with path.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                assert int(row["member_index"]) == 0
                grouped[int(row["source_update_id"])][row["candidate_id"]].append(row)
        result["houses"][house] = {"attribution_sha256": sha(path), "updates": {}}
        for uid, candidates in sorted(grouped.items()):
            tid = hd["updates"][str(uid)]["source_region_binding"]["source_containing_leaf"]
            scores = {cid: np.asarray(event_scores(sorted(rows, key=lambda r: int(r["event_index"])))["M2"]) for cid, rows in candidates.items()}
            rivals = sorted(c for c in candidates if c != tid)
            differences = np.array([scores[tid] - scores[r] for r in rivals])
            m, n = differences.shape
            opt = linprog(np.r_[np.zeros(n), -1.], A_ub=np.c_[-differences, np.ones(m)],
                          b_ub=np.zeros(m), A_eq=np.array([np.r_[np.ones(n), 0.]]),
                          b_eq=np.ones(1), bounds=[(0., None)] * n + [(None, None)], method="highs")
            assert opt.success, opt.message
            w = np.maximum(0., opt.x[:n]); w /= w.sum()
            v = np.maximum(0., -opt.ineqlin.marginals); v /= v.sum()
            lower = float(np.min(differences @ w))
            upper = float(np.max(v @ differences))
            assert upper - lower < 1e-7, (lower, upper)
            equivalent = [r for r in rivals if np.max(np.abs(scores[r]-scores[tid])) < 1e-12]
            tx, ty = (float(candidates[tid][0][k]) for k in ("candidate_x", "candidate_y"))
            aliases = [{"candidate_id": r,
                        "xy": [float(candidates[r][0][k]) for k in ("candidate_x", "candidate_y")],
                        "center_distance_from_source_leaf_center_m": math.hypot(float(candidates[r][0]["candidate_x"])-tx, float(candidates[r][0]["candidate_y"])-ty)} for r in equivalent]
            for alias in aliases:
                ordered_true = sorted(candidates[tid], key=lambda r: int(r["event_index"]))
                ordered_rival = sorted(candidates[alias["candidate_id"]], key=lambda r: int(r["event_index"]))
                assert [float(r["legacy_hit_probability"]) for r in ordered_true] == [float(r["legacy_hit_probability"]) for r in ordered_rival]
            if upper < -1e-7:
                verdict = "NO_STRICT_DISCRIMINATION_NEGATIVE_UPPER_BOUND"
            elif aliases:
                verdict = "NO_STRICT_DISCRIMINATION_EXACT_LOGGED_ALIAS"
            elif lower > 1e-7:
                verdict = "ORACLE_FEASIBLE_NOT_A_DEPLOYABLE_SELECTOR"
            else:
                verdict = "NUMERICALLY_UNRESOLVED_NEAR_ZERO_MARGIN"
            result["houses"][house]["updates"][str(uid)] = {
                "source_leaf": tid, "event_count": n, "rival_ids": rivals,
                "maximin_margin_lower_nats_per_weight_unit": lower,
                "maximin_margin_upper_nats_per_weight_unit": upper,
                "dual_gap": upper-lower, "primal_event_weights": w.tolist(), "dual_rival_weights": v.tolist(),
                "score_aliases": aliases,
                "verdict": verdict}
            print(house, uid, "oracle maximin [lower,upper]", round(lower, 8), round(upper, 8), "aliases", len(aliases))
    args.output.write_bytes((json.dumps(result, indent=2) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
