# Dual-UAV two-point raw-cache audit

Date: 2026-09-13

## Decision

`RAW_CACHE_AUDIT = PASS`

The existing R3B plume caches on `zyc@192.168.111.128` are sufficient for a
read-only same-snapshot query. No new GADEN generation is needed or authorized.

## Direct audit

- Dataset root: `/home/zyc/SCTT_DISCOVERY_DATASET_V2_R3B_RAW_CACHE_ARDO_20260817`
- Inventory: four source interventions by three winds, exactly 12 directories
- Each directory: 446 frame files, numbered `0..445`
- Required contract range: `0..419`
- Required missing or zero-byte frames: zero
- Complete current hashes recorded for all 5,040 required frame files
- Historical sampled-frame hash mismatches: zero
- Physical realizations: one (`GADEN_RNG_SEED=20260817`)
- Stochastic or multiseed robustness claim: prohibited

The machine-readable audit is
`experiments/dual_uav_two_point_v1/RAW_CACHE_AUDIT.json`; the complete frame
hash inventory is `experiments/dual_uav_two_point_v1/RAW_CACHE_SHA256SUMS`.

## Provenance boundary

The audit establishes byte availability and continuity for the frozen R3B
realization. It does not establish that a deployable two-large-UAV formation
fits the House02 map, nor does it establish source identifiability.
