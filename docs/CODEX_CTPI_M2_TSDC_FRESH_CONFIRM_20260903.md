# Codex directive — CTPI M2 TSDC V0 fresh confirmation

Authoritative branch: `research/ctpi-m2-tsdc-committor-20260903`.
Parent terminal NO-GO is preserved at `749c620bffe1d994370b1ac043c5caa4f8662905`.

## 0. Do not redesign M2

The M2 scientific object and coefficients are frozen. Do not change formula, features, coefficients, thresholds, sensor timing, or Gate criteria.

Authoritative runtime file:

`experiments/cg_pc_ctt/ctpi_m2_tsdc_frozen_v0.py`

Required SHA-256:

`854a2fc8513201cdb2ae497a62c0cd3c5fa09fdae2f1bc309ad594a8b1aaacf7`

Freeze JSON:

`docs/CTPI_M2_TSDC_FREEZE_V0_20260903.json`

Fresh-confirm preregistration:

`docs/CTPI_M2_TSDC_FRESH_CONFIRM_PREREG_20260903.json`

The old 60 CAL/CONFIRM worlds are permanently `DEV_SPENT`. They can be used only for parity reproduction, never as new confirmation.

## 1. Frozen M2

TSDC = Transport-Sensor Detection Committor.

For source/action transport-member hit count `K` and the causal decision-time measured sensor state `M_decision`:

`pK=(K+0.5)/9`

`rK=logit(pK)`

`rM=log(1+M_decision/0.1ppm)`

`q=logistic(beta0+betaK*rK+betaM*rM)`

Frozen coefficients:

- beta0 = `-1.1915279295661385`
- betaK = `1.0423583775118566`
- betaM = `2.9896670550884170`

`M_decision` is the measured detector state at the END of the previous completed 80-sample dwell window, before the next action is selected. First action uses zero. Values sampled during candidate transit, at arrival, or immediately before the candidate dwell are forbidden future information.

M2 does NOT update the M1 source posterior. It only predicts the future measured detector event for M3.

## 2. Phase A — reproduce committed DEV audit only

Use the preserved source-intervention NO-GO evidence package with SHA-256:

`36cacb3985f42138b231cec969b3ac19ee41a833bbe3002fe7e509292a764824`

Run:

`experiments/cg_pc_ctt/ctpi_m2_tsdc_frozen_v0.py`

and

`experiments/cg_pc_ctt/ctpi_m2_tsdc_dev_audit.py`

Expected hard checks:

- frozen runtime selftest PASS;
- DEV refit beta max absolute difference to frozen beta <= `1e-12`;
- 900 events / 60 worlds;
- world-grouped 10-fold OOF raw NLL ~= `0.311726648`;
- TSDC NLL ~= `0.210108870`;
- raw Brier ~= `0.095953361`;
- TSDC Brier ~= `0.063798347`;
- TSDC vs raw world NLL = 54/6;
- TSDC vs raw world Brier = 53/7;
- betaK positive in every fold;
- leave-one-House-out NLL improves in H01/H02/H03;
- 31/31 transport-association destructive controls and 31/31 detector-state destructive controls are worse than the real mapping.

This phase is parity only. Do not call it confirmation.

If any committed metric/hash fails to reproduce, STOP and report `CTPI_M2_TSDC_DEV_PARITY_FAIL`.

## 3. Phase B — freeze a NEW 30-world manifest before outcomes

Create exactly 30 new controlled-source worlds: H01=10, H02=10, H03=10.

Before generating any formal outcome:

- select carriers deterministically using frozen bank-only information;
- prefer carriers not used in the 60 DEV_SPENT worlds where feasible;
- do not inspect observation outcomes;
- use the frozen source-region/reserved-placement contract, never a quadtree centroid as physical source XYZ;
- use new observation RNG seeds/domains disjoint from all known bank/historical/CAL/CONFIRM RNG assets;
- predictive bank remains read-only and must not be regenerated;
- freeze and hash the complete 30-world manifest.

## 4. Phase C — generator integrity

For every formal world require:

- one native generator invocation;
- frozen OMP/runtime identity;
- 1500 physical samples;
- 1502 causal sensor samples;
- exactly 15 completed 80-sample dwell windows;
- bank before/after hashes identical;
- per-world audit PASS;
- source metadata not supplied to M1/M3 runtime logic.

A disposable smoke may be used before formal generation, but it is not part of the 30 worlds.

## 5. Phase D — one-shot fresh Gate

Use ONLY `ctpi_m2_tsdc_frozen_v0.py`. The frozen runtime intentionally contains no fitting function.

For each event compute:

- raw comparator: `(K+0.5)/9`;
- TSDC: frozen q using causal `M_decision`.

All preregistered criteria are conjunctive. In particular:

- pooled NLL lower than raw;
- pooled Brier lower than raw;
- ECE-5 not worse;
- paired world NLL one-sided exact sign p <= 0.05;
- paired world Brier one-sided exact sign p <= 0.05;
- each House has >=6/10 NLL wins;
- no House has both mean NLL and mean Brier worse than raw;
- frozen beta/module hashes match;
- no outcome-dependent refit or feature change.

Any failure:

`CTPI_M2_TSDC_FRESH_CONFIRM=NO_GO`

Then stop. Do not tune from these outcomes.

All criteria PASS:

`CTPI_M2_TSDC_FRESH_CONFIRM=PASS`

This authorizes ONLY the M3 offline action Gate. C++, ROS, and formal closed-loop remain forbidden until M3 itself demonstrates an independent increment.
