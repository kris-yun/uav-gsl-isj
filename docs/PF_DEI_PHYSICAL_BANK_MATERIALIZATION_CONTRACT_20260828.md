# PF-DEI physical GADEN forward-bank materialization contract

Date: 2026-08-28

Status: **BANK MATERIALIZATION ONLY / TRUTH-BLIND / NO PERFORMANCE CLAIM**

## 1. Correct status after the run-level blocker

The native physical observation operator itself is already closed by the preserved forward-closure work: a candidate source in a native GADEN field can be queried in physical concentration units and propagated through the exact persistent sensor to PMFS observations with parity.

The current unresolved object is narrower:

`candidate_physical_ppm[S,M,T]`

for the complete source support, a frozen source-independent transport ensemble, and the exact historical trajectories.

Therefore the current blocker should be called:

`PF_DEI_PHYSICAL_BANK_NOT_MATERIALIZED`

not interpreted as evidence that the physical forward operator is scientifically invalid.

## 2. Source identity is a hard prerequisite

Before launching thousands of GADEN jobs, prove what source index `s` means physically.

The energy reference requires one geometry prior `q0[s]` and one source-specific ensemble `X[s,m,t]`.  Therefore each source index must have a stable physical identity:

`source_id[s] <-> (x_s,y_s,z_s) <-> q0[s]`.

Do **not** take the union of the 1,229 adaptive candidate IDs and call it the source support unless the archived provenance proves that those IDs are exactly the source carriers aligned to `q0`.

Preferred order:

1. inspect the V6-A/context payload and its source-carrier manifest;
2. recover the exact candidate coordinates and stable IDs backing `geometry_prior`;
3. prove index-to-coordinate identity across all prefixes of a run;
4. if the same House uses one common support across runs, freeze one House-level support;
5. if supports are legitimately run-specific, freeze run-specific supports and do not force cross-run source-index equality.  Simulation fields may still be deduplicated by exact `(House,x,y,z)`.

If this cannot be proven, stop:

`STOP_PF_DEI_SOURCE_SUPPORT_IDENTITY_UNRESOLVED`.

No physical bank is useful without this alignment.

## 3. Transport ensemble

Transport members are nuisance draws and must be source-independent.

Reuse an existing frozen GADEN transport/RNG member manifest only if its seeds/configuration have a source-proven mapping to native GADEN.  Do not pretend the old occupancy member IDs automatically define physical GADEN concentration members.

If no reusable native manifest exists, freeze a set of distinct legal native GADEN RNG seeds/configurations **before** any run-level source-evidence result is computed.  The choice must not depend on House/seed localization error or source-ranking outcome.

Record for each member:

- stable member ID;
- native RNG seed/substream;
- wind/environment config hash;
- gas-dispersion config hash;
- simulation duration/time origin;
- all source-independent nuisance parameters.

No member may be tuned by source candidate.

## 4. Efficient simulation reuse

Do not multiply work by 30 automatically.

A GADEN gas field is independent of the robot trajectory.  If provenance proves that the ten historical runs of a House share the same environment, time origin semantics and source-independent transport-member definition, then one native simulation for one `(House,source,member)` may be queried along all ten historical pose/time schedules.

Thus the expensive simulation count is potentially

`sum_H (#unique source positions in H) * M`

rather than

`30 * S * M`.

This reuse is legal only after proving those environment/time semantics.  Otherwise materialize run-specific fields.

## 5. Normative per-run bank

For each historical run, materialize one NPZ whose main array is:

`candidate_physical_ppm[S,M,T]`.

`T` is the complete common run-level chronological physical-concentration sequence used by the run-level diagnostic, on the exact timestamps/poses aligned to the deconvolved observation.

Required metadata is enforced by:

`experiments/cg_pc_ctt/pf_dei_physical_bank_contract.py`.

At minimum preserve:

- `sample_time_s[T]`;
- `pose_xyz_m[T,3]`;
- `source_xyz_m[S,3]`;
- `source_id[S]`;
- `geometry_prior[S]` aligned to those exact source IDs;
- `transport_id[M]` and integer `transport_seed[M]`;
- House/run seed;
- SHA-256 hashes of source support, transport manifest, trajectory schedule, query binary, GADEN source, GADEN config and deployed overlay.

Forbidden fields include true source, historical `true_gas_ppm`, localization error and ON/OFF performance.

## 6. Materialization parity

Before scaling, create a smoke bank with at least:

- one House;
- one historical trajectory;
- two source candidates with distinct coordinates;
- at least two transport members;
- the complete trajectory time sequence.

The bank must pass:

`python3 experiments/cg_pc_ctt/selftest_pf_dei_physical_bank_contract.py`

and the real smoke payload must pass `validate_npz(...)`.

For at least 50 pre-frozen `(source,member,time,pose)` samples, compare bank values against direct native concentration query.  Require numerical parity at the already source-proven query tolerance.

Repeat a deterministic subset after a clean process restart and require identical hashes or documented floating tolerance if the native simulator cannot be bitwise deterministic.

## 7. Scaling strategy

Once the smoke bank passes, generate the full bank without opening source truth or localization performance.

Safe parallelism unit:

`(House, source_id, transport_id)`.

Each worker may simulate one field and then query every compatible historical trajectory for that House.  Workers must write to isolated directories and publish only after completeness/hash validation.

Do not silently skip failed source/member fields.  The final bank is complete only when every required `[s,m]` trace exists for every run for which that support is declared.

## 8. Immediate scientific handoff

As soon as all 30 run banks pass the contract, run the already-frozen run-level energy diagnostic.  Do not add another review stage.

Use the existing verdict:

- >=20/30 predictive-pass runs **and** >=5/10 in each House -> `PHYSICAL_RUNLEVEL_SOURCE_FORWARD_ACTIONABLE`;
- otherwise -> `FINITE_TRANSPORT_OR_SOURCE_FORWARD_STILL_INSUFFICIENT`.

If the latter occurs, do not retune energy score or source thresholds.  The next scientific operation is source-independent physics-randomized GADEN transport expansion.

## 9. What is not allowed

- occupancy/hit-map -> ppm conversion;
- historical `true_gas_ppm` as a candidate forward trace;
- substituting the 12 fixed-source simulations for missing candidate sources;
- choosing source grid density from localization outcomes;
- House-specific scoring thresholds;
- C++/Active Probe/60-arm before run-level physical adequacy is established.
