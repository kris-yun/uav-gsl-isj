# Step 1A ¡ª Fix MEMP and rerun a small stable experiment

Context:
- Iteration 3 results show MEMP performs same as DQA_AS.
- Root cause candidate: `workspace/uav_diagsense/src/memp/memp_planner.py` uses `last.get("hit", False)`, so MEMP estimator only receives miss updates.
- Also current GADEN run is unstable and only 1 seed/start position used.

Goal:
- Fix MEMP signal integration.
- Re-run a small reproducible experiment with more than 1 seed if possible.
- Save evidence under `D:\ZYC\A-gas\automation\results`.

Do in small batches only.

---

## Batch 1 (code fix only)
1. Update `workspace/uav_diagsense/src/memp/memp_planner.py`
2. Replace unreliable `last.get("hit", False)` with explicit gas signal:
   - `hit = float(last.get("gas", 0.0)) > 0.01`
3. Keep changes minimal.
4. Save file.

## Batch 2 (unit/integration sanity)
1. Run existing memp tests.
2. Add one more integration test that verifies MEMP posterior changes when `gas>0.01`.
3. Save test file under `workspace/uav_diagsense/tests/test_memp_signal.py`.
4. Run tests until green.

## Batch 3 (small deterministic rerun)
1. Rerun experiment with at least 3 seeds if system allows.
2. If GADEN is still unstable, create a lightweight deterministic fallback runner:
   - file: `workspace/uav_diagsense/scripts/run_small_eval.py`
   - compare methods: MEMP, DQA_AS, GreedyMAP, Random
3. Save results to:
   - `D:\ZYC\A-gas\automation\results\iter3_rerun_summary.md`
   - `D:\ZYC\A-gas\automation\results\iter3_rerun_comparison.csv`

## Batch 4 (summary only)
1. Write concise summary:
   - what changed
   - why it should help
   - result comparison table
   - next step recommendation
2. Save to `D:\ZYC\A-gas\automation\results\iter3_rerun_summary.md`

Acceptance criteria:
- `workspace/uav_diagsense/src/memp/memp_planner.py` no longer depends on missing `hit` key.
- tests pass.
- rerun summary exists and contains MEMP vs baselines comparison.
