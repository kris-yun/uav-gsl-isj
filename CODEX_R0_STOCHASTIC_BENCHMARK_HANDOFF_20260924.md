# CODEX HANDOFF — R0 Stochastic Benchmark Refoundation

Date: 2026-09-24

Branch:
`research/stochastic-benchmark-refoundation-20260924`

Mission:
execute the frozen 18-source × 16-realization stochastic benchmark calibration.

This is **not** a PASI rescue and not a new localization algorithm.

## 1. Checkout

```bash
cd /path/to/uav-gsl-isj
git fetch origin
git checkout research/stochastic-benchmark-refoundation-20260924
git pull --ff-only
git status --short
git rev-parse HEAD
```

Require a clean worktree before execution.

## 2. Read before running

Read:

`research/stochastic_benchmark_refoundation/R0_PROTOCOL_FREEZE_20260924.md`

Do not alter:

- 18-source panel;
- 288 seed matrix;
- House02/W2;
- GADEN settings;
- probe operator;
- 10 times;
- 16 realizations/source;
- metrics;
- PASS/HOLD/STOP thresholds.

No neural model.
No source-localization score.
No PASI rerun.
No PMFS closed loop.

## 3. Syntax checks

```bash
python3 -m py_compile   research/stochastic_benchmark_refoundation/select_r0_panel.py   research/stochastic_benchmark_refoundation/pool_r0_cube.py   research/stochastic_benchmark_refoundation/analyze_r0_stability.py

bash -n research/stochastic_benchmark_refoundation/run_r0_multi_realization_vm.sh
bash -n research/stochastic_benchmark_refoundation/package_r0_review.sh
```

## 4. Execute

```bash
bash research/stochastic_benchmark_refoundation/run_r0_multi_realization_vm.sh
```

The runner must:

1. verify exact simulator/wind/occupancy/extractor contracts;
2. reproduce and verify the frozen 18-source panel;
3. verify 288 unique seeds;
4. generate exactly 16 new realizations per source;
5. preserve full 10×83×119 concentration cubes on VM;
6. create compact 10×30 pooled arrays;
7. compute R0 statistics;
8. produce exactly one frozen decision:
   - `R0_PASS_STOCHASTIC_BENCHMARK_USABLE`
   - `R0_HOLD_MORE_REALIZATIONS_REQUIRED`
   - `R0_STOP_PER_SOURCE_DISTRIBUTION_MAINLINE_UNSTABLE`

The analysis may exit:
- 0 = PASS
- 10 = HOLD
- 20 = STOP
- 30 = infrastructure/incomplete data stop

These are scientific/contract exits, not reasons to edit thresholds.

## 5. No post-result changes

After seeing R0:

Do not:
- change source panel;
- remove “bad” seeds;
- alter K;
- relax Spearman/convergence thresholds;
- choose another stochastic descriptor to convert HOLD/STOP into PASS.

If an infrastructure-only repair is unavoidable, commit it separately before scientific result generation and report it.

## 6. Commit result

After execution:

```bash
git add evidence/stochastic_benchmark_refoundation/r0/
git status --short
git commit -m "evidence: record R0 multi-realization stochastic benchmark"
git push origin research/stochastic-benchmark-refoundation-20260924
```

Do not modify frozen protocol/code after result generation.

## 7. Package for independent review

```bash
bash research/stochastic_benchmark_refoundation/package_r0_review.sh
```

Upload:

`/home/zyc/R0_STOCHASTIC_BENCHMARK_REVIEW_20260924.tar.gz`

The package intentionally contains all 288 compact pooled arrays plus manifests, but not hundreds of full concentration cubes. Full-cube hashes remain in the evidence inventory.

## 8. Report back only

1. branch;
2. final commit SHA;
3. R0 decision;
4. minimum split variability Spearman;
5. first8-vs-last8 variability Spearman;
6. odd8-vs-even8 variability Spearman;
7. minimum variability-tertile agreement;
8. K8→K16 median / q75 relative change;
9. K12→K16 median / q75 relative change;
10. legacy C/D vs R0-16 variability Spearman;
11. package path;
12. package bytes;
13. package SHA256;
14. any infrastructure-only patch.

Then stop. Do not start a new theory or closed loop.
