# L0 Data-Interface Audit — GADEN Filament Identity

Date: 2026-09-23  
Branch: `research/generative-lagrangian-filament-world-model-v1`

## Decision

`M5 PRIORITY = DEMOTE FROM MAIN COMPETITOR TO AUXILIARY / SECONDARY RESEARCH LINE`

Reason: native GADEN snapshots do not provide persistent filament identity.

## 1. Exact GADEN filament state

Official `Filament` contains only:

- `position`;
- `sigma`.

There is no:
- persistent filament ID;
- birth timestamp;
- age;
- source-event identifier.

## 2. Exact update/order semantics

Each `AdvanceTimestep()` performs:

1. `AddFilaments()`
   - newly emitted filaments are appended to the active vector;

2. `MoveFilaments()`
   - all active filaments are moved;

3. survivor compaction
   - filaments reaching an `Outlet` are marked inactive;
   - surviving filaments are copied into an auxiliary vector in their original vector order;
   - inactive filaments are skipped;
   - vectors are swapped.

Therefore survivor **relative ordering** is preserved, but vector indices are not persistent identities.

If an earlier filament exits, every later surviving filament may change index.

Thus consecutive `GetFilaments()` snapshots cannot safely be interpreted as labeled particle trajectories from index alone.

## 3. Consequence

Do NOT construct supervised trajectory pairs by:

[
X_t[i] ightarrow X_{t+1}[i].
]

That silently introduces correspondence errors.

Do NOT add IDs to GADEN solely to rescue M5 before simpler evidence exists.

## 4. Scientifically correct first representation

If M5 is revisited, use the filament population as an empirical measure / particle cloud:

[
mu_t
=
sum_j
m_j,
delta_{(X_t^j,sigma_t^j)}.
]

Learn a **set/distribution evolution law**:

[
mu_t
ightarrow
mu_{t+Delta}
]

conditioned on:

- wind;
- obstacle geometry;
- source injection.

Possible comparison objects:

- set-to-set flow matching;
- measure-valued dynamics;
- unbalanced OT / birth-death particle processes;
- permutation-invariant generative point-cloud dynamics.

However generic OT/UOT is already known and previously unattractive as a main innovation, so M5 should not be rescued merely by relabeling it as OT.

## 5. A cheaper L0 diagnostic remains possible

Before learning any set model, compare source-blind population statistics under GADEN vs native PMFS assumptions:

- displacement distribution at local wind regimes;
- spatial covariance growth;
- plume-cloud anisotropy;
- obstacle-near recirculation;
- filament sigma distribution;
- birth/death counts.

This does not require trajectory IDs.

If these statistics are close to a simple Gaussian/advection model, M5 has no reason to exist.

## 6. Instrumentation option

A future controlled simulator fork could add:

- `uint64_t filament_id`;
- birth time;
- parent/source ID.

But this is research instrumentation, not part of the original simulator.

Use only if a set-level diagnostic first shows a strong non-Gaussian transport signal worth pursuing.

## 7. Current verdict

M5 remains physically appealing but has:

- weaker paper-level novelty than M4/M6;
- a more difficult clean supervision interface;
- a risk of becoming a learned version of an already-filament-based PMFS simulator.

Current priority:

1. M4 / M6;
2. M3 if stochasticity is empirically necessary;
3. M5 only if filament-cloud diagnostics reveal a strong missing transport mechanism.

Status:

`HOLD / AUXILIARY CANDIDATE`.
