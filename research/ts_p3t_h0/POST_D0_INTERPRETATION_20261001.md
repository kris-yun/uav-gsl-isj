# Post-D0 interpretation — from Gaussian support to temporal state sufficiency

Date: 2026-10-01

Parent decision:
\`P3T_D0_NO_POSITIVE_TRUTH_SUPPORT_STOP\`

## What D0 actually falsified

D0 falsifies one specific rescue:

> keeping the same stateless, state0, ~40 s candidate trajectories and replacing point support by the historical GADEN/Gaden-RT Gaussian concentration operator.

It does **not** falsify the broader Task-Sufficient Persistent World Model hypothesis because D0 never had:
- persistent hidden plume state across source updates;
- event-aligned/time-varying transport state;
- history-conditioned latent memory;
- a learned task-sufficient compression.

D0's physical audit shows:
- true-source score improved 0/4;
- true-source continuous support at confident observation cells recovered 0/4;
- H02 true-source G3 had 1463 query-center pairs inside historical 3-sigma support, yet 0 passed historical LOS;
- H01 had essentially no geometric overlap;
- Gaussian support was nonzero elsewhere, so this is not an empty-map failure.

## New root-cause hypothesis

Frozen PMFS source scoring compares two objects with different temporal semantics.

Observation side:
- PMFS measurement updates accumulate log-odds and confidence over the search history.
- The measurement map is not reset at each source update.

Candidate side:
- every candidate simulation allocates fresh filament vectors;
- starts from an empty plume state;
- warmups locally;
- records only 200 x 0.2 s = 40 s;
- state is not inherited across source updates.

R1/D0 additionally use one static CFD state0 for Oracle candidate transport.

The four terminal source updates occur at 274.2–279.6 s.

Therefore the current likelihood effectively asks a fresh ~40 s stateless source simulator to explain a long-history observation state.

The new scientific question is not "should the Gaussian be wider?"

It is:

> Is source location alone a sufficient state for the observation likelihood, or does source localization require a persistent transport state that summarizes plume history under changing flow?

This is the direct bridge to:
- Feng et al., ICML 2026: task-specific, minimal, sufficient world state;
- Garcin et al., ICML 2026: persistent 3-D state rather than finite projected history;
- Lillemark et al., ICML 2026: flow-equivariant memory under self-motion and external dynamics.

## Consequence for the three-module story

The Lagrangian-Gaussian representation is **demoted from a core auxiliary innovation** after D0. It remains an implementation candidate only.

Current core theory candidate becomes:

1. Main: Task-Sufficient Persistent Transport State.
2. Auxiliary: Flow-Equivariant Transport Memory.
3. Second auxiliary: not frozen yet; choose only after the state-sufficiency mechanism survives.

Do not preserve a failed representation merely to keep a three-module outline.

## Next gate

Run TS-P3T-H0 Temporal Closure / State Sufficiency Audit.

This is source-blind until all alternative observation maps and scores are frozen.

It uses existing historical traces/event artifacts and frozen candidate maps only.

No new GADEN.
No new forward.
No training.
No H03.
No closed loop.
