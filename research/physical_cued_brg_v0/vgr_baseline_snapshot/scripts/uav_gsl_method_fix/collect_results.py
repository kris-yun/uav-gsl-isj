#!/usr/bin/env python3
"""Collect fixed UAV-GSL ablation results without pwc/pwc_mac parsing errors.

Reads legacy *_server.csv files and optional *.audit.csv files. Failures are not dropped;
all-run and success-only summaries are reported separately.
"""
from __future__ import annotations

import csv
import math
import re
import statistics as stats
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

CONDITIONS = [
    "baseline", "pwc", "psde_final", "psde_online", "psde_both", "mac", "pwc_mac", "sdr", "full", "bwe", "pgpt", "hce"
]
# Filename parsing is done by suffix matching, not split("_") and not a greedy regex.
# This avoids the legacy bug where House01_pwc_mac_s0 was parsed as dataset=House01_pwc, condition=mac.

@dataclass
class Row:
    dataset: str
    condition: str
    seed: int
    rep: str
    status: str
    navigation_time: float
    search_time: float
    error_expected: float
    error_final: float
    iterations: int
    variance: float
    audit: Optional[dict]
    file: Path


def parse_float(x: str) -> float:
    try:
        return float(x)
    except Exception:
        return math.nan


def parse_server(path: Path) -> Optional[Tuple[str, float, float, float, float, int, float]]:
    lines = [ln.strip() for ln in path.read_text(errors="ignore").splitlines() if ln.strip()]
    if not lines:
        return None
    last = lines[-1]
    parts = last.replace(",", " ").split()
    if not parts:
        return None
    if parts[0].upper() == "FAILED":
        status = "FAILED"
        vals = parts[1:]
    elif parts[0].upper() == "SUCCESS":
        status = "SUCCESS"
        vals = parts[1:]
    else:
        status = "SUCCESS"
        vals = parts
    if len(vals) < 6:
        return None
    nav = parse_float(vals[0])
    search = parse_float(vals[1])
    err_expected = parse_float(vals[2])
    err_final = parse_float(vals[3])
    try:
        iterations = int(float(vals[4]))
    except Exception:
        iterations = -1
    var = parse_float(vals[5])
    return status, nav, search, err_expected, err_final, iterations, var


def read_audit(server_path: Path) -> Optional[dict]:
    audit_path = Path(str(server_path) + ".audit.csv")
    if not audit_path.exists() or audit_path.stat().st_size == 0:
        return None
    with audit_path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    return rows[-1] if rows else None


def parse_filename(name: str) -> Optional[Tuple[str, str, int, str]]:
    if not name.endswith("_server.csv"):
        return None
    stem = name[:-len("_server.csv")]
    for cond in sorted(CONDITIONS, key=len, reverse=True):
        marker = f"_{cond}_s"
        if marker not in stem:
            continue
        dataset, tail = stem.rsplit(marker, 1)
        if not dataset:
            continue
        rep = ""
        if "_r" in tail:
            seed_s, rep_tail = tail.split("_r", 1)
            rep = "_r" + rep_tail
        else:
            seed_s = tail
        if seed_s.isdigit():
            return dataset, cond, int(seed_s), rep
    return None


def load_rows(root: Path) -> List[Row]:
    rows: List[Row] = []
    for path in sorted(root.glob("*_server.csv")):
        meta = parse_filename(path.name)
        if not meta:
            print(f"[WARN] skip unrecognized filename: {path.name}", file=sys.stderr)
            continue
        dataset, condition, seed, rep = meta
        parsed = parse_server(path)
        if parsed is None:
            print(f"[WARN] could not parse: {path}", file=sys.stderr)
            continue
        status, nav, search, err_exp, err_final, iterations, var = parsed
        rows.append(Row(
            dataset=dataset,
            condition=condition,
            seed=seed,
            rep=rep,
            status=status,
            navigation_time=nav,
            search_time=search,
            error_expected=err_exp,
            error_final=err_final,
            iterations=iterations,
            variance=var,
            audit=read_audit(path),
            file=path,
        ))
    return rows


def mean(xs: List[float]) -> float:
    xs = [x for x in xs if math.isfinite(x)]
    return sum(xs) / len(xs) if xs else math.nan


def median(xs: List[float]) -> float:
    xs = [x for x in xs if math.isfinite(x)]
    return stats.median(xs) if xs else math.nan


def fmt(x: float) -> str:
    return "nan" if not math.isfinite(x) else f"{x:.3f}"


def summarize(rows: List[Row]) -> None:
    if not rows:
        print("No rows found.")
        return
    print("dataset,condition,n_all,n_success,n_failed,mean_error_all,median_error_all,mean_error_success,mean_search_time,mean_iterations")
    keys = sorted({(r.dataset, r.condition) for r in rows})
    for dataset, cond in keys:
        grp = [r for r in rows if r.dataset == dataset and r.condition == cond]
        succ = [r for r in grp if r.status == "SUCCESS"]
        print(
            f"{dataset},{cond},{len(grp)},{len(succ)},{len(grp)-len(succ)},"
            f"{fmt(mean([r.error_final for r in grp]))},{fmt(median([r.error_final for r in grp]))},"
            f"{fmt(mean([r.error_final for r in succ]))},{fmt(mean([r.search_time for r in grp]))},"
            f"{fmt(mean([float(r.iterations) for r in grp]))}"
        )


def paired(rows: List[Row]) -> None:
    print("\npaired_vs_baseline,dataset,condition,n_pairs,mean_diff_method_minus_baseline,median_diff,method_better_count,method_worse_count")
    datasets = sorted({r.dataset for r in rows})
    for dataset in datasets:
        base = {(r.seed, r.rep): r for r in rows if r.dataset == dataset and r.condition == "baseline"}
        for cond in sorted({r.condition for r in rows if r.dataset == dataset and r.condition != "baseline"}):
            diffs = []
            better = worse = 0
            for r in rows:
                if r.dataset != dataset or r.condition != cond:
                    continue
                b = base.get((r.seed, r.rep))
                if not b:
                    continue
                d = r.error_final - b.error_final
                if math.isfinite(d):
                    diffs.append(d)
                    if d < 0:
                        better += 1
                    elif d > 0:
                        worse += 1
            if diffs:
                print(f"paired_vs_baseline,{dataset},{cond},{len(diffs)},{fmt(mean(diffs))},{fmt(median(diffs))},{better},{worse}")


def audit_overview(rows: List[Row]) -> None:
    audits = [r for r in rows if r.audit]
    if not audits:
        print("\n[INFO] no audit CSV files found yet.")
        return
    print("\naudit_flags,dataset,condition,seed,estimator,hits,final_x,final_y,error")
    for r in audits[:200]:
        a = r.audit or {}
        print(
            f"audit_flags,{r.dataset},{r.condition},{r.seed},{a.get('selected_estimator','')},"
            f"{a.get('hce_hit_count','')},{a.get('final_x','')},{a.get('final_y','')},{a.get('final_error_m','')}"
        )


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/uav_gsl_ablation_fixed")
    rows = load_rows(root)
    summarize(rows)
    paired(rows)
    audit_overview(rows)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
