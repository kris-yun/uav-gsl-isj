# ATC V1 — Alternating Transport Corrector for Turbulent Gas-Source Localization

Date: 2026-09-22  
Branch: `research/alternating-transport-corrector-v1`  
Status: **PRIMARY MAIN-INNOVATION CANDIDATE / DECISIVE DATA GATE PENDING**

## 1. Mother idea

The current failure is treated as a **model–reality gap in the source-conditioned transport simulator**, not primarily as a posterior-calibration failure.

Borrowed remote-field principle:

- Wang et al., *Learning missing physics from legacy simulators with alternating neural integrators*, Nature Communications 17, 7877 (2026), DOI: 10.1038/s41467-026-74002-2.
- ANI retains a callable frozen prior simulator and alternates it with a learned correction operator, rather than replacing the simulator with a black-box surrogate.

Project transfer:

> Keep PMFS/GADEN-style source-conditioned transport as the reusable prior, but learn a compact shared correction operator for the structured discrepancy that repeatedly makes the native candidate fields rank transport-confounded false sources above the true-source neighborhood.

This is a different scientific object from TNQC: TNQC leaves the candidate transport model unchanged and adds a posterior tilt. ATC changes the **candidate evidence generator itself** before source scoring.

## 2. Why this candidate exists

Frozen project evidence gives a specific contradiction:

- controlled 240-s measured concentration fields have strong cross-transport source identity (affine quotient 12/12);
- the authoritative TNQC V5 six-case 300-s gate is integrity-valid but yields essentially zero localization gain and 6/6 false-confident collapse;
- post-verdict diagnosis shows that in H01/H03 the true-source neighborhood has low/negative online quotient score while several-metre-away candidates can score higher;
- in H02 the true-source owner can fail the final support/candidate condition.

Therefore the most defensible current diagnosis is:

**the measured plume contains source information, but the online source-conditioned transport family is systematically misspecified in a way that converts it into the wrong candidate ordering.**

ATC attacks that failure upstream.

## 3. Minimal mathematical form

Let `P_tau` be the existing callable transport prior for one source candidate and one substep.

A second-order alternating form is

`u_{k+1} = C_{phi,tau/2}( P_tau( C_{phi,tau/2}(u_k, z_k), s, z_k ), z_k )`

where:

- `u_k`: candidate transport / hit field state;
- `s`: candidate source;
- `z_k`: observable context (wind, map geometry, sensor/support state, timing);
- `P`: frozen legacy transport prior;
- `C_phi`: small shared discrepancy corrector.

The corrector is **shared across source candidates**. It may condition on candidate-relative geometry, but there is no per-source lookup table and no evaluation-truth input.

The first falsification implementation does not need a large neural operator. A low-rank/local linear corrector or tiny MLP is sufficient to test whether a learnable structured discrepancy exists.

## 4. Two auxiliary modules

### A1. Nuisance-quotient residual supervision

Do not ask the corrector to reproduce raw concentration scale.

Train/evaluate correction in a nuisance-reduced field coordinate that removes positive affine concentration scale/background where possible. This reuses the already-positive project observation that spatial plume shape is more source-stable than raw amplitude.

Purpose: force model capacity toward source-bearing structural discrepancy instead of release/sensor gain.

This quotient principle is **not claimed as a new main innovation**.

### A2. Correction-trust abstention

A learned corrector must not create a second false-confidence mechanism.

Maintain a source-blind trust variable from quantities such as:

- correction norm relative to prior step;
- distance from training/support manifold;
- disagreement across a tiny corrector ensemble or held-out calibration folds.

When trust is low, retain the prior / abstain from adding corrected source evidence rather than sharpening the posterior.

## 5. Novelty boundary

Not new by itself:

- residual learning;
- gray-box modelling;
- PINNs;
- neural operators;
- simulator calibration;
- model ensembles;
- Bayesian model averaging.

Direct neighboring GSL work already includes the 2025 Journal of Turbulence paper *Many wrong models approach to localise an odour source in turbulence with static sensors*, which ranks/blends multiple imperfect stochastic models.

Targeted novelty hypothesis:

**non-intrusive alternating correction of a callable source-conditioned gas-transport prior, with a candidate-shared lightweight discrepancy operator, where localization is performed from the corrected transport family rather than by posterior blending of multiple wrong models.**

The novelty claim must stay at this level; “learning model discrepancy” alone is not novel.

## 6. Decisive offline test — no closed loop yet

Required data: the authoritative R2 context-bank candidate exports or equivalent paired prior/reference fields.

### Split

Use House-level separation.

For each held-out House:

- fit the corrector on the other Houses only;
- freeze preprocessing, corrector weights and trust threshold;
- evaluate every candidate in the held-out House;
- rotate held-out House until all three are tested.

No endpoint-truth tuning on the held-out House.

### Comparators

1. native frozen prior;
2. additive one-shot residual correction;
3. model-ensemble / variance inflation control where available;
4. ATC alternating correction;
5. ATC without nuisance-quotient supervision;
6. ATC without trust abstention.

ANI transfer is only load-bearing if alternating correction beats a matched additive residual baseline.

### Necessary mechanism gates

Before endpoint evaluation:

- true-source-neighborhood candidate rank improves in at least 4/6 authoritative R2 cases;
- correction does not simply increase field similarity for every candidate;
- improvement survives House holdout;
- correction remains candidate-shared;
- correction magnitude is not strongly source-truth encoded.

### Authoritative 300-s localization gate

Use the native PMFS `ExpectedValue(sourceProbability, 0.05)` endpoint.

Promotion bar:

- pooled error reduction >= 2% over native;
- >= 4/6 cases non-worse;
- no false-confident-collapse case introduced;
- better than matched additive-residual correction;
- native endpoint parity/integrity remains valid.

Only after this passes: SHADOW parity, then a closed-loop matrix interpreted against the known run-to-run trajectory stochasticity.

## 7. Current evidence status

**What is already positive**

- the project has strong evidence that real plume fields contain source-stable structure;
- the frozen online gate independently establishes candidate-model/source-ranking failure rather than an execution failure;
- ANI is a 2026 high-level method explicitly built for callable but structurally incomplete legacy simulators and includes turbulence/subgrid-correction evidence.

**What is not yet demonstrated**

- no ATC corrector has been trained on the authoritative six-case candidate bank;
- no ATC native 300-s endpoint has been computed;
- therefore ATC is not yet authorized as the final main innovation.

The full R2 context-bank archive is not present in the normal Git repository or currently accessible Library artifacts; available reports contain summaries but not the complete paired candidate fields required for a scientifically valid correction test.

## 8. Decision

**ATC V1 = KEEP AS CURRENT PRIMARY CANDIDATE.**

Do not run closed loop.

The next decisive action is a cheap leave-one-House-out correction screen on the existing authoritative candidate bank. If that screen cannot repair true-source candidate ordering beyond an additive residual baseline, reject ATC immediately and resume the remote-domain search.
