#!/usr/bin/env python3
"""Independently recompute primary marginal and RAW fair-U scores."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np


REPO = Path(__file__).resolve().parents[3]
E = REPO/'evidence/ocb_r2'
O = E/'mechanism_census_r0'


def table(path):
    with path.open(newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f, delimiter='\t'))


def full_score(reference, target):
    p = np.asarray(reference, dtype=float).mean(axis=0)
    y = np.asarray(target, dtype=float)
    return {
        'G_M_TIME': float(np.mean((p.mean(axis=1)-y.mean(axis=1))**2)),
        'G_M_SPACE': float(np.mean((p.mean(axis=0)-y.mean(axis=0))**2)),
        'G_M_FULL': float(np.mean((p-y)**2)),
    }


def fair_u(reference, target):
    x = reference.reshape(3, 300).astype(float)
    y = target.reshape(300).astype(float)
    fit = sum(float(np.linalg.norm(x[i]-y)) for i in range(3))/3
    diversity = sum(float(np.linalg.norm(x[i]-x[j])) for i in range(3) for j in range(i+1, 3))/6
    return fit-diversity


def main():
    s2, s2x = table(E/'OCB_R2_S2_DISCOVERY_RUNLIST_32.tsv'), table(E/'s2x/OCB_R2_S2X_RUNLIST_32.tsv')
    indexed = {}
    for r in s2:
        indexed[(f"X{int(r['config_index']):02d}", r['source_id'], int(r['replicate_index']))] = r['run_id']
    for r in s2x:
        indexed[(r['crossover_context'], r['source_id'], int(r['run_id'].rsplit('_r', 1)[1]))] = r['run_id']
    assert len(indexed) == 64
    observations = {run_id: np.load(O/'inputs'/f'{run_id}.pooled.npy', allow_pickle=False)>0
                    for run_id in indexed.values()}
    results = table(O/'pass1/R0_TARGET_EFFECTS.tsv')
    assert len(results) == 64
    maximum = {key: 0. for key in ('G_M_TIME', 'G_M_SPACE', 'G_M_FULL', 'G_RAW')}
    for r in results:
        c, s, a, omit = r['context'], r['truth_source'], r['alternative_source'], int(r['target_replicate'])
        target = observations[indexed[(c, s, omit)]]
        truth = np.stack([observations[indexed[(c, s, k)]] for k in range(1, 5) if k != omit])
        alternative = np.stack([observations[indexed[(c, a, k)]] for k in range(1, 5) if k != omit])
        ts, als = full_score(truth, target), full_score(alternative, target)
        expected = {name: als[name]-ts[name] for name in ts}
        expected['G_RAW'] = fair_u(alternative, target)-fair_u(truth, target)
        for name, value in expected.items():
            difference = abs(value-float(r[name]))
            maximum[name] = max(maximum[name], difference)
            assert difference < 1e-12, (r['run_id'], name, difference)
    output = dict(decision='R0_INDEPENDENT_PRIMARY_ARITHMETIC_PASS', targets=64,
                  max_absolute_difference=maximum, independent_formula=True)
    (O/'R0_INDEPENDENT_ARITHMETIC_CHECK.json').write_text(json.dumps(output, indent=2, sort_keys=True)+'\n')
    print(json.dumps(output, sort_keys=True))


if __name__ == '__main__':
    main()
