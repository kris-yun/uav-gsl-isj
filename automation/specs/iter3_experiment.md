# Iteration 3: Full Experiment - MEMP vs Baselines

## Objective
Run full comparison: MEMP vs DQA-AS vs baselines on House01.

## Step 1: Run Experiment

`ash
cd D:/ZYC/A-gas/workspace/uav_diagsense
python scripts/run_batch.py --method MEMP DQA_AS Random GreedyMAP Infotaxis KLD --seeds 0-4 --sensor ideal slow_mox --house House01
`

## Step 2: Review Results

Check automation/results/ for comparison CSV and summary.

## Step 3: Report Completion

When done, say:
Iteration 3 complete. Results saved to automation/results/

## Success Criteria
1. MEMP mean_error < DQA_AS mean_error on slow_mox
2. MEMP mean_error <= GreedyMAP mean_error on slow_mox
3. No crashes or errors
