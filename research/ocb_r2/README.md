# OCB-R2 Prospective Benchmark

OCB-R2 is the prospective, explicitly seeded, reproducible common benchmark created after the historical OCB-R1 generator was shown to be unrecoverable as a same-seed deterministic reference.

## Current status

**Current benchmark state:** `OCB_R2_S2_DISCOVERY_DATASET_PASS`

**Frozen binary SHA256:**

`ec840fa1f87fca7b7d3af3014895a642562acaacb86e5950ddb07e732adc3688`

**Next permitted work:** execute the preregistered OCB-R2 D0 marginal-preserving dependence gate on the qualified H01/H02 discovery-32 dataset only. Confirmation and H03 remain sealed.

Start here:

- [Current status](./OCB_R2_CURRENT_STATUS_20260929.md)
- [S1 structural smoke result](./OCB_R2_S1_STRUCTURAL_SMOKE_REPORT.md)
- [S2 discovery plan](./OCB_R2_S2_DISCOVERY_32_PLAN.md)
- [S2 dataset qualification](./OCB_R2_S2_DISCOVERY_DATASET_REPORT.md)
- [D0 marginal-preserving dependence gate](./OCB_R2_D0_MARGINAL_PRESERVING_DEPENDENCE_GATE.md)
- [Generator qualification evidence](../../evidence/ocb_r2/OCB_R2_GENERATOR_QUALIFICATION_RESULT.md)

## Experimental separation

- Historical data: legacy/discovery evidence only; do not claim same-seed replay.
- OCB-R2 discovery: H01/H02 32 runs.
- OCB-R2 independent confirmation: H01/H02 32 runs.
- OCB-R2 sealed confirmation: H03 32 runs.
- H03 must remain sealed until the method is frozen.

Do not launch all 96 prospective runs before the staged gates have passed.
