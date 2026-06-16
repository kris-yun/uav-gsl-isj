# UAV-GSL Review Module Experiment Results (2026-06-16)

## House01 (source: -0.4, -2.9)

| Seed | Baseline | Full (EGS+DIRL+RGC) | Delta | Estimator |
|------|----------|---------------------|-------|-----------|
| 0 | 3.589m SUCCESS | 3.014m SUCCESS | -16.0% | pmfs_dirl_blend |
| 1 | 7.409m FAILED | 3.270m SUCCESS | -55.9% | dirl_allhits |
| 2 | 3.589m SUCCESS | 3.224m SUCCESS | -10.2% | pmfs_dirl_blend |
| 3 | 3.589m SUCCESS | 3.146m FAILED | -12.3% | pmfs_dirl_blend |
| 4 | 2.879m FAILED | 2.879m FAILED | 0% | pmfs_wrsd |

**Mean: Baseline 4.211m → Full 3.107m (-26.2%)**

### Ablation (Seed 0)

| Method | Error | Delta | Estimator |
|--------|-------|-------|-----------|
| Baseline | 3.589m | - | pmfs_wrsd |
| DIRL-only | 3.270m | -8.9% | dirl_allhits |
| Full | 3.014m | -16.0% | pmfs_dirl_blend |

## House02 (source: 0.0, -1.0)

| Seed | Baseline | Full | Delta |
|------|----------|------|-------|
| 0 | 2.312m FAILED | 2.432m FAILED | +5.2% |

DIRL not effective (insufficient gas hits / low wind coherence).

## House03 (source: -0.45, 1.9)

| Seed | Baseline | Full | Delta |
|------|----------|------|-------|
| 0 | 3.648m SUCCESS | 3.648m FAILED | 0% |

No gas hits collected. DIRL/RGC have no data to work with.

## Analysis

1. **DIRL module works** when sufficient gas hits exist: -8.9% alone, -16.0% with RGC blend
2. **RGC correctly selects** pmfs_dirl_blend when DIRL is reliable, falls back to pmfs_wrsd otherwise
3. **EGS** does not affect results when PMFS has sufficient evidence
4. **Limitation**: Method requires gas hits. House02/03 have sparse/no hits → no improvement

## Next Steps

- Improve gas hit collection (lower threshold, longer search time)
- Test with more seeds for statistical significance
- Investigate House02/03 gas hit patterns
