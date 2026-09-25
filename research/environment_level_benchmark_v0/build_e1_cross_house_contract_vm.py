#!/usr/bin/env python3
"""E1 geometry-only contract construction; never invokes plume generation."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt


BASE = Path("/home/zyc")
SCENARIOS = Path("/mnt/hgfs/workspace/GADEN_files/scenarios")
REPO_GEOMETRY = Path(__file__).resolve().parents[1] / "causal_biorthogonal_green_v1" / "prepare_gate1a_bank.py"
REPO_EXTRACTOR = Path(__file__).resolve().parents[1] / "causal_biorthogonal_green_v1" / "extract_gate1a_probe_vector.py"
EXPORT_ROOT = BASE / "rmfe_v2_runtime_causal_20260814_a2_002/house123/runs_2seed_v4"
EXPORT_IDS = {"House01": "H01_air_seed", "House02": "H02_seed", "House03": "H03_seed"}
TIMES = (100, 150, 200, 250, 300, 350, 400, 450, 500, 550)
WINDS = {
    "House01": ("1,3-2,4_fast", "2,4-1_fast"),
    "House02": ("3,5-1_fast", "3,5-1_slow", "4,5-3_slow"),
    "House03": ("1-2,5_fast", "5-3_fast"),
}


class SourceHeightContractError(ValueError):
    pass


def import_file(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


GATE = import_file(REPO_GEOMETRY, "gate1a_geometry_for_e1")
EXTRACT = import_file(REPO_EXTRACTOR, "gate1a_extractor_for_e1")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def rows_tsv(path: Path, rows: list[dict]) -> None:
    assert rows
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def nav_for(house: str, occ_min: np.ndarray) -> tuple[np.ndarray, dict, list[Path]]:
    pruned = []
    for seed in (0, 1):
        export = EXPORT_ROOT / f"{EXPORT_IDS[house]}{seed}" / "off/geometry_export"
        pruned.append(export / "pruned_occupancy.bin")
    if sha(pruned[0]) != sha(pruned[1]):
        raise ValueError(f"PMFS navigation mask varies across seed in {house}")
    meta_path = pruned[0].with_name("pruned_meta.json")
    meta = json.loads(meta_path.read_text())
    if meta["scale"] != 3 or not math.isclose(meta["resolution"], 0.30, abs_tol=1e-5):
        raise ValueError(f"unexpected PMFS geometry: {house} {meta}")
    if not np.allclose([meta["origin_x"], meta["origin_y"]], occ_min[:2], atol=1e-5):
        raise ValueError(f"PMFS/GADEN origin mismatch: {house}")
    free = np.fromfile(pruned[0], dtype=np.uint8)
    if free.size != meta["width"] * meta["height"] or not np.isin(free, [0, 1]).all():
        raise ValueError(f"bad PMFS binary: {house}")
    return free.reshape(meta["height"], meta["width"]).T.astype(bool), meta, [meta_path, *pruned]


def pmfs_index(x: float, y: float, meta: dict) -> tuple[int, int]:
    return (int(math.floor((x - meta["origin_x"]) / meta["resolution"])),
            int(math.floor((y - meta["origin_y"]) / meta["resolution"])))


def nav_valid(x: float, y: float, free: np.ndarray, meta: dict) -> bool:
    i, j = pmfs_index(x, y, meta)
    return 0 <= i < free.shape[0] and 0 <= j < free.shape[1] and bool(free[i, j])


def fps_indices(coords: np.ndarray, grid_ij: np.ndarray, count: int) -> list[int]:
    """Integer Euclidean FPS, with exact centroid and lexicographic ties."""
    n = len(coords)
    if n < count:
        raise ValueError(f"only {n} eligible cells for {count} FPS points")
    centroid_numerators = coords * n - coords.sum(axis=0)
    centroid_d2 = np.sum(centroid_numerators ** 2, axis=1)
    first = min(range(n), key=lambda k: (int(centroid_d2[k]), int(grid_ij[k, 0]), int(grid_ij[k, 1])))
    selected = [first]
    min_d2 = np.sum((coords - coords[first]) ** 2, axis=1)
    while len(selected) < count:
        candidates = (k for k in range(n) if k not in selected)
        chosen = min(candidates, key=lambda k: (-int(min_d2[k]), int(grid_ij[k, 0]), int(grid_ij[k, 1])))
        selected.append(chosen)
        min_d2 = np.minimum(min_d2, np.sum((coords - coords[chosen]) ** 2, axis=1))
    return selected


def probes_for(house: str, occ: np.ndarray, env_min: np.ndarray, cell: float,
               nav_free: np.ndarray, nav_meta: dict, obs_z: float) -> tuple[list[dict], np.ndarray, np.ndarray]:
    iz = GATE.fine_index(obs_z, float(env_min[2]), cell)
    if not 0 <= iz < occ.shape[0]:
        raise ValueError(f"observation height outside map: {house}")
    nx, ny = occ.shape[1:]
    candidates = []
    coord_units = []
    grid_ij = []
    for pi in range((nx + 1) // 2):
        for pj in range((ny + 1) // 2):
            x0, x1 = 2 * pi, min(2 * pi + 2, nx)
            y0, y1 = 2 * pj, min(2 * pj + 2, ny)
            if np.any(occ[iz, x0:x1, y0:y1] != 0):
                continue
            all_nav = all(nav_valid(float(env_min[0] + (ix + .5) * cell),
                                    float(env_min[1] + (iy + .5) * cell), nav_free, nav_meta)
                          for ix in range(x0, x1) for iy in range(y0, y1))
            if not all_nav:
                continue
            # Coordinates in doubled native-index units preserve half-cell
            # edge centers exactly for odd sized grids.
            ux, uy = x0 + x1, y0 + y1
            candidates.append(dict(house=house, probe_rank=0, pool_i=pi, pool_j=pj,
                                   native_x0=x0, native_x1_exclusive=x1,
                                   native_y0=y0, native_y1_exclusive=y1,
                                   center_x_m=float(env_min[0] + ux * cell / 2),
                                   center_y_m=float(env_min[1] + uy * cell / 2),
                                   z_m=obs_z, native_cell_count=(x1 - x0) * (y1 - y0)))
            coord_units.append((ux, uy))
            grid_ij.append((pi, pj))
    units = np.asarray(coord_units, dtype=np.int64)
    ij = np.asarray(grid_ij, dtype=np.int64)
    chosen = fps_indices(units, ij, 30)
    result = []
    for rank, k in enumerate(chosen, 1):
        p = candidates[k].copy()
        p["probe_rank"] = rank
        result.append(p)
    return result, units, ij


def sources_for(house: str, occ: np.ndarray, env_min: np.ndarray, cell: float,
                nav_free: np.ndarray, nav_meta: dict, source_z: float) -> tuple[list[dict], int]:
    nz, nx, ny = occ.shape
    iz = GATE.fine_index(source_z, float(env_min[2]), cell)
    if not 0 <= iz < nz:
        raise SourceHeightContractError(f"source height outside map: {house}")
    valid = np.zeros_like(nav_free, dtype=bool)
    index3d = {}
    for i in range(nav_free.shape[0]):
        for j in range(nav_free.shape[1]):
            if not nav_free[i, j]:
                continue
            x = float(env_min[0] + (i + .5) * .30)
            y = float(env_min[1] + (j + .5) * .30)
            fi = GATE.fine_index(x, float(env_min[0]), cell)
            fj = GATE.fine_index(y, float(env_min[1]), cell)
            if 0 <= fi < nx and 0 <= fj < ny and occ[iz, fi, fj] == 0:
                valid[i, j] = True
                index3d[(i, j)] = (fi, fj)
    ij = np.argwhere(valid).astype(np.int64)
    if len(ij) < 6:
        raise SourceHeightContractError(f"fewer than six source cells at z=0.20: {house}")
    centroid_numerators = ij * len(ij) - ij.sum(axis=0)
    first_d2 = np.sum(centroid_numerators ** 2, axis=1)
    clearance = distance_transform_edt(np.pad(valid, 1, constant_values=False))[1:-1, 1:-1]
    anchors: list[tuple[int, int]] = []
    used: set[tuple[int, int]] = set()
    records: list[dict] = []
    offsets = ((1, 0), (0, 1), (-1, 0), (0, -1))
    for pair in range(1, 4):
        if pair == 1:
            order = sorted(range(len(ij)), key=lambda k: (int(first_d2[k]), int(ij[k, 0]), int(ij[k, 1])))
        else:
            distances = np.stack([np.sum((ij - np.asarray(a)) ** 2, axis=1) for a in anchors], axis=0)
            min_d2 = distances.min(axis=0)
            order = sorted(range(len(ij)), key=lambda k: (-int(min_d2[k]), int(ij[k, 0]), int(ij[k, 1])))
        choice = None
        for k in order:
            anchor = (int(ij[k, 0]), int(ij[k, 1]))
            if anchor in used:
                continue
            options = []
            for rank, (di, dj) in enumerate(offsets):
                neighbor = (anchor[0] + di, anchor[1] + dj)
                if 0 <= neighbor[0] < valid.shape[0] and 0 <= neighbor[1] < valid.shape[1]:
                    if valid[neighbor] and neighbor not in used:
                        options.append((-float(clearance[neighbor]), rank, neighbor))
            if options:
                _, _, partner = min(options)
                choice = (anchor, partner)
                break
        if choice is None:
            raise SourceHeightContractError(f"cannot find three disjoint local pairs at z=0.20: {house}")
        anchor, partner = choice
        anchors.append(anchor)
        used.update((anchor, partner))
        for role, (i, j) in (("anchor", anchor), ("partner", partner)):
            fi, fj = index3d[(i, j)]
            records.append(dict(house=house, pair_id=pair, role=role,
                                source_id=f"pmfs_{i}_{j}", pmfs_i=i, pmfs_j=j,
                                x_m=float(env_min[0] + (i + .5) * .30),
                                y_m=float(env_min[1] + (j + .5) * .30), z_m=source_z,
                                gaden_ix=fi, gaden_iy=fj, gaden_iz=iz,
                                clearance_m=float(clearance[i, j] * .30)))
    assert len(records) == 6 and len(used) == 6
    for pair in range(1, 4):
        a, b = [r for r in records if r["pair_id"] == pair]
        assert abs(math.dist((a["x_m"], a["y_m"]), (b["x_m"], b["y_m"])) - .30) < 1e-6
    return records, len(ij)


def pairwise_stats(points: np.ndarray) -> dict:
    distances = np.asarray([math.dist(points[i], points[j])
                            for i in range(len(points)) for j in range(i + 1, len(points))])
    return {"min_m": float(distances.min()), "q10_m": float(np.quantile(distances, .10)),
            "median_m": float(np.median(distances)), "q90_m": float(np.quantile(distances, .90)),
            "max_m": float(distances.max())}


def coverage(candidate_xy: np.ndarray, selected_xy: np.ndarray) -> dict:
    min_d = np.sqrt(((candidate_xy[:, None, :] - selected_xy[None, :, :]) ** 2).sum(axis=2)).min(axis=1)
    return {"radius_m": float(min_d.max()), "median_nearest_m": float(np.median(min_d)),
            "fraction_within_0p5m": float(np.mean(min_d <= .5)),
            "fraction_within_1p0m": float(np.mean(min_d <= 1.0))}


def h02_legacy(probes: list[dict], valid_units: np.ndarray, valid_pool_ij: np.ndarray, env_min: np.ndarray,
               cell: float, contract: dict) -> tuple[str, str]:
    legacy = contract["probe_points"]
    assert len(legacy) == 30 and len(probes) == 30
    old_ij = {(int(p["pool_x"]), int(p["pool_y"])) for p in legacy}
    new_ij = {(p["pool_i"], p["pool_j"]) for p in probes}
    valid_ij = {(int(i), int(j)) for i, j in valid_pool_ij}
    old_xy = np.asarray([(float(p["center_x_m"]), float(p["center_y_m"])) for p in legacy])
    new_xy = np.asarray([(p["center_x_m"], p["center_y_m"]) for p in probes])
    candidate_xy = np.column_stack((env_min[0] + valid_units[:, 0] * cell / 2,
                                    env_min[1] + valid_units[:, 1] * cell / 2))
    exact = old_ij == new_ij
    decision = ("E1_H02_D1R_CONTRACT_EQUIVALENT_ENOUGH_TO_REUSE" if exact else
                "E1_H02_D1R_CONTRACT_ACCEPTED_AS_LEGACY_ONLY")
    summary = {
        "old_probe_count": len(legacy), "new_probe_count": len(probes),
        "exact_pooled_index_overlap": len(old_ij & new_ij),
        "legacy_navigation_valid_count": len(old_ij & valid_ij),
        "old_only": sorted([list(p) for p in old_ij - new_ij]),
        "new_only": sorted([list(p) for p in new_ij - old_ij]),
        "legacy_pairwise": pairwise_stats(old_xy), "fps_pairwise": pairwise_stats(new_xy),
        "legacy_free_space_coverage": coverage(candidate_xy, old_xy),
        "fps_free_space_coverage": coverage(candidate_xy, new_xy),
        "valid_navigation_candidate_count": len(candidate_xy),
        "decision": decision,
    }
    return decision, "# House02 D1R versus E1 FPS30 geometry\n\n```json\n" + json.dumps(summary, indent=2) + "\n```\n"


def h02_budget(source_panel: list[dict], e0_inventory: list[dict], h02_decision: str,
               probes: list[dict], out: Path) -> tuple[list[dict], int]:
    counts = defaultdict(set)
    for r in e0_inventory:
        if r["house"] != "House02" or r["form"] != "cube_10x83x119":
            continue
        if r["gas_type"] != "10" or r["has_D1R_times"] != "1":
            continue
        key = (r["wind"], round(float(r["x_m"]), 4), round(float(r["y_m"]), 4), round(float(r["z_m"]), 4))
        counts[key].add(r["seed"])
    budget = []
    for house, winds in WINDS.items():
        panel = [r for r in source_panel if r["house"] == house]
        for wind in winds:
            for source in panel:
                key = (wind, round(source["x_m"], 4), round(source["y_m"], 4), round(source["z_m"], 4))
                reusable = len(counts[key]) if house == "House02" else 0
                budget.append(dict(house=house, wind=wind, source_id=source["source_id"],
                                   existing_reextractable_seed_count=reusable,
                                   first_stage_required_seed_count=4,
                                   provisional_new_run_count=max(0, 4 - reusable)))
    rows_tsv(out / "E1_SOURCE_WIND_REUSE_BUDGET.tsv", budget)
    # Technical extraction check is strictly after the geometry-only E1A/B
    # decision; it is never used to alter probe or source selection.
    sample_checks = []
    for wind in WINDS["House02"]:
        candidates = [r for r in e0_inventory if r["house"] == "House02" and r["wind"] == wind
                      and r["form"] == "cube_10x83x119"]
        if not candidates:
            continue
        file = Path(candidates[0]["path"]) / "spatial/concentration.npy"
        cube = np.load(file, mmap_mode="r", allow_pickle=False)
        contract_points = [dict(native_x0=p["native_x0"], native_x1_exclusive=p["native_x1_exclusive"],
                                native_y0=p["native_y0"], native_y1_exclusive=p["native_y1_exclusive"])
                           for p in probes]
        v = EXTRACT.pooled_probe_vector(cube, contract_points)
        if v.shape != (300,) or not np.isfinite(v).all():
            raise ValueError(f"new-probe technical extraction failed: {file}")
        sample_checks.append(dict(wind=wind, input_cube=str(file), input_sha256=sha(file),
                                  output_count=int(v.size), output_sha256=hashlib.sha256(v.tobytes()).hexdigest()))
    rows_tsv(out / "E1_H02_REEXTRACTION_CHECK.tsv", sample_checks)
    total = sum(r["provisional_new_run_count"] for r in budget)
    h02 = sum(r["provisional_new_run_count"] for r in budget if r["house"] == "House02")
    note = ["# E1 provisional fill-in budget (not authorized to execute)", "",
            "Screening depth: 6 sources × 4 independent seeds in each of seven proposed environments.",
            "Baseline with no reuse: 7×6×4 = 168 runs; House01+House03 alone require 96.",
            "House02 legacy Gate1A 300-value vectors cannot be re-probed under E1A.",
            "Only retained House02 10×83×119 cubes with matching source/wind/seed count as reuse.",
            f"House02 geometry decision: `{h02_decision}`.",
            f"House02 provisional new run shortfall: **{h02}**.",
            f"Total provisional new plume runs: **{total}**.",
            "", "This is a geometry/asset budget only; E1 does not authorize any simulation.", ""]
    (out / "E1_PROVISIONAL_FILLIN_BUDGET.md").write_text("\n".join(note))
    return budget, total


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--e0-inventory", type=Path, required=True)
    parser.add_argument("--source-z", type=float, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()
    if args.source_z != .20:
        parser.error("E1 source height is frozen at z=0.20 m for all Houses")
    args.out.mkdir(parents=True, exist_ok=True)
    legacy_path = BASE / "bigreen_gate1a_exact_20260924/gate1a_contract.json"
    legacy = json.loads(legacy_path.read_text())
    e0_inventory = list(csv.DictReader(args.e0_inventory.open(newline=""), delimiter="\t"))
    all_probes, all_sources = [], []
    details = {}
    h02_comparison = None
    inputs = [REPO_GEOMETRY, REPO_EXTRACTOR, legacy_path, args.e0_inventory,
              args.repo / "research/environment_level_benchmark_v0/E1_CROSS_HOUSE_CONTRACT_CHARTER_20260925.md",
              args.repo / "research/environment_level_benchmark_v0/E1_IMPLEMENTATION_RULES_20260925.md",
              Path(__file__)]
    h02_probes = None
    for house in ("House01", "House02", "House03"):
        for wind in WINDS[house]:
            if not (SCENARIOS / house / "gas_simulations" / wind).is_dir():
                raise ValueError(f"missing canonical wind directory: {house} {wind}")
        occ_path = SCENARIOS / house / "OccupancyGrid3D.csv"
        headers, occ = GATE.read_occ(occ_path)
        env_min = np.asarray(headers["env_min(m)"], dtype=float)
        cell = float(headers["cell_size(m)"][0])
        assert abs(cell - .10) < 1e-9
        nav_free, nav_meta, nav_paths = nav_for(house, env_min)
        probes, candidate_units, candidate_ij = probes_for(house, occ, env_min, cell, nav_free, nav_meta, .20)
        try:
            sources, source_candidates = sources_for(house, occ, env_min, cell, nav_free, nav_meta, args.source_z)
        except SourceHeightContractError as exc:
            result = {"decision": "E1_FAIL_CROSS_HOUSE_CONTRACT_NOT_COMPARABLE",
                      "stop_reason": "SOURCE_HEIGHT_CONTRACT_INCOMPATIBLE",
                      "house": house, "detail": str(exc), "new_plume_runs": 0}
            (args.out / "E1_RESULT.json").write_text(json.dumps(result, indent=2) + "\n")
            print(json.dumps(result, indent=2))
            return
        all_probes.extend(probes)
        all_sources.extend(sources)
        inputs.extend([occ_path, *nav_paths])
        details[house] = dict(gaden_num_cells=headers["num_cells"],
                              pmfs_grid_shape=list(nav_free.shape), pmfs_pruned_free_count=int(nav_free.sum()),
                              probe_candidate_count=len(candidate_units), source_candidate_count=source_candidates,
                              source_z_m=args.source_z, observation_z_m=.20)
        if house == "House02":
            h02_probes = probes
            h02_comparison = h02_legacy(probes, candidate_units, candidate_ij, env_min, cell, legacy)
    assert h02_comparison is not None and h02_probes is not None
    h02_decision, comparison_md = h02_comparison
    rows_tsv(args.out / "E1_HOUSE_PROBE_CONTRACTS.tsv", all_probes)
    rows_tsv(args.out / "E1_HOUSE_SOURCE_PANELS.tsv", all_sources)
    (args.out / "E1_H02_LEGACY_COMPATIBILITY.md").write_text(comparison_md)
    role_lines = ["# E1 environment roles (geometry only)", "",
                  "Development: House01 + House02. Whole House03 remains sealed from mechanism discovery.",
                  "House01 same-speed different-family winds: `1,3-2,4_fast`, `2,4-1_fast`.",
                  "House02 reusable candidates: `3,5-1_fast`, `3,5-1_slow`, `4,5-3_slow`.",
                  "House03 sealed same-speed different-family winds: `1-2,5_fast`, `5-3_fast`.",
                  "All seven operator directories exist; source/probe cells are geometry-valid.",
                  "No House03 plume result was read or analyzed during E1.", ""]
    (args.out / "E1_ENVIRONMENT_ROLE_SPLIT.md").write_text("\n".join(role_lines))
    budget, total = h02_budget(all_sources, e0_inventory, h02_decision, h02_probes, args.out)
    decision = "E1_PASS_CROSS_HOUSE_CONTRACT_READY_FOR_FILLIN_DESIGN"
    result = dict(decision=decision, h02_legacy_decision=h02_decision,
                  source_z_m=args.source_z, observation_z_m=.20,
                  new_plume_runs=0, provisional_new_run_count=total,
                  houses=details, role_split={"development": ["House01", "House02"],
                                              "sealed_final": ["House03"]},
                  proposed_environments={house: list(winds) for house, winds in WINDS.items()},
                  budget_rows=len(budget))
    (args.out / "E1_RESULT.json").write_text(json.dumps(result, indent=2) + "\n")
    provenance = ["# E1 geometry provenance", "",
                  "Inputs are 3D occupancy, seed-invariant PMFS pruned navigation geometry, legacy probe contract, and E0 metadata.",
                  "Validated mappings: `prepare_gate1a_bank.py` (`read_occ`, `fine_index`) and PMFS `Grid2DMetadata` (0.30 m cell centers, x + width*y).",
                  "Observation is 2×2 native-grid average at z=0.20 m and D1R iteration indices " + ",".join(map(str, TIMES)) + ".",
                  "No plume values informed source/probe selection or E1A/B. A later technical extraction check reads one pre-existing cube per House02 wind after geometry decision is fixed.",
                  "No GADEN generation executable was called.", "",
                  "House candidate counts: " + json.dumps(details, sort_keys=True), "",
                  "## Input SHA256", ""]
    for path in inputs:
        provenance.append(f"- `{path}`: `{sha(path)}`")
    (args.out / "E1_GEOMETRY_PROVENANCE.md").write_text("\n".join(provenance) + "\n")
    manifest = [f"{sha(path)}  {path.name}" for path in sorted(args.out.iterdir())
                if path.is_file() and path.name != "SHA256SUMS.txt"]
    (args.out / "SHA256SUMS.txt").write_text("\n".join(manifest) + "\n")
    print(json.dumps({"decision": decision, "h02": h02_decision,
                      "provisional_new_run_count": total, "details": details}, indent=2))


if __name__ == "__main__":
    main()
