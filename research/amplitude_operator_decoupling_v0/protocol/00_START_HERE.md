# Amplitude Observation-Operator Decoupling V0

Date: 2026-09-27

This package **supersedes** the unexecuted proposal
`MARKED_ENCOUNTER_PMFS_D1_FOOTPRINT_20260927.zip`.

It does NOT alter the frozen scientific decision:
`ME_PMFS_D0_MARK_INFORMATION_FORWARD_INADEQUATE`.

Input evidence:
- Pro amplitude-readout development ZIP SHA256: `79c26ccb52de73cf198c679a6c27fa93a9485cfd24e5913dcf287ea2315e491c`
- D0 review ZIP SHA256: `7a3e436900ab2696c2d7148215cd58b6632a017e447583f77c9c864b56f9c56c`

## Corrected mechanism

The existing PMFS forward contains two conceptually different uses of spatial
processing:

1. **Occurrence / hit-probability channel**
   - native PMFS hit map;
   - Gaussian blur is retained exactly as frozen, because it was introduced for
     robust hit-map comparison.

2. **Amplitude / exposure channel**
   - raw time-averaged filament-count field `rawu`;
   - do NOT reuse the hit-map Gaussian blur `u`;
   - project `rawu` through the explicit observation sampling operator only.

The OPEN 2x2 factorial diagnostic found that the ranking gain comes from
`rawu` rather than `u`; footprint averaging by itself did not change ranking.

Therefore the next step is an **implementation freeze**, not a new scientific
experiment and not a new 1584-forward replay.
