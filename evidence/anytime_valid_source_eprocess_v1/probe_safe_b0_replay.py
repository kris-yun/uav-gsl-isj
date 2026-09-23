#!/usr/bin/env python3
"""SAFE-B0 core e-process replay engine.

This script contains only the statistical core.  Dataset/schema extraction is
kept separate so the frozen R1 archive can be audited before any assumptions
about column names or map indexing are made.

Input long CSV:
    event_index,candidate_id,y,h

Optional:
    stop_id

Rows must contain every candidate for every event.
"""

from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path

EPS = 1e-6


def clip_p(x: float) -> float:
    return min(1.0 - EPS, max(EPS, float(x)))


def read_long(path: Path):
    events = defaultdict(list)
    stop_by_event = {}
    y_by_event = {}
    with path.open(newline="", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        need = {"event_index", "candidate_id", "y", "h"}
        if not need.issubset(set(rd.fieldnames or [])):
            raise RuntimeError(f"missing required columns: {sorted(need)}")
        for row in rd:
            t = int(row["event_index"])
            s = row["candidate_id"]
            y = int(row["y"])
            h = clip_p(float(row["h"]))
            if y not in (0, 1):
                raise RuntimeError("y must be 0/1")
            events[t].append((s, h))
            if t in y_by_event and y_by_event[t] != y:
                raise RuntimeError(f"inconsistent y at event {t}")
            y_by_event[t] = y
            if "stop_id" in row and row["stop_id"] != "":
                sid = row["stop_id"]
                if t in stop_by_event and stop_by_event[t] != sid:
                    raise RuntimeError(f"inconsistent stop_id at event {t}")
                stop_by_event[t] = sid
    ts = sorted(events)
    if ts != list(range(len(ts))):
        raise RuntimeError("event_index must be contiguous 0..T-1")
    ids0 = [s for s, _ in events[ts[0]]]
    if len(ids0) != len(set(ids0)):
        raise RuntimeError("duplicate candidate in event 0")
    set0 = set(ids0)
    for t in ts:
        if set(s for s, _ in events[t]) != set0:
            raise RuntimeError(f"candidate set mismatch at event {t}")
    return events, y_by_event, stop_by_event, sorted(set0)


def choose_events(ts, stop_by_event, mode):
    if mode == "all" or not stop_by_event:
        return list(ts)
    groups = defaultdict(list)
    for t in ts:
        if t not in stop_by_event:
            raise RuntimeError("partial stop_id coverage")
        groups[stop_by_event[t]].append(t)
    ordered = sorted(groups.values(), key=lambda g: min(g))
    if mode == "first":
        return [min(g) for g in ordered]
    if mode == "last":
        return [max(g) for g in ordered]
    if mode == "middle":
        return [sorted(g)[(len(g)-1)//2] for g in ordered]
    raise ValueError(mode)


def interval(h, delta):
    return max(EPS, h-delta), min(1.0-EPS, h+delta)


def run(path: Path, alpha: float, delta: float, mode: str, out: Path):
    events, ys, stop_by_event, candidates = read_long(path)
    selected = choose_events(sorted(events), stop_by_event, mode)
    logE = {s: 0.0 for s in candidates}
    rejected = set()
    threshold = math.log(1.0 / alpha)

    rows = []
    for replay_i, t in enumerate(selected):
        pred = dict(events[t])
        # fixed uniform mixture of OTHER candidate predictions; no data dependence.
        total_h = sum(pred.values())
        n = len(candidates)
        newly = []
        for s in candidates:
            h = pred[s]
            q = clip_p((total_h - h) / (n - 1))
            lo, hi = interval(h, delta)
            pstar = min(hi, max(lo, q))
            y = ys[t]
            if y == 1:
                logfac = math.log(q) - math.log(pstar)
            else:
                logfac = math.log1p(-q) - math.log1p(-pstar)
            logE[s] += logfac
            if s not in rejected and logE[s] >= threshold:
                rejected.add(s)
                newly.append(s)

        alive = [s for s in candidates if s not in rejected]
        vals = sorted(logE.values())
        rows.append({
            "replay_index": replay_i,
            "event_index": t,
            "stop_id": stop_by_event.get(t, ""),
            "y": ys[t],
            "survivors": len(alive),
            "new_rejections": ";".join(sorted(newly)),
            "min_logE": vals[0],
            "median_logE": vals[len(vals)//2],
            "max_logE": vals[-1],
            "survivor_ids": ";".join(alive),
        })

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0]))
        wr.writeheader()
        wr.writerows(rows)

    print(f"events_used={len(selected)}")
    print(f"candidates={len(candidates)}")
    print(f"delta={delta}")
    print(f"mode={mode}")
    print(f"final_survivors={rows[-1]['survivors']}")
    print(f"output={out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--delta", type=float, default=0.0)
    ap.add_argument("--mode", choices=["all", "first", "last", "middle"], default="all")
    args = ap.parse_args()
    run(args.input, args.alpha, args.delta, args.mode, args.output)
