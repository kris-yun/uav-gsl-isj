# C0.5 Spatial Snapshot Time-Alignment Audit — 2026-09-24

Status: **DATA CONTRACT INVALID — MODEL SCIENCE MUST NOT BE INTERPRETED UNTIL REPLAYED**

## Finding

The frozen C0.5 spatial exporter selected:

`iteration_100,150,200,250,300,350,400,450,500,550`

and declared them to be:

`50,75,100,125,150,175,200,225,250,275 s`

by assuming each file index means one 0.5-s physical save interval.

That assumption is false for the GADEN core used by the frozen bank.

GADEN's `RunningSimulation::SaveResults()` names files with
`last_saved_step`, a counter incremented **once per save**. Saving itself is
triggered by the float32 strict inequality:

`currentTime > lastSaveTime + saveDeltaTime`

before the simulation increments `currentTime += deltaTime`.

Therefore `iteration_N` is a **save counter**, not a physical-time index.

## Exact corrected mapping

| file | old label (s) | save loop step | GADEN currentTime (s) | model state after update count | model record time (s) |
|---|---:|---:|---:|---:|---:|
| iteration_100 | 50 | 551 | 55.099731 | 552 | 55.2 |
| iteration_150 | 75 | 851 | 85.099274 | 852 | 85.2 |
| iteration_200 | 100 | 1151 | 115.098816 | 1152 | 115.2 |
| iteration_250 | 125 | 1423 | 142.299484 | 1424 | 142.4 |
| iteration_300 | 150 | 1673 | 167.301010 | 1674 | 167.4 |
| iteration_350 | 175 | 1923 | 192.302536 | 1924 | 192.4 |
| iteration_400 | 200 | 2173 | 217.304062 | 2174 | 217.4 |
| iteration_450 | 225 | 2423 | 242.305588 | 2424 | 242.4 |
| iteration_500 | 250 | 2673 | 267.307098 | 2674 | 267.4 |
| iteration_550 | 275 | 2923 | 292.308624 | 2924 | 292.4 |

The difference is large enough to change the dynamic-wind history and UAV
trajectory location paired with every concentration snapshot.

## Independent corroboration

The later SLL-v2 raw-filament review reconstructed exact save-loop
`simulation_steps` and obtained:
- zero sigma-age reconstruction error;
- zero lineage progression errors;
- zero invalid birth assignments.

That raw-filament analysis did **not** use the legacy
`iteration_index * 0.5` assumption and therefore is not invalidated by this
finding.

## Scope of invalidation

Experiments that directly consumed the C0.5 ten-frame
`concentration.npy` while treating the frames as 50--275 s are not valid
physical tests until replayed with the corrected record steps.

This includes at minimum:
- M4-v2 C0.5 field/generalization comparisons;
- M4-v3 D0 House02;
- M4 memory-closure D1 derived from that D0;
- spatial / vertical oracle and wall-slide audits tied to those records;
- kinetic / residual / direct-transfer / sparse-source-rank experiments using
  those ten frames;
- later MZ/FPE/source-to-sensor probes if they paired those frames with UAV
  poses or winds at the legacy times.

Not invalidated:
- raw GADEN bank provenance and independent seed checks;
- SLL-v2 raw-filament transition L1 and its independent review;
- M4-v3 structural mechanism tests that do not use C0.5 concentration targets;
- W0 wind-interface semantic audit;
- historical Native PMFS / TNQC closed-loop traces that did not use this
  ten-frame C0.5 spatial export.

## Frozen repair rule

This is a data-alignment repair, **not model tuning**.

For M4-v3 corrected D0:
- architecture unchanged;
- train/holdout split unchanged;
- seeds unchanged;
- epochs/lr/loss unchanged;
- all scientific thresholds unchanged;
- concentration arrays unchanged;
- only the record steps and corresponding wind history are corrected to:

`552,852,1152,1424,1674,1924,2174,2424,2674,2924`.

The old `D0_FAIL_STOP_M4_V3` must be treated as
`INVALID_TIME_ALIGNMENT`, not as evidence for or against the mechanism,
until this corrected replay is completed.
