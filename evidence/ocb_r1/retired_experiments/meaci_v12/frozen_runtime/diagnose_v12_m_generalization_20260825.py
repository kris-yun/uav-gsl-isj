#!/usr/bin/env python3
"""Post-unblinding diagnostics; read-only and never used to tune V12-M."""
import csv
import importlib.util
import json
import math
from pathlib import Path

ROOT = Path("/home/zyc/meaci_v12_generalization_20260825_r1")
TRUTHS = {"House01": (-0.40, -2.90, 418310734),
          "House02": (0.00, -1.00, 661532441),
          "House03": (-0.45, 1.90, 538848658)}
spec = importlib.util.spec_from_file_location("evalv12", "/home/zyc/meaci_v12_m_freeze_20260825/evaluate_v12_m_generalization_20260825.py")
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

rows = []
carrier_rows = []
for house, (tx, ty, seed) in TRUTHS.items():
    for arm, mode in (("off", "off"), ("on", "rc_sd_tfei_v12")):
        run = ROOT / f"{house}_seed{seed}_{arm}_{mode}"
        for posterior in sorted((run / "context_bank").glob("source_update_*/source_posterior.csv")):
            update = int(posterior.parent.name.rsplit("_", 1)[1])
            metric = mod.posterior_metrics(posterior, tx, ty)
            rows.append({"house": house, "seed": seed, "arm": arm, "update": update,
                         "error_m": metric["pmfs_expected_value_005_error_m"],
                         "variance_m2": metric["posterior_variance_m2"],
                         "mass_within_1m": metric["mass_within_1m"],
                         "truth_cell_rank": metric["nearest_truth_cell_rank"]})
        if arm == "on":
            with (run / "tadm/v12_candidate_scores.csv").open(newline="") as stream:
                scores = list(csv.DictReader(stream))
            for update in sorted({int(x["source_update_id"]) for x in scores}):
                block = [x for x in scores if int(x["source_update_id"]) == update]
                truth = min(block, key=lambda x: math.hypot(float(x["x"])-tx, float(x["y"])-ty))
                ranked = sorted(block, key=lambda x: -float(x["posterior"]))
                truth_rank = ranked.index(truth) + 1
                best = ranked[0]
                carrier_rows.append({
                    "house": house, "seed": seed, "update": update,
                    "truth_carrier": truth["carrier_id"], "truth_rank": truth_rank,
                    "truth_posterior": float(truth["posterior"]),
                    "top_carrier": best["carrier_id"], "top_posterior": float(best["posterior"]),
                    "cumulative_log_evidence_gap_top_minus_truth":
                        float(best["cumulative_mixture_log_evidence"]) - float(truth["cumulative_mixture_log_evidence"]),
                })

for name, data in (("V12_M_UPDATE_TRAJECTORY.csv", rows),
                   ("V12_M_CARRIER_EVIDENCE_DIAGNOSTIC.csv", carrier_rows)):
    with (ROOT / name).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(data[0]))
        writer.writeheader(); writer.writerows(data)

summary = {}
for house in TRUTHS:
    h = [x for x in carrier_rows if x["house"] == house]
    summary[house] = {
        "truth_carrier_rank_by_update": [x["truth_rank"] for x in h],
        "top_minus_truth_cumulative_log_evidence_by_update":
            [x["cumulative_log_evidence_gap_top_minus_truth"] for x in h],
        "truth_carrier_posterior_by_update": [x["truth_posterior"] for x in h],
    }
(ROOT / "V12_M_POSTUNBLIND_DIAGNOSTIC.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
