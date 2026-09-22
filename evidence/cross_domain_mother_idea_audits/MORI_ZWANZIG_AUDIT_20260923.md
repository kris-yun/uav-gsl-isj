# Cross-domain mother-idea audit 01 — Mori–Zwanzig projection / memory

Date: 2026-09-23  
Branch: `research/cross-domain-mother-idea-audits-20260923`  
Raw independent-plume data commit: `c5271515d565c343d2fd2a63c77bf0484f45772a`

Status: **DIRECT TRANSFER NO-GO / FULL MORI–ZWANZIG TEST DATA-INELIGIBLE**

This document intentionally does **not** define or name a gas-source-localization method. It tests whether a necessary mechanism of the remote-domain mother idea is present in the available data.

## 1. Why this idea was considered

The Mori–Zwanzig (MZ) projection formalism comes from statistical physics / reduced dynamics. After projecting a high-dimensional dynamical system onto partially observed variables, the exact reduced dynamics contains:

- an instantaneous / Markovian contribution;
- a memory contribution from past resolved states;
- orthogonal dynamics/noise representing unresolved degrees of freedom.

This is scientifically relevant to turbulent transport because stochastic plume realizations differ through unresolved turbulent degrees of freedom.

Recent cross-domain anchors retrieved with scite:

- de Wit et al., **Data-driven Mori–Zwanzig modeling of Lagrangian particle dynamics in turbulent flows**, PNAS, 2026, DOI `10.1073/pnas.2525390123`.
- Freitas et al., **Learning turbulent transport via Mori--Zwanzig graph neural networks**, 2026 preprint, DOI `10.48550/arxiv.2606.14918`.

The second work explicitly reports that finite memory is important for recovering intermittent heavy-tailed turbulent-transport statistics.

The question here is **not** whether MZ is a valid theory. The question is whether the currently available source-conditioned PMFS data contain a source-specific MZ-style memory signal that can justify transferring this mother idea into the localization problem.

## 2. Data used

Development only:

- old R2 House01/02/03 × seed0/1 = 6 cases;
- six now-unblinded true independent stochastic plume runs = 6 cases.

Total: 12 cases.

Critical new-run inventory:

- each independent run contains exactly one `source_update_0001`;
- each has the full 1500-step sensor/pose/wind trace;
- no missing source updates are reconstructed.

For each final source candidate, its source-conditioned simulated hit-probability field is sampled along the actual robot trajectory to obtain a scalar candidate sequence (q_s(t)).

This is a **static candidate field sampled along a dynamic trajectory**, not a full time-resolved source-conditioned plume rollout. That limitation matters for the final verdict.

## 3. Necessary-mechanism test

The minimum hypothesis tested was:

> If the correct source hypothesis explains unresolved turbulent memory, then delayed source-conditioned forcing should add predictive information beyond the instantaneous source-conditioned forcing, and this added value should be stronger for candidates near the true source than for wrong candidates.

A lightweight ridge reduced-dynamics model predicts log sensor concentration using:

- two past measured-sensor samples;
- current wind components;
- current candidate forcing (q_s(t)).

This is the **instantaneous baseline**.

The memory version additionally includes delayed candidate forcing

[
q_s(t-1),ldots,q_s(t-8).
]

No source truth enters training or score construction.

Two source-blind train/test protocols were used:

1. interleaved blocked train/test;
2. forward 60/40 train/test.

For every candidate define memory benefit as

[
Delta_s =
L_{m instantaneous}(s)-L_{m memory}(s),
]

so positive (Delta_s) means adding candidate memory improves held-out prediction.

The key diagnostic is the candidate nearest the true source, together with the association of (Delta_s) with source distance.

## 4. Endpoint numbers look superficially positive

Using candidate held-out prediction score to rank final leaves:

### Instantaneous candidate forcing only

all 12:
- mean endpoint ≈ **4.6165 m**
- pooled reduction vs Native ≈ **20.18%**
- non-worse: **8/12**

### Current + 8 delayed candidate forcing samples

all 12:
- mean endpoint ≈ **4.3931 m**
- pooled reduction ≈ **24.05%**
- non-worse: **8/12**

On the six new stochastic-plume cases:

- instantaneous: **28.54%**, 6/6;
- memory-8: **31.60%**, 5/6.

If evaluation stopped at the endpoint metric, this could look like evidence for the MZ transfer.

It is not.

## 5. Necessary source-specific memory condition fails

### Interleaved blocked split

For the candidate nearest the true source:

- adding 8-step candidate memory improves held-out prediction in only **3/12** cases;
- mean truth-nearest memory benefit is **negative**:
  (-1.85	imes10^{-6});
- mean Spearman correlation between memory benefit and negative source distance is approximately **-0.004**, effectively zero;
- mean percentile rank of the truth-nearest candidate by *memory benefit* is only **0.667**.

Thus delayed forcing does not systematically help the true-source neighborhood more than wrong candidates.

### Forward 60/40 split

The result is even less supportive:

- truth-nearest memory improves held-out prediction in only **1/12** cases;
- mean truth-nearest memory benefit:
  (-6.37	imes10^{-6});
- mean correlation between memory benefit and negative source distance: **0.181**;
- mean truth-nearest memory-benefit percentile: **0.558**, close to uninformative.

This is incompatible with the proposed necessary mechanism that the correct source should specifically explain the unresolved memory.

## 6. Residual-memory / whitening interpretation also fails

A second proxy ranked candidates by how much short-lag autocorrelation remained in the sensor residual after conditioning on current source forcing.

For a representative 10-lag residual-memory score:

- apparent endpoint reduction ≈ **16.47%**, 10/12.

But destructive controls invalidate the mechanism:

### Final-leaf score permutation, 300 repetitions

- real mean endpoint: **4.8315 m**
- permutation-null mean: **4.4435 m**
- fraction of nulls as good as or better than real: **0.82**

The random score-location assignment is usually better than the proposed residual-memory ranking.

### Temporal shifts

Shifting the candidate forcing relative to the sensor trace often performs similarly or better:

- shift 50 samples: mean **4.6874 m**, better than the real residual-memory score;
- shift 600 samples: mean **4.6836 m**, also better.

### Candidate-sequence shuffles

Several shuffled controls also match or beat the real score.

Therefore residual whitening is not credible source evidence in this development corpus.

## 7. What can be concluded

### Rejected

The following transfer claim is rejected:

> the correct source can be identified because its candidate history uniquely absorbs the non-Markovian memory left by unresolved turbulent plume dynamics.

The present data do not support that statement.

The small endpoint gain from adding delayed candidate terms is not accompanied by the required candidate-level source-specific predictive-memory effect.

This is exactly the kind of result that should be eliminated **before** giving the idea a method name.

### Not rejected

The Mori–Zwanzig formalism itself is not rejected.

A faithful MZ source-localization test would require candidate-conditioned **time-resolved dynamic rollouts** or equivalent resolved/unresolved state trajectories for every source hypothesis. The present PMFS bank supplies one static source-conditioned spatial hit-probability field at the recorded source update; sampling that static field along the robot path is only a weak proxy for an MZ memory kernel.

Therefore the stronger MZ program is marked:

`DATA-INELIGIBLE_WITH_CURRENT_CANDIDATE_BANK`

rather than being promoted or rescued.

## 8. Decision

Mother idea audit verdict:

`MORI_ZWANZIG_DIRECT_SOURCE_MEMORY_TRANSFER_NO_GO`

Do not:

- invent an MZ localization method from the current endpoint gain;
- tune the memory horizon against truth;
- call delayed PMFS features an MZ kernel;
- generate an expensive holdout for this transfer;
- continue to the CStar intervention gate.

The idea failed its **earlier necessary-mechanism gate**, so the screening loop moves to the next genuinely different remote-domain mother idea.

## 9. Screening lesson

The important distinction is:

> **prediction with more history** is not the same as **source-specific unresolved-memory identification**.

The latter is the scientific claim required to justify Mori–Zwanzig as the paper's mother idea, and that claim is not supported here.
