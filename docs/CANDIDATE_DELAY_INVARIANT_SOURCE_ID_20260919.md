# Candidate M1-B — Delay-Coordinate Invariant Measures for Turbulent Source Identity

Date: 2026-09-19
Branch: research/remote-paradigm-loop-20260919
Status: CANDIDATE / OFFLINE FALSIFICATION ONLY

## 0. Scientific thesis

When pointwise turbulent trajectories are unreliable because of chaos, intermittency, and transport variability, represent each observation history by an **empirical invariant measure in time-delay coordinates** and infer source identity from the dynamical distribution it induces, rather than from instantaneous concentration or a direct time-series classifier.

## 1. Remote-field provenance

### Primary top-journal anchor
- Physical Review Letters 135, 167202 (2025):
  Jonah Botvinick-Greenhouse, Robert Martin, Yunan Yang,
  *Invariant Measures in Time-Delay Coordinates for Unique Dynamical System Identification*.
- Core result: ordinary invariant measures in state coordinates need not uniquely identify dynamics, while invariant measures in delay coordinates can identify dynamics up to topological conjugacy; combining distinct delay-frame observables can remove the remaining ambiguity under stated conditions.

### Independent 2025/2026 support
- ICML 2025:
  *Chaos Meets Attention: Transformers for Large-Scale Dynamical Prediction*.
  Uses the von Neumann mean ergodic theorem to preserve long-time statistics in chaotic dynamics rather than relying only on pointwise trajectory prediction.
- ICML 2025:
  *ResKoopNet: Learning Koopman Representations for Complex Dynamics with Spectral Residuals*.
  Modern spectral/dynamical-system representation with explicit Koopman objects and physical/biological experiments.
- Nature Communications 2026:
  Colbrook, Mezić, Stepanenko,
  *Adversarial dynamical systems characterize when data-driven learning succeeds or fails*.
  Gives convergence/certification and impossibility boundaries for Koopman spectral learning, validated on chaotic fluids and sea ice.
- NeurIPS 2024:
  *When are dynamical systems learned from time series data statistically accurate?*
  Gives an ergodic-theoretic definition of physically meaningful generalization via invariant measures.
- NeurIPS 2023:
  *Training neural operators to preserve invariant measures of chaotic attractors*.
  Shows pointwise RMSE can be wrong objective in chaos and invariant-statistics preservation can be more physically meaningful.

## 2. Why this is a main-idea candidate rather than a feature trick

The transferred scientific object is not “add temporal lags”.

It is:

> **the probability measure induced by the observed trajectory in reconstructed delay state space**.

For source candidate s and observation history y(t), define delay vectors

z_t^(m,tau) = [y_t, y_(t-tau), ..., y_(t-(m-1)tau)]

and the empirical measure

mu_hat_(m,tau) = (1/N) sum_t delta_(z_t).

Source inference can then compare the observed measure against source-conditioned measure families and convert the measure mismatch into PMFS-compatible source probabilities.

Theory-name-removal test:
- if delay coordinates are removed and only ordinary concentration histograms remain, the PRL-identifiability motivation disappears;
- if the empirical measure is removed and only a temporal network remains, the ergodic/invariant-measure claim disappears.

## 3. GSL-specific scientific question

Can source location act as a persistent parameter of the turbulent scalar dynamical system such that the **delay-coordinate invariant measure** retains source identity even when pointwise plume realizations are stochastic and transport-conditioned?

This is distinct from:
- first-passage statistics;
- whiff/blank summary statistics;
- generic temporal classification;
- direct Koopman forecasting;
- ordinary PMFS likelihood updates.

## 4. Existing-data proxy test

Data:
- 12 controlled histories:
  H01/H02/H03 × {SA, SB} × {fast, slow};
- log1p gas concentration only;
- no source labels used inside the measure construction.

Representation:
- m = 1 state-coordinate empirical distribution baseline;
- delay dimensions m = 2,3,4;
- lags tau = 1,2,5,10 s;
- measure distance = deterministic sliced 1-D Wasserstein proxy over delay-coordinate projections and empirical quantiles.

Evaluation:
- fast-wind source measures used as prototypes;
- slow-wind measures classified to SA/SB;
- report same-source cross-wind distance / cross-source distance.

### H01
180 s:
- ordinary m=1: held-wind source identity 1/2, ratio 0.759.
- m=4, tau=10 s: identity 2/2, ratio 0.472.

240 s:
- m=1: 2/2, ratio 0.218.
- m=2, tau=5 s: 2/2, ratio 0.186.
Longer delay is not universally best at 240 s, which argues against trivial “more lags always help”.

### H02
120 s:
- all representations fail (0/2; ratio approximately 1) because source support is physically absent/indistinguishable.
- delay embedding does not invent information.

180 s:
- m=1: 2/2, ratio 0.066.
- m=4, tau=5 s: 2/2, ratio 0.047.

240 s:
- m=1: 2/2, ratio 0.0437.
- m=4, tau=5 s: 2/2, ratio 0.0407.

### H03
120 s:
- m=1: 2/2, ratio 0.145.
- overly long m=4, tau=10 s degrades to 1/2, ratio 0.380.
This is an important finite-horizon counterexample.

180 s:
- m=1: 2/2, ratio 0.158.
- m=4, tau=2–5 s: 2/2, ratio about 0.148.

240 s:
- m=1: 2/2, ratio 0.647.
- m=4, tau=10 s: 2/2, ratio 0.475.

## 5. Interpretation of the proxy

Positive:
- delay-coordinate measures can recover a source distinction lost by ordinary state-coordinate distributions (H01, 180 s).
- in informative H02/H03 regimes they can reduce cross-wind nuisance relative to source separation.
- they obey the physical-support boundary: no source information is manufactured at H02 120 s.

Negative:
- delay choice is not monotonic; long windows can hurt at short horizon (H03 120 s).
- finite mission trajectories are not guaranteed to be asymptotic invariant-measure samples.
- changing wind changes the underlying dynamics, so true cross-wind invariance is not guaranteed by ergodic theory alone.

Therefore this is not yet a validated main innovation.

## 6. Potential auxiliary innovations if M1 survives

### Auxiliary A: Extreme-event-aware measure preservation
2026 Nature Communications η-learning.
Reason:
- rare whiffs are underrepresented in finite empirical measures yet can be source defining.
- tail/intermittency constraints can keep finite-sample measures from being dominated by quiescent blanks.

### Auxiliary B: Adaptive multi-delay / multi-observable identification
Primary scientific source:
- PRL 2025 result itself shows multiple delay frames / distinct observables can resolve ambiguity.
External module implementation must be sourced independently before promotion; do not count a trivial lag sweep as innovation.

Alternative auxiliary B:
- structured shift-aware source region (ICLR/ICML 2025 conformal under shift), if cross-environment reliability remains the dominant failure.

## 7. Lightweight route

No large neural network is required for the core test.

Possible implementation:
- incremental delay vector buffer;
- compact empirical-measure sketch / quantile or random-feature embedding;
- source-conditioned prototype/metric head;
- PMFS-compatible soft source map.

This is significantly lighter than diffusion/world-model candidates.

## 8. Novelty collision status

Current web screen found no direct work combining:
- delay-coordinate invariant measures,
- turbulent robotic gas/odor source localization,
- source probability maps.

Ordinary “ergodic search” in robotics is unrelated: it refers to trajectory coverage, not invariant measures of plume dynamics.

Still required:
- broader atmospheric inverse/source-identification search;
- molecular-communication time-delay embeddings;
- Koopman/DMD odor-plume source inference.

## 9. Kill gates

Reject M1-B if:
1. improvement disappears against a matched temporal-distribution baseline that preserves the same marginal statistics;
2. held-wind gains occur only after tuning m,tau on the held wind;
3. finite-horizon convergence is too slow for 150–300 s missions;
4. source-conditioned delay measures are less stable across simulator/real datasets than simple event statistics;
5. literature collision shows equivalent delay-measure source localization.

## 10. Current verdict

M1-B is now a **serious alternative main candidate**.

It has a stronger pure-science lineage than the current JEPA candidate:
- primary source is PRL 2025 dynamical-systems theory;
- independent ICML/NeurIPS/Nature Communications lines support invariant-statistical learning in chaotic systems;
- existing project data already show one nontrivial recovery case plus clear counterexamples.

Next step:
- matched baseline test: ordinary marginal distribution vs delay-coordinate joint distribution with identical one-point statistics;
- finite-horizon convergence test;
- direct collision screen.


## 11. Destructive time-permutation control

A deterministic within-trace permutation was applied that preserves every one-point concentration value exactly while destroying local temporal ordering. The same delay-measure construction was then recomputed.

This control directly tests whether the apparent advantage of delay-coordinate measures is truly dynamical or only inherited from marginal concentration statistics.

Key results:

### H01, 180 s
- state-coordinate m=1: 1/2 source identity, ratio 0.759; unchanged by permutation as expected.
- ordered m=4, tau=10 s: **2/2**, ratio **0.472**.
- time-permuted m=4, tau=10 s: **1/2**, ratio **0.696**.

The main H01 recovery disappears when temporal order is destroyed while marginal values are preserved.

### H01, 240 s
- ordered m=2, tau=5 s ratio 0.186.
- permuted ratio 0.217, nearly returning to the m=1 marginal baseline 0.218.

### H02, 180 s
- ordered m=4, tau=5 s ratio 0.0473.
- permuted ratio 0.0574.
- both retain 2/2 identity, but temporal ordering provides an incremental reduction in transport/source ratio.

### H03, 240 s
- ordered m=4, tau=10 s ratio 0.475.
- permuted ratio 0.691, worse than the ordered representation and close to / above the marginal baseline 0.647.

### H03, 120 s counterexample
- ordered long-delay m=4, tau=10 s hurts: 1/2, ratio 0.380.
- permutation restores 2/2, ratio 0.130.

This confirms two nontrivial facts simultaneously:
1. temporal ordering is genuinely load-bearing in the successful H01/H03 long-horizon cases;
2. delay dynamics can also hurt when the finite horizon does not support the chosen embedding.

Decision:
- the delay-coordinate candidate passes the theory-name-removal/destructive-control test better than a generic temporal feature proposal;
- however, adaptive/qualified delay selection is mandatory and cannot be tuned on held outcomes.

Status upgraded to **STRONG M1 ALTERNATIVE**, still not GO.


## 12. Finite-horizon convergence audit

Because an invariant-measure argument is asymptotic in spirit, the candidate must survive a finite-mission convergence test.

For each trace, compare the empirical delay measure from a prefix H to the same trace's 240 s measure. Normalize this prefix-to-240 drift by the 240 s cross-source separation.

### H02
For m=4, tau=5 s:
- 120 s relative drift ≈ 0.50 while source separation is essentially zero.
- 180 s relative drift drops to ≈ 0.115.
- 210 s drops further to ≈ 0.061.

Interpretation: once source support appears, the empirical measure stabilizes rapidly enough to be plausible for finite-horizon use.

### H03
For m=4, tau=5 s:
- 120 s relative drift ≈ 1.10.
- 150 s ≈ 1.04.
- 180 s ≈ 0.81.
- 210 s ≈ 0.64.

For m=4, tau=10 s:
- 120 s ≈ 0.93.
- 180 s ≈ 0.72.
- 210 s ≈ 0.51.

Interpretation: H03 is a serious finite-horizon warning. The measure remains substantially non-converged over much of a 150–210 s mission even though source classification can already be correct.

### H01
Prefix drift remains roughly 0.40–0.58 of the 240 s source separation through 60–210 s, consistent with late/intermittent source evidence.

Decision:
- do **not** claim an asymptotic invariant measure is observed inside a short robot mission.
- if retained, the method must be framed as a finite-horizon empirical delay-measure estimator with an explicit reliability/convergence diagnostic.
- this strengthens the case for an uncertainty/validity auxiliary and weakens any overly theoretical ergodic claim.

The candidate remains alive because its destructive temporal-order test is positive, but finite-horizon convergence is now the main scientific risk.


## 13. Matched baseline: marginal distribution + ordinary autocorrelation

To test whether the delay-coordinate result is only a complicated version of standard temporal statistics, a matched baseline was constructed from:
- the exact same one-point empirical quantiles used by the marginal distribution;
- ordinary autocorrelation coefficients at 10, 20 and 30 s;
- no source labels inside feature construction;
- fast-wind source prototypes, slow-wind evaluation.

The marginal and autocorrelation components were normalized by the fast-wind source separation before combination. This is a deliberately strong development baseline.

### H01, 180 s — the key recovery case
- marginal only: 1/2, ratio 0.759.
- marginal + autocorrelation: **1/2**, ratio 0.686.
- full delay-joint measure m=4, tau=10 s: **2/2**, ratio 0.477.

Therefore a few low-order autocorrelations do not reproduce the delay-joint recovery.

### H03, 240 s
- marginal: 2/2, ratio 0.647.
- marginal + autocorrelation: 1/2, ratio 0.828.
- delay-joint: 2/2, ratio 0.471.

Again, the joint delay distribution retains a distinction not captured by simple marginal + second-order temporal correlation.

### H02, 180 s
- marginal: 2/2, ratio 0.066.
- marginal + autocorrelation: 2/2, ratio 0.117.
- delay-joint: 2/2, ratio 0.050.

Here the marginal already contains strong source identity, but the delay joint gives an incremental transport/source improvement.

### Counterexample retained
H03 120 s:
- marginal is already 2/2;
- both marginal+autocorrelation and long-delay joint degrade to 1/2.

This is important: the delay representation is not universally superior and must be finite-horizon qualified.

Decision:
> the PRL-derived object survives the matched low-order temporal-statistics baseline in its strongest recovery case.

The remaining challenge is not “does temporal structure matter?”; it is “can a source-blind finite-horizon rule choose a valid delay representation without outcome tuning?”
