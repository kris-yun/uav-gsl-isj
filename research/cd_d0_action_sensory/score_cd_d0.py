"""Existing Native stop transitions: actual versus broken action-sensory pairing."""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ds_pmfs_identity_d1"))
from score_shadow import bank_for_env, project, readout, sha_file  # noqa: E402


REPO = Path(__file__).resolve().parents[2]
MANIFEST = REPO / "evidence/ds_pmfs_identity_d1/ASSET_FREEZE.json"
COMPACT = REPO / "evidence/ds_pmfs_identity_d1/COMPACT_EVENTS.json"


def profile(pred: np.ndarray, y: np.ndarray) -> np.ndarray:
    dot = pred @ y
    norm = np.einsum("ij,ij->i", pred, pred)
    gain = np.divide(dot, norm, out=np.zeros_like(dot), where=norm > 0)
    gain = np.maximum(0., gain)
    return np.sum((y[None, :] - gain[:, None] * pred) ** 2, axis=1)


def stops(events: list[dict], prefix: int):
    if prefix % 5 or prefix > len(events):
        raise ValueError("not a complete Native stop prefix")
    positions, gas, times = [], [], []
    for start in range(0, prefix, 5):
        block = events[start:start + 5]
        xys = np.asarray([[v["x"], v["y"]] for v in block], dtype=np.float64)
        if not np.allclose(xys, xys[0], atol=1e-9, rtol=0):
            raise ValueError("robot moved within completed stop")
        positions.append(xys[0])
        gas.append(float(np.mean([v["concentration"] for v in block])))
        times.append(float(block[-1]["sim_time_end"]))
    xy = np.asarray(positions)
    if np.count_nonzero(np.linalg.norm(np.diff(xy, axis=0), axis=1) > 1e-6) < 2:
        raise ValueError("no usable action sequence")
    return xy, np.asarray(gas), np.asarray(times)


def permutation_indices(n: int, ordinal: int) -> np.ndarray:
    rng = np.random.default_rng(2026092805 + ordinal)
    original = np.arange(n)
    result = []
    while len(result) < 200:
        permutation = rng.permutation(n)
        if not np.array_equal(permutation, original):
            result.append(permutation)
    return np.asarray(result)


def aggregate(final: list[dict]) -> dict:
    per_source = defaultdict(list)
    for row in final:
        per_source[(row["house"], row["source_id"])].append(row)
    source_rows = []
    for (house, source), group in sorted(per_source.items()):
        r = dict(house=house, source_id=source, trajectory_count=len(group))
        for arm in ("u", "rawu"):
            r[arm] = {name: float(np.mean([v[arm][name] for v in group]))
                      for name in ("real_rank", "permutation_median_rank", "absolute_b2_rank",
                                   "real_margin", "permutation_median_margin", "real_top1", "absolute_b2_top1")}
        source_rows.append(r)
    houses = []
    for house in sorted(set(row["house"] for row in source_rows)):
        group = [row for row in source_rows if row["house"] == house]
        h = dict(house=house, physical_source_units=len(group), trajectory_count=sum(v["trajectory_count"] for v in group))
        for arm in ("u", "rawu"):
            h[arm] = {name: float(np.mean([v[arm][name] for v in group]))
                      for name in ("real_rank", "permutation_median_rank", "absolute_b2_rank",
                                   "real_margin", "permutation_median_margin", "real_top1", "absolute_b2_top1")}
            h[arm]["sources_real_rank_better_than_null_median"] = sum(
                v[arm]["real_rank"] < v[arm]["permutation_median_rank"] for v in group)
            h[arm]["sources_real_rank_worse_than_null_median"] = sum(
                v[arm]["real_rank"] > v[arm]["permutation_median_rank"] for v in group)
        houses.append(h)
    return dict(source_rows=source_rows, house_rows=houses)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--inputs", type=Path, required=True)
    p.add_argument("--f1", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    compact = json.loads(COMPACT.read_text(encoding="utf-8"))
    by_case = {v["case_id"]: v for v in compact}
    selected = [v for v in manifest["episodes"] if v["env"] < 3]
    if len(selected) != 49 or len(by_case) != 50:
        raise ValueError("frozen H01/H02 Native case selection changed")
    banks = {e: bank_for_env(e, args.inputs, args.f1) for e in range(3)}
    final, prefixes = [], []
    for ordinal, ep in enumerate(selected, 1):
        c = by_case[ep["case_id"]]
        meta, ids, maps, _ = banks[ep["env"]]
        truth = ids.index(ep["source_id"])
        for prefix in c["prefixes"]:
            xy, gas, times = stops(c["events"], prefix)
            n = len(xy) - 1
            perm = permutation_indices(n, ordinal) if prefix == c["prefixes"][-1] else None
            row = dict(case_id=ep["case_id"], house=ep["house"], wind=ep["wind"],
                       source_id=ep["source_id"], prefix=prefix, stop_count=len(xy),
                       transition_count=n, movement_m=np.linalg.norm(np.diff(xy, axis=0), axis=1).tolist(),
                       time_s=times.tolist())
            for arm in ("u", "rawu"):
                pred = project(maps[arm], meta, xy)
                dm, dy = np.diff(pred, axis=1), np.diff(gas)
                actual = readout(profile(dm, dy), truth)
                absolute = readout(profile(pred, gas), truth)
                arm_result = dict(real_rank=actual["truth_rank"], real_top1=actual["unique_top1"],
                                  real_top3=actual["top3"], real_margin=actual["best_wrong_margin"],
                                  absolute_b2_rank=absolute["truth_rank"],
                                  absolute_b2_top1=absolute["unique_top1"],
                                  absolute_b2_margin=absolute["best_wrong_margin"])
                if perm is not None:
                    null = [readout(profile(dm[:, idx], dy), truth) for idx in perm]
                    ranks = np.asarray([v["truth_rank"] for v in null])
                    margins = np.asarray([v["best_wrong_margin"] for v in null])
                    arm_result.update(permutation_ranks=ranks.tolist(),
                                      permutation_margins=margins.tolist(),
                                      permutation_median_rank=float(np.median(ranks)),
                                      permutation_median_margin=float(np.median(margins)),
                                      permutation_fraction_rank_at_least_as_good_as_real=float(np.mean(ranks <= actual["truth_rank"])))
                row[arm] = arm_result
            prefixes.append(row)
            if perm is not None:
                final.append(row)
    summary = aggregate(final)
    output = dict(status="CD_D0_OPEN_ACTION_ALIGNMENT_DIAGNOSTIC", no_scientific_pass_gate=True,
                  manifest_sha256=sha_file(MANIFEST), compact_events_sha256=sha_file(COMPACT),
                  trajectory_count=len(final), update_count=len(prefixes),
                  permutation_count_per_trajectory=200, final_results=final,
                  update_results=prefixes, **summary)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"status": output["status"], "houses": summary["house_rows"],
                      "sha256": sha_file(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
