# CPIR M1-only closed-loop contract

Date: 2026-08-31  
Status: **FROZEN BEFORE RUNTIME IMPLEMENTATION OR CLOSED-LOOP RESULT**

## 1. Method identity and retired mechanism

The development method is named **Causal Physical Intervention Reachability
(CPIR)**.  It is an M1-only method.

`CTT_DYNAMIC_TRANSPORT_M2_PREMISE_NO_GO` is permanent.  Exact first-passage
phase, coherent transport identity, dynamic transport identity, stop-labelled
temporal matching, and every neural likelihood are disabled.  They may not be
renamed or reintroduced as CPIR.

The frozen M2 terminal record is
`docs/CTT_DYNAMIC_TRANSPORT_TWO_MODULE_V4_RESULT_20260831.md`, SHA-256
`e22574c3c306aa5c12796019e190e5e2e6b68e747f9b2c8c983a0fc2a5d18948`.

## 2. Authoritative comparator and single allowed intervention

- OFF is authoritative `main_v8` Classic PMFS.
- OFF source, map update, source update cadence, planner, declaration logic,
  official evaluator, and RNG are unchanged.
- ON executes the same native computations, but at a scheduled source update
  replaces only the source gas-likelihood posterior with the CPIR posterior.
- The native PMFS posterior is a comparator, never a CPIR prior, because it has
  consumed the same observations.
- M2 is OFF.  Neural inference is OFF.  Planner modification is OFF.

## 3. Frozen M1 causal operator

For carrier `s`, nuisance member `m`, and the causally visited pose/time stream,
the prediction chain is

`do(S=s) -> native main_v8 GADEN physical ppm -> run-persistent sensor -> reach`.

The eight prediction members use the already frozen V3 train placement and
transport keys.  Their RNG domain is `PF_DEI_V3_REGION_PLACEMENT_V1/train`.
The observation world is the immutable external GADEN data realization used by
the paired Classic run.  It is not generated in the prediction RNG domain.
The observation realization hash and the eight prediction transport keys are
recorded for every House; a missing or overlapping identity invalidates the
pair.

For completed physical stop `b`, exactly the first 80 native 0.2-s measured
samples are inspected.  A reach is

`E=1[max measured_ppm > 0.1]`.

The prediction probability is the frozen Jeffreys finite-ensemble estimate

`p_s,b = (0.5 + sum_m E_s,m,b) / 9`.

M2 is excluded by discarding stop identity before source scoring.  With `B`
completed stops, observed reach count `R`, and

`pbar_s = mean_b p_s,b`,

the only CPIR score is

`L_s = R log(pbar_s) + (B-R) log(1-pbar_s)`.

Thus CPIR uses causal physical reachability but neither first-passage time nor
candidate-to-observation stop matching.  There is no threshold fit, weight,
temperature, blend, gate, House parameter, or learned component.

## 4. Prior and source-channel replacement

The geometry prior gives one equal quantum to every native free PMFS cell.
Carrier prior mass is proportional to its free-cell count.  At source update
`u`,

`q_CPIR,u(s) proportional to q0(s) exp(L_s,u)`.

Every free cell in carrier `s` receives its original equal cell prior quantum
times `exp(L_s,u)`, followed by one normalization.  Batch recomputation from
`q0` and the cumulative ledger is authoritative.  An incremental
implementation must agree within `1e-12` absolute error.

## 5. Observation and provider contracts

- Each real raw 0.2-s sample enters one chronological ledger once.
- Candidate sensor state is run-persistent across motion and stops, with
  `tau=1.2 s`, `dead_time=0.4 s`, initial state zero, and no stop reset.
- A physical stop is one maximal stationary visit.  Only its first 80 samples
  can form the reach event; shorter/incomplete stops are not consumed.
- The ledger records raw-sample ID, simulation time, cell, stop ID, and whether
  it was consumed.  Duplicate sample or stop consumption is fatal.
- The lookup is trajectory-independent: source x member x every native free
  cell x all 1500 samples.  Historical-route lookup is forbidden for ON.
- Missing cell/time, bad hash, nonfinite ppm, posterior mass error, or provider
  mismatch fails closed; native fallback cannot be labelled ON.

## 6. Pairing freeze

For every OFF/ON pair, these are identical: source truth, observation GADEN
realization and wind/world condition, planner RNG seed, native PMFS RNG seed,
initial pose, map, parameters, 300-s simulation horizon, and official
`ExpectedValue(sourceProbability, 0.05)` evaluator.  Arms differ only in
`pfdi_mode=off` versus `pfdi_mode=cpir_m1` and the required read-only CPIR
lookup/audit paths.

## 7. Smoke and experiment

One revealed paired runtime smoke is run first.  It checks OFF identity,
lookup/time/cell parity, one-time ledger consumption, batch/incremental
posterior equality, finite normalized posterior, runtime completion, and
trajectory divergence logging.  Smoke localization error cannot change the
method.

After smoke PASS, freeze source SHA, binary SHA, launch SHA, lookup hashes, and
run exactly:

`H01/H02/H03 x seeds 1,2,3 x OFF/ON`, 9 pairs / 18 runs, 300 s each.

Seeds may not be replaced and no intermediate performance result may alter the
method.  Up to three Houses may run concurrently only with the frozen OMP,
ROS-domain, RNG, and GADEN contracts unchanged.

## 8. Preregistered terminal Gate

`CPIR_M1_ONLY_CLOSED_LOOP_PASS` requires all of:

1. pooled mean final official error improvement at least 10%;
2. at least 6 of 9 pairs improve strictly;
3. no House has catastrophic mean degradation, defined prospectively as ON
   House mean exceeding both OFF House mean + 1.0 m and 1.5 times OFF House
   mean;
4. no crash, NaN, invalid posterior, duplicate consumption, or provider
   fallback;
5. all OFF runs reproduce the authoritative contemporaneous main_v8 contract;
6. no result-dependent tuning or run replacement.

Any failure gives `CPIR_M1_ONLY_CLOSED_LOOP_NO_GO`.  A NO-GO means the main
mechanism is not established in closed loop.  It does not authorize restoring
M2.

## 9. Required output

The evidence package contains the nine-pair error table, House mean errors and
improvements, pooled mean and median errors, wins/losses, exact paired sign
test and bootstrap interval as report-only statistics, catastrophe count,
runtime/ledger/provider audits, complete OFF/ON pose and sensor trajectories,
all final posteriors, and source/binary/launch/lookup SHA-256 manifests.
