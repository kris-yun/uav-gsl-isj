"""H01/H02 OPEN software smoke using saved six-source PMFS amplitude maps.

This does not read target concentration, run a simulator, or claim a closed-loop
result. Uniform six-source weights are only an API smoke input; deployment must
provide the full legal Native PMFS sourceProbability in aligned map order.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import deque
from pathlib import Path

import numpy as np

from hd_plf_action import GoalCandidate, HDPLFActionSelector


ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "research/hd_plf_v0/smoke_input/open_mean_maps.npz"
GEOMETRY = ROOT / "evidence/marked_encounter_pmfs_d0/inputs"
OUT = ROOT / "evidence/hd_plf_v0/open_software_smoke"
NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1),
             (-1, -1), (-1, 1), (1, -1), (1, 1))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reachable_goals(env: int, anchor_xy: tuple[float, float]) -> list[GoalCandidate]:
    base = GEOMETRY / f"env_{env}"
    meta = json.loads((base / "meta.json").read_text())
    width, height = int(meta["width"]), int(meta["height"])
    res, ox, oy = (float(meta[k]) for k in ("resolution", "origin_x", "origin_y"))
    occupancy = np.fromfile(base / "occupancy.u8", dtype=np.uint8)
    if occupancy.size != width * height:
        raise ValueError("invalid frozen occupancy size")

    def free(i: int, j: int) -> bool:
        return 0 <= i < width and 0 <= j < height and occupancy[i + width * j] == 1

    def center(i: int, j: int) -> tuple[float, float]:
        return ox + (i + .5) * res, oy + (j + .5) * res

    sx, sy = int((anchor_xy[0] - ox) / res), int((anchor_xy[1] - oy) / res)
    if not free(sx, sy):
        return []
    parent: dict[tuple[int, int], tuple[int, int] | None] = {(sx, sy): None}
    queue = deque([(sx, sy)])
    while queue:
        cx, cy = queue.popleft()
        for dx, dy in NEIGHBORS:
            nx, ny = cx + dx, cy + dy
            if not free(nx, ny) or (nx, ny) in parent:
                continue
            if dx and dy and (not free(cx + dx, cy) or not free(cx, cy + dy)):
                continue
            parent[(nx, ny)] = (cx, cy)
            queue.append((nx, ny))
    goals = []
    start_center = center(sx, sy)
    for (gx, gy) in parent:
        x, y = center(gx, gy)
        radius = math.hypot(x - anchor_xy[0], y - anchor_xy[1])
        if not .6 - 1e-9 <= radius <= 1.2 + 1e-9:
            continue
        path = []
        cur = (gx, gy)
        while cur is not None:
            path.append(center(*cur))
            cur = parent[cur]
        path.reverse()
        length = math.dist(anchor_xy, start_center)
        length += sum(math.dist(a, b) for a, b in zip(path, path[1:]))
        if length <= 2.7 + 1e-9:
            goals.append(GoalCandidate(gx + width * gy, x, y, length))
    return goals


def main() -> None:
    maps = np.load(INPUT)
    op_root = ROOT / "evidence/amplitude_operator_decoupling_v0/verified_implementation"
    frozen_ops = np.load(op_root / "observation_operators.npz")
    frozen_templates = np.load(op_root / "amplitude_templates.npz")
    projection_parity = {}
    for env in (0, 1, 2):
        for kind in ("u", "rawu"):
            projected = maps[f"env_{env}_{kind}"] @ frozen_ops[f"env_{env}_footprint"].T
            expected = frozen_templates[f"env_{env}_{kind}_footprint"][:, 0, :]
            error = float(np.max(np.abs(projected - expected)))
            if error > 1e-8:
                raise ValueError(f"OPEN template parity failed: env {env} {kind} {error}")
            projection_parity[f"env_{env}_{kind}"] = error
    rows = []
    source_axes = {}
    for env in (0, 1, 2):
        base = GEOMETRY / f"env_{env}"
        source_rows = list(csv.DictReader((base / "sources.csv").open(newline="")))
        if [int(r["source_index"]) for r in source_rows] != list(range(6)):
            raise ValueError(f"env {env}: saved six-source axis is not ordered")
        source_axes[str(env)] = [r["source_id"] for r in source_rows]
        probes = list(csv.DictReader((base / "probes.csv").open(newline="")))
        chosen = None
        for probe in probes:
            anchor = float(probe["x"]), float(probe["y"])
            goals = reachable_goals(env, anchor)
            if len(goals) >= 2:
                chosen = probe, anchor, goals
                break
        if chosen is None:
            raise RuntimeError(f"env {env}: no geometry-only anchor with two local goals")
        probe, anchor, goals = chosen
        history = [int(probe["cell_index"])]
        q = np.full(6, 1 / 6, dtype=np.float64)
        native_placeholder = anchor  # fallback only; not an actual Native goal
        decisions = {}
        for arm, kind in (("LF-u", "u"), ("LF-rawu", "rawu")):
            selector = HDPLFActionSelector(arm, maps[f"env_{env}_{kind}"])
            decision = selector.choose(native_placeholder, anchor, history, q, goals)
            if decision.selected is None:
                raise RuntimeError(f"env {env} {arm}: no selected local goal")
            decisions[arm] = decision
            selected = decision.selected
            rows.append({
                "environment": env,
                "arm": arm,
                "anchor_probe_rank": int(probe["probe_rank"]),
                "anchor_x_m": anchor[0], "anchor_y_m": anchor[1],
                "reachable_local_goals": len(goals),
                "selected_cell_index": selected.goal.cell_index,
                "selected_x_m": selected.goal.x_m,
                "selected_y_m": selected.goal.y_m,
                "selected_pair_separation": selected.pair_separation,
                "history_pair_separation": decision.history_separation,
                "separation_gain": selected.separation_gain,
                "travel_cost_m": selected.goal.path_length_m,
                "travel_penalty": selected.travel_penalty,
                "action_value": selected.action_value,
                "same_goal_as_other_arm": None,
            })
        same = (decisions["LF-u"].selected.goal.cell_index ==
                decisions["LF-rawu"].selected.goal.cell_index)
        rows[-2]["same_goal_as_other_arm"] = same
        rows[-1]["same_goal_as_other_arm"] = same
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "OPEN_SMOKE_WAYPOINTS.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    summary = {
        "status": "OPEN_SIX_SOURCE_SOFTWARE_SMOKE_ONLY",
        "environments": {"0": "House01 OPEN", "1": "House02 W0 OPEN", "2": "House02 W2 OPEN"},
        "mean_map_sha256": sha256(INPUT),
        "frozen_open_footprint_projection_max_abs_diff": projection_parity,
        "q_input": "uniform over six OPEN source hypotheses; not an actual Native PMFS runtime posterior",
        "source_axes": source_axes,
        "anchor_is_actual_stop": False,
        "anchor_selection": "lowest-rank frozen OPEN probe with at least two geometry-feasible local goals; no target read",
        "full_support_deployment_verified": False,
        "actual_vgr_goal_execution_verified": False,
        "target_concentration_read": False,
        "different_waypoint_count": sum(not rows[i]["same_goal_as_other_arm"] for i in (0, 2, 4)),
        "rows": rows,
    }
    with (OUT / "OPEN_SMOKE_RESULT.json").open("w", newline="\n") as f:
        f.write(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
