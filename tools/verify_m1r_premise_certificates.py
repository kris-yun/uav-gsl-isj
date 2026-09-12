"""Independent odds-form replay and primal/dual certificate verification.

Does not import either analyzer or rerun the optimizer. All inputs are local
development logs; true-source coordinates are evaluator-only labels.
"""
import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def direct_scores(rows):
    previous = 0.
    out = []
    for r in sorted(rows, key=lambda x: int(x["event_index"])):
        a = min(.9999, max(.0001, .5*math.erfc((math.log1p(float(r["threshold"]))-math.log1p(previous))/math.sqrt(2))))
        b = min(.9999, max(.0001, float(r["legacy_hit_probability"])))
        c = min(.9999, max(.0001, float(r["context_value"])))
        odds = (a/(1-a))*(b/(1-b))/(c/(1-c))
        q = min(.9999, max(.0001, odds/(1+odds)))
        out.append(math.log(q) if int(r["observed_hit"]) else math.log1p(-q))
        previous = float(r["concentration"])
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo", required=True, type=Path)
    args = p.parse_args()
    directory = args.repo / "evidence/m1r_causal_repair_20260912"
    premise_path, ceiling_path = directory / "PAIRWISE_PREMISE.json", directory / "REWEIGHTING_CEILING.json"
    premise, ceiling = (json.loads(p.read_text(encoding="utf-8")) for p in (premise_path, ceiling_path))
    assert digest(premise_path) == ceiling["premise_sha256"]
    for filename, data in (("check_m1r_pairwise_premise.py", premise), ("certify_m1r_reweighting.py", ceiling)):
        assert digest(args.repo / "tools" / filename) == data["analyzer_sha256"]
    max_difference = 0.
    aliases = 0
    count = 0
    truth = {"H01": (-.4, -2.9), "H02": (0., -1.), "H03": (-.45, 1.9)}
    for house, h in ceiling["houses"].items():
        path = args.repo / f"evidence/m1r_instrumented_20260912/{house}_seed12_M1R/context_bank/contrastive_event_attribution.csv"
        assert digest(path) == h["attribution_sha256"]
        grouped = defaultdict(lambda: defaultdict(list))
        with path.open(newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                grouped[r["source_update_id"]][r["candidate_id"]].append(r)
        for uid, u in h["updates"].items():
            r = premise["houses"][house]["updates"][uid]
            for file in r["source_region_binding"]["inputs"]:
                assert digest(Path(file["path"])) == file["sha256"]
            tid = u["source_leaf"]
            assert tid == r["source_region_binding"]["source_containing_leaf"]
            cs = grouped[uid]
            # Independently bind geometry by physical rectangle bounds, and
            # posterior region mass by cell-center coordinates (the analyzer
            # instead uses integer cell indices).
            bank = path.parent
            with (bank / "source_update_timing.csv").open(newline="", encoding="utf-8") as f:
                meta = next(x for x in csv.DictReader(f) if x["source_update_id"] == uid)
            cell, ox, oy = [float(meta[k]) for k in ("cell_size", "origin_x", "origin_y")]
            sx, sy = truth[house]
            containing = []
            for cid in cs:
                i,j,width,height = map(int, cid.split("_")[1:])
                if ox+i*cell <= sx < ox+(i+width)*cell and oy+j*cell <= sy < oy+(j+height)*cell:
                    containing.append(cid)
            assert containing == [tid]
            i,j,width,height = map(int, tid.split("_")[1:])
            with (bank / f"source_update_{int(uid):04d}/source_posterior.csv").open(newline="", encoding="utf-8") as f:
                post = list(csv.DictReader(f))
            mass = math.fsum(float(x["source_probability"]) for x in post
                             if ox+i*cell <= float(x["x"]) < ox+(i+width)*cell
                             and oy+j*cell <= float(x["y"]) < oy+(j+height)*cell)
            actual = next(x for x in post if abs(float(x["x"])-sx) <= .5*cell and abs(float(x["y"])-sy) <= .5*cell)
            binding = r["source_region_binding"]
            assert math.isclose(mass, binding["native_true_leaf_mass"], rel_tol=1e-10, abs_tol=0.)
            assert float(actual["source_probability"]) == binding["native_true_cell_mass"]
            assert math.isclose(math.fsum(float(x["source_probability"]) for x in post), 1., abs_tol=1e-8)
            positives = [x for x in cs[tid] if int(x["observed_hit"])]
            assert len(positives) == binding["positive_blocks"]
            assert sum(float(x["legacy_hit_probability"]) == 0. for x in positives) == binding["positive_blocks_with_raw_source_probability_zero"]
            ls = {cid: direct_scores(rows) for cid, rows in cs.items()}
            d = [[x-y for x,y in zip(ls[tid],ls[c])] for c in u["rival_ids"]]
            w, v = u["primal_event_weights"], u["dual_rival_weights"]
            assert len(w) == u["event_count"] and len(v) == len(d)
            assert min(w) >= 0 and min(v) >= 0
            assert abs(sum(w)-1) < 1e-9 and abs(sum(v)-1) < 1e-9
            lower = min(math.fsum(x*y for x,y in zip(row,w)) for row in d)
            upper = max(math.fsum(v[j]*d[j][i] for j in range(len(v))) for i in range(len(w)))
            max_difference = max(max_difference, abs(lower-u["maximin_margin_lower_nats_per_weight_unit"]), abs(upper-u["maximin_margin_upper_nats_per_weight_unit"]))
            assert upper-lower < 1e-7
            for rival in r["fixed_rivals"].values():
                for name, values in rival["windows"].items():
                    lo, hi = r["windows"][name]["event_index_range_half_open"]
                    margin = math.fsum(ls[tid][lo:hi])-math.fsum(ls[rival["candidate_id"]][lo:hi])
                    max_difference = max(max_difference, abs(margin-values["M2_proxy_minus_rival"]))
            for alias in u["score_aliases"]:
                a = sorted(cs[tid], key=lambda r: int(r["event_index"]))
                b = sorted(cs[alias["candidate_id"]], key=lambda r: int(r["event_index"]))
                # Exact raw source-probability equality is a stronger witness
                # than merely comparing rounded likelihood vectors.
                assert [float(r["legacy_hit_probability"]) for r in a] == [float(r["legacy_hit_probability"]) for r in b]
                aliases += 1
            count += 1
    assert max_difference < 1e-8, max_difference
    # A constructive counterexample to the old logical implication.
    # Truth improves .1 -> .2 while rival improves .2 -> .8 for a hit.
    assert math.log(.2)-math.log(.1) > 0
    assert (math.log(.2)-math.log(.8))-(math.log(.1)-math.log(.2)) < 0
    result = {"status": "PASS", "verified_updates": count, "verified_exact_raw_aliases": aliases,
              "independent_odds_replay_max_absolute_difference": max_difference,
              "optimizer_rerun": False, "primal_and_dual_feasibility": "PASS",
              "independent_physical_region_and_native_mass_binding": "PASS",
              "absolute_gain_is_not_discrimination_counterexample": "PASS",
              "premise_sha256": digest(premise_path), "ceiling_sha256": digest(ceiling_path),
              "verifier_sha256": digest(Path(__file__))}
    (directory / "VERIFICATION.json").write_bytes((json.dumps(result, indent=2)+"\n").encode("utf-8"))
    print(json.dumps(result))


if __name__ == "__main__":
    main()
