"""Summarize episode-level D0.5 results without pooling goals as samples."""

import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
data = json.loads((ROOT / "evidence/hd_plf_v0/action_validity_d05/D05_RESULT.json").read_text())
episodes = data["episodes"]
out = {}
for env in range(3):
    sub = [e for e in episodes if e["environment"] == env]
    paired = [e for e in sub if all(e[a]["rho_action_rank_gain"] is not None
                                    for a in ("LF-u", "LF-rawu"))]
    differences = [e["LF-rawu"]["rho_action_rank_gain"] - e["LF-u"]["rho_action_rank_gain"]
                   for e in paired]
    paired_margin = [e for e in sub if all(e[a]["rho_action_margin_gain"] is not None
                                           for a in ("LF-u", "LF-rawu"))]
    margin_diff = [e["LF-rawu"]["rho_action_margin_gain"] - e["LF-u"]["rho_action_margin_gain"]
                   for e in paired_margin]
    out[str(env)] = {
        "paired_defined_rank_episodes": len(paired),
        "median_paired_rawu_minus_u_rank_rho": float(np.median(differences)) if differences else None,
        "rawu_rank_rho_greater_count": int(sum(d > 0 for d in differences)),
        "paired_defined_margin_episodes": len(paired_margin),
        "median_paired_rawu_minus_u_margin_rho": float(np.median(margin_diff)),
        "rawu_margin_rho_greater_count": int(sum(d > 0 for d in margin_diff)),
        "different_selected_goals": int(sum(e["LF-u"]["selected_cell"] != e["LF-rawu"]["selected_cell"] for e in sub)),
        "positive_selected_minus_median_rank_gain": {
            arm: int(sum(e[arm]["selected_minus_median_rank_gain"] > 0 for e in sub))
            for arm in ("LF-u", "LF-rawu")
        },
        "per_source_paired_rank_rho_median_difference": {
            str(source): (float(np.median(vals)) if vals else None)
            for source in range(6)
            for vals in [[e["LF-rawu"]["rho_action_rank_gain"] - e["LF-u"]["rho_action_rank_gain"]
                          for e in paired if e["source_index"] == source]]
        },
    }
print(json.dumps(out, indent=2))
