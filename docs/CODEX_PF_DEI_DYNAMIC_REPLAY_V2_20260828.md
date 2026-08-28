# CODEX TASK — PF-DEI full-trace dynamic replay V2

Date: 2026-08-28

Branch: `research/cg-pc-ctt-v6-dynamic-transport-sbi`

Normative files:

- `docs/CG_PC_CTT_PF_DEI_PHASE_MARGINAL_FREEZE_20260828.md`
- `docs/CG_PC_CTT_PF_DEI_OBSERVATION_OPERATOR_ADDENDUM_20260828.md`

Reference:

- `experiments/cg_pc_ctt/pf_dei_phase_marginal_reference.py`
- `experiments/cg_pc_ctt/selftest_pf_dei_phase_marginal_reference.py`
- `experiments/cg_pc_ctt/ctt_dynamic_io.py`

This V2 task supersedes `docs/CODEX_PF_DEI_DYNAMIC_REPLAY_20260828.md` because observation-operator provenance must be proved in addition to timing/phase provenance.

## Objective

Determine truth-blind whether preserving real within-stop temporal plume events and full ordered CTT dynamics repairs V6-A's 0/30 frequency-only predictive failure.

No C++, Active Probe, House/seed threshold, localization-error tuning, phase search, or feature patch is allowed in this task.

## Stage 0 — freeze existing negative evidence

Record without modification:

- V6-A 30 runs / 150 contexts;
- continuous predictive pass 0/30;
- H01 transfer pass 1/10;
- H02 transfer pass 0/10;
- H03 transfer pass 2/10;
- absolute adequacy pass 0/30;
- verdict `CONTINUOUS_SOURCE_TRANSFER_STILL_INSUFFICIENT_DYNAMIC_TRANSPORT_TEST_REQUIRED`.

## Stage 1 — sync and selftests

Pull branch, record exact HEAD, then run:

```bash
cd /home/zyc/uav-gsl-isj
python3 experiments/cg_pc_ctt/selftest_v4_final_reference.py
python3 experiments/cg_pc_ctt/selftest_v5_active_sequential_reference.py
python3 experiments/cg_pc_ctt/selftest_pf_dei_phase_marginal_reference.py
python3 experiments/cg_pc_ctt/selftest_ctt_bank_io.py
```

All applicable tests must PASS.

## Stage 2 — inventory the finest real observation stream available

Before any new bank work, inspect all 30 frozen OFF runs for:

- block-level measurement trace files;
- continuous raw gas-sample trace files;
- action logs containing block averages and `GAS HIT` / `NOTHING`;
- launch parameters for `measurement_block_samples`, `measurement_settle_samples`, `thresholdGas`, and measurement-trace output paths.

Produce a complete 30-run inventory table. Never silently drop a run.

Preferred primary resolution:

1. if all 30 runs contain authoritative raw within-block samples and timestamps, preserve the raw sample event sequence using the frozen threshold and use it as the primary observation tape;
2. otherwise primary analysis remains the common eight completed block-average HIT/NOTHING events per physical stop;
3. if raw samples exist only for a subset, use them only as a separately labeled diagnostic unless a complete outcome-independent rematerialization is possible.

No mixed observation resolution in the primary 30-run verdict.

## Stage 3 — prove the observation-operator contract

Read authoritative PMFS and CTT/GADEN source.

For PMFS prove:

- how raw gas samples are collected;
- how the block average is computed;
- exactly when `GAS HIT` is declared;
- the actual gas threshold used by the frozen development runs.

For CTT prove what one `occupancyWords` bit means physically/statistically.

Classify:

- `O1_EXACT_EVENT_COMPATIBILITY`: CTT occupancy is the same simulator-side binary event as the PMFS threshold event at the relevant sample cadence;
- `O2_NEEDS_EXACT_PMFS_OBSERVATION_OPERATOR`: CTT occupancy is plume presence only; extend the truth-free builder to emit simulated concentration/event values through the exact frozen PMFS observation operator;
- `O3_UNRESOLVED`: semantics cannot be proved.

If O3:

`STOP_PF_DEI_OBSERVATION_OPERATOR_UNRESOLVED`

and stop.

Forbidden rescue choices after outcomes include `any`, `majority`, `max`, fitted occupancy threshold, fitted concentration transform, or an aggregation chosen because it improves transfer.

## Stage 4 — prove timing and phase provenance

Using builder/GADEN source, launch parameters, source-update timing CSV, and measurement timestamps, prove:

- duration of one CTT recorded step;
- real timing of every observed sample/block;
- semantic meaning of CTT trace `t=0`;
- relationship between trace start and source-update context anchor.

Materialize real observation intervals in CTT step units as:

`observation_intervals_steps[...] = [start,end]`.

Freeze outcome-independent `phase_indices`:

- synchronized trace -> one provenance-derived phase;
- genuine trace-age uncertainty -> finite predeclared phase set justified before outcomes;
- never choose best phase from observed events.

If unresolved:

`STOP_PF_DEI_TIMING_ANCHOR_UNRESOLVED`.

## Stage 5 — materialize ordered real events

Use the same validated physical-stop/context boundaries as V4/V5/V6-A.

For eight-block primary mode:

`observed_tape [J,8]`.

For complete raw-sample primary mode, define and document one deterministic common tensor/list schema preserving all sample timestamps and binary threshold events; do not resample using an outcome-selected rate.

Required regression in eight-block mode:

`mean(observed_tape[j]) == old stop_r[j]`

for every stop.

## Stage 6 — materialize full predicted dynamics at actual stop cells

Stream the frozen truth-free CTT V13 bank as before and extract full ordered occupancy with `ctt_dynamic_io.py`.

For every context retain only actual physical stop cells:

`sim_occupancy [S,8,J,T]`.

If Stage 3 classified O2, materialize the exact simulator-side PMFS observation-event trace instead and record its schema/hash.

Before deleting temporary banks verify:

- carrier manifest/order;
- 8 keyed members;
- member key/hash identity;
- actual stop-cell identity;
- ordered trace length/cadence;
- temporal-mean regression to old `stop_probability` where the same event variable is applicable.

## Stage 7 — PF-DEI full-trace likelihood

Do not reduce the predicted trace to a Markov matrix, semi-Markov feature vector, first-hit scalar, slope, autocorrelation, spectrum, or run-count feature.

For each source/member/allowed phase, score the complete ordered real event sequence through the full trace and the frozen observation operator.

In the existing reference for block-HIT mode, the block probability is the Jeffreys-smoothed exposure-weighted occupancy probability over the exact real block interval.

If Stage 3 O2 requires the exact PMFS simulated observation operator, adapt only the observation-probability adapter; preserve the same source/transport/phase factorization and outcome-independent timing contract.

Marginalize member and allowed phase inside each context:

`E_c(s)=logmeanexp_(m,phi) L_c(s,m,phi)`.

Source remains global across contexts.

## Stage 8 — cross-context and absolute predictive checks

Run leave-one-context-out source transfer.

Require:

- no negative transfer fold;
- at least two positive transfer folds;
- every held-out context beats the source-independent Jeffreys semi-Markov dynamic null;
- after full four-member pass, every 3-of-4 scoring-member leave-one-out rerun retains the complete predictive contract.

The semi-Markov model is the null only. It must not replace the full-trace source likelihood.

## Stage 9 — matched static ablation

From the exact same raw dynamic payload, destroy temporal order and reconstruct the old frequency representation.

Report dynamic versus static for every run and House.

No alternate source grid, route, member bank, or observation subset is allowed.

## Stage 10 — falsification suite

Report all:

1. source/candidate permutation invariance;
2. scoring-member permutation invariance;
3. context permutation invariance;
4. phase-index permutation invariance;
5. phase policy cannot change without timing-provenance change;
6. order permutation with identical hit fraction changes dynamic score on a synthetic fixture;
7. same permutation leaves static score unchanged;
8. synchronized trace shift plus timing-anchor shift leaves score invariant;
9. full ordered trace mean reproduces old frequency payload where semantics match;
10. duplicate block/stop pseudo-replication rejected;
11. semi-Markov null finite on every fold;
12. synthetic common misspecification can lose to absolute null;
13. member-LOO is live;
14. no truth/performance field is loaded by primary materialization/scoring;
15. if raw-sample mode is used, aggregating those samples back to the authoritative block average reproduces the historical block decision exactly.

## Stage 11 — frozen truth-blind verdict

Primary count is final `PF_DEI_PASS` including member-LOO.

- >=20/30 and every House nonzero:
  `PF_DEI_TRUTHBLIND_ACTIONABLE_FOR_FROZEN_PERFORMANCE_SCREEN`
- 10..19/30:
  `PF_DEI_PARTIAL_RECOVERY_NO_CPP`
- <10/30:
  `PF_DEI_CTT_DYNAMIC_FAMILY_INSUFFICIENT_ESCALATE_TO_GADEN_SBI`

No formula/phase/operator/member/null modification is allowed after seeing the result.

If <10/30, stop all hand-feature extensions and move to physics-randomized GADEN SBI.

## Stage 12 — only after >=20/30 truth-blind pass

Freeze all code/data/timing/operator hashes before opening localization outcomes.

Then run an offline development performance screen on the frozen archive:

- pooled expected-location error reduction >=10%;
- >=20/30 runs improve;
- no House pooled mean degradation >5%;
- zero new false-confident collapses.

This is not the final closed-loop claim.

Only if the screen passes may Codex implement C++/Python parity and launch the frozen 60-arm paired closed-loop matrix.

## Deliverables

Commit:

- `docs/PF_DEI_OBSERVATION_INVENTORY_20260828.md`;
- `docs/PF_DEI_OBSERVATION_OPERATOR_PROVENANCE_20260828.md`;
- `docs/PF_DEI_TIMING_PROVENANCE_20260828.md`;
- dynamic materializer/extractor code;
- manifest with all 30 runs, hashes, valid/invalid counts;
- `artifacts/pf_dei/pf_dei_truthblind_coverage.json`;
- `artifacts/pf_dei/pf_dei_truthblind_folds.csv`;
- `artifacts/pf_dei/pf_dei_static_ablation.csv`;
- `docs/PF_DEI_TRUTHBLIND_REPORT_20260828.md`.

The report must separate observation-operator validity, timing validity, dynamic source transfer, absolute adequacy, member robustness, and static-vs-dynamic effect. No localization-performance statement before Stage 12.
