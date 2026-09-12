"""Read-only development diagnostic; never an online selector or causal proof.

Reproduce V4.1 scores, then compare each source proxy WITH rivals, rather than
comparing only that proxy's likelihood across two different observation laws.
All windows and rival choices are retrospective diagnostics on frozen logs.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

EPS = 1e-4
TRUTH = {"H01": (-0.4, -2.9), "H02": (0., -1.), "H03": (-0.45, 1.9)}


def clip(p):
    return min(1 - EPS, max(EPS, p))


def logit(p):
    p = clip(p)
    return math.log(p) - math.log1p(-p)


def expit(x):
    if x >= 0:
        return 1 / (1 + math.exp(-x))
    z = math.exp(x)
    return z / (1 + z)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def event_scores(rows):
    previous = 0.
    out = {a: [] for a in ("M0", "M1", "M2")}
    for row in rows:
        p0 = clip(.5 * math.erfc((math.log1p(float(row["threshold"])) -
                                math.log1p(previous)) / math.sqrt(2)))
        z = logit(p0) + logit(float(row["legacy_hit_probability"]))
        ps = (p0, clip(expit(z)), clip(expit(z - logit(float(row["context_value"])))))
        for a, p in zip(out, ps):
            out[a].append(math.log(p) if int(row["observed_hit"]) else math.log1p(-p))
        previous = float(row["concentration"])
    return out


def summarize(values, truth_id):
    value = values[truth_id]
    ranked = sorted(values, key=lambda c: (-values[c], c))
    false = max((c for c in values if c != truth_id), key=lambda c: values[c])
    peak = values[ranked[0]]
    denom = math.fsum(math.exp(x - peak) for x in values.values())
    return {
        "proxy_rank_best": 1 + sum(x > value + 1e-9 for x in values.values()),
        "proxy_rank_worst": sum(x >= value - 1e-9 for x in values.values()),
        "candidate_count": len(values), "top_candidate": ranked[0],
        "top_false_candidate": false,
        "proxy_minus_top_false_log_margin": value - values[false],
        "equal_candidate_normalized_proxy_weight": math.exp(value - peak) / denom,
        "equal_candidate_normalized_top_weight": 1 / denom,
        "normalization_semantics": "diagnostic_equal_candidate_weights_NOT_native_posterior",
    }


def bind_region_and_native_posterior(root, house, uid, candidates, tid, truth):
    directory = root / f"{house}_seed12_M1R/context_bank"
    timing_path = directory / "source_update_timing.csv"
    posterior_path = directory / f"source_update_{uid:04d}/source_posterior.csv"
    with timing_path.open(newline="", encoding="utf-8") as f:
        meta = next(r for r in csv.DictReader(f) if int(r["source_update_id"]) == uid)
    size, ox, oy = (float(meta[k]) for k in ("cell_size", "origin_x", "origin_y"))
    ti, tj = int((truth[0] - ox) / size), int((truth[1] - oy) / size)
    width = int(meta["grid_width"])
    containing = []
    rectangles = {}
    for cid, rows in candidates.items():
        i, j, w, h = map(int, cid.split("_")[1:])
        rectangles[cid] = (i, j, w, h)
        center = (ox + (i + w//2 + .5) * size, oy + (j + h//2 + .5) * size)
        assert math.dist(center, (float(rows[0]["candidate_x"]), float(rows[0]["candidate_y"]))) < 2e-6
        if i <= ti < i+w and j <= tj < j+h:
            containing.append(cid)
    # This verifies rather than assumes that the older nearest-center label is
    # the actual source-containing leaf. If not, stop instead of relabeling.
    assert containing == [tid], (house, uid, containing, tid)
    with posterior_path.open(newline="", encoding="utf-8") as f:
        posterior = list(csv.DictReader(f))
    actual = next(r for r in posterior if int(r["cell_index"]) == ti + tj*width)
    total = math.fsum(float(r["source_probability"]) for r in posterior)
    assert math.isclose(total, 1., abs_tol=1e-8), total
    peak = max(posterior, key=lambda r: float(r["source_probability"]))
    i, j, w, h = rectangles[tid]
    region = [r for r in posterior if i <= int(r["cell_index"]) % width < i+w and j <= int(r["cell_index"]) // width < j+h]
    hit_rows = [r for r in candidates[tid] if int(r["observed_hit"])]
    return {
        "source_cell_indices": [ti, tj], "source_containing_leaf": tid,
        "nearest_center_equals_source_containing_leaf": True,
        "logged_center_geometry_check": "PASS",
        "positive_blocks": len(hit_rows),
        "positive_blocks_with_raw_source_probability_zero": sum(float(r["legacy_hit_probability"]) == 0. for r in hit_rows),
        "positive_blocks_with_raw_source_probability_at_or_below_clip": sum(float(r["legacy_hit_probability"]) <= EPS for r in hit_rows),
        "native_true_cell_mass": float(actual["source_probability"]),
        "native_true_leaf_mass": math.fsum(float(r["source_probability"]) for r in region),
        "native_map_xy": [float(peak["x"]), float(peak["y"])],
        "native_map_error_m": math.dist((float(peak["x"]), float(peak["y"])), truth),
        "native_posterior_sum": total,
        "scope": "post-update native posterior before action selection; raw probabilities are before 1e-4 clipping; correlated blocks are NOT independent trials",
        "inputs": [{"path": str(p), "sha256": sha(p)} for p in (timing_path, posterior_path)],
    }


def evaluate(root, old):
    report = {"contract": "M1R_PAIRWISE_PREMISE_V1_20260912",
              "input_scope": "existing instrumented DEVELOPMENT attribution only",
              "historical_exact_replay": False,
              "causal_effect_identified": False,
              "label_semantics": "nearest-center label verified as source-containing exported leaf; representative forward response is NOT exact physical-source response",
              "windows": "full; first_half; late_half; after_first_release; newest_tranche",
              "window_semantics": "mask factors while preserving recorded rolling persistence; current-update forward maps; NOT online counterfactual trajectories",
              "rival_semantics": "full-M1 and full-M2 best false rivals fixed within each update for early/late comparisons; outcome-selected diagnostic only",
              "inputs": [], "houses": {}}
    parity_error = 0.
    event_fields = ("event_index", "block_id", "sim_time_s", "cell_index", "observed_hit", "concentration", "threshold", "context_value")
    for house, truth in TRUTH.items():
        path = root / f"{house}_seed12_M1R/context_bank/contrastive_event_attribution.csv"
        report["inputs"].append({"path": str(path), "sha256": sha(path)})
        grouped = defaultdict(lambda: defaultdict(list))
        with path.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if int(row["member_index"]) != 0:
                    raise ValueError("this gate is defined for the single-member M1R logs")
                if row["observation_operator"] != "hit_map_probability" or int(row["context_centered_log_odds"]) != 0:
                    raise ValueError("wrong observation law")
                grouped[int(row["source_update_id"])][row["candidate_id"]].append(row)
        updates = {}
        previous_count = 0
        first_count = None
        for uid, candidates in sorted(grouped.items()):
            for rows in candidates.values():
                rows.sort(key=lambda r: int(r["event_index"]))
            ref = next(iter(candidates.values()))
            n = len(ref)
            assert [int(r["event_index"]) for r in ref] == list(range(n))
            for rows in candidates.values():
                assert [[r[k] for k in event_fields] for r in rows] == [[r[k] for k in event_fields] for r in ref], "candidate histories/context differ"
            first_count = first_count or n
            coords = {c: (float(rs[0]["candidate_x"]), float(rs[0]["candidate_y"])) for c, rs in candidates.items()}
            tid = min(coords, key=lambda c: math.dist(coords[c], truth))
            scores = {c: event_scores(rs) for c, rs in candidates.items()}
            full = {a: {c: math.fsum(s[a]) for c, s in scores.items()} for a in ("M0", "M1", "M2")}
            prior = old["houses"][house]["updates"][str(uid)]
            assert tid == prior["true_candidate_id"]
            for a in full:
                parity_error = max(parity_error, abs(full[a][tid] - prior["arms"][a]["log_likelihood"]))
            windows = {"full": (0, n), "first_half": (0, n//2), "late_half": (n//2, n),
                       "after_first_release": (first_count, n), "newest_tranche": (previous_count, n)}
            wresults = {}
            for name, (lo, hi) in windows.items():
                if hi <= lo:
                    continue
                wresults[name] = {"event_index_range_half_open": [lo, hi], "arms": {}}
                for a in full:
                    vals = {c: math.fsum(s[a][lo:hi]) for c, s in scores.items()}
                    wresults[name]["arms"][a] = summarize(vals, tid)
            rivals = {}
            for chosen in ("M1", "M2"):
                rid = max((c for c in full[chosen] if c != tid), key=full[chosen].get)
                rivals[chosen + "_best_false"] = {"candidate_id": rid, "xy": coords[rid], "windows": {}}
                for name, (lo, hi) in windows.items():
                    if hi <= lo:
                        continue
                    diff = {a: math.fsum(scores[tid][a][lo:hi]) - math.fsum(scores[rid][a][lo:hi]) for a in ("M1", "M2")}
                    dtrue = math.fsum(scores[tid]["M2"][lo:hi]) - math.fsum(scores[tid]["M1"][lo:hi])
                    dfalse = math.fsum(scores[rid]["M2"][lo:hi]) - math.fsum(scores[rid]["M1"][lo:hi])
                    assert math.isclose(diff["M2"] - diff["M1"], dtrue-dfalse, abs_tol=1e-9)
                    rivals[chosen + "_best_false"]["windows"][name] = {
                        "M1_proxy_minus_rival": diff["M1"], "M2_proxy_minus_rival": diff["M2"],
                        "M2_minus_M1_at_proxy": dtrue, "M2_minus_M1_at_rival": dfalse,
                        "contrast_change_in_pairwise_margin": diff["M2"] - diff["M1"]}
            updates[str(uid)] = {"nearest_center_proxy_id": tid, "proxy_xy": coords[tid],
                                 "proxy_distance_m": math.dist(coords[tid], truth),
                                 "source_region_binding": bind_region_and_native_posterior(root, house, uid, candidates, tid, truth),
                                 "windows": wresults, "fixed_rivals": rivals}
            previous_count = n
        report["houses"][house] = {"updates": updates}
    assert parity_error < 1e-8, parity_error
    report["verification"] = {"old_score_max_absolute_error": parity_error,
                              "candidate_history_and_context_parity": "PASS",
                              "pairwise_difference_identity": "PASS",
                              "source_containing_leaf_geometry": "PASS"}
    return report


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    oldpath = args.repo / "evidence/m1r_mechanism/M1R_INSTRUMENTED_THREE_ARM_RESULT.json"
    report = evaluate(args.repo / "evidence/m1r_instrumented_20260912", json.loads(oldpath.read_text(encoding="utf-8")))
    report["reference_report_sha256"] = sha(oldpath)
    report["analyzer_sha256"] = sha(Path(__file__))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes((json.dumps(report, indent=2) + "\n").encode("utf-8"))
    print(json.dumps(report["verification"]))
    for h, house in report["houses"].items():
        for uid, u in house["updates"].items():
            r = u["fixed_rivals"]["M2_best_false"]["windows"]
            print(h, uid, "M2 pairwise full/late/newest", *[round(r[w]["M2_proxy_minus_rival"], 3) for w in ("full", "late_half", "newest_tranche")],
                  "delta pairwise late", round(r["late_half"]["contrast_change_in_pairwise_margin"], 3))


if __name__ == "__main__":
    main()
