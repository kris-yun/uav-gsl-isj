# PF-DEI candidate-conditioned residual Set-NRE implementation freeze

Date: 2026-08-29  
Execution status: H01 existing-bank development diagnostic only

## Target

For a frozen Classic PMFS carrier posterior `q(s)` and the currently visible
measured sensing blocks `D`, estimate the conditional correlation ratio

`r(s,D,q) = p_sim(s | D,q) / q(s)`.

The corrected diagnostic posterior is evaluated once as

`q_corr(s|D) proportional to q(s) exp(log r_theta(s,D,q))`.

All arithmetic involving `q` is performed in log space. No PMFS probability is
clipped, tempered, reset, or blended.

## Contrastive sampling

For every simulated pseudo-observation:

1. select one frozen empirical PMFS posterior `q`;
2. draw the positive source `s+ ~ q`;
3. draw a nuisance member `h` and generate `D` from `(s+,h)`;
4. construct every candidate predictive set from the other seven members only;
5. draw `s- ~ q` independently and pair it with the same `D`;
6. use one positive and one negative BCE term.

Using the same `q` for both positive and negative source marginals prevents a
classifier from winning solely from candidate probability. The class signal is
the dependence between source and simulated observation. The held-out nuisance
member is absent for both positive and negative candidates.

## Fixed representation and network

- physical bank: existing `PF_DEI_V3_HISTORICAL_NATIVE_BANK_V1` only;
- sensor: frozen persistent physical-to-measured forward operator;
- block: the exact ten samples consumed by one StopAndMeasure block;
- historical trajectories 0..9 use the previously parity-proven runtime block
  manifest; map-only trajectories use the same initial-tail/later-arrival rule;
- member transform: `log1p(measured_ppm / 0.1)`;
- member encoder: shared MLP over observation, prediction, signed residual and
  absolute residual;
- member Set++ pool: mean, maximum, standard deviation and sqrt-normalized sum;
- block encoder: shared MLP conditioned on candidate geometry, block geometry
  and PMFS-posterior summaries;
- visible-block Set++ pool: the same four permutation-invariant moments;
- scalar output: candidate log-ratio.

Forbidden: TCN, CNN, RNN, Transformer, attention, TrajCast, GADEN regeneration,
A0, temperature, posterior reset and blend coefficient.

## Fixed training

- one seed only: `3101`;
- optimizer: AdamW, learning rate `3e-4`, weight decay `1e-4`;
- hidden width: 32;
- maximum steps: 12,000;
- train trajectories: 0..24;
- simulated validation trajectories: 25..29;
- checkpoint: minimum simulated validation BCE only;
- no architecture, learning-rate, member, threshold or outcome sweep.

Historical H01 measured observations and the evaluation truth carrier are not
opened during training. After training, one script scores all H01 seeds0..9 at
all five source updates before emitting any performance summary.
