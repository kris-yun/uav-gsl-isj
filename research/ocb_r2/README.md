# OCB-R2 Prospective Benchmark

OCB-R2 is the prospective, explicitly seeded, reproducible common benchmark created after the historical OCB-R1 generator was shown to be unrecoverable as a same-seed deterministic reference.

## Current status

**Generator qualification:** `OCB_R2_GENERATOR_REFOUNDATION_PASS`

**Frozen binary SHA256:**

`ec840fa1f87fca7b7d3af3014895a642562acaacb86e5950ddb07e732adc3688`

**Next permitted phase:** S1 H01/H02 structural smoke matrix only.

Start here:

- [Current status](./OCB_R2_CURRENT_STATUS_20260929.md)
- [S1 structural smoke plan](./OCB_R2_S1_H12_STRUCTURAL_SMOKE_PLAN.md)
- [Generator qualification evidence](../../evidence/ocb_r2/OCB_R2_GENERATOR_QUALIFICATION_RESULT.md)

## Experimental separation

- Historical data: legacy/discovery evidence only; do not claim same-seed replay.
- OCB-R2 discovery: H01/H02 32 runs.
- OCB-R2 independent confirmation: H01/H02 32 runs.
- OCB-R2 sealed confirmation: H03 32 runs.
- H03 must remain sealed until the method is frozen.

Do not launch all 96 prospective runs before the staged gates have passed.
