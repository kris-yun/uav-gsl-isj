#!/usr/bin/env python3
"""Export truth-blind spatial stop identities for V5 cumulative replay.

Uses the already-audited V4 archive parser. No source truth, localization
error, ON result, route identifier, or performance field is opened.
"""
from __future__ import annotations
import argparse, csv
from pathlib import Path
import numpy as np

import materialize_v4_truthblind_contexts as m4


def nearest_free_cell(snapshot: Path, xy):
    rows = m4._geometry_rows(snapshot)
    free = [r for r in rows if r["occupancy"] == "Free"]
    q = np.asarray([[float(r["x"]), float(r["y"])] for r in free], dtype=float)
    target = np.asarray(xy, dtype=float)
    dist = np.linalg.norm(q - target[None, :], axis=1)
    k = int(np.argmin(dist))
    if float(dist[k]) > 0.22:
        raise ValueError(f"stop does not map to free PMFS cell: d={float(dist[k])}")
    row = free[k]
    gi, gj = int(row["grid_i"]), int(row["grid_j"])
    return gi, gj, f"{gi}:{gj}", float(dist[k])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive-root", type=Path, required=True)
    ap.add_argument("--out-csv", type=Path, required=True)
    ap.add_argument("--houses", nargs="+", choices=["H01","H02","H03"],
                    default=["H01","H02","H03"])
    ap.add_argument("--seeds", nargs="+", type=int, default=list(range(10)))
    a = ap.parse_args()
    reverse = {v:k for k,v in m4.HOUSE_MAP.items()}
    rows=[]
    for house in a.houses:
        for seed in sorted(set(a.seeds)):
            run=m4._discover_run(a.archive_root, reverse[house], seed)
            specs,_=m4.reconstruct_context_specs(run)
            for spec in specs:
                snapshot=run.context_bank / f"source_update_{spec.update_id:04d}"
                for j,xy in enumerate(spec.stop_xy):
                    gi,gj,key,d=nearest_free_cell(snapshot,xy)
                    rows.append({
                        "context_id":spec.context_id, "house":house, "seed":seed,
                        "update_id":spec.update_id, "stop_index":j,
                        "x":format(xy[0],".17g"), "y":format(xy[1],".17g"),
                        "grid_i":gi, "grid_j":gj, "stop_key":key,
                        "nearest_distance":format(d,".17g"),
                    })
    a.out_csv.parent.mkdir(parents=True, exist_ok=True)
    fields=list(rows[0].keys())
    with a.out_csv.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
    print(f"V5_STOP_MANIFEST PASS rows={len(rows)} runs={len(set((r['house'],r['seed']) for r in rows))}")


if __name__=="__main__":
    main()
