# H03 rank-2 paired physical-measurement probe freeze

Date: 2026-09-13
Status: **FROZEN BEFORE PHYSICAL RESPONSE GENERATION**

## Scientific question

Can a source/gas-blind, physically executed set of three paired-position
contrasts add the missing independent spatial direction and uniquely separate
source responses over the complete H03 support under both existing transport
conditions?

This is the minimum premise test for the only surviving causal direction.  It
is not a PMFS, planner or closed-loop experiment.

## Theory-to-design bridge

The 2026 cross-domain review found a common condition: a new physical
measurement must add an independent constraint; post-hoc processing of one
aliased response cannot do so.  The old H03 route supplied real paired source
contrast, but its four direction vectors had condition number 33.47 and only
0.089% of their energy in the second direction.

The frozen route retains the longest admissible geometry-only line and adds
two map-feasible lines targeted at 60 and 120 degrees from it.  Selection uses
only:

- the source-blind H03 map-cover trajectory;
- the source-independent free-space candidate map;
- fixed alignment, midpoint, length and path-detour terms;
- the 0.3 m/s route-speed limit and 1.2 s sensor time scale.

No gas value, source coordinate, posterior, localization error or House-specific
fit enters route construction.  The resulting direction matrix has rank 2,
singular values `[1.262233, 1.186072]`, and condition number `1.064213`.

Each cycle physically traverses `A -> B`, remains at B for the same duration,
and returns `B -> A`.  The four endpoint samples are equally spaced, so the
contrast weights `[0.5,-0.5,-0.5,0.5]` remove common constant and linear drift.
All paths use the 0.1 m free-space graph; maximum route speed is 0.29438 m/s.

## Frozen worlds

Exactly four offline H03 worlds use the same current runtime, release process,
GADEN RNG seed 1234, sensor seed/configuration and route:

| source | coordinate | transport |
|---|---|---|
| failed H03 truth SA | `(-0.45, 1.90, -0.10)` | existing fast |
| failed H03 truth SA | `(-0.45, 1.90, -0.10)` | existing slow |
| historical strongest-false centroid HF | `(8.15, -1.413, -0.10)` | existing fast |
| historical strongest-false centroid HF | `(8.15, -1.413, -0.10)` | existing slow |

HF is evaluator-side physical falsification support.  It is not supplied to a
runtime estimator.  Its z coordinate is fixed equal to SA to isolate the x-y
source intervention.  No new House or stochastic seed is introduced.

## Frozen evaluation

The provider parameters are the existing H03-held-out LOHO choice trained from
H01+H02 only.  The candidate domain is the full 820-point 0.3 m support.  A
single nonnegative amplitude is profiled per response as the declared release
scale nuisance.  No threshold, temperature, posterior, distance penalty or
House-specific parameter is fitted.

All of the following must pass before any H03 closed-loop run:

1. Four worlds share byte-identical route/time coordinates; each crossed source
   pair shares byte-identical wind observations.
2. The fast and slow observed source-difference vectors have positive cosine,
   and the source-main-effect norm exceeds the source-by-transport interaction
   norm.
3. The held-out provider's source-difference vector has positive cosine with
   the physical observed difference in both transports.
4. The nearest full-support candidate to **both** SA and HF has unique rank 1
   under **both** fast and slow response vectors.

The fourth rule prevents a truth-centred success: `4/4` exact source-world
rankings are required.  Near-source best estimates, removal of only HF, a broad
identified set, or all-zero ties do not pass this main-innovation premise.

Failure returns `NO_GO_NO_CLOSED_LOOP_CURRENT_RANK2_OPERATOR`.  The score,
cycles, worlds and criteria will not be changed after results are visible.

## Frozen artifacts and commands

- Route rule: `route/ROUTE_RULE.json`
- Route: `route/H03/history_route.csv`
- Route builder: `tools/build_h03_rank2_paired_route.py`
- VM raw-world runner: `tools/run_h03_rank2_paired_probe.sh`
- Evaluator: `tools/evaluate_h03_rank2_paired_probe.py`

Build the route from frozen inputs:

```powershell
D:\Anaconda\python.exe -X utf8 tools\build_h03_rank2_paired_route.py `
  --repo D:\ZYC\CSTAR_M1R_CAUSAL_REPAIR_20260912 `
  --output-root evidence\m1r_h03_rank2_paired_probe_20260913\route
```

The VM runner requires a host-verified source archive and receipt bound to the
published commit.  It refuses an existing output root and records input/output
hashes.  Evaluation occurs only after all four raw worlds complete.
