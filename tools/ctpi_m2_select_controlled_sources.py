#!/usr/bin/env python3
"""Freeze CTPI M2 controlled-source carriers and route assignments from bank-only data.

This tool deliberately reads only `carrier_ids` and `q_raw` from the already
frozen route diagnostic. It never reads realized observation outcomes.

The quadtree center is used only as a 2-D carrier-region descriptor for spatial
coverage. It is NOT a physical GADEN source placement. The generation runner
must resolve the selected carrier through the frozen
PF_DEI_V3_REGION_PLACEMENT_V1 reserved placement rows.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import numpy as np

CONTRACT = "CTPI_M2_SOURCE_SELECTION_V3"
HOUSES = ("H01", "H02", "H03")
SETS = ("M2_CAL", "M2_CONFIRM")
MEMBER_COUNT = 8


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hash64(text: str) -> int:
    return int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "big")


def parse_region_center(carrier_id: str) -> tuple[float, float]:
    match = re.fullmatch(r"quadtree_(-?\d+)_(-?\d+)_(\d+)_(\d+)", carrier_id)
    if match is None:
        raise ValueError(f"CTPI_SOURCE_ID:{carrier_id}")
    x, y, width, height = map(float, match.groups())
    return x + width / 2.0, y + height / 2.0


def normalize(values: np.ndarray) -> np.ndarray:
    value = np.asarray(values, dtype=np.float64)
    span = float(np.max(value) - np.min(value))
    return np.zeros_like(value) if span <= 0.0 else (value - np.min(value)) / span


def member_count_from_q(q: np.ndarray) -> np.ndarray:
    raw = np.asarray(q, dtype=np.float64) * 9.0 - 0.5
    member_count = np.rint(raw).astype(np.int64)
    if (
        np.max(np.abs(raw - member_count)) > 1.0e-9
        or np.any(member_count < 0)
        or np.any(member_count > MEMBER_COUNT)
    ):
        raise RuntimeError("CTPI_QRAW_NOT_FINITE8_JEFFREYS")
    return member_count


def select_twenty(
    carrier_ids: np.ndarray,
    q_raw: np.ndarray,
    house: str,
) -> tuple[list[int], np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    centers = np.asarray([parse_region_center(value) for value in carrier_ids], dtype=np.float64)
    mean_probability = np.mean(q_raw, axis=(0, 2))
    member_count = member_count_from_q(q_raw)
    richness = np.asarray(
        [len(np.unique(member_count[:, source, :])) for source in range(len(carrier_ids))],
        dtype=np.int64,
    )
    features = np.column_stack(
        (
            normalize(centers[:, 0]),
            normalize(centers[:, 1]),
            normalize(mean_probability),
            normalize(richness),
        )
    )
    hashes = [hash64(f"{CONTRACT}/FPS/{house}/{carrier_id}") for carrier_id in carrier_ids]

    low_candidates = np.flatnonzero(
        np.isclose(mean_probability, np.min(mean_probability), rtol=0.0, atol=1.0e-15)
    )
    high_candidates = np.flatnonzero(
        np.isclose(mean_probability, np.max(mean_probability), rtol=0.0, atol=1.0e-15)
    )
    low = int(min(low_candidates, key=lambda index: hashes[int(index)]))
    high = int(min(high_candidates, key=lambda index: hashes[int(index)]))
    chosen = [low]
    if high != low:
        chosen.append(high)

    minimum_distance = np.full(len(carrier_ids), np.inf, dtype=np.float64)
    for source in chosen:
        minimum_distance = np.minimum(
            minimum_distance, np.linalg.norm(features - features[source], axis=1)
        )

    while len(chosen) < 20:
        eligible = richness >= 3
        eligible[np.asarray(chosen, dtype=np.int64)] = False
        if not np.any(eligible):
            eligible = np.ones(len(carrier_ids), dtype=np.bool_)
            eligible[np.asarray(chosen, dtype=np.int64)] = False
        best_distance = float(np.max(minimum_distance[eligible]))
        candidates = np.flatnonzero(
            eligible
            & np.isclose(minimum_distance, best_distance, rtol=0.0, atol=1.0e-15)
        )
        selected = int(min(candidates, key=lambda index: hashes[int(index)]))
        chosen.append(selected)
        minimum_distance = np.minimum(
            minimum_distance, np.linalg.norm(features - features[selected], axis=1)
        )

    return chosen, centers, mean_probability, richness, features


def matched_split(
    carrier_ids: np.ndarray,
    features: np.ndarray,
    chosen: list[int],
    house: str,
) -> tuple[list[int], list[int]]:
    remaining = set(chosen)
    pairs: list[tuple[int, int]] = []
    while remaining:
        ordered = sorted(remaining)
        best: tuple[tuple[float, int], int, int] | None = None
        for left_pos, left in enumerate(ordered):
            for right in ordered[left_pos + 1 :]:
                distance = float(np.linalg.norm(features[left] - features[right]))
                key = (
                    round(distance, 15),
                    hash64(f"{CONTRACT}/PAIR/{house}/{carrier_ids[left]}/{carrier_ids[right]}"),
                )
                if best is None or key < best[0]:
                    best = (key, left, right)
        if best is None:
            raise RuntimeError("CTPI_SOURCE_MATCHING")
        _, left, right = best
        remaining.remove(left)
        remaining.remove(right)
        left_hash = hash64(f"{CONTRACT}/SPLIT/{house}/{carrier_ids[left]}")
        right_hash = hash64(f"{CONTRACT}/SPLIT/{house}/{carrier_ids[right]}")
        pairs.append((left, right) if left_hash < right_hash else (right, left))

    cal = sorted(
        [left for left, _ in pairs],
        key=lambda index: hash64(f"{CONTRACT}/ORDER/{house}/CAL/{carrier_ids[index]}"),
    )
    confirm = sorted(
        [right for _, right in pairs],
        key=lambda index: hash64(
            f"{CONTRACT}/ORDER/{house}/CONFIRM/{carrier_ids[index]}"
        ),
    )
    return cal, confirm


def assign_routes(
    carrier_ids: np.ndarray,
    q_raw: np.ndarray,
    selected: list[int],
    house: str,
    set_name: str,
) -> tuple[tuple[int, ...], np.ndarray, list[int]]:
    pair_counts = np.zeros((10, 10, 9), dtype=np.int64)
    for source_pos, source_index in enumerate(selected):
        for route in range(10):
            member_count = member_count_from_q(q_raw[route, source_index, :])
            pair_counts[source_pos, route] = np.bincount(member_count, minlength=9)

    global_count = np.sum(pair_counts, axis=(0, 1)).astype(np.float64)
    rare_weight = 1.0 / np.sqrt(global_count + 1.0)
    pair_score = np.tensordot(pair_counts, rare_weight, axes=([2], [0]))
    pair_score += 0.05 * np.sum(pair_counts > 0, axis=2)
    for source_pos, source_index in enumerate(selected):
        for route in range(10):
            pair_score[source_pos, route] += (
                hash64(
                    f"{CONTRACT}/ROUTE/{house}/{set_name}/"
                    f"{carrier_ids[source_index]}/{route}"
                )
                % 1_000_000
            ) * 1.0e-12

    # Exact 10x10 assignment by bit-mask dynamic programming.  No scipy/runtime
    # dependency and deterministic lexicographic tie handling.
    dynamic: dict[int, tuple[float, tuple[int, ...]]] = {0: (0.0, ())}
    for source_pos in range(10):
        next_dynamic: dict[int, tuple[float, tuple[int, ...]]] = {}
        for mask, (total, routes) in dynamic.items():
            for route in range(10):
                if (mask >> route) & 1:
                    continue
                new_mask = mask | (1 << route)
                new_total = total + float(pair_score[source_pos, route])
                new_routes = routes + (route,)
                old = next_dynamic.get(new_mask)
                if (
                    old is None
                    or new_total > old[0] + 1.0e-12
                    or (
                        abs(new_total - old[0]) <= 1.0e-12
                        and new_routes < old[1]
                    )
                ):
                    next_dynamic[new_mask] = (new_total, new_routes)
        dynamic = next_dynamic

    routes = dynamic[(1 << 10) - 1][1]
    aggregate = np.zeros(9, dtype=np.int64)
    world_levels: list[int] = []
    for source_pos, route in enumerate(routes):
        aggregate += pair_counts[source_pos, route]
        world_levels.append(int(np.count_nonzero(pair_counts[source_pos, route])))
    return routes, aggregate, world_levels


def build(stage1_root: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "contract": CONTRACT,
        "uses_observation_outcomes": False,
        "selection_inputs": ["carrier_ids", "q_raw"],
        "carrier_center_semantics": "REGION_DESCRIPTOR_ONLY_NOT_PHYSICAL_SOURCE_PLACEMENT",
        "physical_placement_requirement": "RESOLVE_FROM_PF_DEI_V3_REGION_PLACEMENT_V1_RESERVED_ROWS",
        "houses": {},
    }
    pooled = {
        "M2_CAL": np.zeros(9, dtype=np.int64),
        "M2_CONFIRM": np.zeros(9, dtype=np.int64),
    }

    for house in HOUSES:
        path = stage1_root / f"{house}_FACTORIAL.npz"
        if not path.is_file():
            raise FileNotFoundError(path)
        # Deliberately access only these two keys.  Realized `observed` stored in
        # the same historical archive is outside this selection procedure.
        with np.load(path, allow_pickle=False) as archive:
            carrier_ids = np.asarray(archive["carrier_ids"]).astype(str)
            q_raw = np.asarray(archive["q_raw"], dtype=np.float64)
        if q_raw.shape != (10, len(carrier_ids), 15):
            raise RuntimeError(f"CTPI_QRAW_SHAPE:{house}:{q_raw.shape}")

        chosen, centers, frequency, richness, features = select_twenty(
            carrier_ids, q_raw, house
        )
        cal, confirm = matched_split(carrier_ids, features, chosen, house)
        house_record: dict[str, Any] = {
            "input_npz_sha256": sha256_file(path),
            "carrier_count": int(len(carrier_ids)),
            "selected_count": 20,
            "cal_confirm_source_disjoint": not bool(
                set(carrier_ids[cal]) & set(carrier_ids[confirm])
            ),
            "sets": {},
        }

        for set_name, selected in (("M2_CAL", cal), ("M2_CONFIRM", confirm)):
            routes, histogram, world_levels = assign_routes(
                carrier_ids, q_raw, selected, house, set_name
            )
            pooled[set_name] += histogram
            worlds = []
            for ordinal, (source_index, route) in enumerate(zip(selected, routes)):
                # Reserved placement member is a deterministic, balanced nuisance
                # draw. The actual xyz must be read from the placement manifest by
                # the generation runner and frozen into the world manifest.
                reserved_member = ordinal % 4
                worlds.append(
                    {
                        "ordinal": ordinal,
                        "controlled_carrier_id": carrier_ids[source_index],
                        "region_descriptor_center_x": float(centers[source_index, 0]),
                        "region_descriptor_center_y": float(centers[source_index, 1]),
                        "bank_mean_event_probability": float(frequency[source_index]),
                        "bank_global_k_richness": int(richness[source_index]),
                        "route_index": int(route),
                        "reserved_placement_member": int(reserved_member),
                    }
                )
            house_record["sets"][set_name] = {
                "source_count": 10,
                "routes_unique": len(set(routes)) == 10,
                "expected_k_histogram": histogram.tolist(),
                "expected_k_levels": sorted(
                    int(value) for value in np.flatnonzero(histogram)
                ),
                "min_world_k_levels": int(min(world_levels)),
                "mean_world_k_levels": float(np.mean(world_levels)),
                "worlds": worlds,
            }
        result["houses"][house] = house_record

    result["pooled_expected_k_histogram"] = {
        key: value.tolist() for key, value in pooled.items()
    }
    result["checks"] = {
        "all_house_sets_cover_k_0_to_8": all(
            result["houses"][house]["sets"][set_name]["expected_k_levels"]
            == list(range(9))
            for house in HOUSES
            for set_name in SETS
        ),
        "all_house_sets_have_10_unique_routes": all(
            result["houses"][house]["sets"][set_name]["routes_unique"]
            for house in HOUSES
            for set_name in SETS
        ),
        "all_house_cal_confirm_sources_disjoint": all(
            result["houses"][house]["cal_confirm_source_disjoint"]
            for house in HOUSES
        ),
        "pooled_cal_min_expected_k_count_ge_15": int(np.min(pooled["M2_CAL"])) >= 15,
        "pooled_confirm_min_expected_k_count_ge_15": int(
            np.min(pooled["M2_CONFIRM"])
        )
        >= 15,
    }
    result["pass"] = all(result["checks"].values())
    result["verdict"] = (
        "CTPI_M2_SOURCE_SELECTION_FREEZE=PASS"
        if result["pass"]
        else "CTPI_M2_SOURCE_SELECTION_FREEZE=FAIL"
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage1-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = build(args.stage1_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(output, indent=2, sort_keys=True) + "\n"
    args.output.write_text(text, encoding="utf-8")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    args.output.with_suffix(args.output.suffix + ".sha256").write_text(
        f"{digest}  {args.output.name}\n", encoding="ascii"
    )
    print(output["verdict"])
    print(f"CTPI_M2_SOURCE_SELECTION_SHA256={digest}")
    return 0 if output["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
