# CODEX HANDOFF — Mori–Zwanzig Gate M0

Date: 2026-09-24  
Branch: `research/mori-zwanzig-source-memory-v1`  
Status: **EXECUTE FROZEN M0 ONLY**

## Mission

Test whether finite-memory reduced dynamics are **load-bearing for source identity** under independent turbulent plume realizations.

This is not a request to build the final model.

Do not implement:

- LSTM / GRU / Transformer;
- GNN;
- MEMnets itself;
- PMFS closed loop;
- ROS navigation;
- Gate M1;
- any rescue experiment after seeing M0.

## Scientific parent

The mother theory is Mori–Zwanzig projection / generalized master-equation reduced dynamics.

Primary far-domain parent:
X. M. de Wit et al.,
“Data-driven Mori–Zwanzig modeling of Lagrangian particle dynamics in turbulent flows,”
PNAS 123(13), 2026,
DOI `10.1073/pnas.2525390123`.

Secondary parent:
B. Liu et al.,
“Memory kernel minimization-based neural networks for discovering slow collective variables of biomolecular dynamics,”
Nature Computational Science 5, 562–571, 2025,
DOI `10.1038/s43588-025-00815-8`.

The scientific hypothesis is **not** “history helps.”
It is that projecting unresolved turbulent degrees of freedom out of the plume state induces non-Markovian memory and orthogonal noise, and that the memory component may carry source-stable information across realizations.

## Frozen branch

Run:

```bash
cd <uav-gsl-isj repository>
git fetch origin
git checkout research/mori-zwanzig-source-memory-v1
git pull --ff-only
git status --short
git rev-parse HEAD
```

Require a clean worktree before scientific execution.

## Read before running

```bash
cat research/mori_zwanzig_source_memory_v1/MZ_MAINLINE_FREEZE_20260924.md
cat research/mori_zwanzig_source_memory_v1/MZ_GATE_M0_DENSE_HISTORY_FREEZE_20260924.md
```

Do not modify the scientific contract after this point.

## Frozen first knife

Parent geometry bank:
- 630 free PMFS support cells from independently reviewed Bi-Green Gate 1A.

M0 subset:
- exactly **180 arbitrary sources**;
- selected by deterministic geometry-only farthest-point sampling;
- exact expected selection/order is frozen in:
  `research/mori_zwanzig_source_memory_v1/MZ_M0_EXPECTED_FPS_ORDER_20260924.tsv`;
- selector may not read plume concentrations or source ranks.

Environment:
- House02;
- W2 = `3,5-1_slow`;
- same frozen occupancy, GADEN binary and physical parameters as Gate 1A;
- same 30 source-blind pooled probes;
- 0.5 s compact history output.

Independent M0 seeds:
- R1 = `2026092403`
- R2 = `2026092404`
- R3 = `2026092405`

Every selected source gets all three seeds.

Total dense realizations:
`180 × 3 = 540`.

Every seed is held out once:
- train/reference on the other two;
- all 180 held-out source histories act as unknown truths;
- each is ranked against all 180 candidate source models.

Total source-retrieval tests:
`180 × 3 = 540`.

## Matched comparison

Both arms use:

- identical dense histories;
- identical reference/held-out split;
- identical global reference-only PCA;
- identical source bank;
- identical scoring interval;
- ridge fitting;
- no target-rank-driven tuning.

Arm 0:
first-order Markov reduced dynamics.

Arm 1:
finite-memory reduced dynamics with globally selected memory order from the frozen grid.

A lower trajectory error by itself is **not enough**.

The memory arm must improve independent-realization **source retrieval** under the frozen PASS criteria.

## Syntax preflight

Run:

```bash
python3 -m py_compile   research/mori_zwanzig_source_memory_v1/select_mz_m0_sources.py   research/mori_zwanzig_source_memory_v1/extract_mz_m0_dense_history.py   research/mori_zwanzig_source_memory_v1/evaluate_mz_m0.py

bash -n research/mori_zwanzig_source_memory_v1/run_mz_m0_dense_history_vm.sh
bash -n research/mori_zwanzig_source_memory_v1/package_mz_m0_review.sh
```

If syntax fails, fix only the implementation bug, commit separately, and do not alter any scientific constant or gate.

## Execute

Run exactly:

```bash
bash research/mori_zwanzig_source_memory_v1/run_mz_m0_dense_history_vm.sh
```

Default output root:

`/home/zyc/mz_m0_dense_history_20260924`

The runner is resume-safe.

If interrupted, rerun the exact same command.

Do not delete valid completed compact histories.

## Important: exit code 10

The evaluator returns exit code 10 when the **scientific gate fails**.

That is a valid completed experiment, not an infrastructure error.

If these files exist and are internally valid:

- `evidence/mori_zwanzig_source_memory_v1/MZ_M0_RESULT_20260924.json`
- `evidence/mori_zwanzig_source_memory_v1/MZ_M0_ALL_TESTS_20260924.csv`

then read the `decision` field.

Possible frozen decisions:

`MZ_M0_PASS_MEMORY_IS_LOAD_BEARING`

or

`MZ_M0_FAIL_STOP_MEMORY_MAINLINE`.

Do not change thresholds after either result.

## Infrastructure-only repairs

An infrastructure-only patch is permitted only when execution cannot reach the frozen scientific computation.

Examples:
- path bug;
- extractor invocation bug;
- file-format bug;
- deterministic resume bug.

Not permitted:
- changing source subset;
- changing any RNG seed;
- changing W2;
- changing probe positions;
- changing cadence;
- changing PCA threshold/cap;
- changing memory-order grid;
- changing ridge grid;
- changing PASS criteria;
- changing scoring;
- adding another model because M0 looks bad.

Every infrastructure patch must:
1. be documented;
2. be committed separately before the evidence commit;
3. state whether any held-out rank had been observed before the patch.

## Frozen decision discipline

If:

`MZ_M0_FAIL_STOP_MEMORY_MAINLINE`

then STOP. Do not rescue with a nonlinear sequence model.

If:

`MZ_M0_PASS_MEMORY_IS_LOAD_BEARING`

then STOP as well. Do not start M1 until independent review.

## Commit evidence

After the completed result, including scientific FAIL:

```bash
git add evidence/mori_zwanzig_source_memory_v1/
git status --short
git commit -m "evidence: record Mori-Zwanzig Gate M0 result"
git push origin research/mori-zwanzig-source-memory-v1
```

If an infrastructure patch was required, that patch must already have its own earlier commit.

## Build independent review package

Run:

```bash
bash research/mori_zwanzig_source_memory_v1/package_mz_m0_review.sh
```

Expected archive:

`/home/zyc/MZ_M0_REVIEW_20260924.tar.gz`

The package intentionally contains all 540 compact histories so ChatGPT can independently recompute the gate without trusting the exported result JSON.

## Final report back

Return only:

1. branch;
2. final commit SHA;
3. decision;
4. source count;
5. total held-out retrieval tests;
6. selected memory order and seconds for each of the 3 folds;
7. Markov vs memory pooled top-1/top-3/top-10;
8. Markov vs memory pooled median truth rank;
9. Markov vs memory mean-log-rank metric;
10. Markov vs memory median true-model prediction error;
11. rank-improved fraction;
12. rank-worsened fraction;
13. every frozen PASS check true/false;
14. review package path;
15. package bytes;
16. package SHA-256;
17. any infrastructure-only patch commit SHA and reason.

Do not interpret or rescue the result.
