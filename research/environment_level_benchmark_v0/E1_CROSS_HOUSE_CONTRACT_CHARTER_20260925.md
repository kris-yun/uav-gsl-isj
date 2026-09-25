# E1 — Cross-House Observation and Source Contract Freeze

Date: 2026-09-25

Status: **ZERO-PLUME-SIMULATION GEOMETRY CONTRACT ONLY**

Upstream E0 decision:
`E0_PARTIAL_ASSETS_REQUIRE_MINIMAL_FILL_IN`.

## 1. Why E1 is mandatory before fill-in

House02's frozen D1R 30 absolute probe coordinates are not a valid cross-House observation operator.

House01 and House03 currently have no compatible multi-source benchmark assets.

Generating plume data before freezing a geometry-valid cross-House observation/source design risks creating incomparable environments.

Therefore E1 generates **0 plume runs**.

## 2. Cross-House benchmark principle

The three Houses need not share the same absolute coordinates.

They must share the same **geometry-only selection rule**.

No source selection, probe selection, clearance threshold, or tie-break may use:
- plume concentration;
- source rank;
- LSC/energy/Bhattacharyya score;
- any model output.

## 3. Frozen observation times

Retain the D1R ten time indices:
`100,150,200,250,300,350,400,450,500,550`.

These are fixed before any House01/03 plume generation.

## 4. Per-House 30-probe observation operator

For each House independently:

1. load the canonical occupancy/navigation free-space representation used by PMFS;
2. restrict to geometry-valid observation cells at the same observation height convention used by D1R;
3. exclude cells failing the repository's existing obstacle/free-space validity rule;
4. select exactly 30 probes by deterministic farthest-point sampling over valid navigable cells;
5. initialize farthest-point sampling from the valid cell nearest the geometric centroid of the valid set;
6. at each step choose the cell maximizing minimum Euclidean distance to selected probes;
7. break exact ties lexicographically by PMFS/grid index.

The selection is source-independent and plume-independent.

Deliver the exact 30 coordinates and indices for H01/H02/H03.

## 5. House02 compatibility audit

Do NOT silently replace the existing D1R contract.

For House02 report both:
- original D1R 30-probe set;
- new geometry-rule FPS30 set.

Quantify:
- coordinate overlap;
- spatial coverage radius;
- pairwise-distance distribution;
- free-space coverage.

Then make one of two frozen decisions:

### E1A
`E1_H02_D1R_CONTRACT_ACCEPTED_AS_LEGACY_ONLY`

Use the new geometry-rule operator for the future cross-House benchmark and retain D1R only as a legacy deep-reference asset.

### E1B
`E1_H02_D1R_CONTRACT_EQUIVALENT_ENOUGH_TO_REUSE`

Only allowed if a preregistered geometry-only equivalence test passes without plume outcomes.

No concentration data may be used to choose between E1A/E1B.

## 5A. Frozen benchmark source-height contract

For the new cross-House benchmark, source height is a controlled variable, not a wind-family attribute.

Freeze one common benchmark world-coordinate height:

`z_source = 0.20 m`

for House01, House02, and House03.

Rationale:
- the completed D1R source bank uses z=0.20 m throughout;
- legacy canonical GADEN source files use wind-family-dependent heights in House01 and House03;
- carrying those historical heights into E1 would confound wind/operator changes with source-height changes;
- the future benchmark requires the same six source xyz positions within a House across all selected winds.

Before source-panel acceptance, verify every proposed source cell at z=0.20 m against the House's frozen 3D occupancy/free-space representation.

Hard rule:
- if all six selected sources are valid at z=0.20 m, accept the common-height contract;
- if any House cannot support a valid six-source panel at z=0.20 m under the frozen geometry-only rules, STOP E1 and report `SOURCE_HEIGHT_CONTRACT_INCOMPATIBLE`;
- do not silently substitute a House-specific or wind-specific legacy z after inspecting geometry or plume outcomes.

Historical source z values remain provenance only; they are not the E1 benchmark source-height contract.

## 6. Per-House six-source panel

Select exactly six evaluation source cells per House using a deterministic geometry-only rule that balances local confusion and spatial coverage.

### Step 1 — valid source candidates
Use the House's PMFS-valid free-source cells under the same source-height convention as the canonical GADEN source contract.

### Step 2 — three spatial anchors
Choose three anchors by deterministic farthest-point sampling over valid source cells:
- first anchor = valid source cell nearest the geometric centroid;
- second = farthest valid cell from first;
- third = cell maximizing minimum distance to the first two;
- lexicographic grid-index tie-break.

### Step 3 — one local partner per anchor
For each anchor, choose one valid four-neighbor source cell.
Primary ordering for candidate partner offsets:
`(+i,0), (0,+j), (-i,0), (0,-j)`.

If several are valid, choose the one with greatest obstacle/free-space clearance; ties follow the fixed offset order.

If an anchor has no valid four-neighbor, move to the next-ranked FPS anchor candidate and repeat.

Result: three spatially separated 0.30 m local source pairs = six sources/House.

No plume outcome can alter this panel.

## 7. Required environment split proposal

E1 must not generate data, but it should verify that the following benchmark roles are geometrically executable:

### Development Houses
`House01 + House02`.

Candidate development environments:
- House01: choose two canonical winds from different wind families at the same speed class where possible;
- House02: reuse the three already-ready environments (`3,5-1_fast`, `3,5-1_slow`, `4,5-3_slow`) when compatible with the frozen cross-House source/probe contract.

### Untouched House
`House03`.

All House03 plume outcomes for the six-source panel remain sealed from mechanism discovery.

E1 must choose two House03 canonical winds from different wind families at the same speed class where possible.

## 8. Provisional minimal fill-in budget — do not execute yet

If E1 geometry/compatibility passes, the current preferred first-stage stochastic depth is:
- 6 sources/environment;
- 4 independent plume realizations/source.

This is a **screening benchmark**, not a final stochastic-law estimator.

Preferred environment set:
- 2 new House01 environments;
- 3 reusable House02 environments if contract-compatible;
- 2 new sealed House03 environments.

If all three House02 environments can truly be reused under the cross-House contract, new generation would be:

`4 new environments × 6 sources × 4 realizations = 96 new plume runs`.

This number is provisional and may only be authorized after E1 reports actual contract compatibility.

## 9. Why four realizations initially

Four seeds/source are intentionally a minimal screening depth.

The purpose is to reject environment-specific mechanisms early, not to estimate high-dimensional stochastic distributions precisely.

No candidate may claim a stable source distribution from R=4.

If a mechanism survives environment-held-out screening, only then may selected environments be deepened to R=8/16.

## 10. Benchmark governance after E1

Before any fill-in generation, freeze:
- exact source IDs and coordinates in every House;
- exact 30 probes in every House;
- exact canonical winds and roles;
- plume seeds;
- House03 seal policy;
- file/hash contract;
- extraction script;
- primary proper-score / mechanism endpoints.

## 11. E1 deliverables

1. `E1_HOUSE_PROBE_CONTRACTS.tsv`
2. `E1_HOUSE_SOURCE_PANELS.tsv`
3. `E1_H02_LEGACY_COMPATIBILITY.md`
4. `E1_ENVIRONMENT_ROLE_SPLIT.md`
5. `E1_PROVISIONAL_FILLIN_BUDGET.md`
6. geometry/occupancy provenance and hashes.

Final E1 decision:
- `E1_PASS_CROSS_HOUSE_CONTRACT_READY_FOR_FILLIN_DESIGN`, or
- `E1_FAIL_CROSS_HOUSE_CONTRACT_NOT_COMPARABLE`.

No scientific mechanism PASS/FAIL is allowed at E1.