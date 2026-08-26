# CTT Data-Contract Feasibility Gate (2026-08-26)

## Verdict

`CURRENT_V12_BANK_INSUFFICIENT__CTT_V2_BANK_REQUIRED`

The current V12 response bank is valid for its original purpose, but it cannot
support the proposed Causal Transport Tomography (CTT) likelihood without
inventing information that was not recorded.

## Read-only evidence

The frozen V12 writer stores exactly one float map for every
`carrier x transport_member`. Each map has one value per spatial cell. The
generator calls `simulateSourceInPosition(...)`, counts whether a cell was
occupied at least once in each simulation step, and finally divides that count
by `recorded_timesteps`. It then discards the step index.

Observed frozen metadata:

| House | Cells | Carriers | Transport members | Recorded steps | dt | Bank body |
|---|---:|---:|---:|---:|---:|---|
| H01 | 1102 | 210 | 8 | 200 | 0.2 s | `210 x 8 x 1102` float frequencies |
| H02 | 1053 | 201 | 8 | 200 | 0.2 s | `201 x 8 x 1053` float frequencies |
| H03 | 1242 | 206 | 8 | 200 | 0.2 s | `206 x 8 x 1242` float frequencies |

Consequently, the recorded map can answer only:

> During the whole simulated horizon, how often was this cell occupied?

It cannot answer:

- when occupancy first arrived at the cell;
- whether two occupied cells belonged to an ordered causal path;
- the time-varying phase/state of a transport member;
- the per-bin onset hazard required by CTT-M1;
- the per-bin path population required by the physical transition operator.

Many distinct temporal histories map to the same V12 frequency map. Therefore
recovering the missing histories is non-identifiable.

## Scientific consequence

The following substitutions are prohibited:

1. treating a cumulative frequency map as a first-passage distribution;
2. manufacturing time bins by spatial interpolation;
3. calling the eight random transport replicas hidden temporal phases without
   a recorded transition statistic;
4. training a network to hallucinate unrecorded path histories;
5. using source truth or final localization error to choose the bank design.

If any of these substitutions is used, CTT loses both its physical meaning and
its ablation contract.

## Required CTT V2 bank

The new bank must be generated from the same frozen geometry, source carriers,
wind field, collision model, deterministic keyed transport streams, and native
PMFS simulation time step. It is an additional read-only export, not a rewrite
of the V12 bank.

For each candidate source `s`, transport member `k`, native time bin `n`, and
free spatial cell `c`, export sufficient statistics:

- `O[s,k,n,c]`: binary occupancy at time `n`, or an exactly documented compact
  equivalent;
- `F[s,k,c]`: first occupied bin, with a sentinel for never reached;
- `A[s,k,n]`: total active-filament population (diagnostic);
- immutable metadata and hashes for geometry, wind, simulator settings, source
  carriers, time grid, RNG key/substream, and exporter binary.

The bank need not store individual filament identities. Occupancy and first-hit
statistics are sufficient for the first CTT premise test and are much smaller
than full particle trajectories.

## Derivation from the V2 bank

For an observation cell or spatial support `c`:

`h[s,k,n,c] = Pr(F[s,k,c] = n)`

is estimated only across a preregistered ensemble axis that represents repeated
transport realizations. A single deterministic member must not be presented as
a probability estimate.

The normalized causal-front population is:

`P[s,k,n,c] = O[s,k,n,c] / sum_c O[s,k,n,c]`

when the denominator is positive. Empty fronts use an explicit pre-arrival
state; they are not silently replaced by a uniform distribution.

The physical overlap transition is then:

`w[s,n](k,k') = sum_c sqrt(P[s,k,n,c] P[s,k',n+1,c])`

followed by the preregistered row normalization and zero-overlap self-loop.

## Gate before implementation may proceed

The exporter must pass all of the following without reading source truth:

1. exact deterministic replay for the same keyed stream;
2. occupancy-to-cumulative-frequency reconstruction agrees with the original
   V12 map on native Free support before blur to numerical tolerance, and
   recorded occupancy is exactly zero on obstacle cells;
3. first-hit bins are consistent with occupancy (`F=n` implies `O[n]=1` and no
   earlier occupancy);
4. no occupied cell appears before a geometry-and-wind lower-bound travel time;
5. all empty-front and never-reached states are explicit;
6. bank header, body size, and SHA-256 are validated at runtime;
7. OFF arm remains byte-identical to the frozen PMFS path.

Only after these pass may M1 direct prediction, M2 conditional placement, and
M3 count/survival premise tests begin. No House123 generalization run is
authorized by this document.
