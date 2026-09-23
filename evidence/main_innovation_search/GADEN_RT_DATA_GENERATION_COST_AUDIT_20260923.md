# GADEN-RT Data-Generation Cost Audit — Implications for M3/M4/M5/M6

Date: 2026-09-23

## Public performance evidence

GADEN-RT (SoftwareX 2025) was explicitly redesigned for faster-than-real-time gas simulation.

Relevant design points:

- `RunningSimulation` can operate without precomputing/storing dense 3-D concentration maps;
- filament motion is advanced online;
- concentration can be queried only at requested points;
- filament-only mode avoids unnecessary dense concentration computation;
- dense concentration generation has also been optimized and supports GPU acceleration.

The paper reports performance evaluation for 300 s simulated-time cases across multiple environments and shows substantial speedup over the original GADEN workflow.

## Implication

The current multi-source/intervention pilot should **not** reuse the old expensive precompute-and-compress workflow by default.

Preferred pilot path:

1. load/preprocess House geometry + wind once;
2. instantiate `RunningSimulation`;
3. modify source position/condition;
4. run with `saveResults=false`;
5. query only:
   - the PMFS sensor-height 2-D grid at selected times; or
   - filament states;
6. store compact training/evaluation arrays.

This makes small source/wind factorial experiments plausibly practical.

## M4 minimum pilot size

2 sources × 2 wind conditions × 2 seeds:

[
8 	ext{simulations}
]

for one held-out-combination fold.

A second held-out fold can reuse the same full 2×2 generated dataset.

Thus C0 does **not** require a large source grid.

## M6 minimum internal pilot

For a low-data transfer test:

- 4–8 source positions;
- 2 seeds/source;
- one House;
- one ground-truth wind condition initially.

This is:

[
8	ext{–}16 	ext{simulations}.
]

Do not generate more until pretrained-vs-random signal exists.

## M5 minimum pilot

M5 can be even cheaper because `GetFilaments()` exposes the particle state directly.

No dense concentration map is required for the L1 transition-residual gate.

## Remaining local benchmark

Public performance evidence is only a feasibility prior.

Codex/VM must benchmark one new House02 source realization and record:

- simulated duration;
- wall-clock;
- CPU/GPU;
- RAM;
- if sampling a sensor-height grid:
  - grid token count;
  - number of sampled times;
  - concentration-query cost;
- disk size.

## Stop rule

Do not launch a batch before the one-source benchmark is committed.

If one 300 s new-source realization plus required slice sampling is unexpectedly expensive on the user's VM, reduce:
- simulated duration for the mechanism smoke test;
- number of sampled times;

but do not change source/wind labels after seeing truth.

Status:

`DATA-GENERATION FEASIBILITY = PROVISIONALLY GREEN; LOCAL BENCHMARK REQUIRED`.
