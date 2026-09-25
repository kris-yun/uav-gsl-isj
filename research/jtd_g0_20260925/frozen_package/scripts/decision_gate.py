#!/usr/bin/env python3
"""Apply the frozen JTD-G0 decision logic to a summary JSON.
Input JSON must already contain computed metrics.
"""
import json, sys

if len(sys.argv) != 2:
    print("usage: decision_gate.py metrics_summary.json")
    sys.exit(2)
m = json.load(open(sys.argv[1], "r", encoding="utf-8"))

if not m.get("input_contract_pass", False):
    d = "JTD_G0_STOP_INPUT_CONTRACT_INVALID"
else:
    rel = float(m["relative_nll_gain"])
    p = float(m["empirical_p"])
    ci_lo = float(m["bootstrap_ci_low"])
    fold = list(map(float, m["fold_delta_nll"]))
    pos = int(m["positive_source_count"])
    loso = int(m["loso_positive_count"])
    full_rank = float(m["full_median_truth_rank"])
    null_rank = float(m["null_median_truth_rank"])
    full_top3 = float(m["full_top3"])
    null_top3 = float(m["null_median_top3"])
    go = (
        rel >= 0.05 and p <= 0.01 and ci_lo > 0
        and len(fold)==4 and all(x > 0 for x in fold)
        and pos >= 12 and loso == 18
        and full_rank <= null_rank
        and full_top3 >= null_top3 - 0.02
    )
    if go:
        d = "JTD_G0_GO_TEMPORAL_DEPENDENCE_SIGNAL"
    else:
        stop = (
            rel <= 0 or p > 0.05
            or (ci_lo <= 0 and rel < 0.02)
            or sum(x < 0 for x in fold) >= 2
            or pos < 9
            or ((full_top3 < null_top3 - 0.02) and (full_rank > null_rank))
        )
        if stop:
            d = "JTD_G0_STOP_NO_INCREMENTAL_TEMPORAL_SIGNAL"
        else:
            d = "JTD_G0_HOLD_WEAK_OR_UNSTABLE_SIGNAL"

print(d)
