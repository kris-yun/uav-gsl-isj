#!/usr/bin/env python3
"""Freeze R3A sources and prospective runs from geometry and context metadata only."""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
from pathlib import Path

GENERATOR_SHA = "ec840fa1f87fca7b7d3af3014895a642562acaacb86e5950ddb07e732adc3688"
ANCHOR_MIN, ANCHOR_MAX = .9, 1.8
MIN_CLEARANCE, MIN_3D_CLEARANCE, MIN_OTHER_OLD, MIN_NEW_NEW = .42, .2, .9, .9
TARGET_ANCHOR_DISTANCE = 1.0


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t", lineterminator="\n")
        w.writeheader(); w.writerows(rows)


def choose(rows: list[dict], house: str, anchors: list[str]) -> tuple[dict, dict, dict]:
    pools = []
    for anchor in anchors:
        p = [r for r in rows if r["house"] == house and r["anchor"] == anchor
             and r["exposed"] == "0" and ANCHOR_MIN <= float(r["anchor_distance_m"]) <= ANCHOR_MAX
             and float(r["2d_clearance_m"]) >= MIN_CLEARANCE
             and float(r["3d_clearance_m"]) >= MIN_3D_CLEARANCE
             and float(r["other_old_distance_m"]) >= MIN_OTHER_OLD]
        assert p, f"no eligible candidate for {house} {anchor}"
        pools.append(p)
    ranked = []
    for a, b in itertools.product(*pools):
        if a["source_id"] == b["source_id"]:
            continue
        sep = math.hypot(float(a["x_m"]) - float(b["x_m"]), float(a["y_m"]) - float(b["y_m"]))
        if sep < MIN_NEW_NEW:
            continue
        da, db = float(a["anchor_distance_m"]), float(b["anchor_distance_m"])
        key = (round(abs(da - TARGET_ANCHOR_DISTANCE) + abs(db - TARGET_ANCHOR_DISTANCE), 8),
               round(max(abs(da - TARGET_ANCHOR_DISTANCE), abs(db - TARGET_ANCHOR_DISTANCE)), 8),
               -round(min(float(a["2d_clearance_m"]), float(b["2d_clearance_m"])), 6),
               -round(sep, 6), a["source_id"], b["source_id"])
        ranked.append((key, a, b, sep))
    assert ranked, f"no valid joint pair for {house}"
    _, a, b, sep = min(ranked)
    return a, b, {"anchor_1_candidates": len(pools[0]), "anchor_2_candidates": len(pools[1]),
                  "valid_joint_pairs": len(ranked), "selected_new_new_distance_m": round(sep, 6)}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    census_path = a.repo / "evidence/ocb_r2/r3a_geometry/R3A_GEOMETRY_CENSUS.json"
    cells_path = census_path.with_name("R3A_ELIGIBLE_CELLS.tsv")
    s2_path = a.repo / "evidence/ocb_r2/OCB_R2_S2_DISCOVERY_RUNLIST_32.tsv"
    s2x_path = a.repo / "evidence/ocb_r2/s2x/OCB_R2_S2X_RUNLIST_32.tsv"
    master_path = a.repo / "evidence/ocb_r2/OCB_R2_MASTER_MANIFEST_96.tsv"
    census = json.loads(census_path.read_text())
    cells, s2, s2x, master = read_tsv(cells_path), read_tsv(s2_path), read_tsv(s2x_path), read_tsv(master_path)
    assert sha(s2_path) == census["inputs"]["s2_runlist_sha256"]
    assert {r["frozen_generator_sha256"] for r in s2x} == {GENERATOR_SHA}
    old_seeds = {int(r["master_seed"]) for r in master + s2x}
    anchors = {h: list(census["houses"][h]["original_sources"]) for h in ("House01", "House02")}
    selected, selection_audit = [], {}
    for house in ("House01", "House02"):
        a1, a2, audit = choose(cells, house, anchors[house])
        selection_audit[house] = audit
        for idx, r in enumerate((a1, a2), 1):
            selected.append({"house": house, "new_source_index": idx, "source_id": r["source_id"],
                "anchor_source_id": r["anchor"], "pmfs_i": r["i"], "pmfs_j": r["j"],
                "source_x": r["x_m"], "source_y": r["y_m"], "source_z": r["z_m"],
                "anchor_distance_m": r["anchor_distance_m"], "other_old_distance_m": r["other_old_distance_m"],
                "source_clearance_2d_m": r["2d_clearance_m"],
                "source_clearance_3d_m": r["3d_clearance_m"], "selection_basis": "GEOMETRY_ONLY"})
    contexts = {int(r["config_index"]): r for r in s2 if int(r["replicate_index"]) == 1}
    assert len(contexts) == 8
    runs = []
    for ci in range(8):
        context = contexts[ci]
        house_sources = [r for r in selected if r["house"] == context["house"]]
        assert len(house_sources) == 2
        for source in house_sources:
            ni = source["new_source_index"]
            for rep in range(1, 5):
                seed = 2026920000 + 100 * ci + 10 * ni + rep
                run_id = f"ocb_r2_r3a_x{ci:02d}_n{ni}_r{rep:02d}"
                runs.append({"run_id": run_id,
                    "context_index": ci, "house": context["house"], "source_id": source["source_id"],
                    "source_x": source["source_x"], "source_y": source["source_y"], "source_z": source["source_z"],
                    "wind_id": context["wind_id"], "wind_asset": context["wind_asset"],
                    "occupancy": context["occupancy"], "gas_type": context["gas_type"],
                    "master_seed": seed, "frozen_generator_sha256": GENERATOR_SHA,
                    "parent_s2_config_index": ci, "parent_s2_original_launch_sha256": context["original_launch_sha256"],
                    "vm_output_path": f"/home/zyc/ocb_r2_r3_multisource/{run_id}",
                    "host_archive_path": f"C:\\GADEN_OCB_R2_ARCHIVE\\r3_multisource\\{run_id}",
                    "phase": "PROSPECTIVE_DISCOVERY_DESIGN", "status": "DESIGN_ONLY_NOT_AUTHORIZED_TO_RUN"})
    assert len(runs) == 64 and len({r["run_id"] for r in runs}) == 64
    seeds = {r["master_seed"] for r in runs}
    assert len(seeds) == 64 and not (seeds & old_seeds)
    a.out.mkdir(parents=True, exist_ok=True)
    write_tsv(a.out / "R3A_NEW_SOURCES_4.tsv", selected)
    write_tsv(a.out / "R3A_PROSPECTIVE_RUNLIST_64.tsv", runs)
    audit = {"status": "R3A_GEOMETRY_DESIGN_ONLY", "source_selection": selection_audit,
        "thresholds": {"anchor_distance_min_m": ANCHOR_MIN, "anchor_distance_max_m": ANCHOR_MAX,
                       "target_anchor_distance_m": TARGET_ANCHOR_DISTANCE, "minimum_clearance_2d_m": MIN_CLEARANCE,
                       "minimum_clearance_3d_m": MIN_3D_CLEARANCE,
                       "minimum_other_old_distance_m": MIN_OTHER_OLD, "minimum_new_new_distance_m": MIN_NEW_NEW},
        "inputs": {"geometry_census_sha256": sha(census_path), "eligible_cells_sha256": sha(cells_path),
                   "s2_runlist_sha256": sha(s2_path), "s2x_runlist_sha256": sha(s2x_path),
                   "master_manifest_96_sha256": sha(master_path),
                   "generator_sha256": GENERATOR_SHA},
        "outputs": {"source_panel_sha256": sha(a.out / "R3A_NEW_SOURCES_4.tsv"),
                    "runlist_sha256": sha(a.out / "R3A_PROSPECTIVE_RUNLIST_64.tsv")},
        "run_count": len(runs), "seed_count": len(seeds), "seed_overlap_with_discovery": 0}
    (a.out / "R3A_DESIGN_AUDIT.json").write_bytes((json.dumps(audit, indent=2, sort_keys=True) + "\n").encode())
    print(json.dumps({"selected": selected, "audit": audit}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
