#!/usr/bin/env python3
"""PMFS3D-R1P5: saved-score suppression/selectivity audit.

No forward simulation is performed. This script reads the completed R1 Oracle-2D
and Oracle-3D candidate_log_scores.csv files and the frozen R1_RESULT.json.
"""
import argparse
import csv
import json
import math
import statistics
from pathlib import Path


def read_csv(path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def scores(path):
    return {r["candidate_id"]: float(r["log_score"]) for r in read_csv(path)}


def midrank(table, truth):
    target = table[truth]
    others = [v for k, v in table.items() if k != truth]
    return 1 + sum(v > target for v in others) + 0.5 * sum(v == target for v in others)


def rankdata(values):
    order = sorted(range(len(values)), key=lambda i: values[i])
    out = [0.0] * len(values)
    k = 0
    while k < len(order):
        m = k + 1
        while m < len(order) and values[order[m]] == values[order[k]]:
            m += 1
        avg = 0.5 * ((k + 1) + m)
        for q in range(k, m):
            out[order[q]] = avg
        k = m
    return out


def pearson(x, y):
    if len(x) < 2:
        return float("nan")
    mx, my = statistics.mean(x), statistics.mean(y)
    dx = [v - mx for v in x]
    dy = [v - my for v in y]
    den = math.sqrt(sum(v*v for v in dx) * sum(v*v for v in dy))
    return sum(a*b for a, b in zip(dx, dy)) / den if den else float("nan")


def spearman(x, y):
    return pearson(rankdata(x), rankdata(y))


def relation(v, truth):
    return "ahead" if v > truth else ("tie" if v == truth else "behind")


def safe_median(vals):
    return statistics.median(vals) if vals else None


def write_tsv(path, rows, fields):
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--science-root", type=Path, required=True,
                   help="R1 PMFS3D_R1_SCIENTIFIC_20261001 folder")
    p.add_argument("--r1-result", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()

    if a.out.exists():
        raise SystemExit("Refusing to overwrite existing R1P5 output directory")
    a.out.mkdir(parents=True)

    r1 = json.loads(a.r1_result.read_text())
    if r1["decision"] != "PMFS3D_R1_HOLD_RANK_NONINFERIORITY":
        raise SystemExit("Unexpected parent R1 decision")

    case_rows = []
    candidate_rows = []
    deltas_by_case = {}
    integrity_errors = []

    for case in r1["cases"]:
        name = case["case"]
        truth = case["truth_owner_leaf"]
        s2 = scores(a.science_root / "repeat1" / name / "oracle2d" / "candidate_log_scores.csv")
        s3 = scores(a.science_root / "repeat1" / name / "oracle3d" / "candidate_log_scores.csv")

        if set(s2) != set(s3):
            integrity_errors.append(f"{name}: candidate sets differ")
            common = sorted(set(s2) & set(s3))
        else:
            common = sorted(s2)

        if truth not in s2 or truth not in s3:
            raise SystemExit(f"{name}: truth leaf absent")

        t2, t3 = s2[truth], s3[truth]
        delta_t = t3 - t2

        r2 = midrank(s2, truth)
        r3 = midrank(s3, truth)
        if r2 != case["arms"]["oracle2d"]["truth_leaf_midrank"]:
            integrity_errors.append(f"{name}: Oracle2D rank mismatch")
        if r3 != case["arms"]["oracle3d"]["truth_leaf_midrank"]:
            integrity_errors.append(f"{name}: Oracle3D rank mismatch")

        wrong2 = [v for k, v in s2.items() if k != truth and math.isfinite(v)]
        wrong3 = [v for k, v in s3.items() if k != truth and math.isfinite(v)]
        if not wrong2 or not wrong3:
            integrity_errors.append(f"{name}: no finite wrong scores")
            continue

        margin2 = t2 - max(wrong2)
        margin3 = t3 - max(wrong3)
        dmargin = margin3 - margin2
        if abs(dmargin - case["delta_margin_3d_vs_oracle2d"]) > 1e-9:
            integrity_errors.append(f"{name}: delta-margin mismatch")

        wrong_ids = [cid for cid in common if cid != truth]
        finite_ids = [cid for cid in wrong_ids if math.isfinite(s2[cid]) and math.isfinite(s3[cid])]
        coverage = len(finite_ids) / len(wrong_ids) if wrong_ids else 0.0
        if coverage < 0.95:
            integrity_errors.append(f"{name}: finite coverage {coverage:.6f} < 0.95")
        if abs(delta_t) > 1e-12:
            integrity_errors.append(f"{name}: truth shift {delta_t:.17g} exceeds tolerance")

        advantages = []
        ahead_adv = []
        repaired = harmful = ties_added = ties_removed = 0
        delta_map = {}

        for cid in finite_ids:
            d = s3[cid] - s2[cid]
            adv = delta_t - d
            rel2 = relation(s2[cid], t2)
            rel3 = relation(s3[cid], t3)
            delta_map[cid] = d
            advantages.append(adv)
            if rel2 == "ahead":
                ahead_adv.append(adv)
            if rel2 == "ahead" and rel3 != "ahead":
                repaired += 1
            if rel2 != "ahead" and rel3 == "ahead":
                harmful += 1
            if rel2 != "tie" and rel3 == "tie":
                ties_added += 1
            if rel2 == "tie" and rel3 != "tie":
                ties_removed += 1
            candidate_rows.append({
                "case": name, "candidate_id": cid,
                "score2d": format(s2[cid], ".17g"),
                "score3d": format(s3[cid], ".17g"),
                "delta_score_3d_minus_2d": format(d, ".17g"),
                "truth_advantage_gain": format(adv, ".17g"),
                "relation2d": rel2, "relation3d": rel3,
            })

        deltas_by_case[name] = delta_map
        pos_all = sum(v > 0 for v in advantages)
        zero_all = sum(v == 0 for v in advantages)
        neg_all = sum(v < 0 for v in advantages)
        pos_ahead = sum(v > 0 for v in ahead_adv)
        frac_ahead = pos_ahead / len(ahead_adv) if ahead_adv else 0.0
        med_ahead = safe_median(ahead_adv)
        selective = bool(ahead_adv) and frac_ahead >= 0.60 and med_ahead is not None and med_ahead > 0

        best2 = max((k for k in s2 if k != truth), key=lambda k: s2[k])
        best3 = max((k for k in s3 if k != truth), key=lambda k: s3[k])

        case_rows.append({
            "case": name,
            "wrong_candidates": len(wrong_ids),
            "finite_wrong_pairs": len(finite_ids),
            "finite_coverage": coverage,
            "delta_truth": delta_t,
            "frac_A_pos_all_wrong": pos_all / len(advantages) if advantages else 0.0,
            "frac_A_zero_all_wrong": zero_all / len(advantages) if advantages else 0.0,
            "frac_A_neg_all_wrong": neg_all / len(advantages) if advantages else 0.0,
            "median_A_all_wrong": safe_median(advantages),
            "ahead2d_count": len(ahead_adv),
            "frac_A_pos_ahead2d": frac_ahead,
            "median_A_ahead2d": med_ahead,
            "selective_case": int(selective),
            "repaired_crossings": repaired,
            "harmful_crossings": harmful,
            "truth_ties_added": ties_added,
            "truth_ties_removed": ties_removed,
            "rank2d": r2, "rank3d": r3,
            "delta_margin_recomputed": dmargin,
            "best_wrong_2d": best2,
            "best_wrong_3d": best3,
        })

    by_name = {c["case"]: c for c in r1["cases"]}
    house_pairs = {
        "House01": ("House01_seed0_off_off", "House01_seed1_off_off"),
        "House02": ("House02_seed0_off_off", "House02_seed1_off_off"),
    }
    stability = {}
    for house, (c0, c1) in house_pairs.items():
        if c0 not in deltas_by_case or c1 not in deltas_by_case:
            stability[house] = {"n_common": 0, "spearman_delta": None, "valid": False}
            continue
        truth_ids = {by_name[c0]["truth_owner_leaf"], by_name[c1]["truth_owner_leaf"]}
        common = sorted((set(deltas_by_case[c0]) & set(deltas_by_case[c1])) - truth_ids)
        x = [deltas_by_case[c0][cid] for cid in common]
        y = [deltas_by_case[c1][cid] for cid in common]
        rho = spearman(x, y) if len(common) >= 2 else float("nan")
        valid = len(common) >= 50 and math.isfinite(rho)
        stability[house] = {
            "n_common": len(common),
            "spearman_delta": rho if math.isfinite(rho) else None,
            "valid": valid,
        }

    integrity_pass = len(integrity_errors) == 0 and len(case_rows) == 4
    selective_cases = sum(int(r["selective_case"]) for r in case_rows)
    broad_selectivity = selective_cases >= 3
    both_stable = all(v["valid"] and v["spearman_delta"] >= 0.50 for v in stability.values())
    partial_stability = any(v["valid"] and v["spearman_delta"] >= 0.30 for v in stability.values())

    if not integrity_pass:
        decision = "PMFS3D_R1P5_INVALID_STOP"
    elif broad_selectivity and both_stable:
        decision = "PMFS3D_R1P5_SELECTIVE_FALSE_SUPPRESSION"
    elif selective_cases >= 2 or partial_stability:
        decision = "PMFS3D_R1P5_HOLD_PARTIAL_SELECTIVITY"
    else:
        decision = "PMFS3D_R1P5_FRAGILE_TOP_COMPETITOR_SUPPRESSION_STOP"

    result = {
        "parent_decision": r1["decision"],
        "decision": decision,
        "integrity_pass": integrity_pass,
        "integrity_errors": integrity_errors,
        "selective_cases": selective_cases,
        "broad_selectivity_pass": broad_selectivity,
        "both_house_stability_pass": both_stable,
        "house_stability": stability,
        "cases": case_rows,
        "new_forward_runs": 0,
        "new_gaden_runs": 0,
        "training_runs": 0,
        "closed_loop_runs": 0,
    }

    (a.out / "R1P5_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")

    case_fields = list(case_rows[0].keys()) if case_rows else ["case"]
    write_tsv(a.out / "R1P5_CASES.tsv", case_rows, case_fields)
    cand_fields = ["case","candidate_id","score2d","score3d","delta_score_3d_minus_2d",
                   "truth_advantage_gain","relation2d","relation3d"]
    write_tsv(a.out / "R1P5_CANDIDATES.tsv", candidate_rows, cand_fields)

    lines = [
        "# PMFS3D-R1P5 decision",
        "",
        f"Decision: **{decision}**",
        "",
        f"- integrity: {integrity_pass}",
        f"- selective cases: {selective_cases}/4",
        f"- broad selectivity (>=3/4): {broad_selectivity}",
        f"- both-house stability >=0.50: {both_stable}",
        "",
        "## Cross-seed stability",
    ]
    for h, v in stability.items():
        lines.append(f"- {h}: n={v['n_common']}, Spearman={v['spearman_delta']}, valid={v['valid']}")
    lines += [
        "",
        "## Boundary",
        "This is a saved-score mechanism audit only. It does not authorize a new scorer, training, H03, confirmation, or closed loop.",
        "STOP after this decision.",
    ]
    (a.out / "R1P5_DECISION.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({"decision": decision, "selective_cases": selective_cases, "stability": stability}, sort_keys=True))


if __name__ == "__main__":
    main()
