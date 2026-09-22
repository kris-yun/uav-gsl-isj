# Ruelle–Pollicott / transfer-operator resonance transfer — NO-GO

Date: 2026-09-22
Status: **NO-GO AS MAIN LINE**

## Mother idea

Dynamical-systems / statistical-physics transfer-operator theory:
microscopic chaotic trajectories can be unpredictable while correlation decay and mixing are governed by nontrivial Koopman/Perron–Frobenius spectral resonances (Ruelle–Pollicott resonances).

Recent scite anchors included:
- *Annealed Ruelle-Pollicott Resonances* (2026), arXiv:2608.05649.
- *Statistical periodicity in noise-induced order from Ruelle-Pollicott resonances* (2026), arXiv:2607.18771.
- *Koopman operator-based discussion on partial observation in stochastic systems* (J. Stat. Mech. 2025), DOI 10.1088/1742-5468/ae250b.

Public implementations used as mature operator-analysis references:
- https://github.com/deeptime-ml/deeptime
- https://github.com/dynamicslab/pykoopman

## GSL transfer tested

For every source candidate:
1. sample its simulated hit-probability field along the actual robot trajectory;
2. rank-uniformize both candidate and measured gas time series;
3. discretize into fixed state counts;
4. estimate lagged Markov transfer matrices;
5. compute nontrivial eigenvalues after removing the stationary eigenvalue 1;
6. match measured and candidate resonance multisets in the complex plane;
7. rank source hypotheses by mean resonance mismatch across fixed lags 1,2,5.

To avoid selecting one state count from results, a development consensus averaged candidate percentiles across 3,4,5,6 states.

## Joint old+new development result

Consensus:
- all-12 mean = **4.3507 m**
- pooled reduction = **24.78%**
- non-worse = **9/12**
- old six = **20.69%**, 5/6
- new six = **28.57%**, 4/6

## Destructive controls

Final-leaf permutation, 300 repetitions:
- null mean = **4.4018 m**
- null as good as/better than real = **44.67%**

Candidate-identity mismatch, 30 repetitions:
- null mean = **4.4341 m**
- null as good as/better than real = **36.67%**

These already fail the failure-informed mechanism gate, so further tuning or lag/state searches were stopped.

## Decision

The resonance framework is scientifically valid but the transferred statistic is not sufficiently source-specific on this development corpus.

Final verdict:
`RUELLE_POLLICOTT_GSL_TRANSFER_NO_GO_20260922`

Do not tune discretization state count, eigenvalue matching, or lag family on these same 12 cases.
