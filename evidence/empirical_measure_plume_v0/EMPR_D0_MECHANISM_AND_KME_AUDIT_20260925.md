# EMPR D0 — Empirical-Measure Plume Representation

Date: 2026-09-25

Decision: **MECHANISM_POSITIVE / GENERIC_MEASURE_MODEL_NOT_ADVANCED**

No new simulation, neural measure model, or closed-loop experiment is authorized.

## 1. Mechanism

For each probe q and one short observation window, represent the ten log-concentration samples as the empirical measure

  mu_hat_q = (1/T) sum_t delta_{log(1+C_tq)}.

D1R evidence shows that source identity is carried mainly by the short-window amplitude distribution at each probe rather than by sample order.

## 2. Order-destruction evidence

On hard neighboring-source pairs:
- binary encounter-rate representation: fresh pair error about 40.7% / 42.0%;
- per-probe mean log-ppm: about 35.1% / 32.8%;
- amplitude mean+std+hit: about 32.4% / 31.8%;
- orderless quantile summary: about 29.8% / 28.6%;
- full ordered 10x30 log-ppm: about 27.1% / 26.9%;
- per-probe sorted ten amplitudes, with temporal order fully destroyed: about 26.4% / 26.7%.

Thus removing temporal order does not reduce the available local source-distinguishability signal.

## 3. Proper-score evidence

Common shrinkage-LDA with train-only calibration:

Fresh direction A:
- ordered full log-ppm: -2.737 bit;
- sorted/orderless full amplitudes: -2.723 bit;
- per-probe empirical-distribution summary (mean,std,q25,q50,q75,max,hit): -2.369 bit.

Fresh direction B:
- ordered full log-ppm: -2.509 bit;
- sorted/orderless full amplitudes: -2.499 bit;
- empirical-distribution summary: -2.106 bit.

The summary representation improves probability quality rather than merely source rank.

## 4. Unified champion re-run

Under a unified implementation using exactly 6 realizations/source for fitting, 2 for train-only calibration and the opposite 8 for fresh evaluation:

- quantile empirical-summary direction A: -2.006 bit, top1 57.6%;
- direction B: -2.040 bit, top1 60.0%.

This is the current ordinary champion that any EMPR method must beat.

## 5. Principled kernel mean embedding negative test

Replace hand summaries with an RBF kernel mean embedding of each probe's empirical measure.

Per-probe RBF centers are training-only empirical quantiles; K in {3,5} and bandwidth scale in {0.5,1,2} are selected by the two training-only calibration realizations. Append hit rate. Use the same shrinkage-LDA and temperature pipeline.

Best fresh results:
- direction A: -2.790 bit, top1 44.9%;
- direction B: -2.773 bit, top1 46.8%.

Therefore a generic characteristic measure embedding does not beat the hand-crafted empirical-distribution summary.

Do not promote a measure-valued neural architecture solely because the mother theory is recent.

## 6. Observation-count saturation

Using the same empirical-distribution summary, restrict each window to the first k frozen snapshots:

| snapshots k | direction A log2 / top1 | direction B log2 / top1 |
|---|---|---|
| 3 | -2.566 / 48.3% | -2.641 / 48.4% |
| 5 | -2.204 / 53.6% | -2.328 / 55.9% |
| 7 | -2.066 / 55.1% | -2.103 / 60.2% |
| 10 | -2.006 / 57.6% | -2.040 / 60.0% |

Most of the distributional benefit is present by roughly 5-7 registered snapshots.

These counts must not yet be converted into seconds because the physical sample interval has not been re-audited here.

## 7. Theory/prior-art boundary

Relevant far-domain families include distribution regression, conditional distribution estimation, neural networks on probability measures, and measure-valued learning.

These theories are not novel.

Targeted GSL/olfaction searches did not surface a direct method that treats each probe's short-window empirical concentration measure as the primary observation object for a PMFS source posterior. This is only a targeted prior-art screen, not a proof of novelty.

## 8. Decision

Retain the scientific fact:

> under the current observation protocol, source information is primarily encoded in short-window per-probe amplitude distributions rather than temporal order.

Retain the empirical-distribution summary as a strong ordinary baseline and likely auxiliary observation module.

Do NOT yet elevate EMPR to the main innovation because a principled generic measure embedding fails badly against the simple summary.

Any later learnable measure model must beat the quantile-summary champion on fresh proper score and transfer, not merely offer a newer mathematical vocabulary.