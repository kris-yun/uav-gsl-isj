# Second-Pro Parallel Workplan — 2026-09-24

Coordination branch:
`research/pro6-sync-handoff-20260924`

This workstream exists to accelerate the project **without contaminating the currently executing PASI S3 confirmation**.

---

## A. What is already being done elsewhere

Codex is executing the frozen fresh-S3 gate on:

`research/path-action-source-inference-v0`

Do not duplicate:
- S3 target generation;
- S3 scoring;
- PASI coefficient changes;
- target-seed changes;
- source changes;
- noise-floor tuning.

Do not push to the active PASI branch until the result is returned and independently reviewed.

---

## B. Highest-value parallel task: adversarial theory/novelty audit

Treat PASI as a candidate that must be attacked, not defended.

Answer these questions with current 2025/2026 literature where possible:

1. Is the frozen PASI D0 score scientifically more than an ordinary heteroscedastic Gaussian NLL?
2. Which exact part maps to Onsager–Machlup / large-deviation / stochastic path-space theory, and which part is only a crude proxy?
3. What extra mathematical object is required for a paper-level second-order innovation?
4. Is there already gas/odor/source-localization work using:
   - ensemble source likelihood;
   - source-dependent covariance;
   - heteroscedastic candidate likelihood;
   - stochastic path likelihood;
   - Onsager–Machlup action;
   - Freidlin–Wentzell action;
   - path-space relative entropy;
   - trajectory-level inverse parameter inference?
5. Which novelty claim is definitely unsafe?
6. Which narrower claim could be defensible if cross-source and cross-House evidence passes?

Prioritize:
- 2026 peer-reviewed;
- 2025 peer-reviewed;
- top journals/conferences;
- papers with public code.

Do not treat arXiv alone as sufficient support when a peer-reviewed parent exists.

---

## C. If PASI S3 passes

Do not immediately celebrate or run closed loop.

Prepare a **pre-registered D1 design** with no target data inspected.

Recommended scientific purpose:
test whether source-conditioned path uncertainty generalizes across stochastic regimes rather than only at the median regime.

A useful D1 design should likely select one fresh source before target generation from a deliberately different C/D variability quantile.

Possible strategy to evaluate:
- choose one source from low-variability quartile and/or one from high-variability quartile;
- remain >=2 m from S1/S2/S3;
- use a deterministic target-blind source-selection rule;
- generate new independent target seeds not used elsewhere;
- keep PASI D0 formula completely frozen.

The second Pro should propose the exact selection rule and PASS/STOP gate **before** any new target is generated.

After a second fresh-source pass:
- design cross-wind or cross-House offline falsification;
- only afterward discuss online PMFS approximation.

### Paper-level upgrade problem

The current D0 proxy is diagonal in time/probe coordinates.

If D0 survives, investigate a principled upgrade that captures true path geometry, for example:
- structured temporal covariance;
- state/source-conditioned diffusion metric;
- path-space action with drift and diffusion;
- nonlocal action if justified;
- large-deviation rate function;
- path-space likelihood ratio.

But do not implement such an upgrade until the diagonal frozen proxy has survived fresh falsification.

---

## D. If PASI S3 fails

Freeze the route.

Do not rescue by:
- changing variance floor;
- removing/adding log variance;
- hand blending raw SSE;
- training a neural variance model;
- changing source or seeds.

The second Pro should then search for **one** next mother-theory candidate satisfying all hard constraints:

1. explicitly source-/state-conditioned stochastic uncertainty;
2. handles heteroscedasticity;
3. can use history/path information;
4. does not require global nuisance deletion;
5. not equivalent to generic Bayesian/SBI/experimental design;
6. 2025/2026 far-domain theoretical anchor;
7. plausible offline test with the existing 630-source bank.

Before suggesting it, explain exactly which prior failed route it differs from and which failure mechanism it addresses.

---

## E. What can be prepared now for the proposal deadline

Without asserting that PASI is already established, prepare a stable scientific-problem formulation:

> UAV gas-source localization fails not only because transport is hard to model, but because the uncertainty of turbulent plume observations is source- and environment-conditioned. The same concentration feature may be reliable evidence in one source region and realization noise in another. The research therefore studies source inference over stochastic plume distributions/path measures while preserving a PMFS source probability map.

This formulation is supported by the accumulated negative/positive evidence and remains useful even if PASI D0 later fails.

Do not state that Onsager–Machlup/PASI is the final method until fresh and cross-environment gates pass.

---

## F. Deliverables expected from the second Pro

Do not return a long brainstorming list.

Produce:

1. **PASI novelty audit** — strong/weak claims, prior art, exact theoretical ancestry.
2. **PASI failure-mode audit** — mathematical and experimental ways D0 may be fooling us.
3. **One pre-registered next gate if S3 passes**.
4. **One contingency mother-theory candidate if S3 fails**.
5. **One-page advisor-safe scientific-problem summary**.
6. Push all analysis to a separate branch, not the active PASI execution branch.

Every proposed experiment must state:
- frozen inputs;
- target-independent choices;
- controls;
- PASS threshold;
- STOP rule;
- what scientific claim a PASS actually establishes.
