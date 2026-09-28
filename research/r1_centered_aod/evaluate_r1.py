#!/usr/bin/env python3
"""Frozen House03 AOD x common-mode audit; no simulation or posterior."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
F1 = ROOT / "research/aod_house03_f1_full624_20260927"
OLD = ROOT / "evidence/aod_house03_f1_full624_20260927/amended"
EVID = ROOT / "evidence/r1_centered_aod"
EPS = 1e-9
CONDS = ("nominal", "state0_stress")
ARMS = ("u-ABS", "rawu-ABS", "u-CENTERED", "rawu-CENTERED")
METRICS = ("true_rank", "unique_top1", "top3", "map_error_m", "best_wrong_margin")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")


def score_abs(y: np.ndarray, m: np.ndarray) -> np.ndarray:
    """The exact archived B2 array shape and operation order."""
    observed = y[:, None]
    pred = np.maximum(m[:, :, None], EPS)
    norm = (pred * pred).sum(axis=(1, 2))
    gain = np.maximum(0, (pred * observed[None]).sum(axis=(1, 2)) / norm)
    return ((observed[None] - gain[:, None, None] * pred) ** 2).sum(axis=(1, 2))


def score_centered(y: np.ndarray, m: np.ndarray) -> np.ndarray:
    """Profile nonnegative gain and unconstrained pathwise additive intercept."""
    pred = np.maximum(m, EPS)
    cy = y - y.mean()
    cm = pred - pred.mean(axis=1, keepdims=True)
    norm = np.square(cm).sum(axis=1)
    # Exactly constant templates have no identifiable gain after profiling b.
    constant = np.all(pred == pred[:, :1], axis=1)
    gain = np.zeros(len(pred), dtype=np.float64)
    valid = (~constant) & (norm > 0)
    gain[valid] = np.maximum(0, (cm[valid] @ cy) / norm[valid])
    return np.square(cy[None, :] - gain[:, None] * cm).sum(axis=1)


def metrics_for(sse: np.ndarray, truth_idx: int, source_ids: np.ndarray,
                distance: np.ndarray) -> dict:
    assert sse.shape == (624,) and np.isfinite(sse).all()
    truth_sse = sse[truth_idx]
    less = int(np.count_nonzero(sse < truth_sse))
    ties = int(np.count_nonzero(sse == truth_sse))
    rank = less + (ties + 1) / 2
    minimum = sse.min()
    winners = np.flatnonzero(sse == minimum)
    top_idx = min(winners, key=lambda i: source_ids[i])
    wrong = np.delete(sse, truth_idx)
    return dict(true_rank=float(rank), unique_top1=int(len(winners) == 1 and top_idx == truth_idx),
                top3=int(rank <= 3), map_error_m=float(distance[top_idx]),
                best_wrong_margin=float(wrong.min() - truth_sse))


def old_parity(rows: pd.DataFrame) -> dict:
    matched = {}
    for cond, filename in (("nominal", "NOMINAL_FULL624_TARGET_METRICS.csv"),
                           ("state0_stress", "STATE0_FULL624_TARGET_METRICS.csv")):
        actual = rows[(rows.condition == cond) & (rows.readout == "ABS")].copy()
        actual["arm"] = actual.operator
        ref = pd.read_csv(OLD / filename)
        keys = ["truth_source", "realization", "path", "arm"]
        comp = actual.merge(ref, on=keys, validate="one_to_one", suffixes=("_new", "_old"))
        assert len(actual) == len(ref) == len(comp) == 384
        for col in ("unique_top1", "true_rank", "map_error_m"):
            new = comp[f"{col}_new"].to_numpy()
            old = comp[f"{col}_old"].to_numpy()
            same = np.isclose(new, old, rtol=0, atol=1e-12) if col == "map_error_m" else new == old
            if not np.all(same):
                bad = np.flatnonzero(~same)
                raise AssertionError((cond, col, len(bad),
                    comp.iloc[bad[:5]][keys + [f"{col}_new", f"{col}_old"]].to_dict("records")))
        matched[cond] = dict(rows=384, rank_top1_exact=True,
                             map_error_max_abs=float(np.max(np.abs(
                                 comp.map_error_m_new - comp.map_error_m_old))))
        paired = actual.pivot(index=keys[:-1], columns="arm", values="unique_top1")
        d = float((paired.rawu - paired.u).mean())
        old = json.loads((OLD / "F1_PRIMARY_RESULT.json").read_text())[cond]["Delta_acc"]
        assert d == old, (cond, d, old)
        matched[cond]["Delta_acc"] = d
    return matched


def effects(rows: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    src = rows.groupby(["condition", "truth_source", "arm"], sort=True)[list(METRICS)].mean().reset_index()
    effects_out = {}
    for cond in CONDS:
        d = src[src.condition == cond]
        means = d.groupby("arm")[list(METRICS)].mean()
        comparisons = {}
        for name, a, b in (("centering_u", "u-ABS", "u-CENTERED"),
                            ("centering_rawu", "rawu-ABS", "rawu-CENTERED"),
                            ("aod_abs", "u-ABS", "rawu-ABS"),
                            ("aod_centered", "u-CENTERED", "rawu-CENTERED")):
            left = d[d.arm == a].set_index("truth_source").sort_index()
            right = d[d.arm == b].set_index("truth_source").sort_index()
            delta = right[list(METRICS)] - left[list(METRICS)]
            # Improved rank is negative; improved Top1/Top3/margin is positive.
            better = -delta.true_rank
            comparable = [k for k in METRICS if k != "best_wrong_margin" or name.startswith("aod_")]
            comparisons[name] = dict(
                mean_delta={k: float(delta[k].mean()) for k in comparable},
                rank_improved_sources=int((better > 0).sum()),
                rank_harmed_sources=int((better < 0).sum()),
                rank_unchanged_sources=int((better == 0).sum()),
                top1_improved_sources=int((delta.unique_top1 > 0).sum()),
                top1_harmed_sources=int((delta.unique_top1 < 0).sum()),
            )
        effects_out[cond] = dict(arms={a: {k: float(means.loc[a, k]) for k in METRICS}
                                         for a in ARMS}, comparisons=comparisons)
    return src, effects_out


def bootstrap(rows: pd.DataFrame) -> dict:
    freeze = json.loads((ROOT / "research/r1_centered_aod/R1_BOOTSTRAP_FREEZE_20260929.json").read_text())
    n = int(freeze["draws"])
    rng = np.random.Generator(np.random.PCG64(int(freeze["seed"])))
    sources = sorted(rows.truth_source.unique())
    assert len(sources) == 12
    # Source x realization x condition x arm; path mean is inside each realization.
    per = rows.groupby(["truth_source", "realization", "condition", "arm"], sort=True)[
        ["true_rank", "unique_top1"]].mean()
    tensor = np.empty((12, 8, 2, 4, 2), dtype=np.float64)
    for si, source in enumerate(sources):
        for ri in range(8):
            for ci, cond in enumerate(CONDS):
                for ai, arm in enumerate(ARMS):
                    tensor[si, ri, ci, ai] = per.loc[(source, ri, cond, arm)].to_numpy()
    keys = (("centering_u", 0, 2), ("centering_rawu", 1, 3),
            ("aod_abs", 0, 1), ("aod_centered", 2, 3))
    draws = {(cond, name, metric): np.empty(n) for cond in CONDS for name, _, _ in keys
             for metric in ("true_rank", "unique_top1")}
    for bi in range(n):
        sample = np.empty((12, 2, 4, 2))
        for si in range(12):
            idx = rng.integers(0, 8, size=8)
            sample[si] = tensor[si, idx].mean(axis=0)
        mean = sample.mean(axis=0)
        for ci, cond in enumerate(CONDS):
            for name, a, b in keys:
                for mi, metric in enumerate(("true_rank", "unique_top1")):
                    draws[(cond, name, metric)][bi] = mean[ci, b, mi] - mean[ci, a, mi]
    out = dict(freeze=freeze, intervals={})
    for cond in CONDS:
        out["intervals"][cond] = {}
        for name, _, _ in keys:
            out["intervals"][cond][name] = {}
            for metric in ("true_rank", "unique_top1"):
                vals = draws[(cond, name, metric)]
                out["intervals"][cond][name][metric] = [float(v) for v in np.quantile(
                    vals, [.025, .975], method="linear")]
    return out


def run(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    y_path = EVID / "assets/TARGET_PATHS_12x8x2x10.npy"
    frozen = json.loads((OLD / "TARGET_DATA_FREEZE.json").read_text())
    assert sha(y_path) == frozen["all_artifact_sha256"][y_path.name]
    y = np.load(y_path, allow_pickle=False)
    assert y.shape == (12, 8, 2, 10) and np.isfinite(y).all()
    support = pd.read_csv(F1 / "templates/CANDIDATE_SUPPORT.csv")
    truth = pd.read_csv(F1 / "protocol/frozen/HOUSE03_F1_TRUTH_PANEL_12.tsv", sep="\t")
    assert len(support) == 624 and support.source_id.nunique() == 624
    assert len(truth) == 12 and truth.source_id.nunique() == 12
    arrays_path = F1 / "templates/candidate_path_templates.npz"
    template_freeze = json.loads((ROOT / "evidence/aod_house03_f1_full624_20260927/TEMPLATE_FREEZE.json").read_text())
    assert sha(arrays_path) == template_freeze["arrays_sha256"][arrays_path.name]
    arrays = np.load(arrays_path, allow_pickle=False)
    ids = support.source_id.to_numpy(str)
    records = []
    for cond in CONDS:
        for si, source in truth.iterrows():
            sid = str(source.source_id)
            idx = int(np.flatnonzero(ids == sid)[0])
            dist = np.hypot(support.x.to_numpy() - float(source.x_m),
                            support.y.to_numpy() - float(source.y_m))
            for ri in range(8):
                for pi, path in enumerate(("A", "B")):
                    observed = y[si, ri, pi]
                    for kind in ("u", "rawu"):
                        m = arrays[f"{cond}_{kind}_path_{path}"]
                        assert m.shape == (624, 10)
                        sse = score_abs(observed, m)
                        rec = dict(condition=cond, truth_source=sid, realization=ri,
                                   path=path, arm=f"{kind}-ABS", operator=kind, readout="ABS")
                        rec.update(metrics_for(sse, idx, ids, dist))
                        records.append(rec)
    abs_rows = pd.DataFrame(records)
    parity = old_parity(abs_rows)
    # No CENTERED score is evaluated before the complete F1 parity gate above.
    for cond in CONDS:
        for si, source in truth.iterrows():
            sid = str(source.source_id)
            idx = int(np.flatnonzero(ids == sid)[0])
            dist = np.hypot(support.x.to_numpy() - float(source.x_m),
                            support.y.to_numpy() - float(source.y_m))
            for ri in range(8):
                for pi, path in enumerate(("A", "B")):
                    observed = y[si, ri, pi]
                    for kind in ("u", "rawu"):
                        m = arrays[f"{cond}_{kind}_path_{path}"]
                        sse = score_centered(observed, m)
                        rec = dict(condition=cond, truth_source=sid, realization=ri,
                                   path=path, arm=f"{kind}-CENTERED", operator=kind,
                                   readout="CENTERED")
                        rec.update(metrics_for(sse, idx, ids, dist))
                        records.append(rec)
    rows = pd.DataFrame(records).sort_values(
        ["condition", "truth_source", "realization", "path", "arm"]).reset_index(drop=True)
    assert len(rows) == 2 * 12 * 8 * 2 * 4
    rows.to_csv(output / "TARGET_METRICS.csv", index=False, lineterminator="\n")
    src, effect = effects(rows)
    src.to_csv(output / "SOURCE_AGGREGATES.csv", index=False, lineterminator="\n")
    boot = bootstrap(rows)
    write_json(output / "BOOTSTRAP.json", boot)
    write_json(output / "R1_RESULT.json", dict(parity=parity, attribution=effect,
              support=624, truth_sources=12, realizations_per_source=8,
              paths_per_realization=2, original_f1_decision="AOD_F1_FULL624_CONFIRMED_STRESS_NONINFERIOR",
              interpretation_label="R1_CENTERING_NOT_CROSS_HOUSE"))
    assets = [y_path, arrays_path, F1 / "templates/CANDIDATE_SUPPORT.csv",
              F1 / "protocol/frozen/HOUSE03_F1_TRUTH_PANEL_12.tsv",
              OLD / "TARGET_DATA_FREEZE.json", OLD / "F1_PRIMARY_RESULT.json",
              OLD / "NOMINAL_FULL624_TARGET_METRICS.csv",
              OLD / "STATE0_FULL624_TARGET_METRICS.csv",
              ROOT / "evidence/aod_house03_f1_full624_20260927/TEMPLATE_FREEZE.json",
              F1 / "amplitude_implementation/amplitude_readout.py",
              F1 / "execution/score_amended_f1_vm.py",
              F1 / "protocol/evaluate_f1_full624.py",
              ROOT / "research/r1_centered_aod/R1_PREREG_20260929.md",
              ROOT / "research/r1_centered_aod/R1_BOOTSTRAP_FREEZE_20260929.json"]
    with (output / "ASSET_MANIFEST_SHA256.tsv").open("w", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["sha256", "bytes", "path"])
        for asset in assets:
            w.writerow([sha(asset), asset.stat().st_size, asset.relative_to(ROOT)])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    run(parser.parse_args().out)
