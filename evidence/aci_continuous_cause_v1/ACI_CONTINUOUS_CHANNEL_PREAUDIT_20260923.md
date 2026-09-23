# ACI continuous-cause channel pre-audit

Date: 2026-09-23
Status: ACTIVE MOTHER-IDEA SCREEN — ZERO-GATE ONLY

## Mother idea

Andreou, Chen & Bollt, *Assimilative causal inference*, Nature Communications 17, 1854 (2026), DOI 10.1038/s41467-026-68568-0.

ACI treats causal inference as a Bayesian inverse/data-assimilation problem: infer potential causes backward from observed effects, and quantify the information gained when future observations are included (smoother versus filter). It is designed for stochastic/turbulent systems, short records, incomplete observation, and single observed realizations.

This is not a generic “Bayesian PMFS update”. If advanced, the intended GSL transfer is:

source location + latent plume state -> continuous moving-sensor effects

and the source evidence would be obtained by backward cause smoothing / uncertainty reduction, rather than by comparing one source candidate's time-averaged hitMap with a stopped spatial map.

## Novelty boundary

Data assimilation and source-term inversion already exist in gas/atmospheric source estimation. Therefore “use data assimilation” is not a valid main innovation. The only viable novelty route is the 2026 ACI filter-vs-smoother causal-information principle combined with a moving UAV's continuous effect stream and latent plume state.

## Why this attacks a different PMFS failure

The preceding distributional-forward H01 test failed: high-order cross-cell plume phase did not add source identity to the final all-miss observation window.

ACI therefore receives a different zero-gate: do not mine more statistics from the same StopAndMeasure block. Test whether the *continuous pre-update sensor path*, which PMFS does not use as its source-update evidence stream, contains source identity in the locations of positive gas effects.

## Frozen H01 zero-gate

Run: H01_R2026092201.
Candidate forward bank: frozen 200-step standalone replay.
Real observation stream: every sensor sample from run start through source update 1 at 195.500216873 s.
Gas threshold: native PMFS `th_gas_present = 0.1 ppm`.

For each terminal source candidate, reconstruct its marginal 200-step occupancy probability q_s(cell).

Primary source-blind statistic for an observed binary hit sequence y(t):

`hit_support(s) = mean_t[q_s(cell(t)) | y(t)=1]`

Higher is better. Compute it independently for:
1. deployable asymmetric measured-gas hits;
2. physical true-gas hits (diagnostic only, never available online).

Secondary diagnostics:
- full-path Brier score over all samples;
- hit-minus-miss occupancy contrast;
- counts of hit samples, unique hit cells, and moving/stationary hit samples.

### Destructive null

Circularly shift the entire measured binary hit sequence relative to the fixed robot path, 500 repetitions, RNG seed 20260923.

This exactly preserves:
- measured hit count;
- temporal clustering / sensor-memory shape of the hit sequence;
- robot path and dwell pattern;
- every candidate hitMap.

It destroys only the association between *where on the path* the positive effects occurred and candidate plume support.

### Predeclared advancement gate

Advance to an actual ACI filter-vs-smoother prototype only if all are true:

1. measured-hit support truth rank is better than 20.5/121 (the strongest frozen H01 static low-occupancy reference);
2. true-gas-hit support truth rank is better than 20.5/121;
3. <= 5% of circular-shift nulls give the truth candidate a measured-hit support rank as good as or better than actual.

No threshold, path window, hit weighting, sensor deconvolution, or candidate score may be tuned after viewing this result.

A failure kills the present “continuous effect stream supplies the missing source-information channel” route before ACI is implemented.
