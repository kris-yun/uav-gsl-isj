#!/usr/bin/env python3
"""Select the frozen 180-source geometry-only MZ M0 bank."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

TRUTH_ID = "pmfs_3_34"
N_SELECT = 180


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-bank", type=Path, required=True)
    ap.add_argument("--out-tsv", type=Path, required=True)
    ap.add_argument("--out-json", type=Path, required=True)
    args = ap.parse_args()

    with args.source_bank.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    if len(rows) != 630:
        raise ValueError(f"expected frozen 630-source parent bank, got {len(rows)}")

    by_id = {r["source_id"]: r for r in rows}
    if len(by_id) != len(rows):
        raise ValueError("duplicate source_id")
    if TRUTH_ID not in by_id:
        raise ValueError(f"truth {TRUTH_ID} missing")

    ids = sorted(by_id)
    xy = np.asarray([[float(by_id[s]["x_m"]), float(by_id[s]["y_m"])] for s in ids])
    centroid = xy.mean(axis=0)

    # First anchor: nearest to geometry centroid, lexical tie-break.
    d0 = np.sum((xy - centroid[None, :]) ** 2, axis=1)
    first = min(range(len(ids)), key=lambda i: (float(d0[i]), ids[i]))

    selected_idx = [first]
    selected_set = {first}
    min_d2 = np.sum((xy - xy[first][None, :]) ** 2, axis=1)

    # Reserve one slot for exact S2 truth unless FPS naturally selects it.
    target_fps_count = N_SELECT if TRUTH_ID == ids[first] else N_SELECT - 1
    while len(selected_idx) < target_fps_count:
        candidates = [i for i in range(len(ids)) if i not in selected_set]
        nxt = max(candidates, key=lambda i: (float(min_d2[i]), tuple(-ord(c) for c in ids[i])))
        selected_idx.append(nxt)
        selected_set.add(nxt)
        d2 = np.sum((xy - xy[nxt][None, :]) ** 2, axis=1)
        min_d2 = np.minimum(min_d2, d2)

    truth_idx = ids.index(TRUTH_ID)
    if truth_idx not in selected_set:
        selected_idx.append(truth_idx)
        selected_set.add(truth_idx)

    while len(selected_idx) < N_SELECT:
        candidates = [i for i in range(len(ids)) if i not in selected_set]
        nxt = max(candidates, key=lambda i: (float(min_d2[i]), tuple(-ord(c) for c in ids[i])))
        selected_idx.append(nxt)
        selected_set.add(nxt)
        d2 = np.sum((xy - xy[nxt][None, :]) ** 2, axis=1)
        min_d2 = np.minimum(min_d2, d2)

    if len(selected_idx) != N_SELECT or len(selected_set) != N_SELECT:
        raise RuntimeError("selection cardinality drift")

    fps_order = {ids[idx]: order + 1 for order, idx in enumerate(selected_idx)}
    selected_rows = []
    for sid in sorted(fps_order):
        r = dict(by_id[sid])
        r["fps_order"] = fps_order[sid]
        selected_rows.append(r)

    args.out_tsv.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys()) + ["fps_order"]
    with args.out_tsv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t")
        w.writeheader()
        w.writerows(selected_rows)

    coords = np.asarray([[float(r["x_m"]), float(r["y_m"])] for r in selected_rows])
    meta = {
        "mode": "MZ_M0_GEOMETRY_ONLY_SOURCE_SELECTION",
        "parent_source_bank": str(args.source_bank),
        "parent_source_bank_sha256": sha256(args.source_bank),
        "parent_source_count": len(rows),
        "selected_source_count": len(selected_rows),
        "truth_source_id": TRUTH_ID,
        "truth_included": TRUTH_ID in fps_order,
        "selection": "deterministic_farthest_point_xy_with_truth_reserved",
        "first_anchor_source_id": ids[first],
        "source_ids_sorted": [r["source_id"] for r in selected_rows],
        "bbox_xy_m": {
            "min": coords.min(axis=0).tolist(),
            "max": coords.max(axis=0).tolist(),
        },
    }
    args.out_json.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({
        "selected": len(selected_rows),
        "truth": TRUTH_ID,
        "first_anchor": ids[first],
        "out_tsv": str(args.out_tsv),
        "out_json": str(args.out_json),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
