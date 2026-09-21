# TNQC V5 — C++ endpoint parity freeze
Date: 2026-09-21

> **Superseded for authoritative execution by**
> `docs/TNQC_V5_LINKED_NATIVE_EXECUTION_FREEZE_20260921.md`.
> This document remains the historical/source-blind falsification record that
> exposed Python tie-breaking and motivated direct linkage to the native
> `GSL::Utils::ExpectedValue` implementation.

This document is an **evaluation correction only**. The frozen TNQC V5
support-coverage / partition-measure / final-leaf method is unchanged.

It is authoritative for the 300-s endpoint computation before the first
House01/02/03 x seed0/1 V5 truth outcome is inspected.

## 1. The remaining evaluation ambiguity

PMFS reports the primary endpoint with:

```cpp
Utils::ExpectedValue(sourceProbability, 0.05)
```

The native implementation builds free-cell records in y-major/x-minor order,
then calls `std::sort` with only

```cpp
a.probability > b.probability
```

as the comparator. Equal-probability cells therefore have no explicit
secondary key.

The previous Python replay instead sorted with probability and then
`cell_index`. That is a different algorithm.

This matters because PMFS assigns one constant posterior score to every cell
inside a quadtree leaf. A 5% cutoff can therefore split a large tied block.

## 2. Falsification of the old Python endpoint

A source-blind synthetic audit used 40 cells with identical posterior
probability 0.025.

The historical Python index tie-break selected two cells whose weighted
location was:

`(0.5, 0.0)`

and whose error to the origin was:

`0.5 m`.

The C++ clone using the PMFS `std::sort` semantics selected a location:

`(0.5, 2.5)`

with error:

`2.5495097568 m`.

Therefore Python index tie-breaking cannot be used for the authoritative
TNQC fixed-trajectory endpoint.

Machine-readable record:

`evidence/TNQC_CPP_ENDPOINT_PARITY_AUDIT_20260921.json`.

## 3. Frozen endpoint evaluator

The repository now contains:

`reference/tnqc_expected_value_eval.cpp`.

It deliberately mirrors the native PMFS endpoint:

1. recover free cells in y-major/x-minor grid order;
2. construct a record equivalent to the native `CellData`;
3. call `std::sort` with probability-only descending comparator;
4. execute the same `i < N*0.05` loop;
5. probability-weight the selected coordinates.

The context bank supplies `grid_i/grid_j` from
`measuredHitProb.metadata.indices2D(i)` and `x/y` from
`measuredHitProb.metadata.indexToCoordinates(i)`, so the standalone
evaluator uses the same coordinate source as native PMFS.

The evaluator was independently compiled in the current analysis environment
with:

```bash
g++ -std=c++20 -O2 -Wall -Wextra -Wpedantic -Werror \
  reference/tnqc_expected_value_eval.cpp -o tnqc_expected_value_eval
```

and passed a unique-probability sanity case.

## 4. Native parity is mandatory

The standalone C++ evaluator is not trusted merely because its source looks
similar.

For every House/seed case it first evaluates the **native exported posterior**.
Its error must agree with the actual PMFS

`RESULT IS: ... Error=...`

within 0.011 m. The tolerance only covers the native log's two-decimal
printing.

If this parity check fails, the case is integrity-invalid and cannot enter
the six-case GO statistic.

Only after native parity passes is the **same compiled binary** used to
evaluate the TNQC fused counterfactual posterior.

Thus the offline comparison is:

- native PMFS endpoint: actual PMFS C++ implementation;
- replay native endpoint: standalone C++ clone, required to reproduce PMFS;
- replay TNQC endpoint: the same validated standalone C++ clone.

Python top-5% output remains diagnostic only and its difference from C++ is
recorded as `endpoint_tie_diagnostics`.

## 5. Authoritative contracts

Replay:

`TNQC_VGR_FIXED_TRAJECTORY_300S_REPLAY_V6_CPP_ENDPOINT_PARITY`

Aggregate:

`TNQC_VGR_FIXED_TRAJECTORY_300S_GATE_V5_CPP_ENDPOINT_PARITY`

Method/gate scope remains:

`final_partition_leaf_candidates_free_cell_measure_support_coverage_weighted`.

The development GO thresholds are unchanged:

- all six integrity-valid;
- pooled top-5% error reduction >= 10%;
- at least 4/6 pairs improve;
- worst pair degradation <= 25%;
- no false-confident collapse.

## 6. Execution

The command remains:

```bash
bash reference/run_tnqc_vgr_offline_gate_20260920.sh
```

The runner now compiles the endpoint evaluator before launching the six cases
and passes that exact binary to every replay.

No method parameter, TNQC equation, candidate scope, House truth, or GO
threshold may be changed after viewing the six outcomes.

## 7. Status

**TNQC V5 METHOD FROZEN / C++ ENDPOINT PARITY FROZEN BEFORE HOUSE 300-S TRUTH /
300-S VGR GATE PENDING / CLOSED LOOP HOLD.**
