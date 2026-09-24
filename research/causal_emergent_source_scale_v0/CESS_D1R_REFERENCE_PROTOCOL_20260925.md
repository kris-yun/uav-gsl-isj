# CESS D1R — 168×16 Reference-Bank Freeze

Date: 2026-09-25

Branch:
`research/causal-emergent-source-scale-v0`

Status:
**DATA CONSTRUCTION ONLY — NO MAINLINE PASS/STOP**

## Purpose

Build a fair dense arbitrary-source reference bank for the revised
multiscale-source-identifiability gate.

D1R does NOT confirm causal emergence and does NOT choose the final partition.

## Frozen panel

Use the existing deterministic builder:

`research/causal_emergent_source_scale_v0/build_cess_d1a_panel.py`

Input:
the exact frozen Gate1A 630-source bank.

Expected output:
- 168 source cells;
- PMFS i=1..24;
- PMFS j=12..18;
- complete 24×7 dense rectangle;
- 0.30 m spacing.

No plume data enter source selection.

## Environment

- House02
- W2 = `3,5-1_slow`
- exact frozen GADEN binary / occupancy / W2 / extractor contracts
- exact Gate1A 10×30 pooled observation operator
- 300 s simulation
- same GADEN physical parameters used by R0

## Reference realizations

Generate exactly 16 fresh realizations/source.

Total:
[
168\times16=2688.
]

Seed:
[
seed(i,r)=2026105000+16i+r
]
for panel row (i=0,ldots,167), replicate (r=1,ldots,16).

No old Gate1A C/D, R0, or S1/S2/S3 realization enters D1R.

## Important lock

Replicates 1..16 are **reference data**.

Do NOT generate replicate 17 or 18.

Future locked confirmation targets will use a separate seed range after the
partition/objective/thresholds are frozen.

## Required outputs

For every run preserve:

- source id / panel index / xyz;
- RNG seed;
- exact simulator/environment hashes;
- 10×30 pooled concentration;
- binary support derivable as concentration >0;
- concentration-cube SHA256;
- pooled-array SHA256;
- manifest.

The heavy filament realization frames may be deleted after the extracted cube
and provenance are verified.

## Reference-only diagnostics allowed

Only integrity/measurement diagnostics:

- completeness 168×16;
- finite/nonnegative arrays;
- per-source basic mass / zero fraction / encounter rate summaries;
- two 8/8 encounter-profile reproducibility summaries.

Do NOT:

- choose a final macro partition;
- choose K/M;
- tune a source scale;
- compute D1C fresh-target proper-score gain;
- declare CESS PASS/HOLD/STOP;
- generate final targets;
- run PMFS closed loop.

## Decision

D1R has only:

`CESS_D1R_REFERENCE_BANK_COMPLETE`

or

`CESS_D1R_INFRASTRUCTURE_STOP`

There is no scientific result at D1R.
