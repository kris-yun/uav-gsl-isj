# CTPI full-law factorial terminal audit

## Decision

`CTPI_FULL_LAW_FACTORIAL_NO_GO`

M1 CREL is retained.  The proposed M2 complete-count-law categorical update is
retired as a main module.  M3 was not evaluated and no C++ runtime, parity run,
ROS smoke, or formal closed-loop run was started.

This is the required result of the preregistered execution boundary: M1 and M2
both had to pass offline before any M3 runtime work was authorized.

## Scope and integrity

- Houses: H01/H02/H03.
- Historical tapes: seeds 0--9, five source updates per tape.
- Arms: authoritative A0, F00 (M1), F01 (M1 plus proposed M2).
- Destructive control: every canonical non-identity source-law reassignment.
- GADEN runs: zero.
- Neural training: none.
- Closed-loop runs: zero.
- Commit: `7a58f02` on `codex/ctpi-full-law-closedloop-20260902`.
- Final factorial summary SHA-256:
  `131a08c0bcff72f0caedb2d69d0e10364494ea20c4497920e363f070dc3396be`.
- Oracle summary SHA-256:
  `44e755038770e54028d591e8fdd510b7497f5e5d7396e0fef19aaeb8d738dbf3`.

The official localization endpoint selects the top 5 percent of cells.  A
machine-epsilon recomputation of F00 could change the last selected cell when
probabilities tied.  Commit `7a58f02` therefore verifies formula parity but
retains the previously frozen F00 posterior bit-for-bit.  Against the prior
authoritative audit, A0/F00 had zero differing per-update rows and zero
differing final/AUC/time/rank case rows.

## M1 result: PASS

`F00 vs A0` gave a repeatable robot-task increment without a stable reverse
House in the selected metrics:

| Metric | A0 mean | F00 mean | wins/losses/ties | one-sided sign p | Result |
|---|---:|---:|---:|---:|---|
| final error (m) | 5.1823 | 2.6271 | 22/8/0 | 0.00806 | PASS |
| time to 2 m (s) | 278.4102 | 208.0386 | 15/3/12 | 0.00377 | PASS |
| true-source normalized rank | 0.7665 | 0.3004 | 30/0/0 | 9.31e-10 | same direction |

Error AUC also improved in the pooled result (1497.73 to 945.45 m s), but H02
had a stable reverse, so AUC was not needed as the M1 Gate metric.

## M2 result: FAIL

`F01 vs F00` did not improve any eligible robot-task metric and moved the true
source rank in the wrong direction:

| Metric | F00 mean | F01 mean | wins/losses/ties | Failure |
|---|---:|---:|---:|---|
| final error (m) | 2.6271 | 2.8637 | 19/11/0 | no clear increment; H03 stable reverse |
| error AUC (m s) | 945.45 | 1169.07 | 7/23/0 | significant worsening; H02/H03 stable reverse |
| time to 2 m (s) | 208.0386 | 234.7304 | 8/11/11 | H03 stable reverse |
| true-source normalized rank | 0.3004 | 0.6564 | 5/25/0 | significant worsening; H01/H02 stable reverse |

The law-reassignment control did degrade: real F01 beat the median reassigned
law on final error (4.4407 to 2.8637 m), AUC (1475.65 to 1169.07 m s), and rank
(0.8494 to 0.6564).  That establishes that source-law association exists.  It
does not establish that the proposed M2 adds useful evidence over F00.

## Failure mechanism

The proposed M2 scores the exact cumulative count `H` under only eight coherent
members and `N+1` count categories.  As `N` grows, most candidate laws are
sparse: many sources receive the same Jeffreys floor because no member has the
exact observed count.  The score also treats two unobserved categories as
equally wrong even when one is adjacent to `H` and the other is far away.  It
therefore replaces F00's smooth count-distance evidence with a high-variance
exact-match decision.  The observed rank collapse and H02/H03 AUC reversals are
the expected downstream signature of that failure.

The destructive control result sharpens this diagnosis: the bank is not
uninformative and the physical source labels are not arbitrary.  The failed
component is the exact-count assimilation rule, not M1 and not bank generation.

## Next admissible path to a three-module closed loop

1. Keep M1 unchanged.
2. Do not tune, temper, blend, or otherwise rescue this full-law categorical
   M2 on H01/H02/H03 seeds 0--9.
3. Design a new M2 around the coherent per-stop member sequence and a calibrated
   sensor-event predictive law.  Before source truth is opened, it must improve
   event NLL/Brier/calibration on held-out observation sequences.
4. Freeze the new formula and use new untouched confirmatory tapes/seeds.  The
   current 30 cases are now development/failure-analysis data.
5. Require the same downstream `F01 vs F00` Gate.  Only after it passes, add the
   M3 predictive-information runtime, prove C++/Python parity, and run one
   four-arm H01 seed1 smoke before the 36 formal closed-loop runs.

This sequence preserves the intended causal loop while preventing M3 planning
from hiding a failed estimator module.

## Evidence package

VM path:

`/home/zyc/CTPI_THREE_MODULE_OFFLINE_NO_GO_20260902_7a58f02_R3.tar.gz`

SHA-256:

`cfc33131ee15eba0172b1bb863e0b98c61e7e42f7188d1862e8156f73ff6f2d4`

The archive contains the exact Git bundle, LF run script, complete log,
authoritative prior Stage-1 artifact, oracle Stage 1/2, and factorial Stage 1/2.
