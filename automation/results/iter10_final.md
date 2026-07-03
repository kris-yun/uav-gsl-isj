# Iteration 9b: Combined Method vs Baselines

## Our Method: DQA-AS + MEMP + BPFM + FDPOE

- MEMP: Laplacian-smoothed posterior (LORETA-inspired spatial regularization)
- BPFM: Particle flow posterior (epidemiological back-tracing along wind)
- FDPOE: Fisher Information D-optimal scoring on action selection
- Composite posterior: 50% MEMP + 50% BPFM blend

## Setup
- Source: (-0.5, -3.0), Wind: [1.0, 0.3]
- Starts: 5 seeds, Grid: 414 cells, Res: 0.5m, Steps: 80

## Results (median across 5 seeds)

| # | Method | Final Err (m) | IQR | Best Err (m) | Δ vs DQA-AS |
|---|--------|--------------|-----|-------------|-------------|
| 1 |  **DQA-AS+MEMP+BPFM+FDPOE** | 4.00 [3.91,4.50] | 3.50 | +36.8% |
| 2 | Random | 5.02 [4.50,5.15] | 2.55 | +20.5% |
| 3 | KLD | 5.10 [5.10,5.15] | 2.92 | +19.4% |
| 4 | GreedyMAP | 5.15 [5.15,6.50] | 2.92 | +18.6% |
| 5 | Infotaxis | 5.52 [5.15,6.02] | 2.92 | +12.7% |
| 6 | DQA-AS | 6.32 [5.15,6.50] | 2.92 | --- |

## Per-Seed Breakdown (Our Method)

| Seed | Start | Final Err (m) |
|------|-------|--------------|
| 0 | (-5,-5) | 5.02 |
| 1 | (-3,-1) | 4.00 |
| 2 | (0,-5) | 2.83 |
| 3 | (-1,0) | 3.91 |
| 4 | (-4,-3) | 4.50 |

## Analysis

- **Our method median**: 4.00m (IQR [3.91, 4.50])
- **Beats 5/5 baselines**
- **vs DQA-AS**: +36.8%
- **vs Random**: 4.00m vs 5.02m (+20.4% better)
- **vs GreedyMAP**: 4.00m vs 5.15m (+22.3% better)
- **vs Infotaxis**: 4.00m vs 5.52m (+27.6% better)
- **vs KLD**: 4.00m vs 5.10m (+21.6% better)
- **vs DQA-AS**: 4.00m vs 6.32m (+36.8% better)

## Acceptance

- Final error: 4.00m >= 3.0m target
- Beats DQA-AS: YES
- Best method: YES