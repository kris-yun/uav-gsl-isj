# CCDE held-out runtime report

Date: 2026-08-07
VM: zyc@192.168.111.128 (4 cores, 5 GB RAM)

## Pipeline

Per seed, the runbook chain was:
`01_single_seed_smoke.sh` (B0-R online run + M0 snapshot triplet verification)
-> snapshot freeze (per-seed immutable copy + SHA-256)
-> candidate packages (`m1_replay_probe TRACE_REPLAY`)
-> nuisance atoms (`m1_replay_probe NUISANCE`, CRN parity on update 0)
-> wind atoms `(g(theta+15)-g(theta-15))/2`
-> fixed-trace gate (A1 MSF, A2 CCDE-Wind) with inference frozen before truth evaluation.

## Wall-clock budget

| seed | baseline smoke (s) | pilot elapsed (s) | candidate+atoms+gate (s) |
|---|---:|---:|---:|
| H01_11 | ~340 | 311.2 | ~90 |
| H01_12 | ~318 | 303.5 | ~71 |
| H01_13 | ~321 | 303.9 | ~69 |
| H03_11 | ~327 | 310.5 | ~88 |
| H03_12 | ~326 | 310.4 | ~85 |
| H03_13 | ~326 | 310.8 | ~80 |

Pilot elapsed is the B0-R action-server result latency reported by
`gsl_pilot_runner` (3 native source updates complete in every seed).

## Notes

- `run_validity.json` reports `formal_completion_invalid` with
  `missing_result_csv` because the pilot runner checks for
  `official_gsl_results.csv` while the action server writes
  `pmfs_results.csv` (pre-existing naming mismatch; the runbook gate does not
  depend on it). The B0-R native result CSV is preserved per seed.
- One smoke retry was needed for H01_11 and H01_13 (natural runs that
  converged before a third source update); retries rerun the same seed with no
  parameter change.
- Runtime is real-time simulation (`realtime_factor=1.0`); the fixed-trace
  gate itself is offline and completes in seconds.
