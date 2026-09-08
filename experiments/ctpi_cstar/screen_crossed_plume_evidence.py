"""LOHO screen of event-level plume evidence on crossed source interventions.

This is a development screen, not a closed-loop or novelty claim. Parameters
are selected using source labels from two Houses and evaluated once on the
third. Candidate support, routes and observations are otherwise untouched.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
from pathlib import Path

import numpy as np


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def candidates(path, spacing=0.3):
    with path.open(newline='') as handle:
        rows = list(csv.DictReader(handle))
    xy = np.array([[float(r['x']), float(r['y'])] for r in rows])
    # PMFS scale=3 on the 0.1 m qualified map. Quantize relative to the actual
    # candidate origin; no coordinate rounding or truth-centred crop.
    origin = xy.min(axis=0)
    index = np.rint((xy - origin) / 0.1).astype(int)
    keep = (index[:, 0] % round(spacing / 0.1) == 0) & (index[:, 1] % round(spacing / 0.1) == 0)
    return xy[keep]


def causal_smooth(v, window):
    out = np.empty_like(v)
    for i in range(len(v)):
        out[i] = v[max(0, i-window+1):i+1].mean(axis=0)
    return out


def estimate(case, candidate_xy, parameter):
    sigma0, spread, wind_window, tau_s, power, direction_sign = parameter
    rows = case['rows'][::5]  # one distinct event per second
    pose = np.array([r['pose_xy'] for r in rows], dtype=float)
    wind = causal_smooth(np.array([r['wind_uv'] for r in rows], dtype=float), wind_window)
    gas = np.log1p(np.array([r['gas_ppm'] for r in rows], dtype=float))
    speed = np.linalg.norm(wind, axis=1)
    unit = direction_sign * wind / np.maximum(speed[:, None], 1e-8)
    displacement = pose[:, None, :] - candidate_xy[None, :, :]
    along = (displacement * unit[:, None, :]).sum(axis=2)
    cross = displacement[:, :, 0] * unit[:, None, 1] - displacement[:, :, 1] * unit[:, None, 0]
    sigma = sigma0 + spread * np.maximum(along, 0.)
    response = np.where(along > 0., np.exp(-.5 * (cross / sigma) ** 2) /
                        np.maximum(along + .3, .3) ** power, 0.)
    # Causal first-order sensor state, initialized at zero as in the generator.
    alpha = 1. - math.exp(-1. / tau_s)
    state = np.zeros(response.shape[1])
    filtered = np.empty_like(response)
    for i in range(len(response)):
        state += alpha * (response[i] - state)
        filtered[i] = state
    # Candidate-specific non-negative release amplitude is a nuisance state.
    # The fixed ridge prevents an arbitrarily tiny footprint from exploding.
    energy = (filtered * filtered).sum(axis=0) + 1e-6
    amplitude = np.maximum(0., filtered.T @ gas) / energy
    residual = gas[:, None] - filtered * amplitude[None, :]
    sse = (residual * residual).sum(axis=0)
    estimate_xy = candidate_xy[int(np.argmin(sse))]
    truth = np.asarray(case['source_xy'])
    error = float(np.linalg.norm(estimate_xy - truth))
    true_index = int(np.argmin(np.linalg.norm(candidate_xy - truth, axis=1)))
    rank = int(np.argsort(sse).tolist().index(true_index) + 1)
    return error, rank, estimate_xy.tolist(), float(sse[true_index]), float(sse.min())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--assets', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    cases = []
    supports = {}
    for house in ('H01', 'H02', 'H03'):
        manifest_path = args.assets / 'manifests' / f'{house}.json'
        manifest = json.loads(manifest_path.read_text())
        support_path = args.assets / 'maps' / house / 'candidate.csv'
        supports[house] = candidates(support_path)
        for episode in manifest['m1_episodes']:
            cases.append(dict(house=house, episode_id=episode['episode_id'],
                              transport=episode['transport_intervention_id'],
                              release=episode['release_intervention_id'],
                              source_xy=episode['source_xyz_m'][:2],
                              rows=read_jsonl(args.assets / episode['history_trace_path']),
                              history_sha256=episode['history_trace_sha256']))
    # Verify actual crossed interventions before using source contrasts.
    pairs = []
    for house in ('H01', 'H02', 'H03'):
        group = [c for c in cases if c['house'] == house]
        for a, b in itertools.combinations(group, 2):
            if a['source_xy'] != b['source_xy'] and a['transport'] == b['transport'] and a['release'] == b['release']:
                pairs.append([a['episode_id'], b['episode_id']])
    if len(pairs) != 6:
        raise ValueError(f'CROSSED_INTERVENTION_COUNT:{len(pairs)}')
    grid = list(itertools.product((.25, .5, 1.), (.15, .3, .6), (1, 5, 15), (1.2, 3.), (.5, 1.), (-1., 1.)))
    folds = []
    for heldout in ('H01', 'H02', 'H03'):
        train = [c for c in cases if c['house'] != heldout]
        scored = []
        for parameter in grid:
            values = [estimate(c, supports[c['house']], parameter)[0] for c in train]
            scored.append((float(np.mean(values)), parameter))
        _, selected = min(scored)
        rows = []
        for case in [c for c in cases if c['house'] == heldout]:
            error, rank, estimate_xy, true_sse, best_sse = estimate(case, supports[heldout], selected)
            rows.append(dict(episode_id=case['episode_id'], error_m=error, true_rank=rank,
                             estimate_xy=estimate_xy, true_sse=true_sse, best_sse=best_sse))
        folds.append(dict(heldout_house=heldout, selected_parameter=dict(zip(
              ('sigma0','spread','wind_window_s','tau_s','distance_power','direction_sign'), selected)),
              mean_error_m=float(np.mean([r['error_m'] for r in rows])), rows=rows))
    report = dict(contract='CSTAR_CROSSED_PLUME_EVIDENCE_LOHO_V1',
                  verdict='DEVELOPMENT_SCREEN_ONLY', crossed_pairs=pairs,
                  parameter_count=len(grid), folds=folds,
                  source_truth_runtime_input=False, source_truth_training_evaluator_only=True,
                  code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  limitations=['exposed development data','not PMFS closed loop','no independent confirmation',
                               'candidate rate is profiled, not integrated under a calibrated prior'])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps([{k:v for k,v in f.items() if k!='rows'} for f in folds], indent=2))


if __name__ == '__main__':
    main()
