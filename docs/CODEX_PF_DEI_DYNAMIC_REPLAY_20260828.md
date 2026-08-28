# CODEX TASK — PF-DEI full-trace dynamic-event replay

Date: 2026-08-28

Branch: `research/cg-pc-ctt-v6-dynamic-transport-sbi`

Normative science contract:
`docs/CG_PC_CTT_PF_DEI_PHASE_MARGINAL_FREEZE_20260828.md`

Reference:
`experiments/cg_pc_ctt/pf_dei_phase_marginal_reference.py`

Selftest:
`experiments/cg_pc_ctt/selftest_pf_dei_phase_marginal_reference.py`

Ordered CTT I/O:
`experiments/cg_pc_ctt/ctt_dynamic_io.py`

## Objective

Test whether preserving the full ordered CTT occupancy dynamics, while factorizing global source identity from context-specific transport/phase nuisance, repairs the V6-A frequency-only cross-context failure.

This task is truth-blind through the primary verdict.

Do NOT implement C++.
Do NOT run V5 Active Probe.
Do NOT tune House/seed thresholds, feature weights, timing lag, phase set, member subset, prior, or null from localization outcomes.

## Stage 0 — freeze the known V6-A negative result

Record as immutable provenance:

- 30 runs / 150 contexts;
- continuous predictive pass 0/30;
- H01 transfer pass 1/10;
- H02 transfer pass 0/10;
- H03 transfer pass 2/10;
- absolute adequacy pass 0/30;
- verdict `CONTINUOUS_SOURCE_TRANSFER_STILL_INSUFFICIENT_DYNAMIC_TRANSPORT_TEST_REQUIRED`.

Do not rerun V6-A with altered rules.

## Stage 1 — pull and run selftests

Record exact HEAD, then run:

```bash
cd /home/zyc/uav-gsl-isj
python3 experiments/cg_pc_ctt/selftest_v4_final_reference.py
python3 experiments/cg_pc_ctt/selftest_v5_active_sequential_reference.py
python3 experiments/cg_pc_ctt/selftest_pf_dei_phase_marginal_reference.py
python3 experiments/cg_pc_ctt/selftest_ctt_bank_io.py
```

All applicable tests must PASS before data materialization.

## Stage 2 — establish the timing/anchor contract before any dynamic score

This stage is blocking and must use authoritative source/config/runtime provenance only.

Recover and report:

1. the physical duration represented by one CTT recorded occupancy step;
2. the physical start/end time of every completed PMFS measurement block;
3. the semantic meaning of CTT trace `t=0` relative to one source-update context;
4. whether the real context and the rebuilt candidate trace share a synchronized time anchor;
5. if not synchronized, exactly which trace-age/phase uncertainty is scientifically justified before seeing HIT/NOTHING outcomes.

Preferred evidence sources:

- CTT builder source;
- GADEN simulation-step and recording code;
- frozen launch parameters;
- source-update timing CSV;
- authoritative action-log timestamps;
- truth-free builder metadata.

Convert every observed completed block to

`block_intervals_steps[j,b] = [start,end]`

in CTT record-step units. Fractional boundaries are allowed.

Freeze `phase_indices` outcome-blind:

- known synchronized anchor -> one provenance-derived phase;
- genuinely unknown trace age -> a predeclared finite phase set justified by provenance;
- never choose the best phase from observed outcomes;
- never enlarge/shrink the phase set after looking at predictive results.

If the timing anchor or allowable phase set cannot be established unambiguously:

`STOP_PF_DEI_TIMING_ANCHOR_UNRESOLVED`

and stop the task.

## Stage 3 — recover the exact ordered observed tape

Reuse the authoritative OFF development archive:

`/home/zyc/CG_PC_CTT_V3_ORR_MULTI30_20260827`

For every context and physical stop recover the same eight completed `GAS HIT`/`NOTHING` decisions used by the validated V4/V5 adapter, but preserve order:

`observed_tape [J,8]`.

Also preserve raw block timestamps and the derived `block_intervals_steps [J,8,2]`.

Required regressions:

- exactly eight completed blocks per physical stop;
- stop and context grouping exactly match V4/V5;
- `mean(observed_tape[j]) == old stop_r[j]` for every stop;
- no true source, localization error, ON outcome, route-success label, or plume-success proxy is loaded by the truth-blind process.

## Stage 4 — recover full ordered CTT occupancy at actual stop cells

Use the frozen truth-free CTT V13 builder and stream banks as before.

For every context materialize only the actual physical-stop cells:

`sim_occupancy [S,8,J,T]` binary.

Use `ctt_dynamic_io.read_selected_occupancy()` or an exact parity-equivalent implementation.

Before deleting a streamed bank verify:

- source carrier manifest and ordering;
- 8 keyed transport members;
- transport-member key/hash identity;
- actual selected stop cells equal those used by V4/V5;
- `mean_t sim_occupancy[s,m,j,:]` reproduces the old V4/V5 `stop_probability[s,m,j]` for every materialized context within binary floating precision;
- `T` and record-step timing match Stage 2 provenance.

Dynamic context schema:

- `sim_occupancy [S,8,J,T]` uint8/bool;
- `observed_tape [J,8]` uint8/bool;
- `block_intervals_steps [J,8,2]` float64;
- `phase_indices [P]` int64;
- `geometry_prior [S]`;
- `house`, `seed`, `update_id`, `context_id`;
- timing-provenance hash/id.

Forbidden fields include truth, true source, final error, ON outcome, improvement label, or any performance-derived tuning field.

## Stage 5 — run the PF-DEI truth-blind predictive contract

For each run, process all five contexts.

For each context/source/member/phase the reference computes exposure-weighted full-trace block probabilities and the ordered Bernoulli log score.

Transport member and allowed phase are marginalized *inside that context*:

`E_c(s) = logmeanexp_(m,phi) L_c(s,m,phi)`.

Then perform leave-one-context-out source transfer.

Require:

- no negative held-out transfer gain;
- at least two strictly positive held-out transfer gains;
- every held-out context beats the source-independent Jeffreys semi-Markov dynamic null;
- after a full four-member pass, all four 3-of-4 scoring-member leave-one-out re-runs must also pass.

Write per-fold values and per-run verdicts.

## Stage 6 — matched frequency-only ablation

From the exact same dynamic payload compute the static ablation:

- predicted source/member/stop probability = full-trace occupancy mean;
- observed stop outcome = 8-block hit mean.

Do not use another archive or another candidate grid.

Report dynamic versus static for every run and House.

## Stage 7 — mandatory falsification checks

All must be reported:

1. candidate/source permutation invariance;
2. scoring-member permutation invariance;
3. context permutation invariance of final source posterior and run verdict;
4. permutation of `phase_indices` leaves marginalized evidence unchanged;
5. changing the phase set is rejected unless the timing-provenance hash changes consistently;
6. an observed block-order permutation with unchanged hit fraction changes PF-DEI score on a non-degenerate synthetic fixture;
7. the same permutation leaves the matched static score unchanged;
8. synchronized trace shift plus equally shifted timing anchor leaves the score invariant on a synthetic fixture;
9. full CTT ordered occupancy mean reproduces old frequency payload;
10. duplicate physical stop/block pseudo-replication is rejected;
11. source-independent semi-Markov null is finite for every held-out fold;
12. a synthetic common-misspecification case can lose to the semi-Markov null even when one source candidate is relatively best;
13. member-LOO test is live: construct a non-degenerate synthetic case in which one scoring member is essential and verify removal changes/fails the contract;
14. truth/performance fields are absent from all primary inputs and process logs.

## Stage 8 — frozen truth-blind decision

Use exact counts:

- `PF_DEI_PASS >= 20/30` and every House has at least one pass:
  `PF_DEI_TRUTHBLIND_ACTIONABLE_FOR_FROZEN_PERFORMANCE_SCREEN`;
- `10..19/30`:
  `PF_DEI_PARTIAL_RECOVERY_NO_CPP`;
- `<10/30`:
  `PF_DEI_CTT_DYNAMIC_FAMILY_INSUFFICIENT_ESCALATE_TO_GADEN_SBI`.

Do not alter the likelihood, timing/phase contract, null, member split, prior, or thresholds after seeing the result.

If `<10/30`, STOP. Do not add slope, first-hit, dwell-time, run-count, autocorrelation, spectral, or manually weighted feature patches.

## Stage 9 — only after a truth-blind >=20/30 pass

Freeze:

- git SHA;
- Python reference hash;
- materializer hash;
- dynamic context manifest SHA-256 values;
- timing-provenance file/hash;
- science-contract hash.

Only then unblind the existing development archive for a clearly labeled offline performance screen.

Screen requirements:

- pooled expected-location error reduction >=10%;
- >=20/30 runs improve;
- no House pooled mean degrades by >5%;
- zero new false-confident collapses.

This offline screen is not the final closed-loop claim.

Only if it passes should Codex implement C++/Python parity and launch the frozen 60-arm OFF/ON closed-loop matrix.

## Deliverables

Commit:

- `docs/PF_DEI_TIMING_PROVENANCE_20260828.md`;
- dynamic materializer/extractor code;
- dynamic NPZ manifest with SHA-256 and invalid/missing counts;
- `artifacts/pf_dei/pf_dei_truthblind_coverage.json`;
- `artifacts/pf_dei/pf_dei_truthblind_folds.csv`;
- `artifacts/pf_dei/pf_dei_static_ablation.csv`;
- `docs/PF_DEI_TRUTHBLIND_REPORT_20260828.md`.

The report must state exact 30-run House counts, member-LOO counts, dynamic-vs-static comparison, timing/phase provenance, every falsification result, and the frozen verdict. No localization-performance statement is allowed before Stage 9.
