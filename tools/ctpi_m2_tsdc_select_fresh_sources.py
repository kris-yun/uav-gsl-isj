#!/usr/bin/env python3
"""Deterministically select 30 fresh TSDC confirmatory carrier/route pairs.

Scientific boundary: this selector reads only the frozen predictive-bank fields
`carrier_ids` and `q_raw`, plus a pre-outcome used-asset registry. It never reads
realized observation outcomes, source truth, localization error, or planner data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import numpy as np

CONTRACT = "CTPI_M2_TSDC_FRESH_SOURCE_SELECTION_V0"
REGISTRY_CONTRACT = "CTPI_M2_TSDC_USED_ASSET_REGISTRY_V0"
HOUSES = ("H01", "H02", "H03")
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
        raise ValueError(f"TSDC_FRESH_SOURCE_ID:{carrier_id}")
    x, y, width, height = map(float, match.groups())
    return x + width / 2.0, y + height / 2.0


def normalize(values: np.ndarray) -> np.ndarray:
    value = np.asarray(values, dtype=np.float64)
    span = float(np.max(value) - np.min(value))
    return np.zeros_like(value) if span <= 0.0 else (value - np.min(value)) / span


def member_count_from_q(q_raw: np.ndarray) -> np.ndarray:
    raw = np.asarray(q_raw, dtype=np.float64) * 9.0 - 0.5
    member_count = np.rint(raw).astype(np.int64)
    if (
        np.max(np.abs(raw - member_count)) > 1.0e-9
        or np.any(member_count < 0)
        or np.any(member_count > MEMBER_COUNT)
    ):
        raise RuntimeError("TSDC_FRESH_QRAW_NOT_FINITE8_JEFFREYS")
    return member_count


def select_ten(
    carrier_ids: np.ndarray,
    q_raw: np.ndarray,
    house: str,
    used_carriers: set[str],
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
    eligible = np.asarray([value not in used_carriers for value in carrier_ids], dtype=np.bool_)
    if int(np.count_nonzero(eligible)) < 10:
        raise RuntimeError(f"TSDC_FRESH_INSUFFICIENT_UNUSED_CARRIERS:{house}")
    hashes = [hash64(f"{CONTRACT}/FPS/{house}/{carrier_id}") for carrier_id in carrier_ids]

    chosen: list[int] = []
    for target in (np.min(mean_probability[eligible]), np.max(mean_probability[eligible])):
        candidates = np.flatnonzero(
            eligible & np.isclose(mean_probability, target, rtol=0.0, atol=1.0e-15)
        )
        selected = int(min(candidates, key=lambda index: hashes[int(index)]))
        if selected not in chosen:
            chosen.append(selected)

    minimum_distance = np.full(len(carrier_ids), np.inf, dtype=np.float64)
    for source in chosen:
        minimum_distance = np.minimum(
            minimum_distance, np.linalg.norm(features - features[source], axis=1)
        )

    while len(chosen) < 10:
        allowed = eligible.copy()
        allowed[np.asarray(chosen, dtype=np.int64)] = False
        rich_allowed = allowed & (richness >= 3)
        if np.any(rich_allowed):
            allowed = rich_allowed
        best_distance = float(np.max(minimum_distance[allowed]))
        candidates = np.flatnonzero(
            allowed & np.isclose(minimum_distance, best_distance, rtol=0.0, atol=1.0e-15)
        )
        selected = int(min(candidates, key=lambda index: hashes[int(index)]))
        chosen.append(selected)
        minimum_distance = np.minimum(
            minimum_distance, np.linalg.norm(features - features[selected], axis=1)
        )
    return chosen, centers, mean_probability, richness, features


def assign_unique_routes(
    carrier_ids: np.ndarray,
    q_raw: np.ndarray,
    selected: list[int],
    house: str,
) -> tuple[tuple[int, ...], np.ndarray, list[int]]:
    pair_counts = np.zeros((10, 10, 9), dtype=np.int64)
    for source_pos, source_index in enumerate(selected):
        for route in range(10):
            k = member_count_from_q(q_raw[route, source_index, :])
            pair_counts[source_pos, route] = np.bincount(k, minlength=9)

    global_count = np.sum(pair_counts, axis=(0, 1)).astype(np.float64)
    rare_weight = 1.0 / np.sqrt(global_count + 1.0)
    pair_score = np.tensordot(pair_counts, rare_weight, axes=([2], [0]))
    pair_score += 0.05 * np.sum(pair_counts > 0, axis=2)
    for source_pos, source_index in enumerate(selected):
        for route in range(10):
            pair_score[source_pos, route] += (
                hash64(f"{CONTRACT}/ROUTE/{house}/{carrier_ids[source_index]}/{route}")
                % 1_000_000
            ) * 1.0e-12

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
                    or (abs(new_total - old[0]) <= 1.0e-12 and new_routes < old[1])
                ):
                    next_dynamic[new_mask] = (new_total, new_routes)
        dynamic = next_dynamic

    routes = dynamic[(1 << 10) - 1][1]
    histogram = np.zeros(9, dtype=np.int64)
    world_levels: list[int] = []
    for source_pos, route in enumerate(routes):
        histogram += pair_counts[source_pos, route]
        world_levels.append(int(np.count_nonzero(pair_counts[source_pos, route])))
    return routes, histogram, world_levels


def build(stage1_root: Path, registry_path: Path) -> dict[str, Any]:
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    if registry.get("contract") != REGISTRY_CONTRACT:
        raise RuntimeError("TSDC_FRESH_REGISTRY_CONTRACT")

    result: dict[str, Any] = {
        "contract": CONTRACT,
        "uses_observation_outcomes": False,
        "selection_inputs": ["carrier_ids", "q_raw", "used_asset_registry"],
        "used_asset_registry_sha256": sha256_file(registry_path),
        "carrier_center_semantics": "REGION_DESCRIPTOR_ONLY_NOT_PHYSICAL_SOURCE_PLACEMENT",
        "physical_placement_requirement": "RESOLVE_FROM_PF_DEI_V3_REGION_PLACEMENT_V1_RESERVED_ROWS",
        "houses": {},
    }
    pooled = np.zeros(9, dtype=np.int64)

    for house in HOUSES:
        used = set(str(value) for value in registry["used_carriers_by_house"][house])
        path = stage1_root / f"{house}_FACTORIAL.npz"
        if not path.is_file():
            raise FileNotFoundError(path)
        with np.load(path, allow_pickle=False) as archive:
            carrier_ids = np.asarray(archive["carrier_ids"]).astype(str)
            q_raw = np.asarray(archive["q_raw"], dtype=np.float64)
        if q_raw.shape != (10, len(carrier_ids), 15):
            raise RuntimeError(f"TSDC_FRESH_QRAW_SHAPE:{house}:{q_raw.shape}")

        selected, centers, frequency, richness, _ = select_ten(
            carrier_ids, q_raw, house, used
        )
        routes, histogram, world_levels = assign_unique_routes(
            carrier_ids, q_raw, selected, house
        )
        pooled += histogram
        worlds = []
        for ordinal, (source_index, route) in enumerate(zip(selected, routes)):
            worlds.append(
                {
                    "ordinal": ordinal,
                    "controlled_carrier_id": carrier_ids[source_index],
                    "region_descriptor_center_x": float(centers[source_index, 0]),
                    "region_descriptor_center_y": float(centers[source_index, 1]),
                    "bank_mean_event_probability": float(frequency[source_index]),
                    "bank_global_k_richness": int(richness[source_index]),
                    "route_index": int(route),
                    "reserved_placement_member": int(ordinal % 4),
                }
            )
        result["houses"][house] = {
            "input_npz_sha256": sha256_file(path),
            "carrier_count": int(len(carrier_ids)),
            "used_carriers_excluded_count": int(len(used)),
            "fresh_source_count": 10,
            "routes_unique": len(set(routes)) == 10,
            "expected_k_histogram": histogram.tolist(),
            "expected_k_levels": np.flatnonzero(histogram).astype(int).tolist(),
            "min_world_k_levels": int(min(world_levels)),
            "mean_world_k_levels": float(np.mean(world_levels)),
            "worlds": worlds,
        }

    result["pooled_expected_k_histogram"] = pooled.tolist()
    result["checks"] = {
        "world_count_30": sum(len(result["houses"][h]["worlds"]) for h in HOUSES) == 30,
        "all_fresh_vs_registry": all(
            not (
                {w["controlled_carrier_id"] for w in result["houses"][h]["worlds"]}
                & set(registry["used_carriers_by_house"][h])
            )
            for h in HOUSES
        ),
        "all_house_routes_unique": all(result["houses"][h]["routes_unique"] for h in HOUSES),
        "all_house_cover_k_0_to_8": all(
            result["houses"][h]["expected_k_levels"] == list(range(9)) for h in HOUSES
        ),
        "pooled_covers_k_0_to_8": np.flatnonzero(pooled).tolist() == list(range(9)),
        "pooled_min_expected_k_count_ge_10": int(np.min(pooled)) >= 10,
    }
    result["pass"] = all(result["checks"].values())
    result["verdict"] = (
        "CTPI_M2_TSDC_FRESH_SOURCE_SELECTION=PASS"
        if result["pass"]
        else "CTPI_M2_TSDC_FRESH_SOURCE_SELECTION=FAIL"
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage1-root", type=Path, required=True)
    parser.add_argument("--used-asset-registry", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = build(args.stage1_root, args.used_asset_registry)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(output, indent=2, sort_keys=True) + "\n").encode("utf-8")
    args.output.write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    args.output.with_suffix(args.output.suffix + ".sha256").write_text(
        f"{digest}  {args.output.name}\n", encoding="ascii"
    )
    print(output["verdict"])
    print(f"CTPI_M2_TSDC_FRESH_SOURCE_SELECTION_SHA256={digest}")
    return 0 if output["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
