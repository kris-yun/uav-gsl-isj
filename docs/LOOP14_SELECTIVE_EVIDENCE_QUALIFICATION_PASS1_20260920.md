# Loop 14 — Selective Evidence Qualification: First Positive M2 Gate

Date: 2026-09-20
Branch: research/remote-paradigm-loop-20260919
Status: M2 promoted to ACTIVE CANDIDATE; still offline/development only.

## 1. Remote-domain paradigm

The candidate comes from recent **selective prediction / abstention** theory rather than experiment design.

Primary top-venue anchors:

- ICLR 2026 — Heng & Soh, *Know When to Abstain: Optimal Selective Classification with Likelihood Ratios*.
  - derives selection from the Neyman–Pearson likelihood-ratio principle;
  - explicitly studies covariate shift;
  - key lesson: reliable prediction may require rejecting observations for which correct and incorrect decisions cannot be separated.

- NeurIPS 2025 — Rabanser & Papernot, *What Does It Take to Build a Performant Selective Classifier?*
  - decomposes selective-classification error into Bayes noise, approximation error, ranking error, statistical noise and shift slack;
  - shows monotone confidence calibration alone does not repair a bad ordering/selection score.

- NeurIPS 2025 — Casacuberta & Kanade, *Selective Omniprediction and Fair Abstention*.
  - formalizes predictors that explicitly abstain at a cost rather than forcing a decision everywhere.

- COLT 2026 — Yu & Blanchard, *Distribution-Free Sequential Prediction with Abstentions*.
  - establishes sequential prediction/abstention tradeoffs under contaminated or adversarial streams.

## 2. Direct GSL collision screen

A targeted 2025/2026 search did not find a robotic gas/odor source-localization method whose core inference step is:
- selective **source-evidence assimilation**;
- abstain/neutral-update when the current candidate family is not physically distinguishable;
- then resume Bayes/PMFS updating once candidate-family separation is restored.

Recent OSL work still generally performs a belief update from each accepted measurement or uses confidence only for final source declaration.

This is distinct from route-level active observability:
- route/OED asks where to measure;
- this M2 asks whether the current measurement is admissible as **source-discriminative evidence**.

## 3. Project-specific physical object

For candidate source (s), let (z_{s,w,t}) be the M1 predictive representation under an admissible transport member (w).

Define:

[
D_{within}(t)
=
max_s max_{w,w'}
d(z_{s,w,t},z_{s,w',t}),
]

the largest same-source transport variation, and

[
D_{cross}(t)
=
min_{s
e s'}min_{w,w'}
d(z_{s,w,t},z_{s',w',t}),
]

the smallest cross-source separation across the transport family.

The natural selective-admissibility score is

[
A_t=lograc{D_{cross}(t)+epsilon}
{D_{within}(t)+epsilon}.
]

The physically interpretable zero boundary is not tuned:

[
A_t>0
iff
D_{cross}>D_{within}.
]

Meaning:
> even the closest two different-source transport realizations are farther apart than the worst same-source transport variation.

Only then is a source-specific update admissible.

If (A_tle 0), the source map is not sharpened by that evidence; the inference abstains / applies a neutral update.

## 4. Existing-data premise test

Data:
- current-runtime controlled factorial bundle;
- H01/H02/H03 × {SA,SB} × {fast,slow};
- horizons 60, 90, 120, 150, 180, 210, 240 s.

Representation:
- the same source-blind predictive proxy used for the current M1;
- source decision evaluated by matching held slow-wind representation to fast-wind source prototypes.

There are 21 House×horizon states, each producing two held-wind source decisions.

### Without selection

Mean held-wind decision accuracy:
- 69.05%.

### Rank by (A_t)

Top 75% coverage:
- 75.0% accuracy.

Top 50%:
- 86.36% accuracy.

Top 33%:
- 100% accuracy.

Top 25%:
- 100% accuracy.

### Natural zero boundary (A_t>0)

The states satisfying the non-overlap condition are:

- H01: 240 s.
- H02: 180, 210, 240 s.
- H03: 120, 150, 180, 210 s.

All of them have:
- held-wind source identity = 2/2.

Rejected states include:
- H02 60–150 s, where cross-source family distance is literally zero in the proxy;
- H03 90 s, where a conventional top-vs-second confidence score was highly confident but one source was wrong;
- H03 240 s, where transport families re-overlap and held-wind identity falls to 1/2;
- H01 60–210 s, where same-source transport variation exceeds robust cross-source separation.

This is important:
the gate is **not merely late-time acceptance**. H03 240 s is rejected even though earlier H03 120–210 s states are accepted.

## 5. Comparison with naive confidence selection

A conventional observation-to-prototype distance-ratio confidence score improved selective accuracy on average but admitted a dangerous failure:
- H03 90 s had very high apparent confidence for both observations while one source was wrong.

The candidate-family score (A_t) rejects H03 90 s because the source-conditioned transport families themselves overlap.

Thus the proposed selector is not simply posterior entropy or maximum probability.

## 6. Relation to previous project evidence

This result is consistent with the 2026-09-09 cross-House information audit, which independently concluded:

> conditional observability: assimilate candidate likelihood only after predicted source contrast exceeds transport interaction.

Loop 14 turns that empirical condition into a **selective inference object**:
candidate-family non-overlap determines whether a source update is admissible.

It also matches the 2026-09-14 physical-support audit principle:
posterior processing cannot create source information outside the effective sensing support.

## 7. Current M2 definition

Working name:

**Selective Source-Evidence Assimilation (SSEA)**

Role:
- M1 extracts predictive latent physical evidence.
- M2 estimates whether candidate source families remain separable under transport uncertainty.
- if not, it abstains from sharpening the PMFS source map.
- if yes, it passes the likelihood/source evidence to the normal map update.

This is an inference gate, not a planner and not an OED module.

## 8. Hard remaining gates

M2 is not yet validated.

It must still pass:

1. **time confound control** — a permuted or horizon-only selector must not explain the same accepted states.
2. **representation destructive control** — target-order-destroyed M1 should reduce/ruin (A_t)'s selective ordering.
3. **held transport member** — when a third transport member is available, compute (A_t) only on design members and evaluate selection on the unopened member.
4. **larger candidate support** — two-source factorial evidence is a premise test, not a full map test.
5. **coverage floor** — abstention cannot solve the task by refusing nearly everything.

## 9. Current 1+2 state

M1 MAIN:
- Predictive latent physical representation — ACTIVE PRIMARY.

M2 AUX:
- Selective Source-Evidence Assimilation — ACTIVE CANDIDATE after first positive gate.

M3 AUX:
- Structured shift-aware source region — ACTIVE CANDIDATE.

No closed-loop test is authorized.
