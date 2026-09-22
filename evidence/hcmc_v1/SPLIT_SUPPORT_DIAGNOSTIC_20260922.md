# HCMC V1 — directional and split-support diagnostic

Date: 2026-09-22
Status: **FULL-SUPPORT SYNERGY CONFIRMED / LOCAL REDUNDANCY NOT ESTABLISHED**

This diagnostic keeps the frozen p=1..4 powers and 1/2/4/8-cell scales. It does not alter HCMC V1.

## Native R2 final-update results

| support used for structure functions | mean endpoint error | cases improved |
|---|---:|---:|
| full x+y support | 2.4488 m | 6/6 |
| x-directed pairs only | 3.1084 m | 5/6 |
| y-directed pairs only | 3.4562 m | 5/6 |
| disjoint macro-spatial fold 0 | 2.9111 m | 5/6 |
| disjoint macro-spatial fold 1 | 3.9159 m | 5/6 |

The two macro-spatial folds assign cells by
`((grid_i // 4 + grid_j // 4) mod 2)`
and calculate structure functions only on pairs whose cells remain inside the retained fold.

## Split-fold candidate-score agreement

Spearman correlation between the two disjoint fold candidate scores:

- House01 seed0: -0.008
- House01 seed1: 0.054
- House02 seed0: 0.223
- House02 seed1: 0.266
- House03 seed0: 0.126
- House03 seed1: 0.326

## Interpretation

The data do **not** support a claim that the same HCMC candidate ranking is redundantly present in every local spatial subset.

Instead:

1. either direction alone still contains useful multiscale information;
2. either large disjoint subset usually improves the endpoint;
3. the strongest and most consistent result requires pooling broad spatial support across directions.

Therefore the current physical interpretation is:

> HCMC is a broad-support statistical consistency test over a turbulent scalar field, not a local plume cue.

This is consistent with two other HCMC diagnostics:

- early source updates can be unreliable before enough support accumulates;
- the H02-SA controlled asset becomes unidentifiable when scalar excitation is essentially absent.

## Consequence

Do not use split-half score agreement as the frozen online maturity gate: this discovery set shows that the two halves need not produce highly correlated candidate rankings.

A future identifiability gate should instead quantify whether the frozen multiscale structure functions themselves are estimable with adequate support/dynamic range, without source truth.
