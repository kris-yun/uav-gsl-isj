#!/usr/bin/env python3
"""Freeze map-only PF-DEI V3 trajectory skeletons.

The sampler never reads gas, source truth, posterior, or localization error. It
uses the native PMFS free-cell graph plus motion/stop cadence estimated only
from stripped OFF pose/time skeletons. Every traversed edge is between adjacent
native PMFS free cells.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import statistics
from collections import defaultdict, deque
from pathlib import Path


HOUSES = ("H01", "H02", "H03")
TRAIN_SEEDS = tuple(range(3001, 3021))
RESERVED_SEEDS = tuple(range(4001, 4006))
DT = 0.2


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def historical_paths(root: Path, house: str) -> list[Path]:
    h = f"House{house[-2:]}"
    return [
        root / h / f"seed{seed}" / "off" / "runtime" / f"{h}_seed{seed}_off_off"
        / "sim_pose_trace.csv"
        for seed in range(10)
    ]


def read_historical(path: Path) -> list[dict]:
    with path.open(newline="") as source:
        rows = list(csv.DictReader(source))
    required = {"t_sim_s", "x", "y", "z", "yaw", "is_moving"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError(f"PF_DEI_V3_BAD_HISTORICAL_SKELETON:{path}")
    return rows


def free_graph(support: Path, house: str) -> tuple[dict[tuple[int, int], tuple[float, float]], dict]:
    cells: dict[tuple[int, int], tuple[float, float]] = {}
    with support.open(newline="", encoding="utf-8") as source:
        for row in csv.DictReader(source):
            if row["house"] != house or int(row["legal_height_count"]) <= 0:
                continue
            key = (int(row["pmfs_grid_i"]), int(row["pmfs_grid_j"]))
            xy = (float(row["pmfs_x"]), float(row["pmfs_y"]))
            if key in cells and cells[key] != xy:
                raise ValueError("PF_DEI_V3_FREE_CELL_COORDINATE_CONFLICT")
            cells[key] = xy
    graph = {
        cell: tuple(
            neighbor for neighbor in (
                (cell[0] - 1, cell[1]), (cell[0] + 1, cell[1]),
                (cell[0], cell[1] - 1), (cell[0], cell[1] + 1),
            ) if neighbor in cells
        )
        for cell in cells
    }
    return cells, graph


def nearest_cell(cells: dict, x: float, y: float) -> tuple[int, int]:
    return min(cells, key=lambda key: ((cells[key][0] - x) ** 2 + (cells[key][1] - y) ** 2, key))


def component(graph: dict, start: tuple[int, int]) -> set[tuple[int, int]]:
    seen = {start}
    queue = deque([start])
    while queue:
        node = queue.popleft()
        for nxt in graph[node]:
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen


def shortest_path(graph: dict, start: tuple[int, int], target: tuple[int, int], order: tuple) -> list:
    queue = deque([start])
    parent = {start: None}
    while queue:
        node = queue.popleft()
        if node == target:
            break
        neighbors = sorted(
            graph[node],
            key=lambda p: (order.index((p[0] - node[0], p[1] - node[1])), p),
        )
        for nxt in neighbors:
            if nxt not in parent:
                parent[nxt] = node
                queue.append(nxt)
    if target not in parent:
        raise ValueError("PF_DEI_V3_MAPONLY_PATH_UNREACHABLE")
    path = []
    node = target
    while node is not None:
        path.append(node)
        node = parent[node]
    return path[::-1]


def stopped_run_lengths(histories: list[list[dict]]) -> list[int]:
    lengths = []
    for rows in histories:
        run = 0
        for row in rows:
            if int(row["is_moving"]) == 0:
                run += 1
            elif run:
                lengths.append(run)
                run = 0
        if run:
            lengths.append(run)
    if not lengths:
        raise ValueError("PF_DEI_V3_NO_NATIVE_STOP_CADENCE")
    return lengths


def emit_skeleton(
    output: Path,
    seed: int,
    cells: dict,
    graph: dict,
    accessible: set,
    starts: list[tuple[int, int]],
    stop_lengths: list[int],
    sample_count: int,
    z: float,
) -> dict:
    rng = random.Random(seed)
    current = starts[rng.randrange(len(starts))]
    if current not in accessible:
        raise ValueError("PF_DEI_V3_START_OUTSIDE_ACCESSIBLE_COMPONENT")
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    rng.shuffle(directions)
    direction_order = tuple(directions)
    available = sorted(accessible)
    rows = []
    stop_id = 0
    step = 0
    last_yaw = 0.0

    def add(x: float, y: float, moving: int, start_marker: int, block_marker: int) -> None:
        nonlocal step, last_yaw
        if len(rows) >= sample_count:
            return
        step += 1
        rows.append({
            "t_sim_s": f"{step * DT:.6f}", "step": step,
            "x": f"{x:.6f}", "y": f"{y:.6f}", "z": f"{z:.6f}",
            "yaw": f"{last_yaw:.6f}", "is_moving": moving, "seed": seed,
            "stop_id": stop_id, "stop_start": start_marker,
            "block_boundary": block_marker,
        })

    start_xy = cells[current]
    initial_hold = stop_lengths[rng.randrange(len(stop_lengths))]
    stop_id += 1
    for index in range(initial_hold):
        add(start_xy[0], start_xy[1], 0, int(index == 0), int(index == 0 and stop_id % 3 == 1))

    visited = {current}
    while len(rows) < sample_count:
        choices = [node for node in available if node != current]
        target = choices[rng.randrange(len(choices))]
        path = shortest_path(graph, current, target, direction_order)
        for left, right in zip(path, path[1:]):
            x0, y0 = cells[left]
            x1, y1 = cells[right]
            last_yaw = math.atan2(y1 - y0, x1 - x0)
            # Native PMFS cells are 0.3 m apart; three 0.1 m substeps retain
            # the observed 0.2 s cadence and stay inside the same free corridor.
            for part in (1.0 / 3.0, 2.0 / 3.0, 1.0):
                add(x0 + part * (x1 - x0), y0 + part * (y1 - y0), 1, 0, 0)
            visited.add(right)
            if len(rows) >= sample_count:
                break
        current = target
        if len(rows) >= sample_count:
            break
        stop_id += 1
        hold = stop_lengths[rng.randrange(len(stop_lengths))]
        x, y = cells[current]
        for index in range(hold):
            add(x, y, 0, int(index == 0), int(index == 0 and stop_id % 3 == 1))

    output.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0])
    with output.open("w", newline="", encoding="utf-8") as sink:
        writer = csv.DictWriter(sink, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return {
        "path": str(output), "sha256": sha256_file(output), "seed": seed,
        "samples": len(rows), "unique_free_cells_visited": len(visited),
        "stop_count": stop_id,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--support", type=Path, required=True)
    parser.add_argument("--historical-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    manifest = {
        "contract": "PF_DEI_V3_MAP_ONLY_NATIVE_FREE_GRAPH_TRAJECTORIES_V1",
        "truth_used": False, "gas_used": False, "posterior_used": False,
        "localization_error_used": False, "dt_s": DT,
        "support_sha256": sha256_file(args.support), "houses": {}, "trajectories": [],
    }
    for house in HOUSES:
        paths = historical_paths(args.historical_root, house)
        histories = [read_historical(path) for path in paths]
        cells, graph = free_graph(args.support, house)
        starts = [nearest_cell(cells, float(rows[0]["x"]), float(rows[0]["y"])) for rows in histories]
        components = [component(graph, start) for start in starts]
        accessible = set.intersection(*components)
        if not accessible or any(start not in accessible for start in starts):
            raise ValueError(f"PF_DEI_V3_HISTORICAL_START_COMPONENT_CONFLICT:{house}")
        stop_lengths = stopped_run_lengths(histories)
        sample_count = int(statistics.median(len(rows) for rows in histories))
        z = statistics.median(float(row["z"]) for rows in histories for row in rows)
        house_rows = []
        for split, seeds in (("train", TRAIN_SEEDS), ("reserved", RESERVED_SEEDS)):
            for seed in seeds:
                output = args.output_root / house / split / f"trajectory_seed_{seed}.csv"
                house_rows.append(emit_skeleton(
                    output, seed, cells, graph, accessible, starts, stop_lengths,
                    sample_count, z,
                ))
                house_rows[-1]["split"] = split
                house_rows[-1]["house"] = house
        manifest["houses"][house] = {
            "free_cell_count": len(cells), "accessible_cell_count": len(accessible),
            "sample_count": sample_count, "robot_z_m": z,
            "native_stop_run_count": len(stop_lengths),
            "native_stop_run_median_samples": statistics.median(stop_lengths),
            "historical_schedule_sha256": [sha256_file(path) for path in paths],
        }
        manifest["trajectories"].extend(house_rows)

    manifest_path = args.output_root / "trajectory_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "PF_DEI_V3_MAPONLY_TRAJECTORIES=PASS "
        f"trajectories={len(manifest['trajectories'])} manifest_sha256={sha256_file(manifest_path)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
