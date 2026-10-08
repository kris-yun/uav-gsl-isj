# M0 E0/E1 evidence review and E2 sentinel execution plan

Date: 2026-10-07 (experiment report date; report archive sealed 2026-10-08 UTC)
Source GitHub commit: `653dae35a72b1e29c52c37745806571bff016ef6`
Status: **M0_E1_BASELINE_QUALIFIED**. The M0 causal hypothesis remains **NOT_TESTED**.

## Independent review

The complete 42.8 MB evidence ZIP was reviewed in a separate Linux environment.
Commands performed on extracted copies, with **no simulator runs**:
- `python -B verify_r0_portable.py`: PASS; 39 R0 design files and parent provenance remain unchanged.
- `python -B verify_e1_independent.py`: PASS; 8 U0 runs; 0 wrong-wind runs; 2,551 native files and 39 frozen files verified.
- archive ZIP CRC integrity: PASS.
- reproduced minimum 3-sigma outlet margin >= 6.622976970672608 m;
- Pair-A baseline mask relevance 8/8;
- route detectable sample count 5–10/51;
- LORO source classification: both frozen baseline inference families 8/8;
- native concentration sampling parity 20,400 queries, zero discrepancy;
- zero-filament-deletion pinned-source control-flow certificate and 246-record matched clocks recorded.

Important limits:
- The baseline is a two-candidate source-discrimination preflight in an idealized, analytic-wind box.
- Near-perfect baseline posterior scores do not show PMFS improvement, calibrated uncertainty, or lake-breeze realism.
- Zero deletions were *certified via native invariants and between-save displacement bounds*, not directly measured with a per-tick deletion counter.
- **Cross-wind CRN alignment is not yet demonstrated.**
- There is no wrong-wind posterior or matched-error result; no M0_PASS/PRIMARY_GO.

## Execution decision

Scientific-contract status: E0+E1 review PASS.

**Recommend the next user authorization be strictly limited to E2 sentinel = exactly four already-budgeted wrong-wind runs**. This document is a review/plan; it does **not** itself authorize simulator runs.

Sentinel block: source S0, realization r01 (master seed 2026100701).

Exact frozen run IDs:
1. `m0r0_A_on_S0_r01`
2. `m0r0_A_off_S0_r01`
3. `m0r0_B_shear_S0_r01`
4. `m0r0_B_speed_S0_r01`

Reference from completed E1: `m0r0_U0_S0_r01`.

Do not alter `M0_RUNLIST_PREVIEW.csv` (`launch_authorized=False` is immutable as evidence). A **separate new** execution authorization manifest may explicitly allow only these four run IDs, while all 28 remaining wrong-wind rows remain blocked.

## Before sentinel

- verify the original R0 39-file seal and E1 evidence seal;
- reuse the same native YAML/project entry validated in E1, because old ROS parameter binding for temperature/pressure was defective;
- audit all four native wind assets against exact E0 hashes and readback; confirm same source/gas/geometry/clock/seed/release/route;
- assert result leaves absent and enforce allowlisted isolated write roots;
- check disk/RAM/resource quotas before launch.

## E2 sentinel audit and mandatory stop

After four runs, compare each to the U0 reference:

1. identical native output-clock vector and record-index list, including 246 saved records and 20–120 s frame assignment;
2. identical emission tick count, filament birth order, full sigma-age sequence and same RNG table/hash/call assignment;
3. zero exit/delete, no out-of-bounds/position exceptions, no hidden retry or alternate RNG branch;
4. all-six-face 1m Gaussian support mean/q95, 3-sigma outlet margin and 0–140 s deletion support for **each wrong-wind arm**;
5. physical admissibility and matched Free+ROI RMSE unchanged from frozen E0 readback, despite swapped actual runtime wind assets;
6. source-blind route, native concentration query parity and field/asset/runtime hashes;
7. full baseline/sentinel response diagnostics and paired differences may be archived **as descriptive quality control only**; do not use sentinel outcomes to choose thresholds, arms, seeds, masks, horizons, sources, or direction for later scoring.

**Verdict after E2**:
- `M0_E2_CRN_SENTINEL_QUALIFIED` if all prerequisites pass;
- `M0_E2_PREREQUISITE_HOLD` otherwise.
In either case STOP. No automatic launch of the remaining 28 intervention runs.

If E2 qualifies, request an explicit fresh review/authorization before the remaining 28. Apply the original frozen material-effect/replication gates only after all 40 rows have legally completed.

## Pro / publication interpretation

Even full M0_PASS would be a positive controlled mechanism result only. The main paper still needs an explicit transport-uncertainty-to-GSL algorithm and FSR lakeshore confirmation. This gate must not be presented as a new method outperforming PMFS.
