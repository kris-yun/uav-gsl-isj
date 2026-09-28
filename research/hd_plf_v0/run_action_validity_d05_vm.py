"""Read-only, observation-grounded audit of the frozen HD-PLF action value.

Run beside the retained OPEN target cubes on the VM. The action selector reads
only its frozen templates, one already observed hit position, and six-source
uniform diagnostic weights. Future concentration and source identity enter only
the evaluation below. This is not a Native posterior or VGR closed-loop test.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from hd_plf_action import HDPLFActionSelector
from smoke_open_saved_maps import reachable_goals


ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "research/hd_plf_v0/smoke_input/open_mean_maps.npz"
GEOMETRY = ROOT / "evidence/marked_encounter_pmfs_d0/inputs"
PROTOCOL = ROOT / "research/marked_encounter_pmfs_d0/protocol"
OUT = ROOT / "evidence/hd_plf_v0/action_validity_d05"
EPS = 1e-9  # The archived B2 template floor.


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def square_reading(cube: np.ndarray, metadata: dict, xy: tuple[float, float], t: int) -> float:
    """0.20 m square area mean of native 0.10 m cells (x,y cube order)."""
    nx, ny = cube.shape[1:]
    dx = float(metadata["coarse_cell"])
    xx = float(metadata["min_x"]) + np.arange(nx + 1) * dx
    yy = float(metadata["min_y"]) + np.arange(ny + 1) * dx
    wx = np.maximum(0., np.minimum(xx[1:], xy[0] + .1) - np.maximum(xx[:-1], xy[0] - .1)) / .2
    wy = np.maximum(0., np.minimum(yy[1:], xy[1] + .1) - np.maximum(yy[:-1], xy[1] - .1)) / .2
    if abs(wx.sum() - 1.) > 1e-7 or abs(wy.sum() - 1.) > 1e-7:
        raise ValueError("future observation square extends beyond retained cube")
    return float(wx @ cube[t] @ wy)


def b2_sse(templates: np.ndarray, observed: np.ndarray) -> np.ndarray:
    p = np.maximum(np.asarray(templates, dtype=np.float64), EPS)
    y = np.asarray(observed, dtype=np.float64)
    norm = np.square(p).sum(axis=1)
    gain = np.maximum(0., (p @ y) / norm)
    return np.square(y[None, :] - gain[:, None] * p).sum(axis=1)


def tie_rank(sse: np.ndarray, truth: int, observed: np.ndarray) -> float:
    tol = 1e-10 * max(1., float(np.square(observed).sum()))
    lower = int(np.sum(sse < sse[truth] - tol))
    tied = int(np.sum(np.abs(sse - sse[truth]) <= tol))
    return 1. + lower + .5 * (tied - 1)


def archived_strict_rank(sse: np.ndarray, truth: int) -> int:
    """Exactly the historical B2 rank rule: 1 + strictly better scores."""
    return int(1 + np.sum(sse < sse[truth]))


def margin(sse: np.ndarray, truth: int) -> float:
    other = np.delete(sse, truth)
    return float(np.min(other) - sse[truth])


def midranks(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="stable")
    ranks = np.empty(len(values), dtype=np.float64)
    i = 0
    while i < len(order):
        j = i + 1
        while j < len(order) and values[order[j]] == values[order[i]]:
            j += 1
        ranks[order[i:j]] = (i + 1 + j) / 2.
        i = j
    return ranks


def spearman(a: np.ndarray, b: np.ndarray) -> float | None:
    ra, rb = midranks(np.asarray(a)), midranks(np.asarray(b))
    ra -= ra.mean()
    rb -= rb.mean()
    den = float(np.linalg.norm(ra) * np.linalg.norm(rb))
    return float(ra @ rb / den) if den > 0 else None


def json_number(value: float | None) -> float | None:
    return None if value is None else float(value)


def main() -> None:
    contract_path = ROOT / "research/hd_plf_v0/D05_ACTION_VALIDITY_CONTRACT_20260928.json"
    maps_path = INPUT
    manifest_path = PROTOCOL / "JTD_E2_FRESH_TARGET_MANIFEST.tsv"
    targets_path = PROTOCOL / "JTD_E2_FRESH_TARGET_10x30.npy"
    templates = np.load(maps_path, allow_pickle=False)
    pooled_targets = np.load(targets_path, allow_pickle=False)
    if pooled_targets.shape != (3, 6, 4, 10, 30):
        raise ValueError("wrong OPEN target tensor shape")
    manifest = list(csv.DictReader(manifest_path.open(newline=""), delimiter="\t"))
    if len(manifest) != 72:
        raise ValueError("expected exactly 72 OPEN target records")
    records: list[dict] = []
    episodes: list[dict] = []
    counts = defaultdict(int)
    max_probe_parity = 0.
    max_probe_parity_scaled = 0.
    max_target_parity = 0.
    for row in manifest:
        env, truth, rep = (int(row[key]) for key in ("environment_index", "source_index", "new_index"))
        if not (0 <= env < 3 and 0 <= truth < 6 and 0 <= rep < 4):
            raise ValueError("invalid target axis")
        base = GEOMETRY / f"env_{env}"
        probes = list(csv.DictReader((base / "probes.csv").open(newline="")))
        if [int(p["probe_rank"]) for p in probes] != list(range(1, 31)):
            raise ValueError("invalid probe ordering")
        run_dir = Path(row["run_dir"])
        cube_path, pooled_path = run_dir / "concentration.npy", run_dir / "pooled.npy"
        if sha(cube_path) != row["cube_sha256"] or sha(pooled_path) != row["pooled_sha256"]:
            raise ValueError(f"historical target hash mismatch: {run_dir}")
        cube = np.load(cube_path, allow_pickle=False)
        pooled = np.load(pooled_path, allow_pickle=False)
        spatial = json.loads((run_dir / "spatial_metadata.json").read_text())
        if (cube.shape != (10, int(spatial["gx"]), int(spatial["gy"])) or
                pooled.shape != (10, 30)):
            raise ValueError("invalid retained concentration/pooled shape")
        max_target_parity = max(max_target_parity, float(np.max(np.abs(pooled - pooled_targets[env, truth, rep]))))
        if max_target_parity > 1e-5:
            raise ValueError("retained pooled target differs from local frozen target")
        for probe_i, probe in enumerate(probes):
            xy = float(probe["x"]), float(probe["y"])
            for t in range(10):
                projected = square_reading(cube, spatial, xy, t)
                deviation = abs(projected - float(pooled[t, probe_i]))
                max_probe_parity = max(max_probe_parity, deviation)
                max_probe_parity_scaled = max(max_probe_parity_scaled,
                                              deviation / max(1., abs(float(pooled[t, probe_i]))))
        if max_probe_parity_scaled > 1e-6:
            raise ValueError(f"physical observation projection failed: {max_probe_parity_scaled}")
        first = next(((t, i) for t in range(9) for i in range(30) if pooled[t, i] > 0), None)
        if first is None:
            counts["no_positive_anchor"] += 1
            continue
        t, probe_i = first
        probe = probes[probe_i]
        xy = float(probe["x"]), float(probe["y"])
        goals = reachable_goals(env, xy)
        if len(goals) < 2:
            counts["fewer_than_two_goals"] += 1
            continue
        history_cell = int(probe["cell_index"])
        q = np.full(6, 1 / 6, dtype=np.float64)
        goal_values = np.array([square_reading(cube, spatial, (g.x_m, g.y_m), t + 1) for g in goals])
        y0 = float(pooled[t, probe_i])
        ep = {"environment": env, "source_index": truth, "target_index": rep,
              "anchor_time_index": t, "future_time_index": t + 1,
              "anchor_probe_rank": probe_i + 1, "anchor_cell": history_cell,
              "feasible_goals": len(goals)}
        for arm, kind in (("LF-u", "u"), ("LF-rawu", "rawu")):
            m = np.asarray(templates[f"env_{env}_{kind}"], dtype=np.float64)
            if m.shape[0] != 6:
                raise ValueError("six-source mean map axis mismatch")
            decision = HDPLFActionSelector(arm, m).choose(xy, xy, [history_cell], q, goals)
            if len(decision.ranked_goals) != len(goals):
                raise ValueError("action selector lost a feasible goal")
            prefix_y = np.array([y0])
            prefix_sse = b2_sse(m[:, [history_cell]], prefix_y)
            before_rank = tie_rank(prefix_sse, truth, prefix_y)
            before_strict_rank = archived_strict_rank(prefix_sse, truth)
            before_margin = margin(prefix_sse, truth)
            by_cell = {g.cell_index: (g, float(y)) for g, y in zip(goals, goal_values)}
            arm_rows = []
            for val in decision.ranked_goals:
                goal, y1 = by_cell[val.goal.cell_index]
                observed = np.array([y0, y1])
                sse = b2_sse(m[:, [history_cell, goal.cell_index]], observed)
                after_rank = tie_rank(sse, truth, observed)
                after_strict_rank = archived_strict_rank(sse, truth)
                after_margin = margin(sse, truth)
                arm_rows.append({
                    "environment": env, "source_index": truth, "target_index": rep,
                    "arm": arm, "anchor_time_index": t, "anchor_probe_rank": probe_i + 1,
                    "goal_cell": goal.cell_index, "goal_x_m": goal.x_m, "goal_y_m": goal.y_m,
                    "travel_m": goal.path_length_m, "model_action_value": val.action_value,
                    "model_pair_separation": val.pair_separation,
                    "observed_prefix_ppm": y0, "observed_goal_ppm": y1,
                    "rank_before_tie_aware": before_rank, "rank_after_tie_aware": after_rank,
                    "rank_gain": before_rank - after_rank,
                    "rank_before_archived_strict": before_strict_rank,
                    "rank_after_archived_strict": after_strict_rank,
                    "rank_gain_archived_strict": before_strict_rank - after_strict_rank,
                    "margin_gain": after_margin - before_margin,
                    "selected": goal.cell_index == decision.selected.goal.cell_index,
                })
            records.extend(arm_rows)
            av = np.array([v["model_action_value"] for v in arm_rows])
            rg = np.array([v["rank_gain"] for v in arm_rows])
            strict_rg = np.array([v["rank_gain_archived_strict"] for v in arm_rows])
            mg = np.array([v["margin_gain"] for v in arm_rows])
            selected = next(v for v in arm_rows if v["selected"])
            ep[arm] = {
                "rho_action_rank_gain": json_number(spearman(av, rg)),
                "rho_action_archived_strict_rank_gain": json_number(spearman(av, strict_rg)),
                "rho_action_margin_gain": json_number(spearman(av, mg)),
                "selected_cell": selected["goal_cell"],
                "selected_rank_gain": selected["rank_gain"],
                "selected_archived_strict_rank_gain": selected["rank_gain_archived_strict"],
                "median_goal_rank_gain": float(np.median(rg)),
                "selected_minus_median_rank_gain": float(selected["rank_gain"] - np.median(rg)),
                "selected_margin_gain": selected["margin_gain"],
                "median_goal_margin_gain": float(np.median(mg)),
            }
        episodes.append(ep)
        counts["evaluated"] += 1

    if counts["evaluated"] + counts["no_positive_anchor"] + counts["fewer_than_two_goals"] != 72:
        raise ValueError("episode accounting mismatch")
    summary = {}
    for env in range(3):
        for arm in ("LF-u", "LF-rawu"):
            sub = [e for e in episodes if e["environment"] == env]
            valid = [e[arm]["rho_action_rank_gain"] for e in sub if e[arm]["rho_action_rank_gain"] is not None]
            valid_margin = [e[arm]["rho_action_margin_gain"] for e in sub if e[arm]["rho_action_margin_gain"] is not None]
            strict_valid = [e[arm]["rho_action_archived_strict_rank_gain"] for e in sub
                            if e[arm]["rho_action_archived_strict_rank_gain"] is not None]
            summary[f"env_{env}_{arm}"] = {
                "episodes": len(sub),
                "defined_rank_correlations": len(valid),
                "median_episode_rho_action_rank_gain": float(np.median(valid)) if valid else None,
                "positive_episode_rank_rho_fraction": float(np.mean(np.array(valid) > 0)) if valid else None,
                "defined_margin_correlations": len(valid_margin),
                "median_episode_rho_action_margin_gain": float(np.median(valid_margin)) if valid_margin else None,
                "defined_archived_strict_rank_correlations": len(strict_valid),
                "median_episode_rho_action_archived_strict_rank_gain": float(np.median(strict_valid)) if strict_valid else None,
                "median_selected_minus_median_rank_gain": float(np.median([e[arm]["selected_minus_median_rank_gain"] for e in sub])) if sub else None,
                "per_source_median_rank_rho": {
                    str(source): (float(np.median(vals)) if vals else None)
                    for source in range(6)
                    for vals in [[e[arm]["rho_action_rank_gain"] for e in sub
                                  if e["source_index"] == source and e[arm]["rho_action_rank_gain"] is not None]]
                },
            }
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "GOAL_COUNTERFACTUALS.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)
    output = {
        "status": "OPEN_SIX_SOURCE_COUNTERFACTUAL_ACTION_AUDIT_NOT_NATIVE_OR_VGR",
        "contract_sha256": sha(contract_path),
        "mean_maps_sha256": sha(maps_path),
        "target_manifest_sha256": sha(manifest_path),
        "pooled_target_tensor_sha256": sha(targets_path),
        "source_weight": "uniform 1/6 diagnostic; aligned Native runtime q unavailable",
        "all_goals_observed_counterfactually_at_next_stored_snapshot": True,
        "cube_probe_projection_max_abs_diff": max_probe_parity,
        "cube_probe_projection_max_scaled_diff": max_probe_parity_scaled,
        "pooled_tensor_max_abs_diff": max_target_parity,
        "counts": dict(counts),
        "summary": summary,
        "episodes": episodes,
    }
    (OUT / "D05_RESULT.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"counts": output["counts"], "projection_max_abs": max_probe_parity,
                      "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
