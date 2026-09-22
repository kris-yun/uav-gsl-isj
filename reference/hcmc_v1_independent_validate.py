#!/usr/bin/env python3
"""Frozen HCMC V1 source-blind generation and linked-native evaluation.

The command has two deliberately separate phases:

``generate`` never accepts a truth file and never opens the historical
``tnqc_fixed_trajectory_evaluation.json`` or terminal launch log.  It derives
the authoritative final-leaf partition from the final candidate geometry,
freezes the HCMC/native posteriors and destructive-control assignments, and
writes a SHA-256 manifest.

``evaluate`` first verifies that manifest, then reads a separate truth sidecar
and calls the linked-native C++ ``GSL::Utils::ExpectedValue(grid, 0.05)``
evaluator for both native and HCMC posteriors.  Truth-dependent diagnostics
and the predeclared PASS/HOLD/NO-GO gate exist only in this phase.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import statistics
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np


CONTRACT = "HCMC_V1_INDEPENDENT_VALIDATION_V1"
POWERS = (1, 2, 3, 4)
SCALES = (1, 2, 4, 8)
CONFIDENCE_FLOOR = 1e-6
LEAF_NULL_REPETITIONS = 300
SPATIAL_NULL_REPETITIONS = 30
ENDPOINT_PARITY_TOLERANCE_M = 0.011
NON_WORSE_NUMERICAL_TOLERANCE_M = 1e-9
EXPECTED_TRACE_ROWS = 1500


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> List[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def write_csv(path: Path, fieldnames: Sequence[str], rows: Iterable[Mapping]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def average_percentile(
    scores: Mapping[str, Optional[float]], all_ids: Sequence[str]
) -> Dict[str, float]:
    good = [
        (candidate_id, value)
        for candidate_id, value in scores.items()
        if value is not None and math.isfinite(value)
    ]
    good.sort(key=lambda item: (item[1], item[0]))
    output = {candidate_id: 0.0 for candidate_id in all_ids}
    count = len(good)
    start = 0
    while start < count:
        stop = start + 1
        while stop < count and good[stop][1] == good[start][1]:
            stop += 1
        percentile = ((start + stop - 1) / 2) / max(1, count - 1)
        for index in range(start, stop):
            output[good[index][0]] = float(percentile)
        start = stop
    return output


@dataclass(frozen=True)
class GridMetadata:
    width: int
    height: int
    cell_size: float
    origin_x: float
    origin_y: float


@dataclass(frozen=True)
class Cell:
    cell_index: int
    grid_i: int
    grid_j: int
    x: float
    y: float
    native_probability: float


@dataclass(frozen=True)
class Geometry:
    origin_i: int
    origin_j: int
    size_i: int
    size_j: int

    @property
    def area(self) -> int:
        return self.size_i * self.size_j

    def contains_grid(self, grid_i: int, grid_j: int) -> bool:
        return (
            self.origin_i <= grid_i < self.origin_i + self.size_i
            and self.origin_j <= grid_j < self.origin_j + self.size_j
        )

    def strictly_contains(self, other: "Geometry") -> bool:
        return (
            self.area > other.area
            and self.origin_i <= other.origin_i
            and self.origin_j <= other.origin_j
            and self.origin_i + self.size_i >= other.origin_i + other.size_i
            and self.origin_j + self.size_j >= other.origin_j + other.size_j
        )


class Candidate:
    def __init__(self, rows: Sequence[dict]):
        filtered = [
            row
            for row in rows
            if float(row["measured_confidence"]) > CONFIDENCE_FLOOR
        ]
        self.measured = np.asarray(
            [float(row["measured_probability"]) for row in filtered], dtype=float
        )
        self.simulated = np.asarray(
            [float(row["simulated_hit_probability"]) for row in filtered],
            dtype=float,
        )
        self.confidence = np.asarray(
            [float(row["measured_confidence"]) for row in filtered], dtype=float
        )
        coordinates = {
            (int(row["grid_i"]), int(row["grid_j"])): index
            for index, row in enumerate(filtered)
        }
        self.pairs: List[Tuple[np.ndarray, np.ndarray, np.ndarray]] = []
        for separation in SCALES:
            left: List[int] = []
            right: List[int] = []
            for (grid_i, grid_j), index in coordinates.items():
                for neighbor in (
                    (grid_i + separation, grid_j),
                    (grid_i, grid_j + separation),
                ):
                    neighbor_index = coordinates.get(neighbor)
                    if neighbor_index is not None:
                        left.append(index)
                        right.append(neighbor_index)
            a = np.asarray(left, dtype=int)
            b = np.asarray(right, dtype=int)
            weights = (
                np.sqrt(self.confidence[a] * self.confidence[b])
                if len(a)
                else np.asarray([], dtype=float)
            )
            self.pairs.append((a, b, weights))

    def score(
        self, simulated_override: Optional[np.ndarray] = None
    ) -> Tuple[Optional[float], dict]:
        simulated = self.simulated if simulated_override is None else simulated_override
        measured_sf = {power: [] for power in POWERS}
        simulated_sf = {power: [] for power in POWERS}
        pair_counts = []

        for a, b, weights in self.pairs:
            pair_counts.append(int(len(a)))
            if len(a) == 0 or float(weights.sum()) <= 0.0:
                for power in POWERS:
                    measured_sf[power].append(None)
                    simulated_sf[power].append(None)
                continue
            measured_increment = np.abs(self.measured[b] - self.measured[a])
            simulated_increment = np.abs(simulated[b] - simulated[a])
            total_weight = float(weights.sum())
            for power in POWERS:
                measured_sf[power].append(
                    float(np.dot(weights, measured_increment**power) / total_weight)
                )
                simulated_sf[power].append(
                    float(np.dot(weights, simulated_increment**power) / total_weight)
                )

        mismatches: List[float] = []
        for power in POWERS:
            for scale_index in range(len(SCALES) - 1):
                measured_a = measured_sf[power][scale_index]
                measured_b = measured_sf[power][scale_index + 1]
                simulated_a = simulated_sf[power][scale_index]
                simulated_b = simulated_sf[power][scale_index + 1]
                values = (measured_a, measured_b, simulated_a, simulated_b)
                if any(value is None for value in values):
                    continue
                if min(float(value) for value in values) <= 0.0:
                    continue
                measured_slope = math.log(float(measured_b) / float(measured_a), 2)
                simulated_slope = math.log(
                    float(simulated_b) / float(simulated_a), 2
                )
                mismatches.append(abs(measured_slope - simulated_slope))

        score = -float(np.mean(mismatches)) if mismatches else None
        diagnostics = {
            "support_rows_above_confidence_floor": int(len(self.measured)),
            "pair_counts_by_scale": dict(zip(map(str, SCALES), pair_counts)),
            "valid_slope_comparisons": len(mismatches),
        }
        return score, diagnostics


def select_final_update(bank_dir: Path, budget_s: float) -> Tuple[int, float, dict]:
    rows = read_csv(bank_dir / "source_update_timing.csv")
    eligible = [
        row
        for row in rows
        if float(row["sim_time"]) <= budget_s + 1e-9
    ]
    if not eligible:
        raise ValueError(f"no source update at or before {budget_s} s: {bank_dir}")
    selected = max(
        eligible,
        key=lambda row: (float(row["sim_time"]), int(row["source_update_id"])),
    )
    return int(selected["source_update_id"]), float(selected["sim_time"]), selected


def grid_metadata(timing_row: Mapping[str, str]) -> GridMetadata:
    metadata = GridMetadata(
        width=int(timing_row["grid_width"]),
        height=int(timing_row["grid_height"]),
        cell_size=float(timing_row["cell_size"]),
        origin_x=float(timing_row["origin_x"]),
        origin_y=float(timing_row["origin_y"]),
    )
    if metadata.width <= 0 or metadata.height <= 0 or metadata.cell_size <= 0:
        raise ValueError(f"invalid grid metadata: {metadata}")
    return metadata


def load_cells(update_dir: Path, metadata: GridMetadata) -> List[Cell]:
    cells = []
    seen = set()
    for row in read_csv(update_dir / "source_posterior.csv"):
        x = float(row["x"])
        y = float(row["y"])
        grid_i = int(round((x - metadata.origin_x) / metadata.cell_size - 0.5))
        grid_j = int(round((y - metadata.origin_y) / metadata.cell_size - 0.5))
        cell_index = int(row["cell_index"])
        if not (0 <= grid_i < metadata.width and 0 <= grid_j < metadata.height):
            raise ValueError(f"posterior cell outside grid: {row}")
        if (grid_i, grid_j) in seen:
            raise ValueError(f"duplicate posterior grid coordinate: {(grid_i, grid_j)}")
        seen.add((grid_i, grid_j))
        cells.append(
            Cell(
                cell_index=cell_index,
                grid_i=grid_i,
                grid_j=grid_j,
                x=x,
                y=y,
                native_probability=float(row["source_probability"]),
            )
        )
    if not cells:
        raise ValueError(f"empty posterior: {update_dir}")
    return cells


def derive_final_leaves(
    update_dir: Path, cells: Sequence[Cell]
) -> Tuple[List[str], Dict[str, Geometry], Dict[int, str]]:
    geometry: Dict[str, Geometry] = {}
    for row in read_csv(update_dir / "candidate_manifest.csv"):
        candidate_id = row["candidate_id"]
        candidate_geometry = Geometry(
            origin_i=int(row["origin_i"]),
            origin_j=int(row["origin_j"]),
            size_i=int(row["size_i"]),
            size_j=int(row["size_j"]),
        )
        previous = geometry.get(candidate_id)
        if previous is not None and previous != candidate_geometry:
            raise ValueError(f"candidate geometry changed: {candidate_id}")
        geometry[candidate_id] = candidate_geometry

    final_ids = sorted(
        candidate_id
        for candidate_id, candidate_geometry in geometry.items()
        if not any(
            candidate_geometry.strictly_contains(other_geometry)
            for other_id, other_geometry in geometry.items()
            if other_id != candidate_id
        )
    )
    if not final_ids:
        raise ValueError(f"could not derive final leaves: {update_dir}")

    ownership: Dict[int, str] = {}
    for cell in cells:
        owners = [
            candidate_id
            for candidate_id in final_ids
            if geometry[candidate_id].contains_grid(cell.grid_i, cell.grid_j)
        ]
        if len(owners) != 1:
            raise ValueError(
                f"final-leaf ownership is not unique for cell {cell.cell_index}: {owners}"
            )
        ownership[cell.cell_index] = owners[0]
    return final_ids, geometry, ownership


def normalize(values: Mapping[int, float]) -> Dict[int, float]:
    clipped = {key: max(float(value), 0.0) for key, value in values.items()}
    total = sum(clipped.values())
    if not (total > 0.0 and math.isfinite(total)):
        raise ValueError("posterior has no finite positive mass")
    return {key: value / total for key, value in clipped.items()}


def posterior_from_ranks(
    cells: Sequence[Cell], ownership: Mapping[int, str], ranks: Mapping[str, float]
) -> Dict[int, float]:
    return normalize(
        {cell.cell_index: float(ranks[ownership[cell.cell_index]]) for cell in cells}
    )


def write_posterior(path: Path, cells: Sequence[Cell], posterior: Mapping[int, float]) -> None:
    ordered = sorted(cells, key=lambda cell: (cell.grid_j, cell.grid_i))
    write_csv(
        path,
        (
            "cell_index",
            "grid_i",
            "grid_j",
            "x",
            "y",
            "source_probability",
        ),
        (
            {
                "cell_index": cell.cell_index,
                "grid_i": cell.grid_i,
                "grid_j": cell.grid_j,
                "x": format(cell.x, ".17g"),
                "y": format(cell.y, ".17g"),
                "source_probability": format(
                    max(float(posterior[cell.cell_index]), 0.0), ".17g"
                ),
            }
            for cell in ordered
        ),
    )


class BlindCase:
    def __init__(self, case_dir: Path, budget_s: float):
        self.case_dir = case_dir.resolve()
        self.name = case_dir.name
        self.bank_dir = self.case_dir / "context_bank"
        self.update_id, self.update_time, timing = select_final_update(
            self.bank_dir, budget_s
        )
        self.metadata = grid_metadata(timing)
        self.update_dir = self.bank_dir / f"source_update_{self.update_id:04d}"
        self.cells = load_cells(self.update_dir, self.metadata)
        (
            self.final_ids,
            self.geometry,
            self.ownership,
        ) = derive_final_leaves(self.update_dir, self.cells)

        rows_by_candidate = {candidate_id: [] for candidate_id in self.final_ids}
        for row in read_csv(self.update_dir / "candidate_support_alignment.csv"):
            candidate_id = row["candidate_id"]
            if candidate_id in rows_by_candidate:
                rows_by_candidate[candidate_id].append(row)
        self.candidates = {
            candidate_id: Candidate(rows_by_candidate[candidate_id])
            for candidate_id in self.final_ids
        }
        score_results = {
            candidate_id: self.candidates[candidate_id].score()
            for candidate_id in self.final_ids
        }
        self.scores = {
            candidate_id: result[0] for candidate_id, result in score_results.items()
        }
        self.diagnostics = {
            candidate_id: result[1] for candidate_id, result in score_results.items()
        }
        self.ranks = average_percentile(self.scores, self.final_ids)
        self.native = normalize(
            {cell.cell_index: cell.native_probability for cell in self.cells}
        )
        self.hcmc = posterior_from_ranks(self.cells, self.ownership, self.ranks)

    def shuffled_ranks(self, rng: np.random.Generator) -> Dict[str, float]:
        scores = {}
        for candidate_id in self.final_ids:
            candidate = self.candidates[candidate_id]
            shuffled = candidate.simulated.copy()
            rng.shuffle(shuffled)
            scores[candidate_id] = candidate.score(shuffled)[0]
        return average_percentile(scores, self.final_ids)


def discover_case_dirs(native_root: Path, requested: Sequence[str]) -> List[Path]:
    if requested:
        paths = [native_root / name for name in requested]
    else:
        paths = sorted(
            path
            for path in native_root.iterdir()
            if path.is_dir() and (path / "context_bank").is_dir()
        )
    missing = [str(path) for path in paths if not (path / "context_bank").is_dir()]
    if missing:
        raise FileNotFoundError(f"missing case context banks: {missing}")
    if not paths:
        raise ValueError(f"no cases found under {native_root}")
    return paths


def input_hashes(case: BlindCase) -> Dict[str, str]:
    paths = {
        "source_update_timing.csv": case.bank_dir / "source_update_timing.csv",
        "candidate_manifest.csv": case.update_dir / "candidate_manifest.csv",
        "candidate_support_alignment.csv": case.update_dir
        / "candidate_support_alignment.csv",
        "source_posterior.csv": case.update_dir / "source_posterior.csv",
    }
    for optional in (
        "sensor_trace.csv",
        "sim_pose_trace.csv",
        "wind_trace.csv",
        "runtime_manifest.json",
        "run_status.json",
    ):
        path = case.case_dir / optional
        if path.is_file():
            paths[optional] = path
    return {name: sha256_file(path) for name, path in sorted(paths.items())}


def generate(args: argparse.Namespace) -> None:
    native_root = args.native_root.resolve()
    output_root = args.output_root.resolve()
    if output_root.exists() and any(output_root.iterdir()):
        raise FileExistsError(f"refusing non-empty pre-truth output: {output_root}")
    output_root.mkdir(parents=True, exist_ok=True)

    cases = [
        BlindCase(path, args.budget_s)
        for path in discover_case_dirs(native_root, args.case)
    ]
    cases.sort(key=lambda case: case.name)

    leaf_controls: Dict[str, List[dict]] = {case.name: [] for case in cases}
    for repetition in range(LEAF_NULL_REPETITIONS):
        rng = np.random.default_rng(0xC0A5E000 + repetition)
        for case in cases:
            values = np.asarray([case.ranks[item] for item in case.final_ids])
            rng.shuffle(values)
            leaf_controls[case.name].append(
                {
                    "repetition": repetition,
                    "ranks": {
                        candidate_id: float(value)
                        for candidate_id, value in zip(case.final_ids, values)
                    },
                }
            )

    spatial_controls: Dict[str, List[dict]] = {case.name: [] for case in cases}
    for repetition in range(SPATIAL_NULL_REPETITIONS):
        rng = np.random.default_rng(0x51A000 + repetition)
        for case in cases:
            spatial_controls[case.name].append(
                {
                    "repetition": repetition,
                    "ranks": case.shuffled_ranks(rng),
                }
            )

    generated_paths: List[Path] = []
    case_entries = []
    for case in cases:
        case_output = output_root / case.name
        case_output.mkdir(parents=True, exist_ok=False)
        score_path = case_output / "candidate_scores.csv"
        rank_path = case_output / "candidate_ranks.csv"
        native_path = case_output / "native_posterior.csv"
        hcmc_path = case_output / "hcmc_posterior.csv"
        controls_path = case_output / "null_control_ranks.json"
        manifest_path = case_output / "source_blind_case_manifest.json"

        write_csv(
            score_path,
            (
                "candidate_id",
                "hcmc_score",
                "valid_slope_comparisons",
                "support_rows_above_confidence_floor",
                "pairs_scale_1",
                "pairs_scale_2",
                "pairs_scale_4",
                "pairs_scale_8",
            ),
            (
                {
                    "candidate_id": candidate_id,
                    "hcmc_score": (
                        ""
                        if case.scores[candidate_id] is None
                        else format(float(case.scores[candidate_id]), ".17g")
                    ),
                    "valid_slope_comparisons": case.diagnostics[candidate_id][
                        "valid_slope_comparisons"
                    ],
                    "support_rows_above_confidence_floor": case.diagnostics[
                        candidate_id
                    ]["support_rows_above_confidence_floor"],
                    **{
                        f"pairs_scale_{scale}": case.diagnostics[candidate_id][
                            "pair_counts_by_scale"
                        ][str(scale)]
                        for scale in SCALES
                    },
                }
                for candidate_id in case.final_ids
            ),
        )
        ordered = sorted(
            case.final_ids, key=lambda item: (-case.ranks[item], item)
        )
        write_csv(
            rank_path,
            ("candidate_id", "average_percentile_rank", "ordinal_rank_best_is_1"),
            (
                {
                    "candidate_id": candidate_id,
                    "average_percentile_rank": format(case.ranks[candidate_id], ".17g"),
                    "ordinal_rank_best_is_1": index + 1,
                }
                for index, candidate_id in enumerate(ordered)
            ),
        )
        write_posterior(native_path, case.cells, case.native)
        write_posterior(hcmc_path, case.cells, case.hcmc)
        write_json(
            controls_path,
            {
                "contract": CONTRACT,
                "random_leaf_permutation": leaf_controls[case.name],
                "simulated_field_spatial_shuffle": spatial_controls[case.name],
            },
        )
        write_json(
            manifest_path,
            {
                "contract": CONTRACT,
                "phase": "PRE_TRUTH_SOURCE_BLIND",
                "truth_inputs_loaded": False,
                "historical_truth_bearing_evaluation_opened": False,
                "case_name": case.name,
                "case_dir": str(case.case_dir),
                "selected_source_update_id": case.update_id,
                "selected_source_update_sim_time": case.update_time,
                "grid": case.metadata.__dict__,
                "free_cell_count": len(case.cells),
                "final_leaf_candidate_count": len(case.final_ids),
                "final_leaf_candidate_ids": case.final_ids,
                "final_leaf_derivation": (
                    "candidate geometries with no strict descendant; unique free-cell coverage"
                ),
                "input_sha256": input_hashes(case),
                "definition": {
                    "powers": POWERS,
                    "scales_cells": SCALES,
                    "directions": "+x,+y",
                    "confidence_floor": CONFIDENCE_FLOOR,
                    "pair_weight": "sqrt(conf_i*conf_j)",
                    "score": "negative mean absolute adjacent-log2-slope mismatch",
                    "rank": "average percentile; invalid candidate density zero",
                },
            },
        )
        case_files = (
            score_path,
            rank_path,
            native_path,
            hcmc_path,
            controls_path,
            manifest_path,
        )
        generated_paths.extend(case_files)
        case_entries.append(
            {
                "case_name": case.name,
                "case_dir": str(case.case_dir),
                "files": [str(path.relative_to(output_root)) for path in case_files],
            }
        )

    code_path = Path(__file__).resolve()
    freeze = {
        "contract": CONTRACT,
        "phase": "PRE_TRUTH_FREEZE",
        "truth_inputs_loaded": False,
        "native_root": str(native_root),
        "budget_s": args.budget_s,
        "cases": case_entries,
        "hcmc_code": str(code_path),
        "hcmc_code_sha256": sha256_file(code_path),
        "generated_file_sha256": {
            str(path.relative_to(output_root)): sha256_file(path)
            for path in sorted(generated_paths)
        },
        "null_controls": {
            "random_leaf_permutation_repetitions": LEAF_NULL_REPETITIONS,
            "random_leaf_seed": "0xC0A5E000 + repetition; continuous across sorted cases",
            "spatial_shuffle_repetitions": SPATIAL_NULL_REPETITIONS,
            "spatial_shuffle_seed": "0x51A000 + repetition; continuous across sorted cases",
        },
    }
    write_json(output_root / "PRE_TRUTH_FREEZE.json", freeze)
    print(json.dumps(freeze, indent=2, sort_keys=True))


def verify_freeze(pretruth_root: Path) -> dict:
    freeze_path = pretruth_root / "PRE_TRUTH_FREEZE.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    if freeze.get("contract") != CONTRACT or freeze.get("phase") != "PRE_TRUTH_FREEZE":
        raise ValueError(f"wrong pre-truth contract: {freeze_path}")
    failures = []
    for relative, expected in freeze["generated_file_sha256"].items():
        path = pretruth_root / relative
        actual = sha256_file(path) if path.is_file() else "MISSING"
        if actual != expected:
            failures.append({"path": relative, "expected": expected, "actual": actual})
    if failures:
        raise ValueError(f"PRE_TRUTH_FREEZE hash mismatch: {failures}")
    return freeze


def read_posterior(path: Path) -> Tuple[List[Cell], Dict[int, float]]:
    cells = []
    posterior = {}
    for row in read_csv(path):
        cell = Cell(
            cell_index=int(row["cell_index"]),
            grid_i=int(row["grid_i"]),
            grid_j=int(row["grid_j"]),
            x=float(row["x"]),
            y=float(row["y"]),
            native_probability=float(row["source_probability"]),
        )
        cells.append(cell)
        posterior[cell.cell_index] = cell.native_probability
    return cells, normalize(posterior)


def linked_native_endpoint(
    evaluator: Path,
    posterior_path: Path,
    metadata: GridMetadata,
    truth_x: float,
    truth_y: float,
) -> dict:
    process = subprocess.run(
        [
            str(evaluator),
            str(posterior_path),
            str(metadata.width),
            str(metadata.height),
            repr(metadata.cell_size),
            repr(metadata.origin_x),
            repr(metadata.origin_y),
            repr(float(truth_x)),
            repr(float(truth_y)),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if process.returncode != 0:
        raise RuntimeError(
            f"linked-native evaluator failed rc={process.returncode}: "
            f"{process.stdout}\n{process.stderr}"
        )
    result = json.loads(process.stdout)
    if result.get("engine") != "gsl_utils_expected_value_linked_native_v1":
        raise ValueError(f"non-authoritative endpoint engine: {result}")
    return result


def posterior_diagnostics(
    cells: Sequence[Cell], posterior: Mapping[int, float], truth_x: float, truth_y: float
) -> dict:
    normalized = normalize(posterior)
    rows = [
        (cell, normalized[cell.cell_index])
        for cell in cells
    ]
    map_cell, map_probability = max(
        rows, key=lambda item: (item[1], -item[0].cell_index)
    )
    mean_x = sum(cell.x * probability for cell, probability in rows)
    mean_y = sum(cell.y * probability for cell, probability in rows)
    expected_distance = sum(
        probability * math.hypot(cell.x - truth_x, cell.y - truth_y)
        for cell, probability in rows
    )
    entropy = -sum(
        probability * math.log(probability)
        for _, probability in rows
        if probability > 0.0
    )
    variance = sum(
        probability * ((cell.x - mean_x) ** 2 + (cell.y - mean_y) ** 2)
        for cell, probability in rows
    )
    return {
        "map_x": map_cell.x,
        "map_y": map_cell.y,
        "map_probability": map_probability,
        "map_error_m": math.hypot(map_cell.x - truth_x, map_cell.y - truth_y),
        "posterior_mean_x": mean_x,
        "posterior_mean_y": mean_y,
        "full_posterior_expected_source_distance_m": expected_distance,
        "mass_within_1m": sum(
            probability
            for cell, probability in rows
            if math.hypot(cell.x - truth_x, cell.y - truth_y) <= 1.0
        ),
        "mass_within_2m": sum(
            probability
            for cell, probability in rows
            if math.hypot(cell.x - truth_x, cell.y - truth_y) <= 2.0
        ),
        "entropy_nats": entropy,
        "effective_support_cells": math.exp(entropy),
        "posterior_spatial_variance_m2": variance,
    }


def nearest_truth_candidate_diagnostic(
    case_output: Path, truth_x: float, truth_y: float
) -> dict:
    manifest = json.loads(
        (case_output / "source_blind_case_manifest.json").read_text(encoding="utf-8")
    )
    metadata = GridMetadata(**manifest["grid"])
    rank_rows = read_csv(case_output / "candidate_ranks.csv")
    ranks = {
        row["candidate_id"]: {
            "percentile": float(row["average_percentile_rank"]),
            "ordinal": int(row["ordinal_rank_best_is_1"]),
        }
        for row in rank_rows
    }
    candidate_rows = read_csv(
        Path(manifest["case_dir"])
        / "context_bank"
        / f"source_update_{int(manifest['selected_source_update_id']):04d}"
        / "candidate_manifest.csv"
    )
    final_ids = set(manifest["final_leaf_candidate_ids"])
    candidates = []
    for row in candidate_rows:
        candidate_id = row["candidate_id"]
        if candidate_id not in final_ids:
            continue
        center_x = metadata.origin_x + (
            int(row["origin_i"]) + int(row["size_i"]) / 2
        ) * metadata.cell_size
        center_y = metadata.origin_y + (
            int(row["origin_j"]) + int(row["size_j"]) / 2
        ) * metadata.cell_size
        candidates.append(
            (
                math.hypot(center_x - truth_x, center_y - truth_y),
                candidate_id,
                center_x,
                center_y,
            )
        )
    distance, candidate_id, center_x, center_y = min(candidates)
    return {
        "candidate_id": candidate_id,
        "candidate_center_x": center_x,
        "candidate_center_y": center_y,
        "candidate_center_truth_distance_m": distance,
        "hcmc_average_percentile_rank": ranks[candidate_id]["percentile"],
        "hcmc_ordinal_rank_best_is_1": ranks[candidate_id]["ordinal"],
    }


RESULT_PATTERN = re.compile(
    r"RESULT IS: Success=([^,]+), Search_t=([0-9.eE+-]+), Error=([0-9.eE+-]+)"
)


def logged_native_endpoint(case_dir: Path) -> dict:
    found = None
    for line in (case_dir / "launch.log").read_text(
        encoding="utf-8", errors="replace"
    ).splitlines():
        match = RESULT_PATTERN.search(line)
        if match:
            found = {
                "success": match.group(1).strip(),
                "search_t": float(match.group(2)),
                "reported_top5_error_m": float(match.group(3)),
            }
    if found is None:
        raise ValueError(f"missing PMFS RESULT IS line: {case_dir}")
    return found


def trace_integrity(case_dir: Path) -> dict:
    reports = {}
    all_pass = True
    for filename in ("sensor_trace.csv", "sim_pose_trace.csv", "wind_trace.csv"):
        path = case_dir / filename
        if not path.is_file():
            reports[filename] = {"pass": False, "reason": "missing"}
            all_pass = False
            continue
        rows = read_csv(path)
        report = {"row_count": len(rows), "pass": len(rows) == EXPECTED_TRACE_ROWS}
        if rows:
            keys = set(rows[0])
            step_key = next(
                (key for key in ("step", "sample_index", "iteration") if key in keys),
                None,
            )
            if step_key:
                values = [int(float(row[step_key])) for row in rows]
                report["step_key"] = step_key
                report["step_contiguous"] = all(
                    b - a == 1 for a, b in zip(values, values[1:])
                )
                report["pass"] = report["pass"] and report["step_contiguous"]
            time_key = next(
                (
                    key
                    for key in (
                        "sim_time",
                        "timestamp",
                        "time",
                        "stamp",
                    )
                    if key in keys
                ),
                None,
            )
            if time_key:
                values = [float(row[time_key]) for row in rows]
                report["time_key"] = time_key
                report["time_strictly_increasing"] = all(
                    b > a for a, b in zip(values, values[1:])
                )
                report["pass"] = report["pass"] and report[
                    "time_strictly_increasing"
                ]
        reports[filename] = report
        all_pass = all_pass and report["pass"]
    reports["pass"] = all_pass
    return reports


def evaluate_null_family(
    family: str,
    pretruth_root: Path,
    cases: Sequence[dict],
    evaluator: Path,
    truths: Mapping[str, dict],
) -> dict:
    by_case = {}
    repetition_count = None
    for case in cases:
        case_name = case["case_name"]
        controls = json.loads(
            (pretruth_root / case_name / "null_control_ranks.json").read_text(
                encoding="utf-8"
            )
        )[family]
        by_case[case_name] = controls
        if repetition_count is None:
            repetition_count = len(controls)
        elif repetition_count != len(controls):
            raise ValueError(f"null repetition count mismatch: {family}")

    pooled = []
    case_errors = {case["case_name"]: [] for case in cases}
    with tempfile.TemporaryDirectory(prefix="hcmc_null_") as temp_dir_text:
        temp_dir = Path(temp_dir_text)
        for repetition in range(int(repetition_count or 0)):
            errors = []
            for case in cases:
                case_name = case["case_name"]
                case_output = pretruth_root / case_name
                manifest = json.loads(
                    (case_output / "source_blind_case_manifest.json").read_text(
                        encoding="utf-8"
                    )
                )
                metadata = GridMetadata(**manifest["grid"])
                cells, _ = read_posterior(case_output / "native_posterior.csv")
                ownership = {}
                update_dir = (
                    Path(manifest["case_dir"])
                    / "context_bank"
                    / f"source_update_{int(manifest['selected_source_update_id']):04d}"
                )
                final_ids, _, ownership = derive_final_leaves(update_dir, cells)
                ranks = by_case[case_name][repetition]["ranks"]
                if set(ranks) != set(final_ids):
                    raise ValueError(f"null ranks do not match leaves: {case_name}")
                posterior = posterior_from_ranks(cells, ownership, ranks)
                posterior_path = temp_dir / f"{family}_{repetition}_{case_name}.csv"
                write_posterior(posterior_path, cells, posterior)
                truth = truths[case_name]
                endpoint = linked_native_endpoint(
                    evaluator,
                    posterior_path,
                    metadata,
                    float(truth["truth_x"]),
                    float(truth["truth_y"]),
                )
                error = float(endpoint["pmfs_top5_error_m"])
                errors.append(error)
                case_errors[case_name].append(error)
            pooled.append(statistics.mean(errors))

    ordered = sorted(pooled)
    return {
        "repetitions": len(pooled),
        "pooled_mean_m": statistics.mean(pooled),
        "pooled_median_m": statistics.median(pooled),
        "pooled_q05_m": ordered[int(0.05 * (len(ordered) - 1))],
        "pooled_q95_m": ordered[int(0.95 * (len(ordered) - 1))],
        "case_mean_errors_m": {
            case_name: statistics.mean(values)
            for case_name, values in case_errors.items()
        },
        "pooled_replicate_errors_m": pooled,
    }


def evaluate(args: argparse.Namespace) -> None:
    pretruth_root = args.pretruth_root.resolve()
    freeze = verify_freeze(pretruth_root)
    evaluator = args.cpp_endpoint_evaluator.resolve()
    if not evaluator.is_file():
        raise FileNotFoundError(evaluator)
    evaluator_sha256 = sha256_file(evaluator)
    truth_payload = json.loads(args.truth_sidecar.read_text(encoding="utf-8"))
    truths = truth_payload["cases"]
    case_entries = freeze["cases"]
    expected_names = {entry["case_name"] for entry in case_entries}
    if set(truths) != expected_names:
        raise ValueError(
            f"truth sidecar cases differ: expected={sorted(expected_names)} "
            f"actual={sorted(truths)}"
        )

    results = []
    integrity_pass = True
    parity_pass = True
    for entry in case_entries:
        case_name = entry["case_name"]
        case_output = pretruth_root / case_name
        manifest = json.loads(
            (case_output / "source_blind_case_manifest.json").read_text(
                encoding="utf-8"
            )
        )
        metadata = GridMetadata(**manifest["grid"])
        truth_x = float(truths[case_name]["truth_x"])
        truth_y = float(truths[case_name]["truth_y"])
        native_path = case_output / "native_posterior.csv"
        hcmc_path = case_output / "hcmc_posterior.csv"
        native_cells, native_posterior = read_posterior(native_path)
        hcmc_cells, hcmc_posterior = read_posterior(hcmc_path)
        if [cell.cell_index for cell in native_cells] != [
            cell.cell_index for cell in hcmc_cells
        ]:
            raise ValueError(f"native/HCMC cell order differs: {case_name}")

        native_endpoint = linked_native_endpoint(
            evaluator, native_path, metadata, truth_x, truth_y
        )
        hcmc_endpoint = linked_native_endpoint(
            evaluator, hcmc_path, metadata, truth_x, truth_y
        )
        case_dir = Path(manifest["case_dir"])
        logged = logged_native_endpoint(case_dir)
        endpoint_delta = abs(
            float(native_endpoint["pmfs_top5_error_m"])
            - float(logged["reported_top5_error_m"])
        )
        case_parity = endpoint_delta <= ENDPOINT_PARITY_TOLERANCE_M
        parity_pass = parity_pass and case_parity
        trace_report = trace_integrity(case_dir)
        integrity_pass = integrity_pass and trace_report["pass"]
        native_diagnostics = posterior_diagnostics(
            native_cells, native_posterior, truth_x, truth_y
        )
        hcmc_diagnostics = posterior_diagnostics(
            hcmc_cells, hcmc_posterior, truth_x, truth_y
        )
        false_confident_collapse = (
            hcmc_diagnostics["full_posterior_expected_source_distance_m"]
            > native_diagnostics["full_posterior_expected_source_distance_m"]
            + NON_WORSE_NUMERICAL_TOLERANCE_M
            and hcmc_diagnostics["effective_support_cells"]
            < native_diagnostics["effective_support_cells"] - 1e-9
        )
        results.append(
            {
                "case_name": case_name,
                "truth": [truth_x, truth_y],
                "native_endpoint": native_endpoint,
                "hcmc_endpoint": hcmc_endpoint,
                "native_logged_endpoint": logged,
                "endpoint_parity_delta_m": endpoint_delta,
                "endpoint_parity_pass": case_parity,
                "trace_integrity": trace_report,
                "native_diagnostics": native_diagnostics,
                "hcmc_diagnostics": hcmc_diagnostics,
                "nearest_truth_candidate": nearest_truth_candidate_diagnostic(
                    case_output, truth_x, truth_y
                ),
                "false_confident_collapse": false_confident_collapse,
            }
        )

    native_errors = [
        float(item["native_endpoint"]["pmfs_top5_error_m"]) for item in results
    ]
    hcmc_errors = [
        float(item["hcmc_endpoint"]["pmfs_top5_error_m"]) for item in results
    ]
    native_mean = statistics.mean(native_errors)
    hcmc_mean = statistics.mean(hcmc_errors)
    improvement_percent = 100.0 * (native_mean - hcmc_mean) / native_mean
    non_worse = sum(
        hcmc <= native + NON_WORSE_NUMERICAL_TOLERANCE_M
        for native, hcmc in zip(native_errors, hcmc_errors)
    )
    false_collapses = sum(item["false_confident_collapse"] for item in results)

    leaf_null = evaluate_null_family(
        "random_leaf_permutation", pretruth_root, case_entries, evaluator, truths
    )
    spatial_null = evaluate_null_family(
        "simulated_field_spatial_shuffle",
        pretruth_root,
        case_entries,
        evaluator,
        truths,
    )
    leaf_null["fraction_as_good_or_better_than_real"] = sum(
        value <= hcmc_mean + NON_WORSE_NUMERICAL_TOLERANCE_M
        for value in leaf_null["pooled_replicate_errors_m"]
    ) / leaf_null["repetitions"]
    spatial_null["fraction_as_good_or_better_than_real"] = sum(
        value <= hcmc_mean + NON_WORSE_NUMERICAL_TOLERANCE_M
        for value in spatial_null["pooled_replicate_errors_m"]
    ) / spatial_null["repetitions"]

    classification = truth_payload["data_independence_classification"]
    scientific_thresholds_pass = (
        improvement_percent >= 10.0
        and non_worse >= 4
        and false_collapses == 0
        and hcmc_mean < leaf_null["pooled_mean_m"]
        and hcmc_mean < spatial_null["pooled_mean_m"]
    )
    if classification == "DISCOVERY_REPLAY":
        verdict = "HCMC_V1_DISCOVERY_REPLAY_ONLY"
    elif not integrity_pass or not parity_pass:
        verdict = "HCMC_V1_INDEPENDENT_OFFLINE_HOLD"
    elif classification != "TRUE_INDEPENDENT_PLUME_VALIDATION":
        verdict = (
            "HCMC_V1_TRAJECTORY_HOLDOUT_POSITIVE"
            if scientific_thresholds_pass
            else "HCMC_V1_TRAJECTORY_HOLDOUT_NO_GO"
        )
    elif scientific_thresholds_pass:
        verdict = "HCMC_V1_INDEPENDENT_OFFLINE_PASS"
    else:
        verdict = "HCMC_V1_INDEPENDENT_OFFLINE_NO_GO"

    output = {
        "contract": CONTRACT,
        "phase": "POST_TRUTH_LINKED_NATIVE_EVALUATION",
        "data_independence_classification": classification,
        "truth_sidecar_sha256": sha256_file(args.truth_sidecar),
        "pre_truth_freeze_sha256": sha256_file(
            pretruth_root / "PRE_TRUTH_FREEZE.json"
        ),
        "endpoint_evaluator": str(evaluator),
        "endpoint_evaluator_sha256": evaluator_sha256,
        "endpoint_semantics": "ceil(0.05*N_free) via native C++ loop",
        "native_errors_m": native_errors,
        "hcmc_errors_m": hcmc_errors,
        "native_mean_m": native_mean,
        "hcmc_mean_m": hcmc_mean,
        "pooled_improvement_percent": improvement_percent,
        "non_worse_count": non_worse,
        "endpoint_parity_all_pass": parity_pass,
        "integrity_all_pass": integrity_pass,
        "false_confident_collapse_definition": (
            "HCMC full-posterior expected truth distance is worse than Native "
            "while HCMC effective support is smaller than Native"
        ),
        "false_confident_collapse_count": false_collapses,
        "random_leaf_control": leaf_null,
        "spatial_shuffle_control": spatial_null,
        "cases": results,
        "promotion_gate": {
            "pooled_improvement_at_least_10_percent": improvement_percent >= 10.0,
            "at_least_4_of_6_non_worse": non_worse >= 4 and len(results) == 6,
            "no_false_confident_collapse": false_collapses == 0,
            "better_than_random_leaf_null_mean": hcmc_mean
            < leaf_null["pooled_mean_m"],
            "better_than_spatial_shuffle_null_mean": hcmc_mean
            < spatial_null["pooled_mean_m"],
            "all_provenance_integrity_parity_pass": integrity_pass and parity_pass,
        },
        "verdict": verdict,
    }
    write_json(args.json_out, output)
    write_csv(
        args.csv_out,
        (
            "case_name",
            "native_error_m",
            "hcmc_error_m",
            "non_worse",
            "endpoint_parity_delta_m",
            "endpoint_parity_pass",
            "false_confident_collapse",
        ),
        (
            {
                "case_name": item["case_name"],
                "native_error_m": item["native_endpoint"]["pmfs_top5_error_m"],
                "hcmc_error_m": item["hcmc_endpoint"]["pmfs_top5_error_m"],
                "non_worse": float(item["hcmc_endpoint"]["pmfs_top5_error_m"])
                <= float(item["native_endpoint"]["pmfs_top5_error_m"])
                + NON_WORSE_NUMERICAL_TOLERANCE_M,
                "endpoint_parity_delta_m": item["endpoint_parity_delta_m"],
                "endpoint_parity_pass": item["endpoint_parity_pass"],
                "false_confident_collapse": item["false_confident_collapse"],
            }
            for item in results
        ),
    )
    print(json.dumps(output, indent=2, sort_keys=True))


def parser() -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser()
    subparsers = argument_parser.add_subparsers(dest="phase", required=True)

    generate_parser = subparsers.add_parser("generate")
    generate_parser.add_argument("--native-root", type=Path, required=True)
    generate_parser.add_argument("--output-root", type=Path, required=True)
    generate_parser.add_argument("--budget-s", type=float, default=300.0)
    generate_parser.add_argument("--case", action="append", default=[])
    generate_parser.set_defaults(function=generate)

    evaluate_parser = subparsers.add_parser("evaluate")
    evaluate_parser.add_argument("--pretruth-root", type=Path, required=True)
    evaluate_parser.add_argument("--truth-sidecar", type=Path, required=True)
    evaluate_parser.add_argument(
        "--cpp-endpoint-evaluator", type=Path, required=True
    )
    evaluate_parser.add_argument("--json-out", type=Path, required=True)
    evaluate_parser.add_argument("--csv-out", type=Path, required=True)
    evaluate_parser.set_defaults(function=evaluate)
    return argument_parser


def main() -> None:
    arguments = parser().parse_args()
    arguments.function(arguments)


if __name__ == "__main__":
    main()
