# CTT causal-temporal audit code (2026-08-30)

This directory is an auditable development/falsification chain for the House01 causal-temporal neural evidence work.

## Status

`CLOSED_LOOP_NOT_AUTHORIZED`

The main scientific direction remains causal + temporal + neural, but the generic candidate-forward residual TCN is not nuisance-stable enough for closed-loop intervention.

## Files

- `train_eval_ctt_temporal_nre.py`: V1 reference data/cache/model/evaluator used by later versions.
- `v2_energy_temporal_nre.py`: energy-anchored temporal NRE.
- `v3_physics_order_temporal_nre.py`: fixed physics coefficient + soft order-consistency loss.
- `v3_parallel_median_eval.py`: V3 median evaluator driver.
- `v4_physics_certified_interval_temporal_nre.py`: full+LOO physical interval-constrained temporal selector.
- `v4_parallel_median_eval.py`: V4 median driver.
- `v5_physics_certified_partial_order_temporal_ranker.py`: robust physical partial order + Kahn temporal linear extension.
- `v5_parallel_eval.py`: V5 median driver.
- `v6_physics_certified_isotonic_temporal_evidence.py`: Dykstra order-cone projection; stopped on frozen numerical certificate.
- `v6_parallel_eval.py`: V6 driver.
- `v7_physics_certified_nnls_temporal_evidence.py`: exact dual NNLS order-cone projection.
- `v7_parallel_eval.py`: V7 median driver.

## Evidence archive

Local frozen archive name: `CTT_TEMPORAL_AUDIT_V3_V7_EVIDENCE_20260830.tar.gz`

SHA-256: `3b28577f8d617645a2573d75dd1dbbe9d6cdc7c33e8b7af585f7a99aaa98eade`

The archive contains frozen contracts, checkpoints, self-tests, per-case CSVs, summaries and terminal reports for V3--V7. The human-readable source and evidence summaries are checked into this audit branch. It intentionally does not contain upstream House01 raw/native bank payloads.

## Upstream data contract

The local evaluator used the frozen H01 source-information audit assets and source-update timing evidence. Paths in the scripts are development-machine paths and are not a portable deployment interface. Codex1 should review scientific semantics and checked-in evidence first; any reproduction on the VM must resolve upstream assets by hash/provenance rather than silently substituting new data.

## Review

Follow `docs/CODEX1_REVIEW_CTT_CAUSAL_TEMPORAL_V3_V7_20260830.md`.
