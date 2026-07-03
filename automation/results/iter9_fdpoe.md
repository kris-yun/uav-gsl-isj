# Iteration 9: Full 5-Way Fair Comparison

## Setup
- Source: (-0.5, -3.0), Wind: [1.0, 0.3]
- Starts: 5 seeds
- Grid: 414 candidates, res=0.5m
- Max steps: 80

## Results (median across 5 seeds)

| Method | Final Err (m) | Best Err (m) | Median Err (m) | Δ vs DQA-AS |
|--------|--------------|-------------|----------------|-------------|
| DQA_AS | 6.32 [5.15,6.50] | 2.92 | 6.32 | --- |
| DQA_AS+MEMP | 3.81 [3.54,4.03] | 3.20 | 3.81 | +39.8% |
| DQA_AS+BPFM | 2.92 [1.12,4.30] | 2.92 | 3.61 | +53.9% |
| DQA_AS+SDM | 6.02 [5.41,6.50] | 4.27 | 6.02 | +4.8% |
| DQA_AS+FDPOE | 5.39 [5.10,6.50] | 2.92 | 5.59 | +14.9% |

## Analysis

- **DQA_AS+MEMP vs DQA-AS**: 3.81m vs 6.32m (+39.8%, PASS)
- **DQA_AS+BPFM vs DQA-AS**: 2.92m vs 6.32m (+53.9%, PASS)
- **DQA_AS+SDM vs DQA-AS**: 6.02m vs 6.32m (+4.8%, PASS)
- **DQA_AS+FDPOE vs DQA-AS**: 5.39m vs 6.32m (+14.9%, PASS)

## Acceptance Criteria

- [x] FIM is positive semi-definite (verified by test_fdpoe.py)
- [x] Fisher score distinguishes informative vs uninformative actions
- [x] No dataset-specific tuning (lam_F=0.3, no calibration)

## Ranking

1. **DQA_AS+BPFM**: 2.92m
2. **DQA_AS+MEMP**: 3.81m
3. **DQA_AS+FDPOE**: 5.39m
4. **DQA_AS+SDM**: 6.02m
5. **DQA_AS**: 6.32m