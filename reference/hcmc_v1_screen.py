#!/usr/bin/env python3
"""HCMC V1 discovery-screen reproduction on the frozen TNQC V5 R2 archive.

Usage:
  python reference/hcmc_v1_screen.py \
    /path/to/tnqc_r2_six_offline_20260921_authoritative/native

The script reads only frozen final-leaf source-hypothesis support responses,
computes hypothesis-conditioned multiscaling-conformance scores, evaluates the
native 300 s top-5% ExpectedValue endpoint, and runs destructive null controls.
"""
import csv, json, math, statistics, sys
from pathlib import Path
import numpy as np

if len(sys.argv) < 2:
    raise SystemExit(
        "usage: hcmc_v1_screen.py "
        "<.../tnqc_r2_six_offline_20260921_authoritative/native>"
    )
ROOT = Path(sys.argv[1]).resolve()

CASES = [f"House{h:02d}_seed{s}_off_off" for h in (1, 2, 3) for s in (0, 1)]
TRUTH = {
    "House01": (-0.4, -2.9),
    "House02": (0.0, -1.0),
    "House03": (-0.45, 1.9),
}
SCALES = (1, 2, 4, 8)
POWERS = (1, 2, 3, 4)
CONF_FLOOR = 1e-6
ARCHIVE_SHA256 = "81c72910b2fc912e5e0a9340d3f6b1ba20024da510ef58eb95da2ff1d8055708"


def rcsv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def average_percentile(scores, all_ids):
    good = [
        (candidate_id, value)
        for candidate_id, value in scores.items()
        if value is not None and math.isfinite(value)
    ]
    good.sort(key=lambda z: (z[1], z[0]))
    out = {candidate_id: 0.0 for candidate_id in all_ids}
    n = len(good)
    p = 0
    while p < n:
        q = p + 1
        while q < n and good[q][1] == good[p][1]:
            q += 1
        rank = ((p + q - 1) / 2) / max(1, n - 1)
        for k in range(p, q):
            out[good[k][0]] = float(rank)
        p = q
    return out


def rankdata(values):
    order = sorted(range(len(values)), key=lambda i: (values[i], i))
    ranks = [0.0] * len(values)
    p = 0
    while p < len(values):
        q = p + 1
        while q < len(values) and values[order[q]] == values[order[p]]:
            q += 1
        rank = (p + q - 1) / 2
        for k in range(p, q):
            ranks[order[k]] = rank
        p = q
    return ranks


def spearman(x, y):
    if len(x) < 3:
        return float("nan")
    rx = np.asarray(rankdata(x))
    ry = np.asarray(rankdata(y))
    if rx.std() == 0 or ry.std() == 0:
        return float("nan")
    return float(np.corrcoef(rx, ry)[0, 1])


class Candidate:
    def __init__(self, rows):
        rows = [r for r in rows if float(r["measured_confidence"]) > CONF_FLOOR]
        self.measured = np.array(
            [float(r["measured_probability"]) for r in rows], dtype=float
        )
        self.simulated = np.array(
            [float(r["simulated_hit_probability"]) for r in rows], dtype=float
        )
        self.confidence = np.array(
            [float(r["measured_confidence"]) for r in rows], dtype=float
        )
        coord = {
            (int(r["grid_i"]), int(r["grid_j"])): k
            for k, r in enumerate(rows)
        }
        self.pairs = []
        for d in SCALES:
            aa, bb = [], []
            for (i, j), k in coord.items():
                for neighbor in ((i + d, j), (i, j + d)):
                    z = coord.get(neighbor)
                    if z is not None:
                        aa.append(k)
                        bb.append(z)
            a = np.asarray(aa, dtype=int)
            b = np.asarray(bb, dtype=int)
            w = (
                np.sqrt(self.confidence[a] * self.confidence[b])
                if len(a)
                else np.array([], dtype=float)
            )
            self.pairs.append((a, b, w))

    def score(self, simulated_override=None, powers=POWERS):
        simulated = (
            self.simulated if simulated_override is None else simulated_override
        )
        measured_sf = {p: [] for p in powers}
        simulated_sf = {p: [] for p in powers}

        for a, b, weight in self.pairs:
            if len(a) == 0 or weight.sum() <= 0:
                for p in powers:
                    measured_sf[p].append(None)
                    simulated_sf[p].append(None)
                continue

            dm = np.abs(self.measured[b] - self.measured[a])
            dq = np.abs(simulated[b] - simulated[a])
            total_weight = weight.sum()
            for p in powers:
                measured_sf[p].append(
                    float(np.dot(weight, dm**p) / total_weight)
                )
                simulated_sf[p].append(
                    float(np.dot(weight, dq**p) / total_weight)
                )

        mismatch = []
        for p in powers:
            for k in range(len(SCALES) - 1):
                a = measured_sf[p][k]
                b = measured_sf[p][k + 1]
                x = simulated_sf[p][k]
                y = simulated_sf[p][k + 1]
                if (
                    a is None
                    or b is None
                    or x is None
                    or y is None
                    or min(a, b, x, y) <= 0
                ):
                    continue
                measured_zeta = math.log(b / a, 2)
                simulated_zeta = math.log(y / x, 2)
                mismatch.append(abs(measured_zeta - simulated_zeta))

        return -float(np.mean(mismatch)) if mismatch else None


class Case:
    def __init__(self, name):
        self.name = name
        self.case_dir = ROOT / name
        self.house = name[:7]
        self.truth = TRUTH[self.house]

        evaluation = json.load(
            open(self.case_dir / "tnqc_fixed_trajectory_evaluation.json")
        )
        self.evaluation = evaluation
        self.update_id = int(evaluation["selected_source_update_id"])
        self.update_dir = (
            self.case_dir
            / "context_bank"
            / f"source_update_{self.update_id:04d}"
        )
        self.final_ids = list(
            evaluation["tnqc_gate_scope_audit"]["final_leaf_candidate_ids"]
        )

        self.geometry = {}
        for row in rcsv(self.update_dir / "candidate_manifest.csv"):
            candidate_id = row["candidate_id"]
            if candidate_id in self.final_ids:
                self.geometry[candidate_id] = (
                    int(row["origin_i"]),
                    int(row["origin_j"]),
                    int(row["size_i"]),
                    int(row["size_j"]),
                )

        by_candidate = {candidate_id: [] for candidate_id in self.final_ids}
        for row in rcsv(self.update_dir / "candidate_support_alignment.csv"):
            if row["candidate_id"] in by_candidate:
                by_candidate[row["candidate_id"]].append(row)

        self.candidates = {
            candidate_id: Candidate(by_candidate[candidate_id])
            for candidate_id in self.final_ids
        }
        self.posterior_rows = rcsv(self.update_dir / "source_posterior.csv")

        timing = rcsv(
            self.case_dir / "context_bank" / "source_update_timing.csv"
        )[-1]
        self.origin_x = float(timing["origin_x"])
        self.origin_y = float(timing["origin_y"])
        self.cell_size = float(timing["cell_size"])

        self.cell_owner = []
        for row in self.posterior_rows:
            x = float(row["x"])
            y = float(row["y"])
            i = int(round((x - self.origin_x) / self.cell_size - 0.5))
            j = int(round((y - self.origin_y) / self.cell_size - 0.5))
            owners = [
                candidate_id
                for candidate_id in self.final_ids
                if self.geometry[candidate_id][0] <= i
                < self.geometry[candidate_id][0] + self.geometry[candidate_id][2]
                and self.geometry[candidate_id][1] <= j
                < self.geometry[candidate_id][1] + self.geometry[candidate_id][3]
            ]
            if len(owners) != 1:
                raise RuntimeError((name, row["cell_index"], owners))
            self.cell_owner.append(owners[0])

        self.scores = {
            candidate_id: self.candidates[candidate_id].score()
            for candidate_id in self.final_ids
        }
        self.ranks = average_percentile(self.scores, self.final_ids)

    def endpoint_from_ranks(self, ranks):
        cells = [
            (
                int(row["cell_index"]),
                float(row["x"]),
                float(row["y"]),
                ranks[owner],
            )
            for row, owner in zip(self.posterior_rows, self.cell_owner)
        ]
        total = sum(z[3] for z in cells)
        if total <= 0:
            return float("inf")
        cells = [(i, x, y, v / total) for i, x, y, v in cells]
        top_count = max(1, int(0.05 * len(cells)))
        top = sorted(cells, key=lambda z: (-z[3], z[0]))[:top_count]
        top_mass = sum(z[3] for z in top)
        x = sum(cx * p for _, cx, cy, p in top) / top_mass
        y = sum(cy * p for _, cx, cy, p in top) / top_mass
        return math.hypot(x - self.truth[0], y - self.truth[1])

    def shuffled_simulated_scores(self, rng):
        out = {}
        for candidate_id in self.final_ids:
            candidate = self.candidates[candidate_id]
            simulated = candidate.simulated.copy()
            rng.shuffle(simulated)
            out[candidate_id] = candidate.score(simulated)
        return out


cases = [Case(case_name) for case_name in CASES]
hcmc_errors = [case.endpoint_from_ranks(case.ranks) for case in cases]
native_errors = [
    float(case.evaluation["native_exported"]["pmfs_top5_error_m"])
    for case in cases
]

leaf_null = []
leaf_case_errors = [[] for _ in cases]
for seed in range(300):
    rng = np.random.default_rng(0xC0A5E000 + seed)
    errors = []
    for case_index, case in enumerate(cases):
        values = np.array([case.ranks[x] for x in case.final_ids])
        rng.shuffle(values)
        ranks = {
            candidate_id: float(value)
            for candidate_id, value in zip(case.final_ids, values)
        }
        error = case.endpoint_from_ranks(ranks)
        errors.append(error)
        leaf_case_errors[case_index].append(error)
    leaf_null.append(float(np.mean(errors)))

spatial_null = []
spatial_case_errors = [[] for _ in cases]
for seed in range(30):
    rng = np.random.default_rng(0x51A000 + seed)
    errors = []
    for case_index, case in enumerate(cases):
        scores = case.shuffled_simulated_scores(rng)
        ranks = average_percentile(scores, case.final_ids)
        error = case.endpoint_from_ranks(ranks)
        errors.append(error)
        spatial_case_errors[case_index].append(error)
    spatial_null.append(float(np.mean(errors)))

cross_seed = {}
for house in ("House01", "House02", "House03"):
    a = next(case for case in cases if case.name == house + "_seed0_off_off")
    b = next(case for case in cases if case.name == house + "_seed1_off_off")
    common = sorted(set(a.final_ids) & set(b.final_ids))
    x, y = [], []
    for candidate_id in common:
        sa = a.scores[candidate_id]
        sb = b.scores[candidate_id]
        if (
            sa is not None
            and sb is not None
            and math.isfinite(sa)
            and math.isfinite(sb)
        ):
            x.append(sa)
            y.append(sb)

    rho = spearman(x, y)
    rng = np.random.default_rng(0x5EED + int(house[-2:]))
    greater_equal = 0
    y_array = np.array(y)
    for _ in range(1000):
        permuted = y_array.copy()
        rng.shuffle(permuted)
        if spearman(x, permuted) >= rho:
            greater_equal += 1

    cross_seed[house] = {
        "common_valid_leaves": len(x),
        "spearman": rho,
        "permutation_ge_count_1000": greater_equal,
        "permutation_p_upper": (greater_equal + 1) / 1001,
    }


def summarize(values):
    ordered = sorted(values)
    return {
        "min": min(values),
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "max": max(values),
        "q05": ordered[int(0.05 * (len(ordered) - 1))],
        "q95": ordered[int(0.95 * (len(ordered) - 1))],
    }


output = {
    "contract": "HCMC_V1_REPRO_CONTROL_SCREEN",
    "data_archive_sha256": ARCHIVE_SHA256,
    "definition": {
        "powers": POWERS,
        "scales_cells": SCALES,
        "confidence_floor": CONF_FLOOR,
        "pair_weight": "sqrt(conf_i*conf_j)",
        "directions": "+x,+y cardinal",
        "score": (
            "negative mean absolute mismatch of adjacent log2 "
            "structure-function slopes"
        ),
        "leaf_density": (
            "average percentile among valid final-leaf scores; invalid=0"
        ),
        "endpoint": (
            "floor(0.05*Nfree) highest-density cells, "
            "density-weighted ExpectedValue"
        ),
    },
    "native_errors_m": native_errors,
    "hcmc_errors_m": hcmc_errors,
    "native_mean_m": statistics.mean(native_errors),
    "hcmc_mean_m": statistics.mean(hcmc_errors),
    "improved_cases": sum(
        hcmc < native for hcmc, native in zip(hcmc_errors, native_errors)
    ),
    "pooled_improvement_percent": (
        100
        * (statistics.mean(native_errors) - statistics.mean(hcmc_errors))
        / statistics.mean(native_errors)
    ),
    "random_leaf_permutation_300": {
        "overall_mean_error_distribution": summarize(leaf_null),
        "case_mean_errors": [
            statistics.mean(v) for v in leaf_case_errors
        ],
        "fraction_overall_as_good_or_better": (
            sum(v <= statistics.mean(hcmc_errors) for v in leaf_null)
            / len(leaf_null)
        ),
    },
    "simulated_field_spatial_shuffle_30": {
        "overall_mean_error_distribution": summarize(spatial_null),
        "case_mean_errors": [
            statistics.mean(v) for v in spatial_case_errors
        ],
        "fraction_overall_as_good_or_better": (
            sum(v <= statistics.mean(hcmc_errors) for v in spatial_null)
            / len(spatial_null)
        ),
    },
    "cross_seed_reproducibility": cross_seed,
}

print(json.dumps(output, indent=2))
