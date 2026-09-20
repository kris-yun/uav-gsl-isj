# Candidate M1 — Demixed Intrinsic vs Input-Driven Dynamics (InputDSA transfer)

Date: 2026-09-20
Branch: research/remote-paradigm-loop-20260919
Status: SCREENED / NO-GO AS PRIMARY

## Remote-field source

- ICLR 2026 — Huang et al., *InputDSA: Demixing, then comparing recurrent and externally driven dynamics*.

Core idea:
- observations of real dynamical systems mix intrinsic recurrent dynamics with externally driven dynamics;
- direct comparison can confuse systems that are intrinsically similar but driven by different inputs;
- InputDSA estimates intrinsic and input-driven operators separately using DMDc/subspace identification, then compares systems in the demixed dynamical space.

## GSL structural mapping

- gas history = partial observation of the dynamical system;
- local wind / motion = external drive;
- source/geometry-dependent plume dynamics = intrinsic/source-conditioned component;
- goal = separate what is due to external transport drive from what persists as source identity.

This is conceptually stronger than naïve domain-invariant feature removal because the wind effect is modeled, not subtracted away.

## Offline ARX proxy

A lightweight source-blind ARX proxy was tested:

y_t = A[y_{t-1},y_{t-2}] + B[u_t,v_t]

where y is log concentration and (u,v) is local wind.

Comparators:
- AR2: intrinsic autoregression only;
- ARX2: intrinsic + measured wind drive;
- B-only: external-drive coefficients.

### Same-block source-vs-wind test

H01:
- 120–180 s ratio AR2 0.288 -> ARX2 0.271 (small improvement).
- 180–240 s AR2 0.048 -> ARX2 0.048 (neutral).

H02:
- 120–180 s AR2 0.0007 -> ARX2 0.0035 (worse, both 2/2).
- 180–240 s remains effectively non-identifying (ratio ~1), consistent with missing support.

H03:
- 120–180 s AR2 0.021 -> ARX2 0.022 (neutral/worse).
- 180–240 s AR2 0.072 -> ARX2 0.089 (worse).

### Cross-time / cross-wind test

Train fast 120–180 s source prototypes; test slow 180–240 s.

- H01: ARX preserves supported-window identity but margins are lower than AR2.
- H02: no physical support in held slow segment; all methods correctly qualify only for abstention.
- H03: ARX does not repair the cross-time failure. At 20 s windows, supported accuracy drops from AR2 0.60 to ARX 0.40.

B-only coefficients occasionally separate H03 late windows, but margins are tiny and inconsistent across Houses.

## Decision

The remote theory is compelling, but the simplest project premise is not positive:

- measured-wind demixing does not consistently improve source identity;
- in H03 it can worsen cross-time source persistence;
- the project's earlier evidence already shows that transport effects are candidate-dependent, so a simple exogenous-input decomposition is insufficient.

STATUS:
- InputDSA principle = RESERVE THEORY.
- ARX/DMDc-style demixing = NO-GO AS PRIMARY.
- do not add a wind-demixing module to the leading architecture without a new independent positive premise.
