# PF-DEI observation-operator addendum

Date: 2026-08-28

Status: **NORMATIVE ADDENDUM / BLOCKING BEFORE PF-DEI SCORING**

This addendum closes a remaining semantic gap between the truth-free CTT occupancy trace and the real PMFS measurement decision.

## 1. Real PMFS observation operator

`StopAndMeasureState.cpp` shows that one completed PMFS measurement block first collects `measurement_block_samples` raw gas readings, computes their average concentration, and then `PMFS::processGasAndWindMeasurements()` declares `GAS HIT` when that block-average concentration exceeds `thresholdGas`.

Therefore the real block label is not automatically identical to a single instantaneous CTT occupancy bit.

The same code can optionally persist:

- block-level measurement trace including raw min/max/mean, raw sample hit count/fraction, actual threshold, block start/end time;
- continuous raw gas samples with one timestamp per sample.

Whether those files exist in the frozen 30-run archive is an empirical provenance question and must be inventoried before scoring.

## 2. CTT occupancy semantic requirement

The V13 binary `occupancyWords[T,...]` is known to reconstruct the old native PMFS cumulative hit-frequency map exactly. That regression proves compatibility with the previous frequency representation, but it does **not by itself** prove that one occupancy bit is the same random variable as one block-average `GAS HIT` event.

Before PF-DEI dynamic likelihood is used, Codex must determine from authoritative CTT builder/GADEN/PMFS source which of the following is true.

### Case O1 — exact event compatibility

If one CTT occupancy bit is explicitly the simulator-side binary event corresponding to the PMFS gas-threshold observation at one sample time, then dynamic scoring may use it after the timing/cadence mapping is proved.

If raw 10-sample-per-block historical observations are available, use the raw sample threshold sequence as the preferred observed event tape. The block-level eight-event tape becomes a matched coarser ablation.

### Case O2 — occupancy is plume presence, not the PMFS sensor event

If `occupancyWords` represents plume/filament presence in a cell rather than the actual sensor-threshold event, do not score real `GAS HIT` labels directly against it.

Instead extend the truth-free builder to emit the same observation operator used by PMFS at the required cadence, for example simulated sensor concentration followed by the frozen threshold/averaging rule. No source truth may enter this conversion.

### Case O3 — observation semantics cannot be proved

Stop with:

`STOP_PF_DEI_OBSERVATION_OPERATOR_UNRESOLVED`

Do not choose an aggregation (`any`, `mean`, `majority`, `max`, fitted threshold, or empirical calibration) because it improves source transfer.

## 3. Preferred observed temporal resolution

Use the finest already-recorded causally available observation resolution whose provenance is complete:

1. **preferred:** raw within-block gas samples with timestamps, if present for all required runs/contexts;
2. otherwise: the authoritative eight completed block-average HIT/NOTHING decisions.

Do not mix resolutions across seeds or Houses in the primary analysis. If raw samples exist only for a subset, report that subset as diagnostic and keep the primary 30-run test at the common eight-block resolution unless a complete rematerialization can be performed without using outcomes.

## 4. Why this matters

PF-DEI is intended to test whether temporal plume structure repairs the V6-A failure. A timing-correct but observation-semantic mismatch would confound that test and could create either false recovery or false failure.

The dynamic model therefore has two independent provenance gates before any truth-blind score:

1. `TIMING/PHASE CONTRACT PASS`;
2. `OBSERVATION OPERATOR CONTRACT PASS`.

Only after both pass may the full-trace PF-DEI likelihood be evaluated.
