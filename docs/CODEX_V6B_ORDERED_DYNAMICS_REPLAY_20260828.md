# CODEX TASK — V6-B ordered-dynamics truth-blind replay

Date: 2026-08-28

Branch: `research/cg-pc-ctt-v6-dynamic-transport-sbi`

Normative science contract:
`docs/CG_PC_CTT_V6B_DYNAMIC_TRANSPORT_FACTOR_FREEZE_20260828.md`

Reference:
`experiments/cg_pc_ctt/v6b_dynamic_transport_reference.py`

Coverage runner:
`experiments/cg_pc_ctt/v6b_truthblind_dynamic_coverage.py`

## Objective

Determine, without using source truth or localization performance, whether preserving ordered within-stop transport dynamics repairs the cross-context source-transfer failure that remained after V6-A removed hard source components.

Do NOT implement C++ or Active Probe in this task.

Do NOT tune any threshold, feature weight, House-specific rule, seed-specific rule, timing lag, transport-member subset, or source prior from localization outcome.

## Stage 0 — sync and selftests

Pull the branch and record exact HEAD.

Run:

```bash
cd /home/zyc/uav-gsl-isj
python3 experiments/cg_pc_ctt/selftest_v4_final_reference.py
python3 experiments/cg_pc_ctt/selftest_v5_active_sequential_reference.py
python3 experiments/cg_pc_ctt/selftest_v6b_dynamic_transport_reference.py
python3 experiments/cg_pc_ctt/selftest_ctt_bank_io.py
```

All applicable tests must PASS. If the V5 file is absent on this branch, record that fact rather than copying it from another checkout.

## Stage 1 — prove the time-base mapping before scoring

This stage is blocking.

Recover from authoritative source/config/runtime provenance:

1. the CTT trace record-step simulator duration or cadence;
2. the PMFS completed-block cadence represented by consecutive `GAS HIT` / `NOTHING` decisions;
3. the relationship between the 200 CTT record steps and PMFS measurement-block time.

Do not infer this from outcome patterns.

Acceptable proof sources include:

- CTT builder/GADEN source code;
- frozen launch/config parameters;
- simulator timestamps recorded by the truth-free builder/runtime.

If

`block_cadence / ctt_record_step`

is an exact positive integer, freeze it as `lag_steps` and report the derivation.

If it is not exact, DO NOT ROUND. Instead adapt the truth-free materializer/builder so predicted occupancy is sampled or aggregated at the actual completed-block cadence, then set `lag_steps=1` on the already cadence-matched predicted tape.

If neither mapping can be established unambiguously, stop with:

`STOP_DYNAMIC_TIMING_UNRESOLVED`.

## Stage 2 — recover ordered observed stop tapes

Reuse the same 30 OFF development runs:

`/home/zyc/CG_PC_CTT_V3_ORR_MULTI30_20260827`

For every source-update context, recover exactly the completed block decisions already used by V4/V5 materialization, but retain order.

One physical stop must have:

`observed_tape[j] = [y1,...,y8]`, each `yb in {0,1}`.

Binding requirements:

- exactly 8 completed blocks per stop;
- no averaging before writing the dynamic context;
- stop ordering and context boundaries identical to the validated V4/V5 adapter;
- repeated blocks never become extra physical stops;
- preserve the raw block timestamps in a manifest for audit;
- do not load true source, final error, ON outcome, route-success label or plume-success proxy.

Prove for every stop:

`mean(observed_tape[j]) == old stop_r[j]`

to numerical equality with the existing V4/V5 NPZ. Any mismatch blocks the replay.

## Stage 3 — recover predicted ordered occupancy at only the actual stop cells

Use the frozen truth-free CTT V13 bank semantics.

The binary format already contains ordered `occupancyWords[T,...]`; do not reconstruct dynamics from the saved frequency alone.

For each context produce:

`sim_occupancy [S,8,J,T]` binary

at the same actual physical stop cells used by the validated V4/V5 context.

Stream banks exactly as in the earlier truth-blind materializer to avoid disk exhaustion. Full banks may be deleted after the dynamic payload/hash is written.

Before deleting a bank, verify:

- carrier manifest identity;
- 8 keyed members;
- `T=200` unless authoritative contract says otherwise;
- every selected stop cell is the same cell used by V4/V5;
- `mean_t sim_occupancy[s,m,j,:]` exactly reproduces the old `stop_probability[s,m,j]` for a regression sample and within binary floating precision for all contexts;
- transport-member key/hash identity is unchanged.

Required dynamic NPZ schema:

- `sim_occupancy [S,8,J,T]` binary;
- `observed_tape [J,8]` binary;
- `geometry_prior [S]`;
- `house`;
- `seed`;
- `update_id`;
- `context_id`;
- `timesteps`;
- `lag_steps`.

Forbidden keys include any truth/performance field.

## Stage 4 — run V6-B and matched static ablation

Run the dynamic coverage:

```bash
python3 experiments/cg_pc_ctt/v6b_truthblind_dynamic_coverage.py \
  /home/zyc/V6B_DYNAMIC_TRUTHBLIND_20260828/contexts \
  --out-json artifacts/v6b_dynamic/v6b_dynamic_coverage.json \
  --out-csv artifacts/v6b_dynamic/v6b_dynamic_folds.csv
```

The coverage script evaluates:

- ordered Markov transport evidence;
- context-specific member marginalization;
- leave-one-context-out source transfer;
- source-independent Jeffreys Markov absolute null;
- a matched frequency-only ablation from the exact same raw dynamic payload.

Do not alter formulas after seeing results.

## Stage 5 — mandatory falsification checks

Run and report all of the following:

1. candidate/source permutation invariance;
2. scoring-member permutation invariance within each context;
3. context permutation invariance of the final source posterior;
4. destroying transport-member identity inside a single context changes at least one non-degenerate synthetic fixture, proving the member test is live;
5. permuting the eight observed block order while keeping hit fraction fixed changes the dynamic score on at least one non-degenerate fixture;
6. the same permutation leaves the matched static frequency score unchanged;
7. duplicating a physical stop is rejected by the materializer or explicitly deduplicated before source evidence;
8. `lag_steps` comes only from Stage 1 timing proof;
9. no true-source coordinate or localization result is opened by the analysis process;
10. every dynamic absolute null is finite.

## Stage 6 — frozen decision

Use exactly the verdict generated by the coverage runner:

- `>=20/30` dynamic predictive pass and every House nonzero:
  `V6B_ORDERED_DYNAMICS_ACTIONABLE_FOR_RUNTIME_REFERENCE`;
- `10..19/30`:
  `V6B_PARTIAL_DYNAMIC_RECOVERY_NO_CPP_YET`;
- `<10/30`:
  `V6B_CTT_DYNAMIC_FAMILY_INSUFFICIENT_ESCALATE_TO_PHYSICS_FACTORIZED_SBI`.

If the last verdict occurs, STOP. Do not add slope, run-length, first-hit, autocorrelation, spectral or manually weighted feature patches after seeing V6-B outcomes. The next method is V6-C physics-factorized GADEN simulation-based inference.

## Deliverables

Commit:

- timing provenance report;
- ordered-observation materializer changes;
- ordered-occupancy extraction changes;
- dynamic NPZ manifest with SHA-256 and invalid/missing counts;
- `artifacts/v6b_dynamic/v6b_dynamic_coverage.json`;
- `artifacts/v6b_dynamic/v6b_dynamic_folds.csv`;
- `docs/V6B_DYNAMIC_TRANSPORT_REPORT_20260828.md`.

The report must include:

- exact branch HEAD;
- exact timing derivation;
- 30-run House breakdown;
- dynamic versus matched-static pass counts;
- all falsification results;
- the frozen verdict;
- no localization-performance claim.
