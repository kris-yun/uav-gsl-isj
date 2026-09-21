#!/usr/bin/env python3
"""Fixed-trajectory VGR/GADEN 300-s TNQC replay.

Consumes a native PMFS context-bank export from a full-budget VGR House run.
The robot trajectory, measurements, wind field, native candidate bank and
refinement decisions stay fixed. TNQC only reweights the frozen candidate
likelihoods. Source truth is used only after all posteriors are constructed.

The replay audits itself by reconstructing native PMFS from the exported
candidate alignment/rectangles and comparing it with source_posterior.csv.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Mapping, Sequence, Tuple, List

EPS = 1e-6


@dataclass(frozen=True)
class Cell:
    cell_index: int
    grid_i: int
    grid_j: int
    x: float
    y: float
    logodds: float
    probability: float
    confidence: float


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    origin_i: int
    origin_j: int
    size_i: int
    size_j: int
    center_x: float
    center_y: float
    manifest_native_score: float

    @property
    def area(self) -> int:
        return self.size_i * self.size_j

    def covers(self, i: int, j: int) -> bool:
        return (self.origin_i <= i < self.origin_i + self.size_i and
                self.origin_j <= j < self.origin_j + self.size_j)


def rows(path: Path):
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def safe_logit(p: float, eps: float = EPS) -> float:
    p = min(max(p, eps), 1.0 - eps)
    return math.log(p / (1.0 - p))


def signum(x: float) -> int:
    return (x > 0.0) - (x < 0.0)


def logsumexp(v: Sequence[float]) -> float:
    m = max(v)
    return m + math.log(sum(math.exp(x - m) for x in v))


def normalize(logw: Mapping[int, float]) -> Dict[int, float]:
    z = logsumexp(list(logw.values()))
    p = {k: math.exp(v - z) for k, v in logw.items()}
    s = sum(p.values())
    return {k: v / s for k, v in p.items()}


def choose_final_update(bank: Path, budget: float) -> Tuple[int, float]:
    eligible = []
    for r in rows(bank / "source_update_timing.csv"):
        t = float(r["sim_time"])
        u = int(r["source_update_id"])
        if t <= budget + 1e-9:
            eligible.append((t, u))
    if not eligible:
        raise ValueError(f"no source update at or before {budget} s")
    t, u = max(eligible, key=lambda z: (z[0], z[1]))
    return u, t


def load_cells(d: Path):
    cells, by_grid = {}, {}
    for r in rows(d / "measured_hit_probability.csv"):
        if r["occupancy"] != "Free":
            continue
        c = Cell(int(r["cell_index"]), int(r["grid_i"]), int(r["grid_j"]),
                 float(r["x"]), float(r["y"]), float(r["logOdds"]),
                 float(r["probability"]), float(r["confidence"]))
        cells[c.cell_index] = c
        by_grid[(c.grid_i, c.grid_j)] = c.cell_index
    if not cells:
        raise ValueError("no free cells")
    return cells, by_grid


def load_candidates(d: Path):
    out = {}
    for r in rows(d / "candidate_manifest.csv"):
        c = Candidate(r["candidate_id"], int(r["origin_i"]), int(r["origin_j"]),
                      int(r["size_i"]), int(r["size_j"]),
                      float(r["center_x"]), float(r["center_y"]),
                      float(r["native_score"]))
        if c.candidate_id in out:
            old = out[c.candidate_id]
            if (old.origin_i, old.origin_j, old.size_i, old.size_j) != (
                    c.origin_i, c.origin_j, c.size_i, c.size_j):
                raise ValueError(f"candidate geometry changed: {c.candidate_id}")
        out[c.candidate_id] = c
    if not out:
        raise ValueError("empty candidate manifest")
    return out


def load_alignment(d: Path, cells: Mapping[int, Cell]):
    out = {}
    for r in rows(d / "candidate_support_alignment.csv"):
        idx = int(r["cell_index"])
        if idx not in cells:
            continue
        out.setdefault(r["candidate_id"], {})[idx] = (
            float(r["measured_probability"]),
            float(r["measured_confidence"]),
            float(r["simulated_hit_probability"]))
    if not out:
        raise ValueError("empty candidate support alignment")
    return out


def local_edges(cells, by_grid):
    support = {idx for idx, c in cells.items()
               if c.confidence > 0.0 and math.isfinite(c.logodds)}
    out = []
    for idx in support:
        c = cells[idx]
        for di, dj in ((1, 0), (0, 1)):
            b = by_grid.get((c.grid_i + di, c.grid_j + dj))
            if b in support:
                out.append((idx, b))
    return out


def native_log_score(alignment, power: float) -> float:
    # Exact current PMFS cell likelihood:
    # lerp(1, 1-|measured-simulated|*power, confidence).
    total = 0.0
    for measured, confidence, simulated in alignment.values():
        p = 1.0 - confidence * abs(measured - simulated) * power
        if not (p > 0.0 and math.isfinite(p)):
            raise ValueError(f"invalid native cell likelihood {p}")
        total += math.log(p)
    return total


def tnqc_score(alignment, cells, edges):
    support = [idx for idx, c in cells.items()
               if c.confidence > 0.0 and math.isfinite(c.logodds)
               and idx in alignment]
    if len(support) < 4:
        return dict(valid=False, support_count=len(support), edge_count=0,
                    canonical_cosine=0.0, local_order_agreement=0.0,
                    evidence=0.0)

    sw = sum(cells[k].confidence for k in support)
    sw2 = sum(cells[k].confidence ** 2 for k in support)
    observed = {k: cells[k].logodds for k in support}
    predicted = {k: safe_logit(alignment[k][2]) for k in support}
    mo = sum(cells[k].confidence * observed[k] for k in support) / sw
    mp = sum(cells[k].confidence * predicted[k] for k in support) / sw
    cross = no = np = 0.0
    for k in support:
        w = cells[k].confidence
        xo, xp = observed[k] - mo, predicted[k] - mp
        cross += w * xo * xp
        no += w * xo * xo
        np += w * xp * xp
    if not (no > 1e-18 and np > 1e-18):
        return dict(valid=False, support_count=len(support), edge_count=0,
                    canonical_cosine=0.0, local_order_agreement=0.0,
                    evidence=0.0)
    qa = max(-1.0, min(1.0, cross / math.sqrt(no * np)))

    ss = set(support)
    signed = ew = 0.0
    ec = 0
    for a, b in edges:
        if a not in ss or b not in ss:
            continue
        so = signum(observed[a] - observed[b])
        sp = signum(predicted[a] - predicted[b])
        if not so or not sp:
            continue
        w = min(cells[a].confidence, cells[b].confidence)
        signed += w * so * sp
        ew += w
        ec += 1
    qo = max(-1.0, min(1.0, signed / ew)) if ew > 0.0 else 0.0

    # Candidate-local score only.  The broader order channel is not mixed
    # here because candidate-wise averaging can preserve sign yet reverse the
    # relative ordering between two source hypotheses.  A single shared bank
    # gate is computed below after all candidates are available.
    return dict(valid=True, support_count=len(support), edge_count=ec,
                effective_support=(sw * sw) / sw2,
                canonical_cosine=qa, local_order_agreement=qo)


def candidate_order_concordance(diag):
    valid = [q for q in diag.values() if q.get("valid") and q.get("edge_count", 0) >= 2]
    signed = 0.0
    pairs = 0
    for i in range(len(valid)):
        for j in range(i + 1, len(valid)):
            sa = signum(valid[i]["canonical_cosine"] - valid[j]["canonical_cosine"])
            so = signum(valid[i]["local_order_agreement"] - valid[j]["local_order_agreement"])
            if not sa or not so:
                continue
            signed += sa * so
            pairs += 1
    if pairs == 0:
        return dict(valid=False, pair_count=0, concordance=0.0, strength=0.0)
    concordance = max(-1.0, min(1.0, signed / pairs))
    return dict(valid=True, pair_count=pairs, concordance=concordance,
                strength=max(0.0, concordance))


def final_partition(cells, candidates):
    out = {}
    for idx, cell in cells.items():
        cover = [c for c in candidates.values()
                 if c.covers(cell.grid_i, cell.grid_j)]
        if not cover:
            raise ValueError(f"candidate rectangles do not cover free cell {idx}")
        out[idx] = min(cover, key=lambda c: (c.area, c.candidate_id)).candidate_id
    return out


def posterior(partition, scores):
    return normalize({idx: scores[cid] for idx, cid in partition.items()})


def exported_posterior(d: Path):
    p = {int(r["cell_index"]): max(float(r["source_probability"]), 0.0)
         for r in rows(d / "source_posterior.csv")}
    s = sum(p.values())
    return {k: v / s for k, v in p.items()}


def diff(a, b):
    keys = set(a) | set(b)
    ds = [abs(a.get(k, 0.0) - b.get(k, 0.0)) for k in keys]
    return dict(l1=sum(ds), max_abs=max(ds) if ds else 0.0)


def metrics(p, cells, tx, ty):
    rr = [(idx, cells[idx].x, cells[idx].y, max(v, 0.0))
          for idx, v in p.items()]
    total = sum(x[3] for x in rr)
    rr = [(idx, x, y, q / total) for idx, x, y, q in rr]
    mx = sum(x*q for _, x, _, q in rr)
    my = sum(y*q for _, _, y, q in rr)
    ranked = sorted(rr, key=lambda z: (-z[3], z[0]))
    n = max(1, math.ceil(0.05 * len(ranked)))
    top = ranked[:n]
    sm = sum(q for _, _, _, q in top)
    tx5 = sum(x*q for _, x, _, q in top) / sm
    ty5 = sum(y*q for _, _, y, q in top) / sm
    mode = max(rr, key=lambda z: (z[3], -z[0]))
    var = sum(q*((x-mx)**2 + (y-my)**2) for _, x, y, q in rr)
    return dict(pmfs_top5_x=tx5, pmfs_top5_y=ty5,
                pmfs_top5_error_m=math.hypot(tx5-tx, ty5-ty),
                pmfs_top5_cell_count=n,
                map_x=mode[1], map_y=mode[2],
                map_error_m=math.hypot(mode[1]-tx, mode[2]-ty),
                mean_x=mx, mean_y=my,
                mean_error_m=math.hypot(mx-tx, my-ty),
                variance_m2=var)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", type=Path, required=True)
    ap.add_argument("--truth-x", type=float, required=True)
    ap.add_argument("--truth-y", type=float, required=True)
    ap.add_argument("--budget-s", type=float, default=300.0)
    ap.add_argument("--source-discrimination-power", type=float, default=1.0)
    ap.add_argument("--native-reconstruction-max-abs", type=float, default=5e-6)
    ap.add_argument("--native-reconstruction-l1", type=float, default=5e-4)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()

    bank = args.run_dir / "context_bank"
    uid, sim_time = choose_final_update(bank, args.budget_s)
    d = bank / f"source_update_{uid:04d}"
    cells, by_grid = load_cells(d)
    candidates = load_candidates(d)
    alignment = load_alignment(d, cells)
    missing = sorted(set(candidates) - set(alignment))
    if missing:
        raise ValueError(f"{len(missing)} candidates missing alignment: {missing[:3]}")
    edges = local_edges(cells, by_grid)
    part = final_partition(cells, candidates)

    native_s, diag = {}, {}
    for cid in candidates:
        native_s[cid] = native_log_score(
            alignment[cid], args.source_discrimination_power)
        diag[cid] = tnqc_score(alignment[cid], cells, edges)

    bank_gate = candidate_order_concordance(diag)
    fused_s, only_s = {}, {}
    for cid in candidates:
        q = diag[cid]
        e = (bank_gate["strength"] * q["canonical_cosine"]
             if bank_gate["valid"] and q["valid"] else 0.0)
        e = max(-1.0, min(1.0, e))
        q["bank_evidence"] = e
        fused_s[cid] = native_s[cid] + e
        only_s[cid] = e

    native_replay = posterior(part, native_s)
    fused = posterior(part, fused_s)
    only = posterior(part, only_s)
    native_export = exported_posterior(d)
    audit = diff(native_replay, native_export)
    audit_pass = (audit["max_abs"] <= args.native_reconstruction_max_abs and
                  audit["l1"] <= args.native_reconstruction_l1)

    # Evaluator-only truth enters only below this line.
    nm = metrics(native_export, cells, args.truth_x, args.truth_y)
    nr = metrics(native_replay, cells, args.truth_x, args.truth_y)
    fm = metrics(fused, cells, args.truth_x, args.truth_y)
    om = metrics(only, cells, args.truth_x, args.truth_y)
    ev = [q["bank_evidence"] for q in diag.values() if q["valid"]]

    payload = {
        "contract": "TNQC_VGR_FIXED_TRAJECTORY_300S_REPLAY_V1",
        "run_dir": str(args.run_dir),
        "budget_s": args.budget_s,
        "selected_source_update_id": uid,
        "selected_source_update_sim_time": sim_time,
        "budget_to_last_update_gap_s": args.budget_s - sim_time,
        "truth": [args.truth_x, args.truth_y],
        "free_cell_count": len(cells),
        "candidate_count": len(candidates),
        "local_edge_count": len(edges),
        "native_reconstruction_audit": {
            **audit,
            "max_abs_threshold": args.native_reconstruction_max_abs,
            "l1_threshold": args.native_reconstruction_l1,
            "pass": audit_pass,
        },
        "tnqc_candidate_bank_gate": bank_gate,
        "tnqc_evidence": {
            "valid_candidate_count": len(ev),
            "min": min(ev) if ev else None,
            "median": statistics.median(ev) if ev else None,
            "max": max(ev) if ev else None,
            "mean": statistics.fmean(ev) if ev else None,
        },
        "native_exported": nm,
        "native_replay": nr,
        "tnqc_fused": fm,
        "tnqc_only": om,
        "fused_improvement_fraction_vs_native":
            (nm["pmfs_top5_error_m"] - fm["pmfs_top5_error_m"]) /
            max(nm["pmfs_top5_error_m"], 1e-12),
        "only_improvement_fraction_vs_native":
            (nm["pmfs_top5_error_m"] - om["pmfs_top5_error_m"]) /
            max(nm["pmfs_top5_error_m"], 1e-12),
        "valid_for_gate": audit_pass,
    }
    text = json.dumps(payload, indent=2, sort_keys=True)
    print(text)
    out = args.json_out or args.run_dir / "tnqc_fixed_trajectory_evaluation.json"
    out.write_text(text + "\n", encoding="utf-8")
    if not audit_pass:
        raise SystemExit(3)


if __name__ == "__main__":
    main()
