# CTRE H01 closed-loop lookup contract

Date: 2026-08-30  
Status: FROZEN AFTER H01 SHADOW GO, BEFORE LOOKUP MATERIALIZATION

## Purpose

The H01 historical shadow cannot be used as a runtime bank because an active
CTRE posterior changes the planner trajectory.  Runtime therefore requires a
source-by-transport physical concentration lookup over every native H01 free
cell and every 0.2-s sample in the 300-s horizon.

## Frozen tensor and indexing

For closed-loop airflow context 14, materialize native float32 concentration

`C[source=210, member=8, free_cell=626, time=1500]`.

Each `(source,member)` remains a separate native world file in PFV3STR1 format.
Its 626 streams follow the exact native free-cell order from the archived PMFS
posterior, and every stream has 1,500 samples.  Carrier placement and transport
seeds come unchanged from the V3 train placement manifest. The 8 member IDs
remain coherent over the complete 300-s run.

The lookup contains physical ppm only. It contains no true-source label,
measured gas, PMFS posterior, localization error, route or planner decision.

## Runtime observation chain

At each real 0.2-s step, runtime maps the current native PMFS free cell and
simulation index to `C[s,z,cell,t]`, updates one persistent sensor state for
each `(s,z)`, and records one binary event only after a physical stop completes
80 samples. It must not reset sensor state at movement or source updates.

At update `t`, accumulated physical-stop events form the coherent CTRE
likelihood. Runtime must implement exact single-window replacement using the
pre-native-update posterior. It must not multiply the CTRE likelihood into a
native posterior that already consumed the same observations.

## Frozen pilot

- House: H01 only.
- Planner seed: one already-revealed development seed.
- Candidate airflow: context 14.
- Candidate nuisance: train members 0..7.
- True airflow/source simulation: source-independent reserved nuisance, never
  one of the candidate member streams.
- Duration: complete 300 s.
- Baseline: contemporaneous PMFS OFF under the same true simulation.

Before active takeover, shadow mode must prove cell/time lookup parity, sensor
state parity, 15-event consumption, finite normalized posterior, and exact
ABSTAIN/native return if lookup or time alignment is unavailable.

The pilot reports formal error, exact true-carrier rank and mass (evaluation
only), variance, false-confident collapse, accepted/abstained updates and
trajectory divergence. It cannot establish cross-House generalization.

## Prohibitions

No neural model, interpolation across obstacles, occupancy-to-ppm conversion,
temperature, blend, adaptive weight, source/error gate, House-specific
threshold or result-driven member expansion is allowed.
