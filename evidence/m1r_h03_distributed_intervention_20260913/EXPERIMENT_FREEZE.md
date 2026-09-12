# H03 distributed paired-intervention premise freeze

Date: 2026-09-13
Status: **FROZEN BEFORE NEW GAS RESPONSE GENERATION**

## Question

Does distributing the physical rank-2 action over three source-blind map
stations provide global source support that the failed one-station operator
lacked, while paired contrasts and the common-source constraint are both
load-bearing?

This is an offline H03 source-response premise test.  It is not a PMFS,
planner, posterior or closed-loop run.

## Frozen route and worlds

The route contains a fixed 60 s prefix from the existing H03 source-blind
map-cover trajectory.  Three stations are selected by deterministic farthest
sampling from the source-independent candidate support and visited in the
shortest feasible order.  Each station executes three `A-B-B-A` cycles at
absolute target directions 0, 60 and 120 degrees.  The generated route:

- ends at 222.2 s, below the existing 240 s budget;
- has maximum average speed 0.300000000000003 m/s;
- has rank 2 at every station;
- has maximum station direction condition number 1.162477;
- reads no gas value, source coordinate, posterior, localization error or
  result during construction.

Exactly four worlds use the same route, release process, GADEN RNG seed 1234,
sensor configuration and current H03 runtime:

| physical source intervention | coordinate | existing transport |
|---|---|---|
| failed H03 truth SA | `(-0.45, 1.90, -0.10)` | fast |
| failed H03 truth SA | `(-0.45, 1.90, -0.10)` | slow |
| historical strongest-false HF | `(8.15, -1.413, -0.10)` | fast |
| historical strongest-false HF | `(8.15, -1.413, -0.10)` | slow |

No new House or seed is introduced.  HF is a simulator-side falsification
world and is unavailable to the runtime scorer.

## Frozen estimator

For each station, three contrasts use weights `[0.5,-0.5,-0.5,0.5]` at the
four equally spaced endpoints.  A station is active only when at least one
endpoint exceeds the native 0.1 ppm PMFS threshold.  Fewer than two active
stations is an automatic failure.

The H03-held-out provider parameter was selected from H01+H02 before this
experiment.  The complete 820-point 0.3 m source support is retained.  One
nonnegative amplitude is profiled independently at each active station, while
one candidate source identity is shared by all active stations.  Per-station
squared residuals are divided by observed station contrast energy and summed.
There is no parameter fit after results are visible.

## Gates evaluated once

All seven conditions must pass before one H03 closed-loop development screen:

1. Every physical world has at least two active stations.
2. The full nine-contrast SA-minus-HF vector has positive fast/slow cosine and
   its source main-effect norm exceeds the source-by-transport interaction norm.
3. The held-out provider source-difference vector has positive cosine with the
   physical source difference in fast and slow transport.
4. The nearest full-support candidate to SA and HF has unique rank 1 in all
   four source-by-transport worlds.
5. Compared with fitting the same 12 endpoint samples per active station
   without contrasts, paired ranking never degrades in any world.
6. Paired ranking strictly improves over that same-endpoint comparator in at
   least one world.
7. In every world, at least one active station alone does not uniquely rank the
   truth first; the cross-station shared-source constraint must resolve real
   ambiguity rather than merely concatenate already solved stations.

Failure returns `NO_GO_NO_CLOSED_LOOP_DISTRIBUTED_OPERATOR`.  No gate,
threshold, station, scale contract, source world or score will be changed after
the four physical results are visible.  A two-of-four result, a near-source
best point, or one successful transport is not a pass.

## Frozen artifacts

- `THEORY_AND_LITERATURE.md`: derivation and DOI-level provenance.
- `route/ROUTE_RULE.json`: source/gas-blind design and hashes.
- `route/H03/history_route.csv`: exact physical route.
- `tools/build_h03_distributed_paired_route.py`: route constructor.
- `tools/run_h03_distributed_paired_probe.sh`: authenticated VM runner.
- `tools/evaluate_h03_distributed_paired_probe.py`: one-shot gate evaluator.
