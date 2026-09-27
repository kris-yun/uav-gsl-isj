# Physical time / observation contract

This contract replaces the earlier 3-second concentration averaging draft.

## Time origin

F1 defines:

`t=0` = GADEN simulator start = configured gas-release start = path schedule
origin.

Before reading concentration, runtime metadata/logging must verify that gas
emission actually begins at physical simulator time 0.0 s under the frozen
configuration.

If simulator/runtime semantics show a nonzero or ambiguous release offset,
STOP:
`AOD_F1_HOLD_TIMEBASE`.

Do NOT redefine t=0 after inspecting gas.

## Main observation slots

Exactly one concentration snapshot per path slot:

`50,100,150,200,250,300,350,400,450,500 s`.

The frozen 3-second dwell remains only a motion/settling budget used by F0 path
feasibility. It is NOT a 3-second concentration average and does not create
multiple observations.

At each slot, use the frozen probe footprint and the concentration field at the
single exact physical time `t`.

## Simulation/save configuration

Keep:
- integration `time_step=0.1 s`;
- saved result interval `0.5 s`;
- `results_min_time=0.0`;
- House03 / `1-2,5_fast`;
- frozen 96 GADEN seeds and source xyz.

Set total simulation duration to **510.0 s** solely to ensure the final 500 s
sample exists with write-out margin.

Scientific target times stop at 500.0 s; data after 500 s are never scored.

## Timestamp mapping

Never infer physical time by multiplying an ordinal filename/index by 0.5.

Instrumentation must write:

`RESULT_TIME_MAP.tsv`

with at least:
- run_id
- save_record_id
- physical_sim_time_s
- output path/file identifier
- active wind index/state at that physical time

Before concentration extraction:
1. generate only the first scheduled GADEN run;
2. inspect timestamp/writer/wind metadata only;
3. do not read concentration values;
4. verify all ten exact target times exist within 1e-9 s;
5. verify source release start is 0.0 s;
6. freeze the mapping implementation/commit.

If any target time is missing:
do not nearest-neighbour, clip, wrap or reuse legacy 300 s output.
STOP `AOD_F1_HOLD_TIMEBASE`.

## Wind-phase reporting

Archived config includes `wind_time_step=1.0`, looping steps 1..10.
Because 50 s slot spacing may phase-lock to the wind schedule, record the
actual wind index at every scored target timestamp.

Do NOT phase sweep or alter target times.

If all ten slots land on the same wind phase, report that as a limitation:
this F1 remains a fresh source-location confirmation, not a claim of independent
sampling of ten wind phases.
