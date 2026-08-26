# CTT V2 Physical Bank: Frozen Implementation Contract

## Scope

Implement a new exporter and reader in an isolated CTT source tree. Do not edit
the V12 frozen source, V12 binaries, V12 banks, native PMFS OFF path, planner,
truth evaluator, or previous evidence packages.

## Minimal simulator change

Add an optional recorder callback to the existing filament loop. At every
native recording step, after cell occupancy has been marked and before the
filaments are moved, the callback receives:

- current recording-step index;
- a sparse list/bitset of cells occupied in that step;
- active-filament count.

The default `nullptr` path must preserve the original implementation and output.
The old cumulative `hitMap` remains computed by the original code. The recorder
is an observer and must not alter RNG draw order, filament order, movement,
collision handling, or floating-point operations on the PMFS path.

## Storage format

Use a versioned, fail-closed binary format with:

1. fixed header and magic;
2. geometry/occupancy metadata;
3. carrier manifest;
4. simulator and RNG contract;
5. immutable wind-context identifier plus a full wind-field hash;
6. per `(source, transport)` active-count trace;
7. compressed per-step occupancy bitsets;
8. derived first-hit bins;
9. trailing content hash or a sidecar SHA-256 manifest.

The writer refuses overwrite and uses atomic rename. The reader rejects unknown
versions, mismatched dimensions/settings/hashes, truncation, or trailing bytes.

## Memory bound

Do not materialize `source x transport x time x cell` as floats. For the current
largest House03 shape, occupancy bitsets require approximately:

`206 x 8 x 200 x ceil(1242/8) ~= 51 MB`

before compression, which is practical. Stream one `(source, transport)` record
at a time so peak exporter memory is bounded by one simulation plus one record.

## Truth-blind premise sequence

One static per-House bank is prohibited. The physical design bank must span a
preregistered ensemble of wind contexts and is used to train/validate the
wind-conditioned first-passage neural field. The first implementation batch is
not a localization-performance batch.

### G0: parity and integrity

- Recorder OFF reproduces frozen cumulative maps exactly.
- Recorder ON reconstructs the same cumulative maps from recorded occupancy.
- Same keys produce identical bank bytes.

### G1: M1 physical prediction

Using only training-bank transport members and frozen observation traces,
evaluate held-out transport members on:

- first-onset negative log likelihood;
- integrated Brier score for arrival-by-time;
- time-to-onset absolute error;
- pre-Bayes true-vs-best-false evidence margin.

M1 advances only if both the proper-score aggregate and the source margin improve
over the V12 cumulative-frequency comparator under a preregistered paired test.

### G2: M2 incremental ordered information

Compare A1 (`J1`) and A2 (`J2`) on the same held-out traces. Require positive
incremental source margin and a loss of that increment under within-trace time
permutation or phase-order destruction.

### G3: M3 incremental count/survival information

Compare A2 (`J2`) and A3 (`J2+J3`). Require positive incremental source margin.
Shifted-exposure and missed-detection controls must reduce the claimed M3 gain.

Any failed gate is a module NO-GO. Final localization error, posterior variance,
or a favorable seed cannot rescue a failed premise gate.

## Ablation mapping

- A0: native PMFS only.
- A1: independent physical onset placement `J1`.
- A2: hidden-phase conditional placement/order `J2`.
- A3: full exact sequence likelihood `J2 + J3 = log L2`.

The four arms consume the same block once. Native PMFS must not consume that
same block again in A1--A3.

## Stop condition before closed loop

Do not freeze a closed-loop candidate until G0--G3 pass and the exact formula,
bank hashes, binary hash, candidate/source-strength grid, background estimator,
seeds, observation blocks, and controls have been sealed in a manifest.
