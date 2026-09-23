import json
from pathlib import Path
import numpy as np
import pandas as pd
import zstandard as zstd

T = 200
TH = 0.1
TRUTH = np.array([-0.4, -2.9], dtype=float)
NULL_REPS = 500
SEED = 20260923
STATIC_REF = 20.5

def pick(df, names):
    d = {c.lower(): c for c in df.columns}
    for n in names:
        if n in d:
            return d[n]
    raise KeyError((names, list(df.columns)))

def rank_desc(score):
    return pd.Series(-np.asarray(score, float)).rank(method="average").to_numpy(float)

def rank_asc(score):
    return pd.Series(np.asarray(score, float)).rank(method="average").to_numpy(float)

with open("/tmp/occupied_cells.csv.zst", "rb") as src, open("/tmp/occupied_cells.csv", "wb") as dst:
    zstd.ZstdDecompressor().copy_stream(src, dst)

ev = pd.read_csv("/tmp/occupied_cells.csv")
parity = pd.read_csv("/tmp/parity_all.csv")
sen = pd.read_csv("/tmp/sensor_trace.csv")
tim = pd.read_csv("/tmp/source_update_timing.csv").sort_values("source_update_id")
tm = tim.iloc[0]
update_t = float(tm["sim_time"])

terminal = parity[parity["terminal_leaf"].astype(int) == 1].copy().reset_index(drop=True)
terminal["truth_distance_m"] = np.hypot(
    terminal["expected_source_x"].astype(float) - TRUTH[0],
    terminal["expected_source_y"].astype(float) - TRUTH[1],
)
ids = terminal["candidate_id"].astype(str).tolist()
truth_i = int(terminal["truth_distance_m"].to_numpy().argmin())
truth_id = ids[truth_i]

obs = sen[sen["t_sim_s"].astype(float) <= update_t + 1e-6].copy().reset_index(drop=True)
w = int(tm["grid_width"]); h = int(tm["grid_height"])
cs = float(tm["cell_size"]); ox = float(tm["origin_x"]); oy = float(tm["origin_y"])
gx = np.floor((obs["x"].astype(float).to_numpy() - ox) / cs + 1e-9).astype(int)
gy = np.floor((obs["y"].astype(float).to_numpy() - oy) / cs + 1e-9).astype(int)
valid = (gx >= 0) & (gx < w) & (gy >= 0) & (gy < h)
obs = obs.loc[valid].reset_index(drop=True)
gx = gx[valid]; gy = gy[valid]
path_cells = gy * w + gx

measured_y = (obs["measured_gas_ppm"].astype(float).to_numpy() > TH).astype(np.int8)
true_y = (obs["true_gas_ppm"].astype(float).to_numpy() > TH).astype(np.int8)

cells = np.array(sorted(set(map(int, path_cells))), dtype=int)
cell_to_j = {c:j for j,c in enumerate(cells)}
path_j = np.array([cell_to_j[int(c)] for c in path_cells], dtype=int)

cand_col = pick(ev, ["candidate_id","candidate","source_candidate"])
cell_col = pick(ev, ["cell_index","cell","grid_index"])
cand_to_i = {c:i for i,c in enumerate(ids)}
q = np.zeros((len(ids), len(cells)), dtype=float)

e = ev[ev[cand_col].astype(str).isin(cand_to_i) & ev[cell_col].astype(int).isin(cell_to_j)].copy()
# occupied_cells is one occupied-cell indicator per internal step; aggregate to marginal occupancy probability.
grp = e.groupby([e[cand_col].astype(str), e[cell_col].astype(int)]).size()
for (cid, cell), count in grp.items():
    q[cand_to_i[str(cid)], cell_to_j[int(cell)]] = float(count) / T

q_path = q[:, path_j]

def hit_support(y):
    mask = y.astype(bool)
    if not np.any(mask):
        return np.full(len(ids), np.nan)
    return q_path[:, mask].mean(axis=1)

def brier(y):
    return ((q_path - y[None, :]) ** 2).mean(axis=1)

def contrast(y):
    hit = y.astype(bool); miss = ~hit
    if not np.any(hit) or not np.any(miss):
        return np.full(len(ids), np.nan)
    return q_path[:, hit].mean(axis=1) - q_path[:, miss].mean(axis=1)

m_support = hit_support(measured_y)
t_support = hit_support(true_y)
m_brier = brier(measured_y)
t_brier = brier(true_y)
m_contrast = contrast(measured_y)
t_contrast = contrast(true_y)

m_rank = rank_desc(m_support)
t_rank = rank_desc(t_support)
mb_rank = rank_asc(m_brier)
tb_rank = rank_asc(t_brier)
mc_rank = rank_desc(m_contrast)
tc_rank = rank_desc(t_contrast)

native_rank = rank_desc(terminal["expected_score"].astype(float).to_numpy())

# Motion diagnostic only: no threshold enters scoring.
xy = obs[["x","y"]].astype(float).to_numpy()
disp = np.zeros(len(obs), dtype=float)
if len(obs) > 1:
    disp[1:] = np.linalg.norm(np.diff(xy, axis=0), axis=1)
moving = disp > 1e-6

# Destructive null: circularly shift complete measured hit sequence relative to fixed path.
rng = np.random.default_rng(SEED)
null_ranks = []
n = len(measured_y)
for _ in range(NULL_REPS):
    k = int(rng.integers(1, n))
    y0 = np.roll(measured_y, k)
    s0 = hit_support(y0)
    null_ranks.append(float(rank_desc(s0)[truth_i]))
null_ranks = np.asarray(null_ranks, float)
actual_rank = float(m_rank[truth_i])
frac = float(np.mean(null_ranks <= actual_rank))

g1 = bool(actual_rank < STATIC_REF)
g2 = bool(float(t_rank[truth_i]) < STATIC_REF)
g3 = bool(frac <= 0.05)
passed = bool(g1 and g2 and g3)

out = {
    "contract": "ACI_CONTINUOUS_CHANNEL_H01_ZERO_GATE_V1",
    "date": "2026-09-23",
    "input_run": "H01_R2026092201",
    "source_update_time_s": update_t,
    "gas_threshold_ppm": TH,
    "terminal_candidate_count": len(ids),
    "path_sample_count": int(len(obs)),
    "path_unique_grid_cells": int(len(cells)),
    "measured_hit_count": int(measured_y.sum()),
    "measured_unique_hit_cells": int(len(set(path_cells[measured_y.astype(bool)]))),
    "true_hit_count": int(true_y.sum()),
    "true_unique_hit_cells": int(len(set(path_cells[true_y.astype(bool)]))),
    "measured_hits_while_moving": int(np.sum(measured_y.astype(bool) & moving)),
    "true_hits_while_moving": int(np.sum(true_y.astype(bool) & moving)),
    "truth_candidate_id_evaluation_only": truth_id,
    "truth_candidate_distance_m": float(terminal.loc[truth_i, "truth_distance_m"]),
    "ranks": {
        "native_pmfs": float(native_rank[truth_i]),
        "static_low_occupancy_reference": STATIC_REF,
        "measured_hit_support_primary": actual_rank,
        "true_hit_support_physical_diagnostic": float(t_rank[truth_i]),
        "measured_full_path_brier_secondary": float(mb_rank[truth_i]),
        "true_full_path_brier_secondary": float(tb_rank[truth_i]),
        "measured_hit_minus_miss_contrast_secondary": float(mc_rank[truth_i]),
        "true_hit_minus_miss_contrast_secondary": float(tc_rank[truth_i]),
    },
    "truth_scores": {
        "measured_hit_support": float(m_support[truth_i]),
        "true_hit_support": float(t_support[truth_i]),
        "measured_brier": float(m_brier[truth_i]),
        "true_brier": float(t_brier[truth_i]),
        "measured_contrast": float(m_contrast[truth_i]),
        "true_contrast": float(t_contrast[truth_i]),
    },
    "circular_shift_null": {
        "repetitions": NULL_REPS,
        "seed": SEED,
        "truth_rank_median": float(np.median(null_ranks)),
        "truth_rank_q05": float(np.quantile(null_ranks, 0.05)),
        "truth_rank_q95": float(np.quantile(null_ranks, 0.95)),
        "fraction_as_good_or_better_than_actual": frac,
    },
    "gate": {
        "measured_hit_support_better_than_20p5": g1,
        "true_hit_support_better_than_20p5": g2,
        "circular_shift_fraction_lte_0p05": g3,
        "pass": passed,
    },
    "interpretation": "PASS_H01_ACI_CONTINUOUS_CHANNEL_ZERO_GATE" if passed else "NO_GO_H01_ACI_CONTINUOUS_CHANNEL_ZERO_GATE",
    "note": "Candidate scores are source-blind. Truth location is used only after score freeze for evaluation. Primary hit-support uses the continuous pre-update path; the circular-shift null preserves the complete measured hit temporal pattern and candidate hitMaps while destroying hit-location/path association."
}

outdir = Path("evidence/aci_continuous_cause_v1")
outdir.mkdir(parents=True, exist_ok=True)
(outdir / "H01_ACI_CONTINUOUS_CHANNEL_ZERO_GATE_RESULT_20260923.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")

md = f"""# H01 ACI continuous-channel zero gate

Date: 2026-09-23

Status: **{out['interpretation']}**

Frozen continuous stream through source update {update_t:.3f} s:
- path samples: {len(obs)}
- unique path cells: {len(cells)}
- measured hits (> {TH} ppm): {int(measured_y.sum())}, unique hit cells {out['measured_unique_hit_cells']}, moving-hit samples {out['measured_hits_while_moving']}
- physical true-gas hits: {int(true_y.sum())}, unique hit cells {out['true_unique_hit_cells']}, moving-hit samples {out['true_hits_while_moving']}
- terminal candidates: {len(ids)}

| source-blind score | truth rank |
|---|---:|
| Native PMFS reference | {native_rank[truth_i]:.2f}/{len(ids)} |
| frozen static low-occupancy reference | {STATIC_REF:.2f}/{len(ids)} |
| **measured positive-hit support (primary)** | **{m_rank[truth_i]:.2f}/{len(ids)}** |
| true-gas positive-hit support (physical diagnostic) | {t_rank[truth_i]:.2f}/{len(ids)} |
| measured full-path Brier (secondary) | {mb_rank[truth_i]:.2f}/{len(ids)} |
| true full-path Brier (secondary) | {tb_rank[truth_i]:.2f}/{len(ids)} |
| measured hit-minus-miss contrast (secondary) | {mc_rank[truth_i]:.2f}/{len(ids)} |
| true hit-minus-miss contrast (secondary) | {tc_rank[truth_i]:.2f}/{len(ids)} |

## Circular-shift destructive null

- repetitions: {NULL_REPS}
- null truth-rank median: {np.median(null_ranks):.2f}
- null truth-rank 5-95%: {np.quantile(null_ranks,.05):.2f}-{np.quantile(null_ranks,.95):.2f}
- fraction null as good or better than actual: {frac:.4f}

The null circularly shifts the complete measured binary hit sequence against the unchanged robot path. Hit count, temporal clustering, sensor-memory pattern, path, dwell pattern, and all candidate mean hitMaps are preserved; only the location of effects along the path is destroyed.

## Predeclared gate

- measured hit-support truth rank < 20.5: **{g1}**
- physical true-hit support truth rank < 20.5: **{g2}**
- null as-good-or-better fraction <= 0.05: **{g3}**
- **PASS: {passed}**

""" + (
    "The continuous effect channel contains source-identifying information strong enough to justify an ACI filter-vs-smoother prototype. The next test must use the frozen ACI causal-information principle; do not jump directly to a generic particle-filter localization method.\n"
    if passed else
    "The continuous pre-update effect locations do not pass the source-identity prerequisite for ACI on H01. Do not implement or tune an ACI smoother to rescue this case; move to a different mother mechanism.\n"
)
(outdir / "H01_ACI_CONTINUOUS_CHANNEL_ZERO_GATE_RESULT_20260923.md").write_text(md)
print(json.dumps(out, indent=2, sort_keys=True))
