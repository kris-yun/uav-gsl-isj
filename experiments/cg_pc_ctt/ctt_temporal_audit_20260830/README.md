# CTT causal-temporal audit code (2026-08-30)

This directory is an auditable development/falsification chain for the House01 causal-temporal neural evidence work.

## Status

`CLOSED_LOOP_NOT_AUTHORIZED`

The paper-level direction remains causal + temporal + neural, but the generic candidate-forward residual TCN tested in V1--V7 is not nuisance-stable enough for closed-loop intervention.

## Checked-in source completeness

All 12 Python source/evaluator files from the frozen V1--V7 audit chain are checked into this directory:

- `train_eval_ctt_temporal_nre.py`: V1 reference data/cache/model/evaluator used by later versions.
- `v2_energy_temporal_nre.py`: energy-anchored temporal NRE.
- `v3_physics_order_temporal_nre.py`: fixed physics coefficient + soft order-consistency loss.
- `v3_parallel_median_eval.py`: V3 median evaluator driver.
- `v4_physics_certified_interval_temporal_nre.py`: full+LOO physical interval-constrained temporal selector.
- `v4_parallel_median_eval.py`: V4 median driver.
- `v5_physics_certified_partial_order_temporal_ranker.py`: robust physical partial order + Kahn temporal linear extension.
- `v5_parallel_eval.py`: V5 median driver.
- `v6_physics_certified_isotonic_temporal_evidence.py`: Dykstra order-cone projection; stopped on the frozen numerical certificate.
- `v6_parallel_eval.py`: V6 driver.
- `v7_physics_certified_nnls_temporal_evidence.py`: exact dual NNLS order-cone projection.
- `v7_parallel_eval.py`: V7 median driver.

`CTT_TEMPORAL_AUDIT_FILE_SHA256.tsv` records the original frozen SHA-256 and byte size for these files and for evidence artifacts that existed at freeze time. For V1/V4/V5/V6/V7, source recovery was accepted only after byte-for-byte SHA-256 and size equality with that manifest; the recovered files also passed `py_compile` before upload. GitHub blob SHAs are Git object identifiers and must not be confused with the file SHA-256 values in the manifest.

## Evidence completeness and provenance boundary

A combined local evidence archive was frozen earlier as:

`CTT_TEMPORAL_AUDIT_V3_V7_EVIDENCE_20260830.tar.gz`

Recorded SHA-256: `3b28577f8d617645a2573d75dd1dbbe9d6cdc7c33e8b7af585f7a99aaa98eade`

That combined V3--V7 archive is **not checked into this branch and is not present in the current conversation artifact set**. Its recorded hash is retained only as provenance; do not claim independent metric reproduction from it unless the exact archive is supplied and the hash matches.

A separate V3-only frozen evidence archive is available outside this branch:

`CTT_TEMPORAL_V3_H01_FRESH_GATE_EVIDENCE_20260830.tar.gz`

SHA-256: `27a6e9aa89526f41a452b61caa9a0e45f0b4799224ac1cbd43c580059b5c7cce`

Therefore this GitHub branch currently supports a **complete source/contract audit** and a **documented frozen-result audit**, but not a full independent V4/V5/V7 per-case metric recomputation unless the missing exact evidence artifacts are supplied. A reviewer must report this as an evidence/provenance limitation rather than regenerate, retune, or substitute data.

## Upstream data contract

The local evaluator used frozen H01 source-information audit assets and exact source-update timing evidence. Paths in the scripts are development-machine paths and are not a portable deployment interface. Any VM reproduction must resolve upstream assets by their frozen hashes/provenance and must not silently substitute new trajectories, banks, members, source subsets, or update cutoffs.

## Scientific boundary

The V1--V7 chain is a falsification record, not the next closed-loop method. The next scientific implementation must change the temporal representation itself toward explicit candidate-conditioned transport phase / first-passage / hazard plus persistent-sensor event/no-event evidence. Do not rescue the generic residual TCN with post-hoc blend weights, temperatures, thresholds, Top-K gates, or projection margins.

## Review

Follow `docs/CODEX1_REVIEW_CTT_CAUSAL_TEMPORAL_V3_V7_20260830.md` and `docs/CTT_TEMPORAL_AUDIT_UPLOAD_COMPLETENESS_20260830.md`.
