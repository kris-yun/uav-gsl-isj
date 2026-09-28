#!/usr/bin/env python3
"""Join committed TCMA adequacy to the frozen AEC source-rank outcomes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'evidence/tcma_d0'
AEC = ROOT / 'evidence/aec_d0'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def corr(x, y):
    if len(np.unique(x)) < 2 or len(np.unique(y)) < 2:
        return None
    value = float(spearmanr(x, y).statistic)
    return value if np.isfinite(value) else None


def main():
    freeze_path = OUT / 'ADEQUACY_FREEZE.json'
    freeze = json.loads(freeze_path.read_text())
    assert freeze['rank_outcomes_read'] is False
    for name, digest in freeze['output_sha256'].items():
        assert sha(OUT / name) == digest, name

    parent_result = json.loads((AEC / 'AEC_D0_RESULT.json').read_text())
    parent_source = AEC / 'AEC_D0_SOURCE_RESULTS.csv'
    assert sha(parent_source) == parent_result['joined_source_results_sha256']
    source = pd.read_csv(OUT / 'SOURCE_ADEQUACY.csv')
    wide = source.pivot(index=['house', 'source_id'], columns='operator',
                        values=['mean_adequacy', 'target_count']).reset_index()
    wide.columns = [f'{a}_{b}' if b else a for a, b in wide.columns]
    assert len(wide) == 21
    outcomes = pd.read_csv(parent_source)
    joined = wide.merge(outcomes[['house', 'source_id', 'target_paths',
                                  'mean_rank_u', 'mean_rank_rawu', 'delta_g']],
                        on=['house', 'source_id'], validate='one_to_one')
    assert len(joined) == 21
    assert (joined.target_count_u == joined.target_count_rawu).all()
    assert (joined.target_count_u == joined.target_paths).all()
    joined['delta_a'] = joined.mean_adequacy_rawu - joined.mean_adequacy_u
    joined['sign_agree'] = np.where((joined.delta_a != 0) & (joined.delta_g != 0),
                                    np.sign(joined.delta_a) == np.sign(joined.delta_g),
                                    np.nan)
    joined['selected_operator'] = np.where(joined.delta_a > 0, 'rawu', 'u')
    joined['selected_rank'] = np.where(joined.delta_a > 0,
                                       joined.mean_rank_rawu, joined.mean_rank_u)
    joined = joined.sort_values(['house', 'source_id'])
    source_path = OUT / 'TCMA_D0_SOURCE_RESULTS.csv'
    joined.to_csv(source_path, index=False, lineterminator='\n')

    houses = {}
    for house, g in joined.groupby('house', sort=True):
        x = g.delta_a.to_numpy()
        y = g.delta_g.to_numpy()
        valid = g.sign_agree.dropna()
        mean_u = float(g.mean_rank_u.mean())
        mean_rawu = float(g.mean_rank_rawu.mean())
        selected = float(g.selected_rank.mean())
        loo = {}
        for row in g.itertuples(index=False):
            subset = g[g.source_id != row.source_id]
            loo[row.source_id] = corr(subset.delta_a.to_numpy(), subset.delta_g.to_numpy())
        houses[house] = dict(
            source_count=int(len(g)), target_count=int(g.target_paths.sum()),
            spearman_delta_a_vs_delta_g=corr(x, y),
            nonzero_sign_count=int(len(valid)),
            sign_agreement=float(valid.mean()) if len(valid) else None,
            always_u_mean_rank=mean_u, always_rawu_mean_rank=mean_rawu,
            adequacy_selector_mean_rank=selected,
            selector_no_worse_than_best_fixed=selected <= min(mean_u, mean_rawu) + 1e-12,
            selector_strictly_better_than_best_fixed=selected < min(mean_u, mean_rawu) - 1e-12,
            positive_delta_a_sources=int((x > 0).sum()),
            negative_delta_a_sources=int((x < 0).sum()),
            zero_delta_a_sources=int((x == 0).sum()),
            loo_spearman=loo,
            secondary_spearman_adequacy_vs_negative_rank={
                'u': corr(g.mean_adequacy_u.to_numpy(), -g.mean_rank_u.to_numpy()),
                'rawu': corr(g.mean_adequacy_rawu.to_numpy(), -g.mean_rank_rawu.to_numpy()),
            },
        )

    # Each conjunct is reported independently. A failed conjunct cannot be
    # rescued by an exploratory interpretation of another House.
    g1 = all(v['spearman_delta_a_vs_delta_g'] is not None and
             v['spearman_delta_a_vs_delta_g'] > 0 for v in houses.values())
    g2 = all(v['sign_agreement'] is not None and
             v['sign_agreement'] > 0.5 for v in houses.values())
    g3 = all(v['spearman_delta_a_vs_delta_g'] is not None and
             v['spearman_delta_a_vs_delta_g'] > -0.5 for v in houses.values())
    g4 = (all(v['selector_no_worse_than_best_fixed'] for v in houses.values()) and
          sum(v['selector_strictly_better_than_best_fixed'] for v in houses.values()) >= 2)
    # Conservative operationalization of the preregistered single-source
    # condition: deletion of any source must preserve positive association.
    g5 = all(all(r is not None and r > 0 for r in v['loo_spearman'].values())
             for v in houses.values())
    gates = dict(positive_spearman_all_houses=g1, sign_agreement_all_houses=g2,
                 no_strong_reversal=g3, selector_noninferiority_and_two_improvements=g4,
                 leave_one_source_out_positive_all_houses=g5)
    decision = ('TCMA_D0_CROSS_HOUSE_TARGET_CONDITIONED_SIGNAL' if all(gates.values())
                else 'TCMA_D0_NO_CROSS_HOUSE_TARGET_CONDITIONED_SIGNAL')
    result = dict(decision=decision, gates=gates, houses=houses,
                  physical_sources=int(len(joined)), source_unit=True,
                  source_aware_oracle_diagnostic=True, no_fresh_confirmation=True,
                  adequacy_freeze_sha256=sha(freeze_path),
                  frozen_outcome_sha256=sha(parent_source),
                  source_results_sha256=sha(source_path),
                  percentile_is_not_conformal=True,
                  target_and_simulator_sse_units_not_calibrated=True)
    result_path = OUT / 'TCMA_D0_RESULT.json'
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
