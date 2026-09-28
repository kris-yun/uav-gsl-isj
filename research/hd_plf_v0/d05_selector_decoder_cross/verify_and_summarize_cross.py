"""Independently verify the supplied cross table and retain source-level effects.

This reads only the two original D0.5 files and the crossed CSV. No B2 score,
observation, or action is recomputed; archived expected ranks are reused.
"""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
ORIGINAL = ROOT / "evidence/hd_plf_v0/action_validity_d05"
OUT = ROOT / "evidence/hd_plf_v0/d05_selector_decoder_cross"
ARMS = ("LF-u", "LF-rawu")
POLICIES = (*ARMS, "uniform_actions_exact_mean", "truth_oracle_diagnostic_only")


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def sign_counts(values: list[float]) -> dict[str, int]:
    # Difference is rank(candidate) - rank(baseline): lower is better.
    return {"candidate_better": sum(v < -1e-12 for v in values),
            "tied": sum(abs(v) <= 1e-12 for v in values),
            "candidate_worse": sum(v > 1e-12 for v in values)}


def main() -> None:
    original = rows(ORIGINAL / "GOAL_COUNTERFACTUALS.csv")
    data = json.loads((ORIGINAL / "D05_RESULT.json").read_text(encoding="utf-8"))
    crossed = rows(OUT / "crossed_episode_results.csv")
    scores: dict[tuple[int, int, int, str], dict[int, float]] = defaultdict(dict)
    for r in original:
        key = (int(r["environment"]), int(r["source_index"]), int(r["target_index"]), r["arm"])
        goal = int(r["goal_cell"])
        if goal in scores[key]:
            raise ValueError("duplicate raw goal")
        scores[key][goal] = float(r["rank_after_tie_aware"])
    selected = {(e["environment"], e["source_index"], e["target_index"]):
                {arm: e[arm]["selected_cell"] for arm in ARMS} for e in data["episodes"]}
    if len(scores) != 144 or len(selected) != 72 or len(crossed) != 576:
        raise ValueError("incomplete archived axes")
    computed = {}
    for ep, actions in selected.items():
        for decoder in ARMS:
            bank = scores[(*ep, decoder)]
            if not set(actions.values()).issubset(bank):
                raise ValueError("selected goal not in archived bank")
            values = {arm: bank[actions[arm]] for arm in ARMS}
            values["uniform_actions_exact_mean"] = mean(list(bank.values()))
            values["truth_oracle_diagnostic_only"] = min(bank.values())
            for policy, value in values.items():
                computed[(*ep, decoder, policy)] = value
    observed = {}
    for r in crossed:
        key = (int(r["environment"]), int(r["source_index"]), int(r["target_index"]),
               r["decoder"], r["selector"])
        if key in observed:
            raise ValueError("duplicate crossed episode")
        observed[key] = float(r["expected_final_rank"])
    if set(observed) != set(computed):
        raise ValueError("supplied tool cross axis mismatch")
    max_diff = max(abs(observed[key] - value) for key, value in computed.items())
    if max_diff > 1e-12:
        raise ValueError(f"independent cross verification failed: {max_diff}")

    source_rows = []
    for env in range(3):
        for source in range(6):
            for decoder in ARMS:
                for policy in POLICIES:
                    vals = [computed[(env, source, rep, decoder, policy)] for rep in range(4)]
                    source_rows.append({"environment": env, "source_index": source,
                                        "decoder": decoder, "selector": policy,
                                        "realizations": len(vals), "mean_expected_rank": mean(vals)})
    with (OUT / "crossed_per_source.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(source_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(source_rows)

    contrasts = []
    for env in range(3):
        for decoder in ARMS:
            # Freeze decoder: compare where each selector sends it.
            diffs = [computed[(env, source, rep, decoder, "LF-rawu")] -
                     computed[(env, source, rep, decoder, "LF-u")]
                     for source in range(6) for rep in range(4)]
            contrasts.append({"environment": env, "fixed": "decoder", "fixed_arm": decoder,
                              "candidate": "LF-rawu selector", "baseline": "LF-u selector",
                              "mean_rank_difference": mean(diffs), **sign_counts(diffs),
                              "per_source_mean_difference": {str(source): mean(diffs[4*source:4*source+4])
                                                             for source in range(6)}})
        for policy in ARMS:
            # Freeze selected goal: compare the two decoders at that same goal.
            diffs = [computed[(env, source, rep, "LF-rawu", policy)] -
                     computed[(env, source, rep, "LF-u", policy)]
                     for source in range(6) for rep in range(4)]
            contrasts.append({"environment": env, "fixed": "selector", "fixed_arm": policy,
                              "candidate": "LF-rawu B2 decoder", "baseline": "LF-u B2 decoder",
                              "mean_rank_difference": mean(diffs), **sign_counts(diffs),
                              "per_source_mean_difference": {str(source): mean(diffs[4*source:4*source+4])
                                                             for source in range(6)}})
    output = {"status": "OPEN_READ_ONLY_SELECTOR_DECODER_ATTRIBUTION",
              "independent_cross_rows_checked": len(computed),
              "max_absolute_cross_difference": max_diff,
              "scientific_independent_unit": "physical source/target episode, not individual feasible goal",
              "oracle_online_use": False,
              "contrasts": contrasts}
    (OUT / "CROSS_INDEPENDENT_CHECK_AND_CONTRASTS.json").write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"rows_checked": len(computed), "max_diff": max_diff,
                      "contrasts": contrasts}, indent=2))


if __name__ == "__main__":
    main()
