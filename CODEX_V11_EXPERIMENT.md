# Codex direct instructions — ME-ACI V11 reversible cumulative

Repository: `kris-yun/uav-gsl-isj`
Branch: `meaci-v11-reversible-cumulative`
Base commit: `c7f665fce061e1ea766fe08c5c8cf36e6919a13d`

## 0. Do not modify V10 main evidence

Do not commit experimental V11 results onto `main` and do not overwrite the frozen V10 evidence package.  Work only on this branch or a child branch.

## 1. Pull and materialize the two-line semantic patch

```bash
git fetch origin
git checkout meaci-v11-reversible-cumulative
git reset --hard origin/meaci-v11-reversible-cumulative
python3 tools/apply_meaci_v11_reversible_patch.py
python3 reference/verify_meaci_v11_source.py
git diff -- ros2_package/src/gsl_server/algorithms/PMFS/internal/Simulations.cpp
```

The source diff must contain only the intended sequential-bookkeeping changes plus comments:

1. cumulative likelihood posterior uses `pcAciDesignPriorGrid`, not the previous causal posterior;
2. accepted events are retained in `meAciEvidenceReservoir`, not cleared.

Do not alter the 54-member inverse-transport family, gate, cadence, planner, evaluation metric, or any House-specific threshold.

## 2. Build isolated V11 binary

Use the same ROS2/GADEN overlay and build procedure as frozen V10.  Record:

- patched `Simulations.cpp` SHA-256;
- final binary SHA-256;
- all build flags and linked `libgaden.so` provenance.

Do not overwrite `artifacts/gsl_actionserver_node` from V10.

## 3. First run: H02 seed 824201 mechanism regression only

This seed is **development-only now** because its failure was inspected and used to design V11.

Run full 300 s V11 ON with all V10 runtime settings unchanged.  A matched OFF rerun is optional if the exact frozen OFF archive is already available and all provenance matches.

Required truth-blind structural evidence before reading truth:

- update 3 (or first identifiable update) can establish the causal posterior;
- later new events are appended to the retained history;
- update 4 recomputes candidate evidence on the larger history;
- posterior after update 4 is not copied byte-for-byte from update 3 merely because the new block is all miss;
- no new truth/distance/performance gate is introduced.

Export per update:

- cumulative event count;
- new-block event count if easy to derive in the runner;
- candidate conditional log evidence;
- posterior file hash;
- previous accepted posterior file hash;
- max absolute posterior change;
- PMFS top-5% error only in the external evaluator after the run.

If the posterior is still mechanically persistent after new all-miss evidence, stop and report `V11_REVERSIBILITY_IMPLEMENTATION_FAIL`.

If the posterior changes but H02 still has catastrophic final regression, report `V11_H02_COUNTEREXAMPLE_NO_GO`.  Do **not** tune gates, slopes, nuisance ranges, or planner parameters.

## 4. Freeze V11 candidate after H02 mechanism passes

Freeze source/binary/config hashes before any new qualification seed.

Suggested candidate contract name:

`MEACI_REVERSIBLE_CUMULATIVE_V1`

Suggested formula marker:

`inverse_transport_cumulative_reversible_v1`

## 5. Truth-blind full-300 qualification

Select genuinely new seeds not used in V10/V11 method design.

Minimum:

- H01: OFF vs V11 ON, 300 s;
- H02: OFF vs V11 ON, 300 s;
- H03: OFF vs V11 ON, 300 s.

Both arms must use the same map, seed, wind, GADEN, PMFS cadence, timeout and evaluator.  No first-accepted-update early stop.

Primary metric:

`ExpectedValue(sourceProbability, 0.05)` final localization error.

Predeclared minimum pass:

- at least 2/3 Houses improve;
- pooled improvement >= 10%;
- zero catastrophic regressions, where catastrophe remains the frozen criterion: >=1 m absolute regression and <=-25% relative improvement;
- no newly introduced false-confident wrong posterior collapse.

Do not change the method after seeing qualification truth.  If it fails, archive the failure.
