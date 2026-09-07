# CSTAR M1/M2 revision protocol V1

Date: 2026-09-07. This is a prospective protocol for a possible next
implementation. It does not change the frozen `M1_CONTROLLED_SCREEN_NO_GO`,
does not authorize a production run, and does not convert the literature search
into a novelty claim.

## Decision in one paragraph

The next attempt will not add another invariant encoder or retune CPO's hit
threshold. It will test one shared **conditional innovation law**. M2 predicts
the distribution of the next measured sensor block under an explicit feasible
route intervention, starting from an audited sensor/transport state. M1 scores
a source only by the incremental log evidence of that same law relative to a
source-agnostic context law. This directly attacks PMFS's spatially aggregated,
correlated hit-map product: source preference must come from time-resolved
observation innovations, not from a pose/time shortcut or a candidate-only bias.

## 1. Estimands

For a candidate source region `s`, executed prefix `h_t`, and a predeclared
future route `a_{t:t+H}`:

`L0 = log p(Y_{t+1:t+H} | h_t, a, G, W, M_t)`

is a context-only predictive law. It must not contain candidate source identity.

`Ls = log p(Y_{t+1:t+H} | S=s, h_t, a, G, W, M_t)`

is the candidate-conditional law. The M1 evidence increment is

`Delta_s = Ls - L0`.

The source posterior is `pi(s) ∝ pi0(s) exp(sum_blocks Delta_s)`, with the
normalizer evaluated over the fixed all-free-cell candidate support. Every
candidate uses the same route, observation timestamps, sensor contract and
transport uncertainty. No source truth, future wind/gas, House ID, realization
ID or site-specific bank is an input.

The primary utility estimand is final XY source error at the frozen full horizon.
The secondary estimand is the proper predictive score of the held-out future
sensor block. A lower training-only score is never evidence of causal utility.

## 2. Shared causal state and observation law

The state passed between M1 and M2 is typed and minimal:

`q_t = (pose_t, executed route history, measured gas history, measured wind,
        audited sensor parameters, uncertainty over delayed sensor state)`.

`q_t` must not contain the simulator's raw-input delay queue. The current gas EMA
is not a FOPDT state and cannot be renamed as one. A missing frame is represented
by a validity mask; a valid zero gas reading remains evidence and is not replaced
by neutral likelihood.

The physical prior is a named, executable transport/FOPDT predictor with a
versioned code hash and parameter manifest. Its output is a distribution or
bounded ensemble over the next sensor block, not a single deterministic plume
curve. If that prior cannot be bound and independently replayed, M2 is blocked;
no neural residual is allowed to hide the missing prior.

The learned residual may alter the conditional law only through `q_t`, route
geometry and candidate-conditioned prior summaries. It is zero-initialized or
otherwise explicitly calibrated against the prior and is regularized by:

1. next-block proper score (Gaussian/logistic mixture only if its joint temporal
   normalization is explicit);
2. sensor-state consistency under the audited delay/response recurrence;
3. route-shuffle falsification: removing the route intervention must remove any
   claimed route-specific improvement;
4. source-agnostic nested-law check: `Ls` reduces to `L0` when candidate source
   contrast is masked.

No per-step independent likelihood product is acceptable unless the conditional
   factorization and dependence state are specified and tested.

## 3. M1 PICR replacement boundary

PICR's causal responsibility becomes **incremental source attribution**, not
embedding invariance for its own sake. A source representation may be used only
as a low-dimensional parameterization of `Ls - L0`; it cannot directly output a
map posterior. The following checks are mandatory:

- gas-response ablation: remove measured gas while retaining wind/pose/time;
  a valid model must become calibrated and no better than `L0` on source evidence;
- route/pose permutation: preserve gas and wind values but break their executed
  route pairing; source evidence must degrade;
- nuisance-pair check: same-source fast/slow episodes should not increase source
  evidence solely from the nuisance label, while a real changed observation law
  may change uncertainty;
- candidate-bias check: with identical `q_t`, permuting candidate coordinates
  permutes scores exactly;
- proper-score check against uniform, context-only, native PMFS and physical-prior
  baselines. A MAP tie or a training loss is not a pass.

The old same/different latent-distance gate is retained as a diagnostic only. It
is not a causal proof because the frozen source groups are not matched
`do(source)` interventions under a common transport draw.

## 4. M2 CPO replacement boundary

CPO is evaluated on a route-conditioned *future observation block*, not merely
the first threshold-crossing index. The route is a predeclared intervention;
future observations are evaluator targets only. For each frozen route and prefix,
report:

- joint next-block negative log score and Brier/calibration summaries;
- contrast to the current-threshold train-only strong null;
- contrast to the executable physical transport/FOPDT prior;
- route shuffle and prefix-only controls;
- the number of route pairs whose observed future blocks actually differ.

The first-hit law can remain an auxiliary derived quantity, but it cannot be the
sole CPO gate while 168/252 outcomes are immediate hits and the current-value
baseline reaches 95.24–100% held-House accuracy. A CPO pass requires a positive
route-conditioned predictive increment on the same contexts where future blocks
are distinguishable, with no post-hoc selection of those contexts.

## 5. Data split and one-shot execution rule

Use only the existing 12 raw realizations and frozen House123 seed12 routes. Keep
the current outer leave-one-House-out split and all existing outcome hashes. No
new source, seed, horizon, threshold, route or map may be introduced.

Before any model fit, materialize a single protocol manifest containing:

- code/model hashes;
- reusable environment preflight hash;
- physical prior and sensor manifest hashes;
- candidate support and route-freeze hashes;
- exact prefix/block boundaries and primary endpoint;
- fixed optimizer, regularization and stopping rules;
- the three strong baselines and all falsification controls.

Then run a cheap offline forward/inference gate. Only if the conditional law beats
the context-only and physical-prior proper-score baselines without failing a
falsification control may one House123 seed12 closed-loop pilot be launched.
If that pilot fails the predeclared final-error gate, stop. Do not use additional
seeds to average away the failure and do not change the protocol after seeing it.

The first online boundary implementation is
`closed_loop/ctpi/cstar_m2_online.py`. It wraps the existing stamped ROS ingress
with an injected route-law provider, copies only the past prefix, requires a
prediction token before each positive observation, and rejects an incomplete
horizon. Its `selftest_m2_online.py` is a state-machine/plumbing test only; it
does not count as a CPO scientific result because the injected provider is a
synthetic reference law.

The first executable physical prior behind that boundary is
`experiments/ctpi_cstar/m2_cpo/physical_prior.py`. It mirrors the declared V2
finite-volume/FOPDT contracts and is covered by CPU integration checks, but is
not yet a qualified House-data predictor: C++/Python parity, proper-score
calibration, and the route-intervention gate are still open.

The first M1 implementation candidate is
`experiments/ctpi_cstar/m1_picr/conditional_evidence.py`. Its score is the
candidate-conditioned observation log score minus a source/gas-masked context
log score. This is not claimed as a new posterior algebra by itself: the
scientific contribution would be the identifiable nuisance intervention and
the falsification result showing that candidate-only context shortcuts are
removed without removing source contrast. Its synthetic self-test does not
count as localization evidence.

`experiments/ctpi_cstar/m1_picr/route_law_score.py` now supplies the missing
normalization boundary for this candidate: a declared AR(1) innovation
factorization over M2's route-law mean/scale, with invalid frames omitted and
valid zero readings retained. It is an auditable scoring primitive, not a
qualified M1 result; its physical-prior parity, held-out proper scores and
causal controls remain open.

## 6. What would count as a real M1/M2 result

**M1 useful:** source evidence improves held-out proper score and final error over
native PMFS and context-only, while gas removal, route permutation and candidate
permutation behave as specified. A lower latent-distance ratio alone is not enough.

**M2 useful:** the shared law predicts route-dependent future sensor blocks better
than both current-state and physical-prior baselines, with calibrated uncertainty;
its route choices reduce final error in the one-shot pilot. First-hit accuracy
alone is not enough.

**Causal claim support:** only if the effect disappears under the corresponding
controlled intervention (gas/route/source contrast) and the intervention does not
also change map geometry or the evaluation target. Otherwise report association or
conditional prediction, not causality.

## 7. Hard stops

- Missing or stale reusable environment certificate: stop before launch.
- Unbound physical prior or unresolved sensor state: M2 NO-GO, no residual rescue.
- Candidate source labels confounded with House/transport/gas type: no causal claim.
- Proper-score loss to uniform/context-only baseline: no closed-loop launch.
- A route target whose label is recovered by the current threshold alone: auxiliary
  diagnostic only, not a CPO success gate.
- Any result that requires selecting prefixes, routes or Houses after outcomes:
  development finding only, not a qualification result.

This protocol deliberately makes a positive result harder to obtain. That is
necessary for the requested claim that M1/M2 genuinely reduce PMFS localization
error rather than merely change a posterior map.
