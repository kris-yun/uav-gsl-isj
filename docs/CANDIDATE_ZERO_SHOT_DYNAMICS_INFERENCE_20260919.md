# Candidate M1 — Zero-Shot Dynamical-System Inference for Turbulent GSL

Date: 2026-09-19
Branch: research/remote-paradigm-loop-20260919
Status: SECONDARY ACTIVE CANDIDATE / OFFLINE FALSIFICATION ONLY

## 1. Main paradigm

### Zero-shot / in-context inference of dynamical systems

Primary 2025 top-venue sources:

1. **NeurIPS 2025 — Hemmer & Durstewitz, _True Zero-Shot Inference of Dynamical Systems Preserving Long-Term Statistics_ (DynaMix).**
   - reconstructs previously unseen dynamical systems from context without target-system retraining;
   - explicitly targets long-term dynamical statistics rather than only short-horizon point forecasting;
   - reports very small parameter count relative to time-series foundation models.

2. **NeurIPS 2025 — Seifner et al., _In-Context Learning of Stochastic Differential Equations with Foundation Inference Models_ (FIM-SDE).**
   - estimates drift and diffusion functions of stochastic systems from noisy time series;
   - one pretrained recognition model performs zero-shot/in-context inference across unseen processes.

3. **Nature Communications 2025 — Zhai, Stern & Lai, _Bridging known and unknown dynamics by transformer-based machine-learning inference from sparse observations_.**
   - reconstructs unseen nonlinear dynamics from one-time sparse observations;
   - training excludes the target system and instead uses diverse synthetic dynamical systems.

Critical 2026 negative baseline:
- **ICLR 2026 — Zhang & Gilpin, _Context parroting: A simple but tough-to-beat baseline for foundation models in scientific machine learning_.**
  - shows that many apparent zero-shot physical forecasts can reduce to copying/repeating context or mean regression;
  - any proposed in-context GSL model must beat this cheap baseline.

## 2. Scientific translation to GSL

A turbulent plume time series is not only a sequence to classify. It is an observation from a hidden stochastic dynamical system whose governing structure depends on:

- source position;
- geometry;
- transport/wind regime;
- sensor dynamics;
- robot trajectory.

The proposed paper-level question is:

> Can a source-location probability map be obtained by first identifying the latent local plume dynamics from sparse context, and then asking which source hypotheses are dynamically compatible with those inferred dynamics, without target-environment retraining?

This is distinct from:
- direct supervised source classification;
- full 3-D plume reconstruction;
- ordinary Bayesian forward-model likelihood;
- world-model planning.

## 3. Candidate mathematical object

For a local observation state (x_t), infer an effective stochastic law

[
dx_t = f_phi(x_t,c_t),dt + g_phi(x_t,c_t),dW_t,
]

where (c_t) may contain pose / local context but source truth is never an inference input.

The inferred dynamical fingerprint is

[
mathcal D(Y_{0:T}) = {hat f,hat g,	ext{long-term / transition statistics}}.
]

A source candidate (s) receives evidence according to how compatible its predicted/local reference dynamics are with (mathcal D), yielding

[
P(S=smid Y_{0:T})
]

over PMFS source cells.

The model need not explicitly reconstruct the full plume.

## 4. Existing-data premise test

A conservative SDE-like fingerprint was estimated from the 12 existing controlled histories.

For each House and horizon:
- state = log(1+gas);
- fixed concentration-state bins were defined source-blind within each House;
- per bin, estimate empirical drift, diffusion scale, and occupancy;
- append threshold-crossing rates;
- compare same-source/different-wind distance against different-source distance.

Results:

### H01
- 120 s: raw identity 2/2; SDE fingerprint 2/2; wind/source ratio 0.133 -> 0.106.
- 180 s: both raw and SDE 1/2; no rescue.
- 240 s: both 2/2; SDE ratio 0.481 vs raw 0.375.

### H02
- 120 s: both 0/2 because source evidence is physically absent/indistinguishable.
- 180 s: both 2/2; SDE ratio 0.269 vs raw 0.096.
- 240 s: both 2/2; SDE ratio 0.333 vs raw 0.406.

### H03
- 120 s: both 2/2.
- 180 s: both 2/2.
- **240 s: raw summary identity 1/2; SDE fingerprint 2/2**, with ratio 0.745 vs 0.779.

Interpretation:
- an inferred stochastic-dynamics object can recover a source distinction lost by static raw summaries in the difficult H03 late regime;
- it does not manufacture source information in H02 before support exists;
- the improvement is not uniform, so dynamics inference is not yet validated as the final M1.

## 5. Comparison with current predictive-representation candidate

Predictive JEPA-class candidate:
- strongest premise: latent prediction suppresses transport innovations after support;
- failure: generic prediction can wash out late/rare H01 source evidence;
- requires explicit extreme-event preservation.

Zero-shot dynamical-inference candidate:
- strongest premise: a dynamics fingerprint can preserve or recover source identity in H03 where static summaries fail;
- failure: drift/diffusion statistics can be more wind-sensitive in H02 and H01;
- requires an intermittency-aware description of stochastic dynamics.

Thus the two candidates are scientifically related but not equivalent:
- JEPA asks **which latent content is predictable?**
- zero-shot DS inference asks **what stochastic law generated the observed local dynamics?**

## 6. Possible 1+2 structure

### M1 — Zero-Shot Stochastic Dynamics Inference
Infer a compact drift/diffusion/transition representation from sparse plume context without target-House retraining.

### M2 — Extreme-Event-Aware Dynamics Preservation
Primary remote source:
- Nature Communications 2026, Chang & Sapsis, Extreme Event Aware (eta-) Learning.

Reason:
- ordinary drift/diffusion estimation is dominated by common low-concentration states;
- source-defining whiffs can be rare;
- eta-style constraints can force inferred dynamics to reproduce source-relevant tail/intermittency statistics.

### M3 — Structured Shift-Aware Source Region
Primary recent sources:
- ICLR 2025 distribution-shift conformal prediction;
- ICML 2025 structured / OT conformal prediction.

Reason:
- zero-shot dynamics inference can still fail on an unseen physical regime;
- the source probability map needs calibrated spatial uncertainty / abstention under unsupported shift.

## 7. Lightweight strategy

Not a contribution:
- low-dimensional effective state rather than full field;
- small ALRNN / FIM-inspired recognition head rather than large foundation model;
- amortized drift/diffusion inference;
- no target-environment retraining;
- few source-map compatibility evaluations.

## 8. Hard falsification gates

Kill M1 if:
1. source identity from inferred dynamics does not beat matched static/context-parroting baselines on held transport;
2. H03-240 rescue disappears under a representation not tuned to the four traces;
3. inferred dynamics are dominated by wind identity rather than source identity across Houses;
4. shuffled temporal order does not destroy its benefit;
5. the method needs target-House fine-tuning to work.

Kill the 1+2 combination if:
- eta-style preservation adds no incremental benefit to dynamics inference;
- conformal source regions become nearly map-wide under the intended cross-dataset shifts.

## 9. Collision status

Focused 2025/2026 GSL search found:
- supervised temporal plume encoding;
- diffusion-state clustering;
- Mamba/state-space backtracking;
- probabilistic forward-model OSL;
- receptor-mimetic temporal latent localization.

No direct 2025/2026 GSL work was found that performs **zero-shot/in-context stochastic dynamical-system identification from sparse plume histories and maps the identified dynamics to a source probability field**.

This remains a positive novelty signal, not a proof of absence.

## 10. Current verdict

Scorecard (provisional):
- paradigm-level strength: 10/10
- 2025/26 top-venue provenance: 10/10
- match to sparse/intermittent turbulent physics: 9/10
- novelty room in GSL after current search: 9/10
- lightweight potential: 9/10
- public-dataset definability: 9/10
- existing-data premise: 7/10

**Status: ACTIVE SECOND M1 CANDIDATE.**

It is not yet preferred over Predictive–Intermittency Representation Learning.
Next gate: held-context / time-order destructive tests plus a context-parroting baseline on the exact same histories.
