# CESS D1C Locked Confirmation Skeleton

Date: 2026-09-25

Status:
**PRE-REGISTRATION SKELETON — NO TARGET GENERATION AUTHORIZED**

This file records what must be frozen after D1R and before any final D1C
targets are generated.

No numerical PASS thresholds are set here.

---

## A. Outcome space and prior

- micro source support: the frozen 168-cell dense panel;
- one fixed microcell prior \(\pi_s\);
- same prior for identity, candidate, and every baseline;
- every final method outputs a normalized 168-cell probability map.

No macro-only classification metric is primary.

---

## B. Observation channel

Before target generation freeze exactly one primary observation/model channel.

Candidate legal channels:

1. binary 10x30 encounter support;
2. raw 10x30 concentration with an explicitly specified likelihood/model;
3. a predeclared joint or calibrated combination.

The chosen primary channel must be selected using D1R reference-only
cross-validation.

No target-based channel switching.

---

## C. Candidate partition/model family

Freeze a finite family before targets.

Required controls:

1. identity;
2. all-in-one negative control;
3. connected geometry-only hierarchy;
4. connected encounter-profile clustering;
5. size-matched random partitions;
6. ordinary pooling/shrinkage baseline;
7. one explicitly defined CESS/FSEI candidate.

For each freeze:

- algorithm;
- search range;
- random seeds;
- calibration procedure;
- smoothing/prior parameters;
- computational budget.

---

## D. Honest micro lift

For any hard partition \(g\):

\[
q_g(s\mid y)
=
Q_g(g(s)\mid y)
\frac{\pi_s}{\Pi_{g(s)}}.
\]

No within-group target-dependent refinement is permitted unless it is a
separate predeclared model used by all appropriate baselines.

---

## E. Reference-only model selection

D1R is the only development dataset.

Use source-stratified realization folds.

Candidate model selection may consider only predeclared reference metrics,
including:

- cross-fitted microcell log score;
- partition stability;
- fidelity loss;
- calibration;
- connectedness;
- group size/diameter.

After the final candidate is selected, serialize and hash:

- partition labels;
- model parameters;
- calibration parameters;
- probability floors;
- all hyperparameters;
- code commit.

Only then assign D1C target seeds.

---

## F. D1C target data

Planned but NOT YET AUTHORIZED:

- exactly 2 new independent targets/source;
- 168 x 2 = 336 target simulations;
- new seed range disjoint from D1R and every prior experiment.

Targets must not influence any model choice.

---

## G. Primary endpoint

For each target:

\[
b_{sr}
=
\log_2
\frac{
q_{\rm candidate}(s\mid y_{sr})
}{
q_{\rm identity}(s\mid y_{sr})
}.
\]

Primary mean:

\[
\Delta_B
=
\frac1N
\sum_s
\frac1J
\sum_r b_{sr}.
\]

The final PASS rule must specify before target generation:

- minimum meaningful effect;
- confidence interval construction;
- candidate-vs-identity requirement;
- strongest-baseline requirement;
- calibration requirement;
- partition-stability/fidelity prerequisites.

---

## H. Uncertainty unit

The 300 observation coordinates are not independent experimental replicates.

D1C uncertainty must be computed at the source/realization level.

Preferred design to be finalized:

- source as the top-level resampling unit;
- target realization nested within source;
- report cluster/bootstrap or hierarchical bootstrap CI.

Do not create artificial sample size by bootstrapping individual
time-probe coordinates.

---

## I. Required secondary diagnostics

Report for all models, without allowing them to replace the primary endpoint:

- truth rank;
- top-1 / top-3;
- MAP spatial error;
- probability mass within 0.5 m;
- probability mass within 1.0 m;
- entropy / sharpness;
- calibration;
- performance stratified by source location / stochasticity.

---

## J. Final target firewall

After target generation:

Forbidden:

- changing partition;
- changing K;
- changing clustering family;
- changing probability floor;
- changing likelihood;
- changing calibration;
- adding a new baseline because the candidate loses;
- changing the primary endpoint;
- relaxing PASS thresholds.

Any such change creates a new development cycle and requires a new untouched
target set.

---

## K. Claim ladder

D1C PASS can establish only:

**fresh-target finite-sample multiscale identifiability signal in one dense
House02/W2 region.**

It cannot alone establish:

- universal causal emergence;
- cross-House generalization;
- cross-wind robustness;
- closed-loop PMFS benefit;
- real-flight benefit.

Those require separate frozen gates.
