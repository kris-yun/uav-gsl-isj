# Codex execution contract — CTPI V0.4 VM exact offline -> runtime parity -> development closed loop

Repository: `kris-yun/uav-gsl-isj`  
Branch: `research/ctpi-crel-psrg-aprs-v04-20260902`

Do not redesign the method. Do not tune from localization outcomes.

## Stage 0 — integrity and selftest

```bash
git fetch origin
git checkout research/ctpi-crel-psrg-aprs-v04-20260902
git reset --hard origin/research/ctpi-crel-psrg-aprs-v04-20260902
python3 experiments/cg_pc_ctt/ctpi_v04_reference.py --selftest --iterations 3000
```

Require `CTPI_V04_REFERENCE_SELFTEST=PASS`. Record HEAD, source hashes, environment and input hashes.

## Stage 1 — exact fixed-trajectory/offline replay before ROS closed loop

Use frozen H01/H02/H03 historical tapes and exact candidate transport assets on the VM. Do not generate new GADEN fields to improve a failed result.

For every source update, before truth is opened:

1. **CREL:** build candidate x transport-member current response probabilities using only current map/current causal wind/executed route or current observation support/candidate query coordinates.
2. **PSRG:** compute Fisher-Rao pullback tensor on exact shared-edge quadtree neighbours. Export tensor, eigenstructure and fit residual. Do not use local scale as a posterior confidence radius.
3. **APRS:** score candidates against the current `measured_hit_probability` and current confidence field using the transport-marginal logarithmic score. No future blocks, truth, temperature, blend or learned reliability gate.
4. Reproduce native C0/F00 shadow on identical trajectory/update windows.
5. Freeze all scores/hashes before external truth evaluation.

Controls from the same frozen predictions:
- canonical source-law reassignment;
- leave-one-transport-member-out;
- candidate/member order invariance;
- source-label destruction for PSRG local geometry;
- stale-context replay only as a negative diagnostic.

### Stage-1 decision

Do not invent a post-outcome numerical threshold. Advance only on a Pareto-consistent exact-offline result: no House has a stable normalized-AUE reversal against matched C0/F00, equal-House mean AUE is strictly better, and correct source-law association beats its destructive-control baseline. Report Houses separately.

If a House reverses stably, return `CTPI_V04_VM_EXACT_OFFLINE_NO_GO` and stop. Do not tune M1/M2/M3.

## Stage 2 — runtime/reference parity

Only after Stage 1 passes:

- implement exact CREL/APRS reference in runtime;
- prove Python <-> C++ candidate-score parity on frozen contexts;
- prove OFF/native path parity;
- prove no truth/future/planner reward enters inference;
- prove each observation is consumed exactly once.

**No-double-consumption rule:** APRS cannot simply be multiplied onto a native PMFS posterior that already assimilated the same measured-hit field. First runtime qualification must keep APRS shadow-only or replace the corresponding native source-evidence scorer under an explicit A/B contract.

PSRG is initially `prospective shadow`: log it at each update, but do not clip posterior support, set a confidence radius, or steer the planner until unseen-run prospective validation shows the geometry is load-bearing.

Parity/integration failure => `CTPI_V04_RUNTIME_PARITY_NO_GO`.

## Stage 3 — first development closed-loop test

Only after Stages 1 and 2 pass. Compare identical-contract C0/OFF vs V0.4 ON with unchanged planner/cadence/budget. Start one mechanically valid smoke, then matched H01/H02/H03 seed pairs.

Initial ON contract:
- M1 CREL active;
- M3 APRS active only under the no-double-consumption source-scorer contract;
- M2 PSRG prospective shadow only, not an error radius.

Report endpoint error, normalized AUE, standard time-to-threshold metric if already used, source rank, update-level score traces, latency and PSRG prospective diagnostics. Truth remains evaluator-only.

If M1+M3 ON is mechanically valid but clearly worsens source evidence/localization in the first matched smoke, stop rather than tune.

## Stage 4 — M2 active qualification, separately

A full **three-load-bearing-module** closed-loop claim requires a separate prospective test showing PSRG improves sensing/refinement decisions on unseen runs. Do not activate it merely because H01 development correlations were positive. Never interpret `1/sqrt(lambda_min)` as a metric error radius without calibration.

## Prohibited rescue

- no temperature/alpha/blend chosen from results;
- no candidate-specific source-strength fit;
- no truth-aware gate;
- no future wind/gas/route;
- no planner tuning to rescue source scoring;
- no new bank generation after scientific NO-GO;
- no removal of hard Houses/seeds.

## Terminal strings

- `CTPI_V04_VM_EXACT_OFFLINE_NO_GO`
- `CTPI_V04_RUNTIME_PARITY_NO_GO`
- `CTPI_V04_DEVELOPMENT_CLOSED_LOOP_NO_GO`
- `CTPI_V04_DEVELOPMENT_CLOSED_LOOP_PASS_M2_SHADOW`
- `CTPI_V04_THREE_MODULE_ACTIVE_DEVELOPMENT_PASS` (only after separate M2-active prospective qualification)
