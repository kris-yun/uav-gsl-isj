"""Read-only ABS / CENTERED / adjacent / jointly permuted stop-order audit."""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "research/ds_pmfs_identity_d1"))
sys.path.insert(0, str(REPO / "research/cd_d0_action_sensory"))
from score_shadow import bank_for_env, project, readout, sha_file  # noqa: E402
from score_cd_d0 import profile, stops  # noqa: E402

ASSET = REPO / "evidence/ds_pmfs_identity_d1/ASSET_FREEZE.json"
EVENTS = REPO / "evidence/ds_pmfs_identity_d1/COMPACT_EVENTS.json"
EXPECTED_ASSET_SHA = "c4b87c1a11571ba792bd79f1b82c9205ea17f3f32fb7e161aab42441adbd2328"
EXPECTED_EVENTS_SHA = "47b8fffb2764737ff0eb3b3f6a93bc495cfdf00c53e99bf8fa6a105128372051"


def joint_stop_permutations(n: int, ordinal: int) -> np.ndarray:
    rng = np.random.default_rng(2026092805 + ordinal)
    identity = np.arange(n)
    rows = []
    while len(rows) < 200:
        permutation = rng.permutation(n)
        if not np.array_equal(permutation, identity):
            rows.append(permutation)
    return np.asarray(rows)


def metrics(scores: np.ndarray, truth: int, observed: np.ndarray) -> dict:
    item = readout(scores, truth)
    item["margin_over_observation_energy"] = float(item["best_wrong_margin"] /
                                                     max(float(observed @ observed), 1e-9))
    return item


def aggregate(final_rows: list[dict]) -> dict:
    by_source = defaultdict(list)
    for row in final_rows:
        by_source[(row["house"], row["source_id"])].append(row)
    sources = []
    for (house, source), group in sorted(by_source.items()):
        out = dict(house=house, source_id=source, trajectories=len(group),
                   winds=sorted(set(r["wind"] for r in group)))
        for arm in ("u", "rawu"):
            a = {}
            for method in ("ABS", "CENTERED", "REAL_ADJ"):
                a[method] = {key: float(np.mean([r[arm][method][key] for r in group]))
                             for key in ("truth_rank", "unique_top1", "top3", "best_wrong_margin",
                                         "margin_over_observation_energy")}
            a["JOINT_SHUFFLED_ADJ"] = {
                "median_truth_rank": float(np.mean([
                    r[arm]["JOINT_SHUFFLED_ADJ"]["median_truth_rank"] for r in group])),
                "median_best_wrong_margin": float(np.mean([
                    r[arm]["JOINT_SHUFFLED_ADJ"]["median_best_wrong_margin"] for r in group])),
            }
            a["rank_gain_abs_to_centered"] = a["ABS"]["truth_rank"] - a["CENTERED"]["truth_rank"]
            a["rank_gain_centered_to_adj"] = a["CENTERED"]["truth_rank"] - a["REAL_ADJ"]["truth_rank"]
            a["rank_gain_joint_null_to_real_adj"] = (a["JOINT_SHUFFLED_ADJ"]["median_truth_rank"]
                                                      - a["REAL_ADJ"]["truth_rank"])
            out[arm] = a
        sources.append(out)
    houses = []
    for house in sorted(set(s["house"] for s in sources)):
        group = [s for s in sources if s["house"] == house]
        house_row = dict(house=house, physical_sources=len(group),
                         trajectories=sum(s["trajectories"] for s in group))
        for arm in ("u", "rawu"):
            a = {}
            for method in ("ABS", "CENTERED", "REAL_ADJ"):
                a[method] = {key: float(np.mean([s[arm][method][key] for s in group]))
                             for key in ("truth_rank", "unique_top1", "top3", "best_wrong_margin",
                                         "margin_over_observation_energy")}
            a["JOINT_SHUFFLED_ADJ"] = {
                "median_truth_rank": float(np.mean([
                    s[arm]["JOINT_SHUFFLED_ADJ"]["median_truth_rank"] for s in group])),
                "median_best_wrong_margin": float(np.mean([
                    s[arm]["JOINT_SHUFFLED_ADJ"]["median_best_wrong_margin"] for s in group])),
            }
            for key in ("rank_gain_abs_to_centered", "rank_gain_centered_to_adj",
                        "rank_gain_joint_null_to_real_adj"):
                values = [s[arm][key] for s in group]
                a[key] = dict(mean=float(np.mean(values)), improved=sum(v > 0 for v in values),
                              harmed=sum(v < 0 for v in values), tied=sum(v == 0 for v in values))
            house_row[arm] = a
        houses.append(house_row)
    return dict(source_rows=sources, house_rows=houses)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--inputs", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if sha_file(ASSET) != EXPECTED_ASSET_SHA or sha_file(EVENTS) != EXPECTED_EVENTS_SHA:
        raise ValueError("R0.75 pre-score input hash mismatch")
    manifest = json.loads(ASSET.read_text(encoding="utf-8"))
    event_rows = json.loads(EVENTS.read_text(encoding="utf-8"))
    by_case = {r["case_id"]: r for r in event_rows}
    episodes = [r for r in manifest["episodes"] if r["env"] < 3]
    if len(episodes) != 49 or len(by_case) != 50:
        raise ValueError("R0.75 frozen 49-case selection mismatch")
    for env in range(3):
        for name in (f"env_{env}_bank.npz", f"env_{env}_occupancy.u8"):
            if sha_file(args.inputs / name) != manifest["input_sha256"][name]:
                raise ValueError(f"frozen full-support bank changed: {name}")
    # env 0..2 use only their own Native-legal banks; House03 F1 is not an input.
    banks = {env: bank_for_env(env, args.inputs, Path(".")) for env in range(3)}
    all_updates, finals = [], []
    for ordinal, episode in enumerate(episodes, 1):
        saved = by_case[episode["case_id"]]
        meta, ids, maps, support = banks[episode["env"]]
        if support != "Native legal":
            raise ValueError("R0.75 requires full Native legal support")
        truth = ids.index(episode["source_id"])
        for prefix in saved["prefixes"]:
            xy, y, times = stops(saved["events"], prefix)
            row = dict(case_id=episode["case_id"], house=episode["house"], wind=episode["wind"],
                       source_id=episode["source_id"], candidate_count=len(ids),
                       event_prefix=prefix, stop_count=len(y), stop_times_s=times.tolist())
            is_final = prefix == saved["prefixes"][-1]
            permutations = joint_stop_permutations(len(y), ordinal) if is_final else None
            for arm in ("u", "rawu"):
                template = project(maps[arm], meta, xy)
                centered_y = y - y.mean()
                centered_m = template - template.mean(axis=1, keepdims=True)
                adj_y, adj_m = np.diff(y), np.diff(template, axis=1)
                result = {
                    "ABS": metrics(profile(template, y), truth, y),
                    "CENTERED": metrics(profile(centered_m, centered_y), truth, centered_y),
                    "REAL_ADJ": metrics(profile(adj_m, adj_y), truth, adj_y),
                }
                if is_final:
                    null = []
                    for permutation in permutations:
                        py = np.diff(y[permutation])
                        pm = np.diff(template[:, permutation], axis=1)
                        null.append(metrics(profile(pm, py), truth, py))
                    result["JOINT_SHUFFLED_ADJ"] = {
                        "truth_ranks": [r["truth_rank"] for r in null],
                        "best_wrong_margins": [r["best_wrong_margin"] for r in null],
                        "median_truth_rank": float(np.median([r["truth_rank"] for r in null])),
                        "median_best_wrong_margin": float(np.median([
                            r["best_wrong_margin"] for r in null])),
                    }
                row[arm] = result
            all_updates.append(row)
            if is_final:
                finals.append(row)
    grouped = aggregate(finals)
    result = dict(status="R075_OPEN_RELATIVE_ACTION_ATTRIBUTION", pre_score_protocol_commit="e246493036589ae820c5275f24db1a51ce31f751",
                  input_sha256={"ASSET_FREEZE.json": EXPECTED_ASSET_SHA, "COMPACT_EVENTS.json": EXPECTED_EVENTS_SHA},
                  trajectory_count=len(finals), update_count=len(all_updates),
                  permutation_count_per_trajectory=200, final_results=finals,
                  update_results=all_updates, **grouped)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True,
                                       separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps(dict(status=result["status"], houses=grouped["house_rows"],
                          sha256=sha_file(args.output)), ensure_ascii=False))


if __name__ == "__main__":
    main()
