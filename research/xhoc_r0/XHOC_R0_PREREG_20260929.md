# XHOC-R0 — Cross-House Observation Contract Feasibility Audit
Date: 2026-09-29
Branch: `research/cross-house-observation-contract-r0-20260929`
Base: `f5d0abf9d6ac4c9d7d0ac5c655c0ce1e8d75882c`

Status: AUDIT ONLY — NO SCIENTIFIC MECHANISM TEST

## Trigger

The frozen TCMA-D0 remains STOP. Its post-hoc code/contract audit found no
source-index, path-alignment, ranking-direction, or arithmetic bug, but found a
fundamental comparability defect: the adequacy percentile compared residual
magnitudes from GADEN concentration targets and PMFS filament-count proxy
simulations. In addition, the current H01/H02 and H03 evaluations use different
observation processes.

Therefore no further "cross-House mechanism" is to be tested on the current
heterogeneous observation contracts.

## Goal

Determine whether the repository already contains enough raw assets to build a
single **source-blind, method-independent, physically comparable observation
contract** across H01, H02, and H03 without generating new plumes.

This audit does not score a candidate mechanism and must not inspect prior
method wins/losses to choose the contract.

## Contract dimensions to inventory

For every House and candidate raw dataset, record:

1. raw physical observable available:
   - GADEN gas concentration field / point concentration;
   - binary encounter support if derivable from the same physical observable;
   - PMFS filament/count proxy (record separately; do not treat as same units);
2. spatial sampling operator:
   - exact point / footprint dimensions;
   - grid resolution;
   - interpolation rule;
3. temporal operator:
   - writer timestamps / wind-state indices;
   - stop duration;
   - number of readings per stop;
   - aggregation rule;
4. trajectory policy:
   - fixed open-loop path;
   - Native closed-loop path;
   - source-dependent or source-blind;
5. source panel:
   - number of independent physical source positions;
   - whether source choice was made before method outcomes;
6. stochastic replication:
   - independent plume realizations per source;
7. candidate support:
   - legal source cells and geometry;
8. occupancy / wind metadata;
9. whether a target and candidate-model representation share the SAME
   measurement semantics or only a monotone/proxy relationship.

## Desired common contract

Prefer, in order:

A. **Raw-field common contract**
   - source-blind fixed/open-loop sampling rule;
   - same number of observations per episode;
   - same footprint/interpolation semantics;
   - same temporal sampling rule;
   - same raw GADEN concentration observable in all Houses;
   - source-balanced physical-source units;
   - candidate scoring may later use a dimensionless transform, but the target
     acquisition contract itself must be common.

B. If A is impossible from historical assets, identify exactly which Houses /
   sources / realizations are missing and estimate the minimal new simulation
   campaign required.

Do NOT fall back to mixing Native adaptive trajectories in H01/H02 with fixed
paths in H03 merely because both can be converted to the same vector length.

## Residual-scale rule

Any future adequacy/likelihood statistic that compares residual magnitudes
across target and simulator must satisfy one of:

1. target and simulator are in the same physical observable and units; or
2. the statistic is dimensionless and explicitly invariant to arbitrary
   positive rescaling of either representation.

A free gain fit is not sufficient to make residual magnitudes comparable.

Rank/EDF transforms can be listed as scale-invariant baselines but are not to be
executed as a scientific cross-House gate until the acquisition contract is
common.

## Outcome labels

Exactly one:

### XHOC_R0_COMMON_CONTRACT_AVAILABLE
Historical raw assets are sufficient to instantiate one common acquisition
contract across H01/H02/H03 with >= 8 independent physical sources per House
and >= 4 independent plume realizations/source, without outcome-dependent source
or path selection.

### XHOC_R0_COMMON_CONTRACT_PARTIAL
A common contract is possible only with a smaller source/realization panel or
requires excluding a House for objective asset reasons. Report the exact loss
of coverage; do not run a mechanism test.

### XHOC_R0_NEW_DATA_REQUIRED
Historical assets cannot support a defensible common cross-House observation
contract. Specify the minimal preregistered new data campaign.

### XHOC_R0_HOLD_ASSET_INTEGRITY
Required raw assets cannot be verified or provenance is insufficient.

## If new data are required

Prepare, but DO NOT execute, a proposed acquisition manifest using:
- >= 12 physical sources per House when feasible;
- >= 8 independent plume realizations/source;
- a single source-blind open-loop sampling policy frozen before plume outcomes;
- identical observation count and sensor footprint semantics across Houses;
- identical temporal sampling rule;
- reserved source identities/realizations for confirmation after method design.

The acquisition manifest must separate:
- discovery panel;
- untouched confirmation panel.

## Forbidden

- no new GADEN plume in R0;
- no VGR / ROS / planner change;
- no PMFS scientific forward;
- no EDF/CENTERED/AOD/CD/TCMA/AEC scientific score;
- no method-dependent path selection;
- no source selection based on prior wins/losses;
- no residual normalization chosen by looking at rank outcomes.

## Stop boundary

STOP after the asset/contract audit and package provenance.
