#!/usr/bin/env python3
"""Fixed-trajectory VGR/GADEN 300-s TNQC replay.

Consumes a native PMFS context-bank export from a full-budget VGR House run.
The robot trajectory, measurements, wind field, native candidate bank and
refinement decisions stay fixed. TNQC only reweights the frozen candidate
likelihoods. This matches the online V5 method contract: quadtree refinement
is native within each source update; the concordance gate is computed only on
terminal active leaves, weighted by represented free-cell multiplicity and
attenuated by local-order support coverage. Source truth is used only after
all posteriors are constructed.

The replay audits itself by reconstructing native PMFS from the exported
candidate alignment/rectangles and comparing it with source_posterior.csv.
The authoritative top-5% endpoint is evaluated by a standalone C++ clone of
PMFS ExpectedValue(..., 0.05), and that clone must reproduce the native PMFS
logged endpoint before any TNQC counterfactual is accepted.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import statistics
import subprocess
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


def native_result_line(run_dir: Path):
    """Read the authoritative C++ PMFS terminal endpoint from launch.log."""
    pat = re.compile(
        r"RESULT IS: Success=([^,]+), Search_t=([0-9.eE+-]+), "
        r"Error=([0-9.eE+-]+)")
    found = None
    for line in (run_dir / "launch.log").read_text(
            encoding="utf-8", errors="replace").splitlines():
        m = pat.search(line)
        if m:
            found = {
                "success": m.group(1).strip(),
                "search_t": float(m.group(2)),
                "reported_top5_error_m": float(m.group(3)),
            }
    if found is None:
        raise ValueError(f"missing authoritative PMFS RESULT IS line: {run_dir}")
    return found


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


def candidate_order_concordance(
        diag, candidate_ids=None, hypothesis_measure=None):
    """Support-coverage-aware gate over a specified hypothesis measure.

    Reference mass contains every valid candidate pair for which q_aff has a
    non-tied ordering. Local-order ties or insufficient edge support contribute
    zero signed evidence but remain in that reference mass. Consequently sparse
    auxiliary support attenuates the shared gate instead of renormalizing to
    full strength.

    hypothesis_measure maps candidate id -> represented free-cell count.
    """
    ids = list(diag) if candidate_ids is None else list(candidate_ids)

    def measure(cid):
        if hypothesis_measure is None:
            return 1.0
        if cid not in hypothesis_measure:
            raise ValueError(f"missing hypothesis measure for {cid}")
        m = float(hypothesis_measure[cid])
        if not (m > 0.0 and math.isfinite(m)):
            raise ValueError(f"invalid hypothesis measure for {cid}: {m}")
        return m

    valid = [(cid, diag[cid], measure(cid)) for cid in ids
             if cid in diag and diag[cid].get("valid")]

    signed = 0.0
    informative_weight = 0.0
    reference_weight = 0.0
    informative_pairs = 0
    reference_pairs = 0

    for i in range(len(valid)):
        for j in range(i + 1, len(valid)):
            _, qi, mi = valid[i]
            _, qj, mj = valid[j]
            sa = signum(qi["canonical_cosine"] - qj["canonical_cosine"])
            if not sa:
                continue

            pair_weight = mi * mj
            reference_weight += pair_weight
            reference_pairs += 1

            if qi.get("edge_count", 0) < 2 or qj.get("edge_count", 0) < 2:
                continue
            so = signum(
                qi["local_order_agreement"] - qj["local_order_agreement"])
            if not so:
                continue

            signed += pair_weight * sa * so
            informative_weight += pair_weight
            informative_pairs += 1

    if not (reference_weight > 0.0):
        return dict(valid=False, pair_count=0, pair_weight=0.0,
                    reference_pair_count=0, reference_pair_weight=0.0,
                    informative_coverage=0.0,
                    concordance=0.0, strength=0.0)

    coverage = max(0.0, min(1.0, informative_weight / reference_weight))
    concordance = (
        max(-1.0, min(1.0, signed / informative_weight))
        if informative_weight > 0.0 else 0.0)
    strength = max(0.0, signed / reference_weight)
    return dict(valid=True,
                pair_count=informative_pairs,
                pair_weight=informative_weight,
                reference_pair_count=reference_pairs,
                reference_pair_weight=reference_weight,
                informative_coverage=coverage,
                concordance=concordance,
                strength=strength)


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


def write_endpoint_posterior(path: Path, p, cells):
    """Write one posterior in the controlled format consumed by C++."""
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["cell_index", "grid_i", "grid_j", "x", "y",
                    "source_probability"])
        ordered = sorted(cells.items(),
                         key=lambda kv: (kv[1].grid_j, kv[1].grid_i))
        for idx, cell in ordered:
            w.writerow([idx, cell.grid_i, cell.grid_j,
                        format(cell.x, ".17g"), format(cell.y, ".17g"),
                        format(max(float(p.get(idx, 0.0)), 0.0), ".17g")])


def cpp_endpoint_metrics(evaluator: Path, posterior_csv: Path, tx, ty):
    proc = subprocess.run(
        [str(evaluator), str(posterior_csv), repr(float(tx)), repr(float(ty))],
        check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"C++ endpoint evaluator failed rc={proc.returncode}: "
            f"{proc.stdout}\n{proc.stderr}")
    out = json.loads(proc.stdout)
    required = {"pmfs_top5_x", "pmfs_top5_y", "pmfs_top5_error_m",
                "pmfs_top5_cell_count"}
    if not required.issubset(out):
        raise ValueError(f"incomplete C++ endpoint output: {out}")
    return out


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
    ap.add_argument("--native-endpoint-rounding-tolerance-m",
                    type=float, default=0.011)
    ap.add_argument("--cpp-endpoint-evaluator", type=Path, required=True)
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

    # Only candidates that own at least one cell in the final partition are
    # terminal source hypotheses.  The all-evaluated-candidate gate is kept
    # below as a source-blind audit only; it must not control TNQC evidence.
    active_candidate_ids = sorted(set(part.values()))
    active_candidate_measure = {}
    for cid in part.values():
        active_candidate_measure[cid] = active_candidate_measure.get(cid, 0) + 1

    bank_gate = candidate_order_concordance(
        diag, active_candidate_ids, active_candidate_measure)
    final_leaf_unweighted_gate_audit = candidate_order_concordance(
        diag, active_candidate_ids)
    all_evaluated_gate_audit = candidate_order_concordance(diag)

    fused_s, only_s = {}, {}
    active_set = set(active_candidate_ids)
    for cid in candidates:
        q = diag[cid]
        e = (bank_gate["strength"] * q["canonical_cosine"]
             if cid in active_set and bank_gate["valid"] and q["valid"] else 0.0)
        e = max(-1.0, min(1.0, e))
        q["bank_evidence"] = e
        fused_s[cid] = native_s[cid] + e
        only_s[cid] = e

    native_replay = posterior(part, native_s)
    fused = posterior(part, fused_s)
    only = posterior(part, only_s)
    native_export = exported_posterior(d)
    audit = diff(native_replay, native_export)
    reconstruction_pass = (
        audit["max_abs"] <= args.native_reconstruction_max_abs
        and audit["l1"] <= args.native_reconstruction_l1)

    # Evaluator-only truth enters only below this line.
    # Python metrics remain diagnostics for MAP/mean/variance and for exposing
    # any tie-cutoff sensitivity. The authoritative top-5% endpoint is
    # evaluated by a small C++ clone of PMFS ExpectedValue(..., 0.05).
    nm_py = metrics(native_export, cells, args.truth_x, args.truth_y)
    nr = metrics(native_replay, cells, args.truth_x, args.truth_y)
    fm_py = metrics(fused, cells, args.truth_x, args.truth_y)
    om_py = metrics(only, cells, args.truth_x, args.truth_y)

    evaluator = args.cpp_endpoint_evaluator.resolve()
    if not evaluator.is_file():
        raise FileNotFoundError(evaluator)
    endpoint_dir = args.run_dir / "tnqc_endpoint_posteriors"
    endpoint_dir.mkdir(parents=True, exist_ok=True)
    native_csv = endpoint_dir / "native_exported.csv"
    fused_csv = endpoint_dir / "tnqc_fused.csv"
    only_csv = endpoint_dir / "tnqc_only.csv"
    write_endpoint_posterior(native_csv, native_export, cells)
    write_endpoint_posterior(fused_csv, fused, cells)
    write_endpoint_posterior(only_csv, only, cells)

    nm_cpp = cpp_endpoint_metrics(
        evaluator, native_csv, args.truth_x, args.truth_y)
    fm_cpp = cpp_endpoint_metrics(
        evaluator, fused_csv, args.truth_x, args.truth_y)
    om_cpp = cpp_endpoint_metrics(
        evaluator, only_csv, args.truth_x, args.truth_y)

    nm = {**nm_py, **nm_cpp}
    fm = {**fm_py, **fm_cpp}
    om = {**om_py, **om_cpp}

    # The standalone evaluator is accepted only if it reproduces the actual
    # PMFS C++ endpoint for the native posterior. The PMFS log prints Error to
    # two decimals, hence the frozen 0.011 m tolerance. Once this parity check
    # passes, the same std::sort implementation is used for the counterfactual
    # TNQC posterior, including equal-probability cutoff ties.
    native_cpp = native_result_line(args.run_dir)
    endpoint_delta = abs(
        nm_cpp["pmfs_top5_error_m"] - native_cpp["reported_top5_error_m"])
    endpoint_pass = (
        endpoint_delta <= args.native_endpoint_rounding_tolerance_m)
    audit_pass = reconstruction_pass and endpoint_pass

    ev = [diag[cid]["bank_evidence"] for cid in active_candidate_ids
          if diag[cid]["valid"]]

    payload = {
        "contract": "TNQC_VGR_FIXED_TRAJECTORY_300S_REPLAY_V6_CPP_ENDPOINT_PARITY",
        "run_dir": str(args.run_dir),
        "budget_s": args.budget_s,
        "selected_source_update_id": uid,
        "selected_source_update_sim_time": sim_time,
        "budget_to_last_update_gap_s": args.budget_s - sim_time,
        "truth": [args.truth_x, args.truth_y],
        "free_cell_count": len(cells),
        "candidate_count": len(candidates),
        "total_evaluated_candidate_count": len(candidates),
        "final_leaf_candidate_count": len(active_candidate_ids),
        "candidate_gate_scope":
            "final_partition_leaf_candidates_free_cell_measure_support_coverage_weighted",
        "final_leaf_hypothesis_measure_cells": active_candidate_measure,
        "local_edge_count": len(edges),
        "native_reconstruction_audit": {
            **audit,
            "max_abs_threshold": args.native_reconstruction_max_abs,
            "l1_threshold": args.native_reconstruction_l1,
            "pass": reconstruction_pass,
        },
        "native_cpp_endpoint_audit": {
            "cpp_result": native_cpp,
            "standalone_cpp_native_top5_error_m":
                nm_cpp["pmfs_top5_error_m"],
            "python_diagnostic_native_top5_error_m":
                nm_py["pmfs_top5_error_m"],
            "absolute_error_difference_m": endpoint_delta,
            "rounding_tolerance_m":
                args.native_endpoint_rounding_tolerance_m,
            "pass": endpoint_pass,
        },
        "endpoint_evaluator": {
            "engine": "cpp_std_sort_clone_of_PMFS_ExpectedValue_0p05",
            "binary": str(evaluator),
            "sha256": hashlib.sha256(evaluator.read_bytes()).hexdigest(),
            "native_posterior_csv": str(native_csv),
            "fused_posterior_csv": str(fused_csv),
            "only_posterior_csv": str(only_csv),
        },
        "endpoint_tie_diagnostics": {
            "native_cpp_minus_python_error_m":
                nm_cpp["pmfs_top5_error_m"] - nm_py["pmfs_top5_error_m"],
            "fused_cpp_minus_python_error_m":
                fm_cpp["pmfs_top5_error_m"] - fm_py["pmfs_top5_error_m"],
            "only_cpp_minus_python_error_m":
                om_cpp["pmfs_top5_error_m"] - om_py["pmfs_top5_error_m"],
        },
        "tnqc_candidate_bank_gate": bank_gate,
        "tnqc_final_leaf_unweighted_gate_audit":
            final_leaf_unweighted_gate_audit,
        "tnqc_all_evaluated_candidate_gate_audit": all_evaluated_gate_audit,
        "tnqc_gate_scope_audit": {
            "unweighted_final_leaf_gate_differs_from_measure_gate":
                final_leaf_unweighted_gate_audit != bank_gate,
            "all_evaluated_gate_differs_from_measure_gate":
                all_evaluated_gate_audit != bank_gate,
            "final_leaf_candidate_ids": active_candidate_ids,
        },
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
        "gate_validity_requires":
            ["native_posterior_reconstruction",
             "standalone_cpp_expected_value_matches_native_pmfs",
             "same_cpp_expected_value_engine_for_tnqc_counterfactual",
             "partition_measure_final_leaf_gate_scope",
             "local_order_support_coverage_attenuation"],
    }
    text = json.dumps(payload, indent=2, sort_keys=True)
    print(text)
    out = args.json_out or args.run_dir / "tnqc_fixed_trajectory_evaluation.json"
    out.write_text(text + "\n", encoding="utf-8")
    if not audit_pass:
        raise SystemExit(3)


if __name__ == "__main__":
    main()
