# 05 Direction 2: LP-PF (Learned Plume Particle Filter)

## Status: FAILED (experiment audit: data leakage, overfitting)

## Method
Replace Gaussian plume likelihood with a neural network surrogate trained
on synthetic plume data. The NN learns actual plume physics and provides
more accurate likelihood than the analytical Gaussian plume model.

Cross-domain: borrowed from groundwater PF + NN surrogate
(Hydrogeology Journal 2022, 27 citations)

## Novelty Check
S2 search: "learned plume" + "particle filter" + source localization = 0 papers
Closest: Groundwater PF + NN surrogate (different domain)

## Experiment Results (BEFORE AUDIT)

### Synthetic Data (5 scenarios × 10 seeds)
| Scenario | Gauss PF | LP-PF | Improvement |
|----------|----------|-------|-------------|
| Strong wind | 145.7m | 84.3m | **+42.1%** (10W/0L) |
| Medium wind | 103.0m | 78.8m | **+23.5%** (8W/2L) |
| Noisy | 106.8m | 81.0m | **+24.2%** (7W/3L) |
| Far source | 146.0m | 135.8m | +7.0% (6W/4L) |
| Weak wind | 84.1m | 91.1m | -8.3% (3W/7L) |
| **Overall** | — | — | **+17.7%** |

### MATRIX Real Data (9 trials)
- 7/9 wins, best: 225_01 (68.5m → 3.4m), 225_02 (67.2m → 3.6m)
- Weak-wind trials (314_01/02): mixed results

## EXPERIMENT AUDIT: FAIL

### Critical Issues Found

1. **Data leakage**: Training data (Gaussian plume variant A) and synthetic
   test data (Gaussian plume variant B) come from the SAME distribution family.
   NN learns "Gaussian plume shape" not general physics.

2. **+95% result is artifact**: Source at (172, -87) is OUTSIDE training domain
   (-100 to 100). NN extrapolation creates false precision, not real improvement.

3. **No theoretical basis**: NN trained on Gaussian plume CANNOT beat the
   analytical Gaussian plume formula. This is a mathematical impossibility.
   The "improvement" comes from NN's sharper gradients (numerical artifact),
   not better physics understanding.

4. **NN sharpness ≠ accuracy**: Sharher gradients = faster particle concentration
   ≠ correct localization. Could mean overconfident WRONG answers.

5. **Only 9 trials, no cross-validation**: Insufficient scope.

6. **No ablation modules**: Single monolithic method.

### Root Cause
The experiment design is fundamentally flawed. Training a NN on synthetic data
from a known model and then claiming it's "better than the model" is circular.
The NN can only be as good as the data it was trained on.

### Verdict: FAIL — results not trustworthy. Direction abandoned.

## Code Location
- `workspace/scripts/run_lppf_pilot.py` (v1)
- `workspace/scripts/run_lppf_v2.py` (v2, balanced training)
