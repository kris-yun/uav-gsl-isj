# Step 2 ¡ª Fair Comparison (DQA-AS baselines required)

## Problem
`iter6_comparison.csv` compares against UniformPrior (no updates). This is not a real baseline.
`iter3_rerun_comparison.csv` shows MEMP_fixed loses to GreedyMAP/Infotaxis/Random.

## Task (single batch)

1. Update `workspace/uav_diagsense/scripts/run_small_eval.py` to include:
   - DQA-AS (original, standard posterior)
   - DQA-AS+MEMP
   - DQA-AS+BPFM
   - DQA-AS+SDM
   - GreedyMAP (reference baseline)
   - Infotaxis (reference baseline)
   - Random (lower bound)

2. Run 5 seeds on the same synthetic plume (deterministic).

3. Save results to:
   - `D:\ZYC\A-gas\automation\results\iter7_fair_comparison.csv`
   - `D:\ZYC\A-gas\automation\results\iter7_fair_summary.md`

4. Summary must include:
   - Table: method, median_final_error, median_best_error, vs DQA-AS delta
   - Honest verdict: which innovations beat DQA-AS, which dont
   - If none beat DQA-AS: suggest parameter tuning directions

5. Update `D:\ZYC\A-gas\automation\results\final_gate.md` with honest status.

Acceptance criteria:
- DQA-AS is in the comparison as baseline
- Results table shows delta vs DQA-AS
- final_gate.md reflects actual results (not premature PASS)
