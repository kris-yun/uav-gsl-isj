# Codex directive — replace posterior-smeared M2 calibration before data generation

Base audit branch: `research/ctpi-m2-ba0de54-audit-fix-20260902`.

Read first:

1. `docs/CTPI_M2_BA0DE54_CODE_AUDIT_20260902.md`
2. `docs/CTPI_M2_BA0DE54_ISOTONIC_INFORMATION_AUDIT_20260902.md`
3. `experiments/cg_pc_ctt/ctpi_m2_source_intervention_forecast.py`

Do not generate the previously preregistered single-true-source `M2_CAL` / `M2_CONFIRM` tapes. No such tape existed when this redesign was frozen, so changing the pre-generation design does not contaminate confirmation.

## Scientific reason

The `ba0de54` posterior-weighted isotonic fit improves posterior-mixture event scores by copying one realized event fractionally across every candidate source. Static theory and old development-only cross-validation show that this fit drives source-conditioned event probabilities toward a common base rate and destroys nearly all mutual information needed by M3.

The eight-member bank itself is not degenerate. Preserve the M2 role but change the identification experiment.

## Frozen M2 role

M2 remains the causal/action-conditioned transport predictive law

`P(Y_next | do(S=s), action=a, physical context)`.

At runtime, M2 must receive candidate source and candidate action from the planner/inference state. It must never receive the actual unknown source.

During simulator calibration only, the source is a deliberately controlled intervention. Knowing which source was set by the experiment is not localization leakage; it is the independent variable of the forward-model experiment.

## Reuse the same 60-world budget

Do not rebuild the predictive bank.

Repurpose the planned 60 new worlds as controlled-source intervention worlds:

- H01: 10 CAL + 10 CONFIRM worlds;
- H02: 10 CAL + 10 CONFIRM worlds;
- H03: 10 CAL + 10 CONFIRM worlds.

CAL and CONFIRM source sets, RNG domains, and numeric world seeds must be disjoint.

Each world still follows one frozen 15-stop route and yields 15 direct source-conditioned event records.

## Controlled-source selection before generation

Use only the frozen predictive bank and source geometry, never outcomes.

For every House, compute for each carrier/source:

- spatial centroid from the frozen carrier/cell manifest;
- frozen raw event-frequency summary over the ten historical route geometries, using only predictive members.

Select 20 distinct carriers before any new world is generated with a deterministic coverage rule that spans both space and predicted event prevalence. Preferred implementation:

1. normalize `(x, y, predicted_event_frequency)` within House;
2. choose the first point by minimum SHA-256 of `CTPI_M2_SOURCE_SELECTION_V1/<HOUSE>/<carrier_id>`;
3. choose the next 19 by deterministic farthest-point sampling in the three normalized coordinates; hash is the tie-breaker;
4. assign alternating selected points to CAL and CONFIRM after a second deterministic hash ordering;
5. pair the ten CAL and ten CONFIRM sources one-to-one with route indices 0..9 by hash order.

Freeze the selected source IDs, coordinates, route IDs, predictive summaries, bank hashes, and selection-code hash before generation.

Do not change source selection after seeing CAL outcomes.

## Direct CAL fit

For every completed stop in a CAL controlled-source world, record:

- House;
- controlled source carrier ID;
- source coordinates;
- route ID;
- action/stop ID and coordinates;
- independent observation-world RNG identity;
- eight-member hit count `K` for that same controlled source/action from the read-only predictive bank;
- realized event `Y` from the independent controlled-source world.

Fit the reference rule in `ctpi_m2_source_intervention_forecast.py`:

`r_k = (A_k + 0.5)/(W_k + 1)`

where `W_k` counts direct controlled-source records with `K=k` and `A_k` counts realized hits among those exact records. Then apply deterministic weighted PAV with weights `W_k+1`.

No M1 posterior enters this fit. No localization truth/rank/error enters this fit. No planner reward enters this fit.

This table is a reliability implementation inside M2; it is not itself the claimed main innovation.

## CONFIRM Gate

Freeze the CAL table, code commit, source-selection manifest, generator environment manifest, and all hashes before opening CONFIRM.

Evaluate the table directly at the controlled source:

`p0 = (K+0.5)/9`

`p1 = g[K]`.

Score `p0` and `p1` against the event generated from the same controlled source/action. Do not posterior-mix across candidate sources for the M2 scientific Gate.

Required PASS conditions:

- pooled direct source-conditioned NLL strictly improves;
- pooled direct source-conditioned Brier strictly improves;
- one of paired tape NLL/Brier has one-sided exact sign p <= 0.05;
- five-bin ECE is not worse;
- no House has stable reverse on both NLL and Brier with >=8/10 tape losses;
- at least three distinct calibrated table values;
- at least three observed `K` levels in CONFIRM;
- every probability finite and strictly inside `(0,1)`.

Emit only one of:

- `CTPI_M2_SOURCE_CONDITIONED_PREDICTIVE_GATE_PASS`
- `CTPI_M2_SOURCE_CONDITIONED_PREDICTIVE_GATE_NO_GO`

If NO-GO, stop. Do not use M3 to rescue M2.

## M3 authorization after M2 PASS

Only after the direct source-conditioned M2 Gate passes, compute M3 counterfactual action scores from

- frozen M1 posterior;
- M2 probabilities for every candidate `(source, action)`;
- truth-blind feasibility;
- deterministic travel-cost tie-break.

Use the same predictive-information utility already frozen. First run an offline action-discrimination Gate; fixed historical replay cannot claim localization gain.

The old development-only route evidence already shows nontrivial planning opportunity, but this is not a closed-loop PASS.

## Engineering blockers still apply

Before any new world generation, also close the independent code-audit blockers:

- unequal H01/H02/H03 carrier dimensions must not be silently padded;
- RNG disjointness must come from an asset-derived legacy inventory;
- OpenMP/GADEN runtime provenance must be frozen;
- a fail-closed one-world-per-invocation tape materializer must be committed;
- source/action metadata and hashes must be explicit;
- bank root must remain read-only;
- no CAL/CONFIRM output directory may be reused.

## Terminal sequence

Required order:

1. `CTPI_M2_SOURCE_SELECTION_FREEZE=PASS`
2. `CTPI_M2_PREGEN_ENGINEERING_AUDIT=PASS`
3. generate CAL only
4. fit/freeze M2 table
5. generate/open CONFIRM only after fit hash is frozen
6. source-conditioned confirmatory Gate
7. only on PASS: M3 offline action Gate
8. only on M3 PASS: C++ parity and one true closed-loop smoke

Do not generate the old single-hidden-source CAL design.
