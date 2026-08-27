# CG-PC-CTT V4 final three-module freeze

Date: 2026-08-28
Status: **IMPLEMENTATION AUTHORIZED / PERFORMANCE NOT YET CLAIMED**

## Paper-level innovation

**Causal Spatiotemporal Representation and Assimilation for Robotic Gas-Source Localization**

The method is frozen as exactly three modules. V2/V3 gates, LOSO, quotienting and KL projection are internal mechanisms, not separate paper-level innovations.

## M1 — Spatiotemporal Transport Representation

For source carrier `s`, keyed transport realization `m` and physical stop `j`, PMFS provides the source-conditioned predictive response

`p[s,m,j] = P(hit at physical stop j | source s, transport member m, context R_j)`.

A transport member is one coherent realization across all physical stops. Member identity may not be re-selected per stop.

The inferential unit is **one physical stop**, not one completed block. If stop `j` contains `B_j` completed measurement blocks, the primary stop outcome is

`r_j = (1/B_j) sum_b y_jb`.

All blocks at the same stop have total source-likelihood weight one. Repeated blocks refine the stop response but cannot create new spatial dimensions.

Temporal first-arrival/occupancy information remains part of M1 physics and ablation evidence, but is not a hard online M2 vote because real CTT tests did not show reliable tie-breaking beyond hit frequency.

Probability continuity floor is

`eps_T = 0.5/(T+1)`,

where `T=settings.iterationsToRecord` (currently 200). Candidate count is unrelated.

## M2 — Cross-Context Invariant Causal Source Residual

The causal object is source-specific predictive information that remains stable across physical observation contexts.

Offline qualification decomposes multi-context response fields as

`X[c,s] = mu + A_s + B_c + I[c,s]`,

where `A_s` is source-stable variation, `B_c` is context variation and `I[c,s]` is source×context interaction. The generalized source-stable eigenspace satisfies

`C_S v = lambda C_N v`,

with modes `lambda>1` interpreted as source variation exceeding context/nuisance variation. This is **offline qualification only**; it must never project unobserved full-field cells into an online decision.

Online M2 uses only actual physical stops. Scoring members 4..7 are accumulated coherently across a stop set before member marginalization:

`L_J(s) = log mean_m exp[ sum_{j in J} log P(r_j | s,m,R_j) ]`.

A source-independent context null integrates source identity under frozen geometry prior `q0`:

`L_ctx(j) = log sum_s q0(s) exp[L_j(s)]`.

### Strict leave-one-physical-stop-out qualification

Require at least three distinct physical stops in the current source-update window.

For each held-out stop `h`:

1. use only `J\{h}` to select the best observation-resolved source component;
2. all held-out folds must identify one common component `B`;
3. at held-out stop `h`, `B` may not lose to any rival component;
4. `B` must beat the source-independent context mixture;
5. at least two held-out stops must provide strict source-discriminating support rather than numerical ties;
6. deleting any one scoring transport member may not reverse the accepted component.

If any condition fails: **ABSTAIN**.

ABSTAIN is not failure; it means current observations have not earned source-specific causal authority.

## M3 — Observation-Resolved Minimum Causal Assimilation

M3 never replaces the complete PMFS posterior from a geometry prior.

Accepted stable evidence updates an independent causal macro-state `q_C`, only for the validated region `B` versus its complement. Conditional fine structure inside unresolved regions is preserved.

Let stable state assign mass

`alpha = Q_C(B)`

and current native PMFS posterior assign

`beta = Q_N(B)`.

The final posterior is the KL-nearest distribution to native PMFS subject only to the validated mass floor:

`q* = argmin_q D_KL(q || q_N)` subject to `Q(B)>=alpha`.

Closed form:

- if `beta >= alpha`: `q* = q_N` **exactly**;
- if `beta < alpha`: raise only `B` to mass `alpha`, preserving native conditional proportions inside `B` and outside `B`.

Therefore the method can rescue a native posterior that underweights a cross-predictively validated region, but it cannot deconcentrate a native posterior already stronger on that region.

Each raw source-update window is consumed once. ABSTAIN returns native PMFS exactly and does not replay old raw observations. Accepted stable evidence is cumulative and is never cleared by a later update.

## Forbidden behavior

- no block-level pseudo-replication;
- no full-field online stable-eigenspace projection;
- no normal-rank evidence transform;
- no posterior temperature;
- no PMFS/V4 blend weight;
- no House/seed-specific thresholds;
- no truth, final error, route id, wind id or plume seed in runtime decisions;
- no reusing ABSTAIN raw windows later;
- no per-stop re-selection of the best transport member;
- no full posterior reset from a geometry prior.

## Development and confirmation

Seeds 0..9 have been revealed and are **development-only** forever.

After implementation and infrastructure smoke, run one fixed development matrix:

`H01/H02/H03 × seeds 0..9 × OFF/ON = 60 arms`.

Frozen development endpoint:

- all 30 matched pairs valid;
- pooled PMFS top-5 expected-location error reduction >=10%;
- at least 20/30 pairs improve (paired one-sided sign p<=0.05);
- no House pooled mean degrades by >5%;
- ON introduces zero new false-confident collapses;
- all runtime invariants/audits pass.

If and only if development passes, freeze source/binary/launch hashes and run fresh confirmatory seeds 10..19.

`CODEX_IMPLEMENTATION_AUTHORIZED = YES`
